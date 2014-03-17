#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

try:
    from Storage import Storage

    import logging
    from logging.config import dictConfig

    from os import environ
    import json

    from celery import Celery
    import celeryconfig
except Exception, e:
    raise e

celery = Celery()
celery.config_from_object(celeryconfig)

current_env = environ.get("APPLICATION_ENV", 'development')

with open('../../config/%s/config.%s.json' % (current_env, current_env)) as f:
    config = json.load(f)
    dictConfig(config['loggingconfig'])

logger = logging.getLogger('celery')


@celery.task
def hello():
    return 'hello world'


@celery.task
def add(x, y):
    return x + y


@celery.task
def storage_list(db, current_page, rows, sidx, sord):
    logger.debug(u"База данных: %s" % db)
    result = Storage(db=db).list(current_page, rows, sidx, sord)
    logger.info(u"Получаем список файлов: %s" % result)
    return result


@celery.task
def storage_get(filename, db):
    logger.debug(u"База данных: %s" % db)
    logger.info(u"Получаем файл: %s" % filename)
    return Storage(db=db).get(filename)


@celery.task
def storage_put(file, content_type='application/octet-stream', metadata=None,
                db=None):
    logger.debug(u"База данных: %s" % db)
    logger.info(u"Кладем файл")
    return Storage(db=db).put(file, content_type, metadata)


@celery.task
def storage_delete(filename, db):
    logger.debug(u"База данных: %s" % db)
    logger.info(u"Удаляем файл: %s" % filename)
    return Storage(db=db).delete(filename)


@celery.task
def storage_info(filename, db):
    logger.debug(u"База данных: %s" % db)
    logger.info(u"Получаем информацию по файлу: %s" % filename)
    return Storage(db=db).info(filename)

if __name__ == "__main__":
    celery.start()
