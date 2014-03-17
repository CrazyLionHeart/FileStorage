#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

try:
    from .JsonApp import make_json_app
    from celery.result import AsyncResult
    from .tasks import storage_list, storage_get, storage_put, storage_delete
    from .tasks import storage_info
    import json

    from base64 import b64decode

    import logging
    from logging.config import dictConfig

    from flask import jsonify, request, Response, make_response, current_app
    from flask import url_for
    from datetime import timedelta
    from functools import update_wrapper

    from os import environ
except Exception, e:
    raise e

current_env = environ.get("APPLICATION_ENV", 'development')
basePath = environ.get("basePath", './')

with open('%s/config/%s/config.%s.json' %
          (basePath, current_env, current_env)) as f:
    config = json.load(f)
    dictConfig(config['loggingconfig'])

logger = logging.getLogger('file_storage')


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

app = make_json_app(__name__)


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

    app.logger.debug(u"База даных: %s" % database)
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

        logger.debug(metadata)
        logger.debug(file)
        logger.debug(content_type)

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

    result = AsyncResult(task_id)
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

    result = AsyncResult(task_id)
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
