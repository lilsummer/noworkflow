# Copyright (c) 2014 Universidade Federal Fluminense (UFF)
# Copyright (c) 2014 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.

from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

import sqlite3
import sys
import weakref
import threading

from os.path import join, isdir, exists
from os import makedirs
from pkg_resources import resource_string
from collections import OrderedDict

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from ..utils import print_msg, resource
from ..cross_version import cvzip, row_keys

PROVENANCE_DIRNAME = '.noworkflow'
CONTENT_DIRNAME = 'content'
DB_FILENAME = 'db.sqlite'
DB_SCRIPT = '../resources/noworkflow.sql'
PARENT_TRIAL = '.parent_config.json'


def row_to_dict(row):
    return OrderedDict(cvzip(row_keys(row), row))


class DeclarativeBase(object):

    def to_dict(self, ignore=tuple(), extra=tuple()):
        result = OrderedDict(
            (attr, getattr(self, attr)) for attr in extra
        )
        for column in self.__mapper__.columns:
            key = column.key
            if key not in ignore and key not in extra:
                result[key] = getattr(self, key)

        return result


class Provider(object):

    def __init__(self, path=None, connect=False):
        self.base_path = None # Exeution path
        self.provenance_path = None  # Base .noworkflow path
        self.content_path = None # Base path for storing content of files
        self.parent_config_path = None # Base path for restore references
        self.db_conn = None # Connection to the database

        self.std_open = open # Original Python open function.

        self.base = declarative_base(cls=DeclarativeBase)
        self.base._persistence = weakref.proxy(self)

        if path:
            self.path = path

        if connect:
            self.connect(path)

    @property
    def path(self):
        return self.base_path

    @path.setter
    def path(self, path):
        self.base_path = path
        self.provenance_path = join(path, PROVENANCE_DIRNAME)
        self.content_path = join(self.provenance_path, CONTENT_DIRNAME)
        self.parent_config_path = join(self.provenance_path, PARENT_TRIAL)

    def make_session(self):
        return scoped_session(self.session_factory)

    @property
    def session(self):
        ident = threading.current_thread().ident
        if ident not in self._session_map:
            self._session_map[ident] = self.make_session()
            self._session_map[ident].configure(expire_on_commit=False)
        return self._session_map[ident]

    def connect(self, path=None):
        from .. import models
        if path:
            self.path = path

        db_path = join(self.provenance_path, DB_FILENAME)

        if not isdir(self.content_path):
            makedirs(self.content_path)

        new_db = not exists(db_path)
        self.db_conn = sqlite3.connect(db_path)
        self.db_conn.row_factory = sqlite3.Row

        self.engine = create_engine('sqlite:///' + db_path, echo=False)
        self.session_factory = sessionmaker()
        self.session_factory.configure(bind=self.engine, autoflush=False,
                                       expire_on_commit=True)
        self._session_map = {}

        if new_db:
            print_msg('creating provenance database')
            self.base.metadata.create_all(self.engine)
            # Accessing the content of a file via setuptools
            #with self.db_conn as db:
            #    db.executescript(resource(DB_SCRIPT, 'utf-8'))

    def has_provenance(self, path=None):
        if path:
            return isdir(join(path, PROVENANCE_DIRNAME))
        return isdir(self.provenance_path)

    def connect_existing(self, path=None):
        if path:
            self.path = path
        if not self.has_provenance():
            print_msg('there is no provenance store in the current directory',
                True)
            sys.exit(1)
        self.connect()

    def query(self, text):
        with self.db_conn as db:
            for row in db.execute(text):
                yield row_to_dict(row)