#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import environ
import json
current_env = environ.get("APPLICATION_ENV", 'development')
from .app import app

with open('../../config/%s/config.%s.json' % (current_env, current_env)) as f:
    config = json.load(f)

try:
    port = int(config["File_Storage"]["port"])
    host = config['File_Storage']["hostname"]
    app.run(host=host, port=port)
except KeyboardInterrupt:
    pass
