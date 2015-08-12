import celery
import os

def celery_app(main, task_path, routes, broker_url=None, track_started=False):
    app = celery.Celery(main, include=task_path)

    app.conf['CELERY_ROUTES'] = routes

    if broker_url is not None:
        app.conf['BROKER_URL'] = broker_url
    else:
        app.conf['BROKER_URL'] = os.environ['CELERY_BROKER_URL']

    _DEFAULT_CELERY_CONFIG = {
        'CELERY_RESULT_BACKEND': 'redis://localhost',
        'CELERY_ACCEPT_CONTENT': ['json'],
        'CELERY_ACKS_LATE': True,
        'CELERY_RESULT_SERIALIZER': 'json',
        'CELERY_TASK_SERIALIZER': 'json',
        'CELERY_TRACK_STARTED': track_started,
        'CELERYD_PREFETCH_MULTIPLIER': 10,
    }
    for var, default in _DEFAULT_CELERY_CONFIG.iteritems():
        if var in os.environ:
            app.conf[var] = os.environ[var]
        else:
            app.conf[var] = default

    return app
