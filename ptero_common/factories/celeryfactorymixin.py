import abc


class CeleryFactoryMixin(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, celery_app=None):
        self.celery_app = celery_app

    @abc.abstractmethod
    def _initialize_celery(self):
        pass
