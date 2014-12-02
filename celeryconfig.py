from celery.schedules import crontab

## Broker settings.
BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'

# List of modules to import when celery starts.
#CELERY_IMPORTS = ('app.tasks', )

## Using the database to store task state and results.
CELERY_RESULT_BACKEND = 'db+sqlite:///results.db'

#CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '1/s'}}

CELERY_TASK_SERIALIZER='json',
CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
CELERY_RESULT_SERIALIZER='json',
CELERY_TIMEZONE='Europe/Paris',
CELERY_ENABLE_UTC=True,

CELERYBEAT_SCHEDULE = {
    'every-minute': {
        'task': 'app.tasks.add',
        'schedule': crontab(minute='*/1'),
        'args': (12, 16)
    },
},
