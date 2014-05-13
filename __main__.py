#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sys
    import os
    path = os.path.dirname(sys.modules[__name__].__file__)
    path = os.path.join(path, '..')
    sys.path.insert(0, path)

    from FileStorage.app import app
except ImportError, e:
    raise e

if __name__ == '__main__':
    app.run(debug=True)
