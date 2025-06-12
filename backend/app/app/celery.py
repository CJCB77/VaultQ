import os
from celery import Celery

# Set the default django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

app = Celery('app')

# pull in config from Django's settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# auto-discover task modules in each installed app
app.autodiscover_tasks()