"""Celery task definition for scope_core app"""
from __future__ import absolute_import, unicode_literals

from celery.utils.log import get_task_logger
from django_celery_beat.models import PeriodicTask, PeriodicTasks, IntervalSchedule
from django.core.cache import cache
from scopy.celery import app
from scope_core.core import job_control

LOGGER = get_task_logger(__name__)
P_PRIOR_HIGH = 60
P_PRIOR_MID = 90
P_PRIOR_LOW = 120
LOCK_EXPIRE = 60
LOCK_ID = "shared-lock"

def init_tasks():
    """Initialize schedules and tasks
    1) Define prioritized schedules
    2) Create tasks
    3) Poll device status on system startup to initialize environment
    """
    schedule_high, created_high = IntervalSchedule.objects.get_or_create(
        every=P_PRIOR_HIGH,
        period=IntervalSchedule.SECONDS,
    )
    schedule_low, created_low = IntervalSchedule.objects.get_or_create(
        every=P_PRIOR_LOW,
        period=IntervalSchedule.SECONDS,
    )
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=P_PRIOR_MID,
        period=IntervalSchedule.SECONDS,
    )
    PeriodicTask.objects.get_or_create(
        interval=schedule_high,
        name='Polling device status',
        task='scope_core.tasks.poll_status_task',
    )
    PeriodicTask.objects.get_or_create(
        interval=schedule_low,
        name='Polling alarm status',
        task='scope_core.tasks.poll_alarm_task',
    )
    metric_task = PeriodicTask.objects.get_or_create(
        name='Polling production metrics',
        task='scope_core.tasks.poll_metrics_task',
    )
    metric_task[0].interval_id = schedule.id
    metric_task[0].save()
    PeriodicTask.objects.all().update(last_run_at=None)
    poll_status_task.delay()

@app.task
def poll_status_task():
    """Task to poll device status"""
    global LOCK_ID
    global LOGGER
    LOCK_ID = '{0}-lock'.format('statustask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        LOGGER.info("Polling device status (p={})...".format(P_PRIOR_HIGH))
        try:
            job_control.poll_device_status()
        finally:
            release_lock()
    else:
        LOGGER.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))

@app.task
def poll_alarm_task():
    """Task to poll alarm status"""
    global LOCK_ID
    global LOGGER
    LOCK_ID = '{0}-lock'.format('alarmtask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        LOGGER.info("Polling alarm status (p={})...".format(P_PRIOR_LOW))
        try:
            job_control.poll_alarm_status()
        finally:
            release_lock()
    else:
        LOGGER.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))

@app.task
def poll_metrics_task():
    """Task to poll production metrics"""
    global LOCK_ID
    global LOGGER
    LOCK_ID = '{0}-lock'.format('infotask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        pTask = PeriodicTask.objects.filter(task='scope_core.tasks.poll_metrics_task')[0]
        LOGGER.info("Polling production data (p={})...".format(pTask.interval.every))
        try:
            job_control.poll_prod_status()
        finally:
            release_lock()
    else:
        LOGGER.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))
