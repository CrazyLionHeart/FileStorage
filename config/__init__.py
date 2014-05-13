#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from os import environ, path
    import json
    from logging.config import dictConfig
except ImportError, e:
    raise e

current_env = environ.get("APPLICATION_ENV", 'development')

try:
    with open(
        '%s/%s/config.%s.json' % (path.dirname(path.abspath(__file__)),
                                  current_env, current_env)) as f:
        config = json.load(f)
        config["APPLICATION_ENV"] = current_env
        dictConfig(config["loggingconfig"])

except IOError, e:
    with open(
        '%s/%s/sample_config.json' % (path.dirname(path.abspath(__file__)),
                                      current_env)) as f:
        print(
            "Конфиг не найден. Поместите в файл: %s/%s/config.%s.json" % (path.dirname(path.abspath(__file__)),
                                                                          current_env, current_env))
        print("Пример конфига: %s " % f.read())
    exit(1)
