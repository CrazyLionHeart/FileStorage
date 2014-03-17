#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

try:
    from pymongo.mongo_replica_set_client import MongoReplicaSetClient
    from pymongo.errors import AutoReconnect, ConnectionFailure
    from pymongo.read_preferences import ReadPreference
    from gridfs import GridFS
    from gridfs.errors import NoFile, FileExists
    from pymongo.errors import InvalidName

    import logging

    import hashlib
except ImportError, e:
    raise e

import itertools
import math

from .config import *


logging.basicConfig(level=logging.DEBUG,
                    format=u'''%(filename)s[LINE:%(lineno)d]# %(levelname)-8s
                    [%(asctime)s]  %(message)s''')


class Storage(object):

    def __init__(self, db=None):

        try:
            readPreference = ReadPreference.SECONDARY_PREFERRED
            self.client = MongoReplicaSetClient(",".join(host),
                                                replicaSet=replicaSet,
                                                use_greenlets=True,
                                                w=writeConcern,
                                                j=journal,
                                                read_preference=readPreference)

            if db:
                self.db = getattr(self.client, db)
                self.fs = GridFS(self.db)
            else:
                raise Exception("DB not selected")

        except AutoReconnect, e:
            pass
        except ConnectionFailure, e:
            raise e
        except InvalidName, e:
                raise e

    def list(self, current_page=None, rows=None, sidx=None, sord="asc"):
        row_data = list()
        info_data = list()

        start = (current_page - 1) * rows
        end = current_page * rows

        all_data = self.fs.list()
        total = int(math.ceil(len(all_data) / rows))

        for element in all_data:
            info_data.append(self.info(element))

        if sord == "desc":
            reverse = True
        else:
            reverse = False

        if not (sidx is None):
            info_data.sort(key=lambda tup: tup[sidx], reverse=reverse)

        for element in itertools.islice(info_data, start, end):
            row_data.append(element)

        return dict(total=total, page=current_page, rows=row_data,
                    records=len(all_data))

    def get(self, filename):
        try:
            result = self.fs.get_last_version(filename=filename)
            return dict(content=result.read(), content_type=result.content_type)
        except NoFile, e:
            raise e

    def put(self, file, content_type='application/octet-stream', metadata=None):
        m = hashlib.sha512()
        m.update(file)
        filename = m.hexdigest()

        if self.fs.exists(filename=filename):
            # Если файл уже существует возвращаем инфу по нему
            pass
        else:
            # Иначе загружаем файл и возвращаем инфу по нему
            self.fs.put(file, filename=filename,
                        content_type=content_type, metadata=metadata)
        return self.info(filename)

    def delete(self, filename):
        try:
            result = self.fs.get_last_version(filename=filename)
            self.fs.delete(result._id)
            return filename
        except FileExists, e:
            raise e

    def info(self, filename):
        try:
            result = self.fs.get_version(filename=filename)
            return dict(
                filename=result.filename, content_type=result.content_type,
                length=result.length, metadata=result.metadata,
                upload_date=result.upload_date)
        except NoFile, e:
            raise e
