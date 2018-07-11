"""Model managers."""
from __future__ import absolute_import, unicode_literals

import warnings
from functools import wraps
from itertools import count
from typing import Union

from celery.result import AsyncResult
from celery.states import READY_STATES, PROPAGATE_STATES, SUCCESS, UNREADY_STATES
from django.conf import settings
from django.db import connections, router, transaction
from django.db import models
from django.db.models import F, Q, Value

from .task_utils import precedence_propagating_exceptions, precedence_non_propagating_exceptions, \
    revoke_task
from .utils import now

try:
    from celery.utils.time import maybe_timedelta
except ImportError:  # pragma: no cover
    from celery.utils.timeutils import maybe_timedelta  # noqa

W_ISOLATION_REP = """
Polling results with transaction isolation level 'repeatable-read'
within the same transaction may give outdated results.

Be sure to commit the transaction for each poll iteration.
"""


class TxIsolationWarning(UserWarning):
    """Warning emitted if the transaction isolation level is suboptimal."""


def transaction_retry(max_retries=1):
    """Decorator to retry database operations.

    For functions doing database operations, adding
    retrying if the operation fails.

    Keyword Arguments:
        max_retries (int): Maximum number of retries.  Default one retry.
    """

    def _outer(fun):

        @wraps(fun)
        def _inner(*args, **kwargs):
            _max_retries = kwargs.pop('exception_retry_count', max_retries)
            for retries in count(0):
                try:
                    return fun(*args, **kwargs)
                except Exception:  # pragma: no cover
                    # Depending on the database backend used we can experience
                    # various exceptions. E.g. psycopg2 raises an exception
                    # if some operation breaks the transaction, so saving
                    # the task result won't be possible until we rollback
                    # the transaction.
                    if retries >= _max_retries:
                        raise

        return _inner

    return _outer


