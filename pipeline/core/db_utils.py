import io
import logging
import os
from dataclasses import dataclass
from typing import Dict

import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

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


def get_db_config(db_name: str = 'postgres') -> DbConfig:

    return DbConfig(
        host=os.environ.get('POSTGRES_HOST') or 'db',
        port=os.environ.get('POSTGRES_PORT') or 5432,
        database=db_name,
        password=os.environ.get('POSTGRES_PASSWORD'),
        username=os.environ.get('POSTGRES_USER') or 'postgres',
    )


def get_db_engine(db_name: str):
    db_config = get_db_config(db_name)
    engine = create_engine(db_config.uri)
    return engine


def get_db_conn(db_name: str):
    print('getting db_config: ')
    conn = psycopg2.connect(**get_db_config(db_name).psycopg2_compatible_dict)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def create_database_if_not_exists(db_name: str):
    conn = get_db_conn(db_name='postgres')
    print(conn)
    logger.info(f' creating {db_name} database')

    with conn.cursor() as cur:
        try:
            sql_create_db_query = f'create database {db_name};'
            cur.execute(sql_create_db_query)
        except psycopg2.errors.DuplicateDatabase:
            logger.info(f'Database {db_name} exists already')

    conn.close()


def copy_csv_to_table(
    csv_file_path: str,
    table_name: str,
    db_engine: Engine,
    csv_sep: str = ',',
) -> None:
    """
    Use SQL COPY to populate a csv file into a Postgres table.
    """

    conn = db_engine.raw_connection()
    isolation_level = conn.isolation_level
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Copy the data from the CSV file into the table
    # By default copy appends to the existing table and doesn't truncate
    with open(csv_file_path, 'r') as f:
        cur.copy_from(f, table_name, sep=csv_sep)

    # Close the cursor and connection
    cur.close()
    conn.set_isolation_level(isolation_level)
    conn.close()


def copy_pandas_df_to_table(
    pandas_df: pd.DataFrame,
    table_name: str,
    db_engine: Engine,
):
    """
    Use SQL COPY to upload a pandas dataframe to a postgres db table,
    ref: https://stackoverflow.com/a/47984180/7275926

    Args:
        - pandas_df: pd.DataFrame, dataframe to upload
    """

    conn = db_engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    pandas_df.to_csv(output, sep=',', header=False, index=False)
    output.seek(0)
    # _ = output.getvalue()
    cur.copy_from(output, table_name, null='', sep=',')  # null values become ''
    conn.commit()

    cur.close()
    conn.close()
