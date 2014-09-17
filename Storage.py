#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

try:
    from pymongo.mongo_replica_set_client import MongoReplicaSetClient
    from pymongo.errors import ConnectionFailure, OperationFailure
    from pymongo import ASCENDING, DESCENDING
    from gridfs import GridFS

    from FileStorage.config import config

    import logging
    import json

    import hashlib
except ImportError as e:
    raise e


class Storage(object):

    def __init__(self, db=None):

        if not db:
            raise Exception("DB not selected")

        logging.debug("Database: %s" % db)

        self.mongodb = config['mongodb']
        self.host = ",".join(self.mongodb['host'])
        self.replicaSet = self.mongodb['replicaSet']
        self.writeConcern = self.mongodb['writeConcern']
        self.journal = self.mongodb['journal']
        self.current_db = db

    def list(self, filters=None, limit=None, sort=None, skip=None):

        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure as e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        self.fs = GridFS(db)

        kwargs = dict()

        if limit:
            kwargs['limit'] = limit

        if skip:
            kwargs['skip'] = skip

        if filters:
            results = self.fs.find(filters, **kwargs)
        else:
            results = self.fs.find(**kwargs)

        if sort:
            if sort['direction'] == 'asc':
                results = results.sort(sort['key'], ASCENDING)
            else:
                results = results.sort(sort['key'], DESCENDING)
        return results

    def get(self, filename):
        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure as e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        self.fs = GridFS(db)

        result = self.fs.get_last_version(filename=filename)

        if (isinstance(result.metadata, basestring)):
            metadata = json.loads(result.metadata)
        else:
            metadata = result.metadata

        return dict(content=result.read(),
                    content_type=result.content_type,
                    metadata=metadata,
                    filename=result.filename)

    def put(self, file, content_type='application/octet-stream', metadata=None):
        m = hashlib.sha512(file)
        filename = m.hexdigest()

        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure as e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        self.fs = GridFS(db)

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
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure as e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        self.fs = GridFS(db)

        result = self.fs.get_last_version(filename=filename)
        self.fs.delete(result._id)
        return filename

    def info(self, filename):
        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure as e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        self.fs = GridFS(db)

        result = self.fs.get_version(filename=filename)

        if (isinstance(result.metadata, basestring)):
            metadata = json.loads(result.metadata)
        else:
            metadata = result.metadata

        return dict(
            filename=result.filename, content_type=result.content_type,
            length=result.length, metadata=metadata,
            upload_date=result.upload_date)

    def count(self):

        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure as e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]

        try:
            result = db.command('collstats', 'fs.files')
            client.close()
            return result['count']
        except OperationFailure:
            return 0
