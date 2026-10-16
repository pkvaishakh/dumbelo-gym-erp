"""Celery for the jobs that aren't part of a request: today's reminder list, and more later.

With no `CELERY_BROKER_URL` set, tasks run in the process that calls them (see `CELERY_TASK_ALWAYS_EAGER` in
settings), so the tests and a laptop without Redis behave the same as a server with a worker.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("rackline")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
