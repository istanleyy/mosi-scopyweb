from __future__ import absolute_import, unicode_literals

# Ensure app is always imported when Django starts.
# shared_task will use this app.
from .celery import app as celery_app

__all__ = ['celery_app']
