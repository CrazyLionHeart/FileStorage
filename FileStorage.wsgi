#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import app

try:
    from cherrypy import wsgiserver
except Exception, e:
    raise e

port = int(environ.get("PORT", 8381))
d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', port), d)

if __name__ == '__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
