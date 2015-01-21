#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from base64 import b64decode

    import math
    import json
    import re
    import io
    import mimetypes
    import magic

    from raven.contrib.flask import Sentry
    from raven.middleware import Sentry as SentryMiddleware

    from flask import jsonify, request, url_for, Response

    from FileStorage.JsonApp import make_json_app, crossdomain
    from FileStorage.config import config
    from FileStorage.Storage import Storage

    import urllib

except Exception as e:
    raise e

dsn = "http://%(public)s:%(private)s@%(host)s" % config['Raven']

app = make_json_app(__name__)
app.config['SENTRY_DSN'] = dsn
sentry = Sentry(dsn=dsn, logging=True)
sentry.init_app(app)
app.wsgi = SentryMiddleware(app.wsgi_app, sentry.client)


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

    app.logger.debug("Args: %s" % request.args)
    app.logger.debug("Files: %s" % request.files)
    app.logger.debug("Forms: %s" % request.form)

    page = int(request.args.get('page', 1))
    rows = int(request.args.get('rows', 30))
    sidx = request.args.get("sidx")
    sord = request.args.get("sord")
    _search = request.args.get("_search")
    searchField = request.args.get("searchField")
    searchString = request.args.get("searchString")
    searchOper = request.args.get("searchOper")
    other_search = request.args.get("other_search")
    full_props = request.args.get("full_props")
    gridFilters = request.args.get("filters")
    filtersMain = (request.args.get("filtersMain"))
    showcols = request.args.get("showcols")
    totalrows = int(request.args.get("totalrows", 1000))

    if not filtersMain:
        filtersMain = {"groupOp": "AND", "rules": []}
    else:
        filtersMain = json.loads(filtersMain)

    if not gridFilters:
        gridFilters = {"groupOp": "AND", "rules": []}
    else:
        gridFilters = json.loads(gridFilters)

    if showcols:
        showcols = showcols.split(',')
        showcols = [elem for elem in showcols if elem.upper() != elem]

    filters = {}
    sort = None

    info_data = []

    if _search:
        for rule in filtersMain['rules']:

            if not filters.get(rule['field']):
                filters[rule['field']] = list()

            if rule['op'] == "bw":
                filters[rule['field']] = {
                    '$regex': re.compile("^%s" % rule['data'], re.UNICODE)}
            elif rule['op'] == "ew":
                filters[rule['field']] = {
                    '$regex': re.compile("%s$" % rule['data'], re.UNICODE)}
            elif rule['op'] == "eq":
                filters[rule['field']].append(rule['data'])
            elif rule['op'] == "ne":
                filters[rule['field']].append({'$ne': rule['data']})
            elif rule['op'] == "lt":
                filters[rule['field']].append({'$lt': rule['data']})
            elif rule['op'] == "le":
                filters[rule['field']].append({'$lte': rule['data']})
            elif rule['op'] == "gt":
                filters[rule['field']].append({'$gt': rule['data']})
            elif rule['op'] == "ge":
                filters[rule['field']].append({'gte': rule['data']})
            elif rule['op'] == "cn":
                filters[rule['field']].append(
                    {'$text': {'$search': rule['data']}})
            elif rule['op'] == 'nc':
                filters[rule['field']] = {
                    '$not': re.compile("%s" % rule['data'], re.UNICODE)}
            elif rule['op'] == 'bn':
                filters[rule['field']] = {
                    '$not': re.compile("^%s" % rule['data'], re.UNICODE)}
            elif rule['op'] == 'en':
                filters[rule['field']] = {
                    '$not': re.compile("%s$" % rule['data'], re.UNICODE)}

        if gridFilters.get('rules'):
            for rule in gridFilters['rules']:

                if not filters.get(rule['field']):
                    filters[rule['field']] = list()

                if rule['op'] == "bw":
                    filters[rule['field']] = {
                        '$regex': re.compile("^%s" % rule['data'], re.UNICODE)}
                elif rule['op'] == "ew":
                    filters[rule['field']] = {
                        '$regex': re.compile("%s$" % rule['data'], re.UNICODE)}
                elif rule['op'] == "eq":
                    filters[rule['field']] = rule['data']
                elif rule['op'] == "ne":
                    filters[rule['field']] = {'$ne': rule['data']}
                elif rule['op'] == "lt":
                    filters[rule['field']] = {'$lt': rule['data']}
                elif rule['op'] == "le":
                    filters[rule['field']] = {'$lte': rule['data']}
                elif rule['op'] == "gt":
                    filters[rule['field']] = {'$gt': rule['data']}
                elif rule['op'] == "ge":
                    filters[rule['field']] = {'gte': rule['data']}
                elif rule['op'] == 'nc':
                    filters[rule['field']] = {
                        '$not': re.compile("%s" % rule['data'], re.UNICODE)}
                elif rule['op'] == 'bn':
                    filters[rule['field']] = {
                        '$not': re.compile("^%s" % rule['data'], re.UNICODE)}
                elif rule['op'] == 'en':
                    filters[rule['field']] = {
                        '$not': re.compile("%s$" % rule['data'], re.UNICODE)}
                elif rule['op'] == "cn":
                    filters[rule['field']].append(
                        {'$text': {'$search': rule['data']}})
    else:
        filters = None

    app.logger.debug("Filters: %s" % filters)

    if sidx:
        if sord:
            sort = dict(key=sidx, direction=sord)

    skip = int((page - 1) * rows)

    app.logger.debug(u"База даных: %s" % database)

    all_data = Storage(database).list(filters, rows, sort, skip)

    for element in all_data:
        info_data.append(Storage(database).info(element.filename))

    count_data = Storage(database).count()

    total = int(math.ceil(count_data / float(rows)))

    return jsonify(results=dict(total=total, page=page, rows=info_data,
                                records=count_data))


