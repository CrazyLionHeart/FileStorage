#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

try:
    from pymongo.mongo_replica_set_client import MongoReplicaSetClient
    from pymongo.errors import AutoReconnect, ConnectionFailure
    from pymongo.read_preferences import ReadPreference
    from pymongo import ASCENDING, DESCENDING
    from gridfs import GridFS
    from gridfs.errors import NoFile
    from bson.json_util import dumps

    import time
    import json

    from FileStorage.config import config

    import logging

    import hashlib
except ImportError, e:
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
        self.readPreference = ReadPreference.SECONDARY_PREFERRED
        self.current_db = db

    def list(self, filters=None, limit=None, sort=None, skip=None):

        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           use_greenlets=True,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           read_preference=self.readPreference,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure, e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        db.read_preference = self.readPreference
        self.fs = GridFS(db)

        kwargs = dict()

        if limit:
            kwargs['limit'] = limit

        if skip:
            kwargs['skip'] = skip

        for i in xrange(self.mongodb["max_autoreconnect"]):
            try:
                logging.debug("""Trying to send data.
                              Alive hosts: %r""" % client)

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

            except AutoReconnect:
                time.sleep(pow(2, i))
                logging.debug("""Autoreconnect error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

        client.close()
        logging.exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")
        raise Exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")

    def get(self, filename):
        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           use_greenlets=True,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           read_preference=self.readPreference,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure, e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        db.read_preference = self.readPreference
        self.fs = GridFS(db)

        for i in xrange(self.mongodb["max_autoreconnect"]):
            try:
                logging.debug("""Trying to send data.
                              Alive hosts: %r""" % client)

                result = self.fs.get_last_version(filename=filename)
                return dict(content=result.read(),
                            content_type=result.content_type,
                            metadata=result.metadata)

            except NoFile:
                time.sleep(pow(2, i))
                logging.debug("""NoFile error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

            except AutoReconnect:
                time.sleep(pow(2, i))
                logging.debug("""Autoreconnect error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

        client.close()
        logging.exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")
        raise Exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")

    def put(self, file, content_type='application/octet-stream', metadata=None):
        m = hashlib.sha512(file)
        filename = m.hexdigest()

        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           use_greenlets=True,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           read_preference=self.readPreference,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure, e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        db.read_preference = self.readPreference
        self.fs = GridFS(db)

        for i in xrange(self.mongodb["max_autoreconnect"]):
            try:
                logging.debug("""Trying to send data.
                              Alive hosts: %r""" % client)

                if self.fs.exists(filename=filename):
                    # Если файл уже существует возвращаем инфу по нему
                    pass
                else:
                    # Иначе загружаем файл и возвращаем инфу по нему
                    self.fs.put(file, filename=filename,
                                content_type=content_type, metadata=metadata)

                return self.info(filename)

            except AutoReconnect:
                time.sleep(pow(2, i))
                logging.debug("""Autoreconnect error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

        client.close()
        logging.exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")
        raise Exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")

    def delete(self, filename):

        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           use_greenlets=True,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           read_preference=self.readPreference,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure, e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        db.read_preference = self.readPreference
        self.fs = GridFS(db)

        for i in xrange(self.mongodb["max_autoreconnect"]):
            try:
                logging.debug("""Trying to send data.
                              Alive hosts: %r""" % client)

                result = self.fs.get_last_version(filename=filename)
                self.fs.delete(result._id)
                return filename

            except NoFile:
                time.sleep(pow(2, i))
                logging.debug("""NoFile error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

            except AutoReconnect:
                time.sleep(pow(2, i))
                logging.debug("""Autoreconnect error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

        client.close()
        logging.exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")
        raise Exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")

    def info(self, filename):
        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           use_greenlets=True,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           read_preference=self.readPreference,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure, e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        db.read_preference = self.readPreference
        self.fs = GridFS(db)

        for i in xrange(self.mongodb["max_autoreconnect"]):
            try:
                logging.debug("""Trying to send data.
                              Alive hosts: %r""" % client)

                result = self.fs.get_version(filename=filename)
                return dict(
                    filename=result.filename, content_type=result.content_type,
                    length=result.length, metadata=result.metadata,
                    upload_date=result.upload_date)

            except NoFile:
                time.sleep(pow(2, i))
                logging.debug("""NoFile error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)
            except AutoReconnect:
                time.sleep(pow(2, i))
                logging.debug("""Autoreconnect error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

        client.close()
        logging.exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")
        raise Exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")

    def count(self):

        try:
            client = MongoReplicaSetClient(self.host,
                                           replicaSet=self.replicaSet,
                                           use_greenlets=True,
                                           w=self.writeConcern,
                                           j=self.journal,
                                           read_preference=self.readPreference,
                                           slave_okay=True,
                                           connectTimeoutMS=200)
        except ConnectionFailure, e:
                logging.exception("Connection falure error reached: %r" % e)
                raise Exception(e)

        db = client[self.current_db]
        db.read_preference = self.readPreference
        self.fs = GridFS(db)

        for i in xrange(self.mongodb["max_autoreconnect"]):
            try:
                logging.debug("""Trying to send data.
                              Alive hosts: %r""" % client)

                return self.fs.find().count()
            except AutoReconnect:
                time.sleep(pow(2, i))
                logging.debug("""Autoreconnect error reached.
                          Trying to resend data by timeout.
                          Previous alive hosts: %r""" % client)

        client.close()
        logging.exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")
        raise Exception("""Error: Failed operation!
                      Is anybody from mongo servers alive?""")
