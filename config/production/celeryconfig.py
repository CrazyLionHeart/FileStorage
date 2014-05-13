#!/usr/bin/env python
# -*- coding: utf-8 -*-

BROKER_URL = 'redis://192.168.1.213/0'
CELERY_RESULT_BACKEND = 'redis://192.168.1.213/0'
CELERY_IMPORTS = ("FileStorage.tasks", )
CELERY_TASK_RESULT_EXPIRES = 300
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_ENABLE_UTC = True
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_ACCEPT_CONTENT = [
    'pickle', 'json', 'msgpack', 'yaml'
]
CELERY_CACHE_BACKEND_OPTIONS = {
    'binary': True,
    'behaviors': {
        'tcp_nodelay': True
    }
}
BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'fanout_prefix': True,
    'fanout_patterns': True
}

# Name and email addresses of recipients
ADMINS = (
    ("Administrators", "it_babypages_K52@babypages.ru"),
)

# Email address used as sender (From field).
SERVER_EMAIL = "robot@babypages.ru"

# Mailserver configuration
EMAIL_HOST = "localhost"
EMAIL_PORT = 25