@app.route('/files/<database>', methods=['PUT', 'POST'])
@crossdomain(origin='*')
def upload(database):
    """Загружаем файл в базу данных"""

    app.logger.debug("Args: %s" % request.args)
    app.logger.debug("Files: %s" % request.files)
    app.logger.debug("Forms: %s" % request.form)

    if request.method == 'POST':
        fileObject = request.files.get('file')
        metadata = json.loads(request.form.get('metadata', '{}'))

        if fileObject:
            file = fileObject.read()
            content_type = fileObject.mimetype
            metadata['filename'] = fileObject.filename
        else:
            file = request.form.get('file').encode('utf-8')
            content_type = request.form.get('content_type')

        if content_type:
            if content_type == 'dataURL':
                file = b64decode(file.split(',')[1])
                content_type = 'image/png'
        else:
            content_type = magic.from_buffer(file)

        if file:
            res = Storage(database).put(file, content_type, metadata)
            return jsonify(results=res)
        else:
            raise Exception("Нет файлов для добавления")

    elif request.method == 'PUT':
        file = request.data
        metadata = {}
        content_type = request.content_type

        res = Storage(database).put(file, content_type, metadata)

        return jsonify(results=res)


@app.route('/info/<database>/<file_name>', methods=['GET'])
@crossdomain(origin='*')
def info(database, file_name):
    """Получаем информацию по файлу из базы данных"""

    app.logger.debug("Args: %s" % request.args)
    app.logger.debug("Files: %s" % request.files)
    app.logger.debug("Forms: %s" % request.form)

    res = Storage(database).info(file_name)
    return jsonify(results=res)


@app.route('/file/<database>/<file_name>', methods=['GET'])
@crossdomain(origin='*')
def get(database, file_name):
    """Получаем файл из базы данных"""

    app.logger.debug("Args: %s" % request.args)
    app.logger.debug("Files: %s" % request.files)
    app.logger.debug("Forms: %s" % request.form)

    res = Storage(database).get(file_name)

    result = Response(io.BytesIO(res['content']), direct_passthrough=True,
                      mimetype=res['content_type'])

    if res['content_type']:
        ext = mimetypes.guess_extension(res['content_type'], True)
    else:
        ext = ''

    filename = res['metadata'].get('filename', '%s.%s' % (file_name, ext))

    try:
        encoded_filename = urllib.quote(filename.encode('utf8'))
    except AttributeError:
        encoded_filename = urllib.parse.quote(filename.encode('utf8'))

    result.headers.add(
        "Content-Disposition", "attachment; filename*=UTF-8''%s" % encoded_filename)

    return result


@app.route('/file/<database>/<file_name>', methods=['DELETE'])
@crossdomain(origin='*')
def remove(database, file_name):
    """Удаляем файл из базы данных"""

    app.logger.debug("Args: %s" % request.args)
    app.logger.debug("Files: %s" % request.files)
    app.logger.debug("Forms: %s" % request.form)

    res = Storage(database).delete(file_name)
    return jsonify(results=res)
