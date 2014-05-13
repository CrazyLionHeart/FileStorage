#!/usr/bin/env python
# -*- coding: utf-8 -*-

from FileStorage.config import config

gunicorn = config['gunicorn']

bind = '%s:%s' % (gunicorn["hostname"],
                  int(gunicorn["port"]))
workers = int(gunicorn["workers"])
worker_class = gunicorn["worker_class"]
worker_connections = int(gunicorn["worker_connections"])
timeout = int(gunicorn["timeout"])
keepalive = int(gunicorn["keepalive"])
