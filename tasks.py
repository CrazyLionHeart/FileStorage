#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from FileStorage.Storage import Storage
    from FileStorage.config import config

    import logging
    from celery import Celery

except ImportError, e:
    raise e

celery = Celery()
celery.config_from_object(
    'FileStorage.config.%s.celeryconfig' % config["APPLICATION_ENV"])


@celery.task
def hello():
    return 'hello world'


@celery.task
def add(x, y):
    return x + y


@celery.task
def storage_list(db, current_page, rows, sidx, sord):
    logging.debug(u"База данных: %s" % db)
    result = Storage(db=db).list(current_page, rows, sidx, sord)
    logging.info(u"Получаем список файлов: %s" % result)
    return result


@celery.task
def storage_get(filename, db):
    logging.debug(u"База данных: %s" % db)
    logging.info(u"Получаем файл: %s" % filename)
    return Storage(db=db).get(filename)


@celery.task
def storage_put(file, content_type='application/octet-stream', metadata=None,
                db=None):
    logging.debug(u"База данных: %s" % db)
    logging.info(u"Кладем файл")
    return Storage(db=db).put(file, content_type, metadata)


@celery.task
def storage_delete(filename, db):
    logging.debug(u"База данных: %s" % db)
    logging.info(u"Удаляем файл: %s" % filename)
    return Storage(db=db).delete(filename)


@celery.task
def storage_info(filename, db):
    logging.debug(u"База данных: %s" % db)
    logging.info(u"Получаем информацию по файлу: %s" % filename)
    return Storage(db=db).info(filename)

if __name__ == "__main__":
    celery.worker_main()
