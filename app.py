#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from gevent import monkey
    monkey.patch_all()

    from FileStorage.tasks import storage_list, storage_get, storage_put
    from FileStorage.tasks import storage_info, storage_delete, celery

    from base64 import b64decode

    import logging

    from raven.contrib.flask import Sentry

    from flask import jsonify, request, url_for, Response

    from FileStorage.JsonApp import make_json_app, crossdomain
    from FileStorage.config import config

except Exception, e:
    raise e

dsn = "http://%s:%s@%s" % (config['Raven']['public'],
                           config['Raven']['private'],
                           config['Raven']['host'])

app = make_json_app(__name__)

app.config['SENTRY_DSN'] = dsn
sentry = Sentry(app)


@app.route('/')
@crossdomain(origin='*')
def example():
    """Помощь по API"""

    import urllib
    links = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            options = {}
            for arg in rule.arguments:
                options[arg] = "[{0}]".format(arg)

            methods = ','.join(rule.methods)

            url = url_for(rule.endpoint, **options)
            docstring = app.view_functions[rule.endpoint].__doc__
            links.append(dict(methods=methods, url=urllib.unquote(url),
                         docstring=docstring))

    return jsonify(results=links)


@app.route('/files/<database>', methods=['GET'])
@crossdomain(origin='*')
def list(database):
    """Получаем список файлов в базе данных"""

    page = int(request.args.get('page', 1))
    rows = int(request.args.get('rows', 30))
    sidx = request.args.get("sidx", None)
    sord = request.args.get("sord", None)

    logging.debug(u"База даных: %s" % database)
    res = storage_list.apply_async((database, page, rows, sidx, sord))
    result = "/status/%s/%s" % ('storage_list', res.task_id)

    return jsonify(results=result)


@app.route('/files/<database>', methods=['PUT', 'POST'])
@crossdomain(origin='*')
def upload(database):
    """Загружаем файл в базу данных"""

    if request.method == 'POST':
        fileObject = request.files.get('file')
        metadata = request.form.get('metadata')

        if fileObject:
            file = fileObject.read()
            content_type = fileObject.mimetype
        else:
            file = request.form.get('file')
            content_type = request.form.get('content_type')

        logging.debug(metadata)
        logging.debug(file)
        logging.debug(content_type)

        if content_type:
            if content_type == 'dataURL':
                file = b64decode(file.split(',')[1])
                content_type = 'image/png'

        if file:
            res = storage_put.apply_async((file, content_type, metadata,
                                          database))
            result = "/status/%s/%s" % ('storage_put', res.task_id)
            return jsonify(results=result)
        else:
            raise Exception("Нет файлов для добавления")

    elif request.method == 'PUT':
        file = request.data
        metadata = None
        content_type = request.content_type

        res = storage_put.apply_async((file, content_type, metadata, database))
        result = "/status/%s/%s" % ('storage_put', res.task_id)

        return jsonify(results=result)


@app.route('/info/<database>/<file_name>', methods=['GET'])
@crossdomain(origin='*')
def info(database, file_name):
    """Получаем информацию по файлу из базы данных"""

    res = storage_info.apply_async((file_name, database))
    result = "/status/%s/%s" % ('storage_info', res.task_id)
    return jsonify(results=result)


@app.route('/file/<database>/<file_name>', methods=['GET'])
@crossdomain(origin='*')
def get(database, file_name):
    """Получаем файл из базы данных"""

    res = storage_get.apply_async((file_name, database))
    result = "/status/%s/%s" % ('storage_get', res.task_id)
    return jsonify(results=result)


@app.route('/file/<database>/<file_name>', methods=['DELETE'])
@crossdomain(origin='*')
def remove(database, file_name):
    """Удаляем файл из базы данных"""

    res = storage_delete.apply_async((file_name, database))
    result = "/status/%s/%s" % ('storage_delete', res.task_id)
    return jsonify(results=result)


@crossdomain(origin='*')
@app.route("/status/<task_name>/<task_id>", methods=['GET'])
def get_status(task_name, task_id):
    """Получаем результат асинхронной работы из Celery"""

    result = celery.AsyncResult(task_id)
    if result:
        retval = "/result/%s/%s" % (task_name, task_id)
        return jsonify(results=retval, state=result.state)
    else:
        raise Exception(u"""Не могу получить результат: функцию либо не
                        вызывали, либо результат протух""")


@crossdomain(origin='*')
@app.route("/result/<task_name>/<task_id>", methods=['GET'])
def get_result(task_name, task_id):
    """Получаем результат асинхронной работы из Celery"""

    result = celery.AsyncResult(task_id)
    if result:
        if result.ready():
            retval = result.get()
            if task_name == 'storage_get':
                return Response(retval['content'], direct_passthrough=True,
                                mimetype=retval['content_type'])
            else:
                return jsonify(results=retval, state=result.state)
    else:
        raise Exception(u"""Не могу получить результат: функцию либо не
                        вызывали, либо результат протух""")
