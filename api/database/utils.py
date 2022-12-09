import logging
import os
from dataclasses import dataclass
from typing import Dict

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql.schema import Table

logger = logging.getLogger(__name__)


@dataclass
class DbConfig:
    host: str
    database: str
    username: str
    password: str
    port: int = 5432

    @property
    def uri(self) -> str:
        return f'postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'  # noqa

    @property
    def psycopg2_compatible_dict(self) -> Dict[str, str]:
        return {
            'host': self.host,
            'port': self.port,
            'user': self.username,
            'password': self.password,
            'database': self.database,
        }


# TODO fix how to pass port (expore docker ENV)
def get_db_config(db_name: str = 'postgres') -> DbConfig:
    print('POSTGRES_HOST: ', os.environ.get('POSTGRES_HOST'))
    return DbConfig(
        host=os.environ.get('POSTGRES_HOST') or 'db',
        port=os.environ.get('POSTGRES_PORT') or 5432,
        database=db_name,
        password=os.environ.get('POSTGRES_PASSWORD'),
        username=os.environ.get('POSTGRES_USER') or 'postgres',
    )


def drop_table(db_engine, table: Table):
    table.drop(db_engine, checkfirst=True)


def create_schema_if_not_exists(db_engine: Engine, schema_name: str):
    if not db_engine.dialect.has_schema(db_engine, schema_name):
        db_engine.execute(CreateSchema(schema_name))


def create_table(db_engine: Engine, table: Table):
    drop_table(db_engine, table)

    schema = table.schema if table.schema is not None else 'public'
    create_schema_if_not_exists(db_engine=db_engine, schema_name=schema)
    table.create(db_engine)


def get_db_engine(db_name: str):
    db_config = get_db_config(db_name)
    engine = create_engine(db_config.uri)
    return engine


def get_db_conn(db_name: str):
    conn = psycopg2.connect(**get_db_config(db_name).psycopg2_compatible_dict)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def create_database_if_not_exists(db_name: str):
    conn = get_db_conn(db_name='postgres')
    logger.info(f' creating {db_name} database')

    with conn.cursor() as cur:
        try:
            sql_create_db_query = f'create database {db_name};'
            cur.execute(sql_create_db_query)
        except psycopg2.errors.DuplicateDatabase:
            logger.info(f'Database {db_name} exists already')

    conn.close()
