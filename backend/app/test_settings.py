from .settings import *
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None
MIGRATION_MODULES = DisableMigrations()
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
DEBUG = False
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
import logging
logging.disable(logging.CRITICAL)