class TaskManager(models.Manager):
    _last_id = None

    EXCLUDE_FROM_TRACKING = {
        'celery.chord_unlock',
        'advanced_celery.track_tasks',
        'advanced_celery.track_session_completed',
        'advanced_celery.update_main_task',
        'advanced_celery.clean_dead_tasks',
        'advanced_celery.clean_tasks',
        'advanced_celery.end_chord'
    }

    def get_task(self, task_id):
        """Get result for task by ``task_id``.

        Keyword Arguments:
            exception_retry_count (int): How many times to retry by
                transaction rollback on exception.  This could
                happen in a race condition if another worker is trying to
                create the same task.  The default is to retry once.
        """
        try:
            return self.get(id=task_id)
        except self.model.DoesNotExist:
            if self._last_id == task_id:
                self.warn_if_repeatable_read()
            self._last_id = task_id
            return self.model(id=task_id)

    @transaction_retry(max_retries=2)
    def init_task(self, task_id: str, task_name: str, root_id: str, description: str = None):
        try:
            main_task = self.get(id=root_id) if root_id and root_id != task_id else None
        except:
            print('Bad sub-task: task_id={0}, root_id={1}, task_name={2}'.format(task_id,
                                                                                 root_id,
                                                                                 task_name))
            raise

        if description and len(description) > 1020:
            description = description[:1020]

        obj, created = self.get_or_create(id=task_id, defaults={
            'name': task_name,
            'description': description,
            'main_task_id': main_task.id if main_task else None,
            'date_start': now()})
        if not created:
            obj.name = task_name
            obj.description = description
            obj.main_task_id = main_task.id if main_task else None
            obj.date_done = None
            obj.save()

        return obj

    @transaction_retry(max_retries=2)
    def update_progress(self,
                        task_id,
                        progress: int):
        task = self.get(id=task_id)

        if task.is_sub_task():
            self.filter(id=task_id).update(own_progress=progress, progress=progress)
        else:
            self.filter(id=task_id).update(own_progress=progress)

    @transaction_retry(max_retries=2)
    def increase_progress(self,
                          task_id,
                          progress_increase: int):
        task = self.get(id=task_id)

        if task.is_sub_task():  # this is a sub-task
            self.filter(id=task_id).update(
                own_progress=F('own_progress') + progress_increase,
                progress=F('progress') + progress_increase)
        else:
            self.filter(id=task_id).update(
                own_progress=F('own_progress') + progress_increase)

    @transaction_retry(max_retries=2)
    def set_push_steps(self, task_id, push_steps: int):
        self.filter(id=task_id).update(push_steps=push_steps)

    @transaction_retry(max_retries=2)
    def set_log_extra(self, task_id, log_extra):
        self.filter(id=task_id).update(log_extra=log_extra)

    @transaction_retry(max_retries=2)
    def set_failure_processed(self, task_id, v: bool):
        self.filter(id=task_id).update(failure_processed=v)

    @transaction_retry(max_retries=2)
    def push(self, task_id):
        task = self.get(id=task_id)

        if task.is_sub_task():
            self.filter(id=task_id).update(
                own_progress=F('own_progress') + Value(100) / F('push_steps'),
                progress=F('progress') + Value(100) / F('push_steps'))
        else:
            self.filter(id=task_id).update(
                own_progress=F('own_progress') + Value(100) / F('push_steps'))

    def main_tasks(self):
        return self.filter(Q(main_task__isnull=True) | Q(main_task_id=F('id'))) \
            .exclude(name__in=self.EXCLUDE_FROM_TRACKING)

    def unready_main_tasks(self):
        return self.main_tasks().filter(status__in=UNREADY_STATES)

    def update_main_task(self, main_task_id: str):
        all_task_info_rows = self.filter(
            Q(id=main_task_id) | Q(main_task_id=main_task_id)) \
            .exclude(name__in=self.EXCLUDE_FROM_TRACKING) \
            .values_list('propagate_exceptions', 'own_status', 'own_progress', 'own_date_done')

        total_status_non_propagating_exceptions = None
        total_status_propagating_exceptions = None
        found_propagating_exceptions = False
        total_progress = 0
        total_done = True
        total_date_done = None
        for propagate_exceptions, status, progress, date_done in all_task_info_rows:
            if propagate_exceptions:
                found_propagating_exceptions = True
                total_status_propagating_exceptions = status \
                    if total_status_propagating_exceptions is None \
                    else max(total_status_propagating_exceptions,
                             status,
                             key=precedence_propagating_exceptions)
            else:
                total_status_non_propagating_exceptions = status \
                    if total_status_non_propagating_exceptions is None \
                    else max(total_status_non_propagating_exceptions,
                             status,
                             key=precedence_non_propagating_exceptions)

            if progress is None:
                progress = 0
            if status in READY_STATES:
                progress = 100

            total_progress += progress

            # if there is at least one date_done = None then we are not done
            if date_done is None:
                total_done = False

            # if we still did not got any date_done = None (meaning we are done)
            # then calc total date done as the max date done we got
            if total_done:
                total_date_done = max(total_date_done, date_done) if total_date_done else date_done
            else:
                total_date_done = None

        total_progress = (total_progress / len(all_task_info_rows)) if len(
            all_task_info_rows) else 100

        if total_status_propagating_exceptions in PROPAGATE_STATES:
            # we have error in an important sub-task
            total_status = total_status_propagating_exceptions
        elif found_propagating_exceptions:
            # we don't have errors in important sub-tasks
            # but there were important sub-tasks and we should take their statuses into account
            # (this is mostly to take care of None state in total_status_propagating_exceptions
            # meaning PENDING)
            total_status = max(total_status_propagating_exceptions,
                               total_status_non_propagating_exceptions,
                               key=precedence_non_propagating_exceptions)
        else:
            # we did not see any important sub-tasks and should not take into account
            # None in total_status_propagating_exceptions
            total_status = total_status_non_propagating_exceptions

        self.filter(id=main_task_id).update(date_done=total_date_done,
                                            status=total_status,
                                            progress=total_progress)

        if total_status_propagating_exceptions in PROPAGATE_STATES:
            revoke_task(AsyncResult(main_task_id))

    @transaction_retry(max_retries=2)
    def store_result(self,
                     task_id: str,
                     main_task_id: str,
                     task_name: str,
                     result,
                     status: str,
                     traceback=None, metadata=None):
        date_now = now()

        initial_values = {
            'name': task_name,
            'main_task_id': main_task_id,
            'own_status': status,
            'date_start': date_now,
            'own_date_done': date_now if status in READY_STATES else None,
            'result': result,
            'traceback': traceback,
            'celery_metadata': metadata,
        }

        if initial_values['own_status'] == SUCCESS:
            initial_values['own_progress'] = 100

        if main_task_id and main_task_id != task_id:  # this is a sub-task
            initial_values['status'] = initial_values.get('own_status')
            initial_values['date_done'] = initial_values.get('own_date_done')
            initial_values['progress'] = initial_values.get('own_progress')

        obj, created = self.get_or_create(id=task_id, defaults=initial_values)

        if not created:
            if task_name and not obj.name:
                obj.name = task_name

            # Main task id should be assigned in init_task or on initial store result.
            # If the task is already initialized with main_task_id = None - here it can be rewritten
            # with some value by Celery itself.

            obj.own_status = status

            if obj.own_date_done is None:
                obj.own_date_done = now() if status in READY_STATES else None

            if obj.own_status == SUCCESS:
                obj.own_progress = 100

            obj.result = result
            obj.traceback = traceback
            obj.celery_metadata = metadata

            if obj.is_sub_task():
                obj.status = obj.own_status
                obj.date_done = obj.own_date_done
                obj.progress = obj.own_progress

            obj.save()

        return obj

    def warn_if_repeatable_read(self):
        # copy-pasted from django-celery-results
        if 'mysql' in self.current_engine().lower():
            cursor = self.connection_for_read().cursor()
            if cursor.execute('SELECT @@tx_isolation'):
                isolation = cursor.fetchone()[0]
                if isolation == 'REPEATABLE-READ':
                    warnings.warn(TxIsolationWarning(W_ISOLATION_REP.strip()))

    def connection_for_write(self):
        return connections[router.db_for_write(self.model)]

    def connection_for_read(self):
        return connections[self.db]

    def current_engine(self):
        try:
            return settings.DATABASES[self.db]['ENGINE']
        except AttributeError:
            return settings.DATABASE_ENGINE

    def get_all_expired(self, expires):
        """Get all expired task results."""
        return self.filter(own_date_done__lt=now() - maybe_timedelta(expires))

    def delete_expired(self, expires):
        """Delete all expired results."""
        meta = self.model._meta
        with transaction.atomic():
            self.get_all_expired(expires).update(hidden=True)
            cursor = self.connection_for_write().cursor()
            cursor.execute(
                'DELETE FROM {0.db_table} WHERE hidden=%s'.format(meta),
                (True,),
            )