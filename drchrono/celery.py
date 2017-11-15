from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

from .tasks import task_debug


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drchrono.settings')

app = Celery('proj')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    #sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    sender.add_periodic_task(10.0, task_debug.s(), name='tasts_py_debug')
