#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from .Storage import Storage

    import logging

    from celery import Celery
except ImportError, e:
    raise e

celery = Celery()
celery.config_from_object('celeryconfig')

logging.basicConfig(level=logging.DEBUG,
                    format=u'''%(filename)s[LINE:%(lineno)d]# %(levelname)-8s
                    [%(asctime)s]  %(message)s''')


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
    celery.start()
