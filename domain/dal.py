import os
import warnings

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData
from sqlalchemy import event
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker


postgres_host = os.getenv('POSTGRES_HOST')
postgres_database = os.getenv('POSTGRES_DB')
postgres_username = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')

if postgres_host is None:
    raise ValueError('You should specify POSTGRES_HOST environment variable to be able to connect to PostgreSQL DB Server.')

if postgres_database is None:
    raise ValueError('You should specify POSTGRES_DB environment variable to be able to connect to PostgreSQL DB Server.')

if postgres_username is None:
    raise ValueError('You should specify POSTGRES_USER environment variable to be able to connect to PostgreSQL DB Server.')

if postgres_password is None:
    raise ValueError('You should specify POSTGRES_PASSWORD environment variable to be able to connect to PostgreSQL DB Server.')


def _add_engine_pidguard(engine):
    """Add multiprocessing guards.

    Forces a connection to be reconnected if it is detected
    as having been shared to a sub-process.

    """

    # Called at the moment a particular DBAPI connection is first created for a given Pool.
    @event.listens_for(engine, 'connect')
    def connect(_, connection_record):
        connection_record.info['pid'] = os.getpid()

    # Called when a connection is retrieved from the Pool.
    @event.listens_for(engine, 'checkout')
    def checkout(_, connection_record, connection_proxy):
        pid = os.getpid()
        if connection_record.info['pid'] != pid:
            # substitute log.debug() or similar here as desired
            warnings.warn(
                f'Parent process {connection_record.info["pid"]}s forked ({pid}s) with an open '
                'database connection, '
                'which is being discarded and recreated.')
            connection_record.connection = connection_proxy.connection = None
            raise exc.DisconnectionError(
                f'Connection record belongs to pid {connection_record.info["pid"]}, '
                f'attempting to check out in pid {pid}'
            )


DB_AND_DRIVER = 'postgresql+psycopg2'


def _build_full_connection_string(password):
    return f'{DB_AND_DRIVER}://{postgres_username}:{password}@{postgres_host}/{postgres_database}'


def build_connection_string():
    return _build_full_connection_string(postgres_password)


_app_db_engine = create_engine(
    build_connection_string(),
    isolation_level='READ COMMITTED',
    pool_pre_ping=True,
)

_add_engine_pidguard(_app_db_engine)

meta = MetaData(bind=_app_db_engine)
db = SQLAlchemy(metadata=meta)
migrate = Migrate()


def create_session():
    session_factory = sessionmaker(bind=_app_db_engine, autoflush=False, autocommit=False)

    return session_factory()
