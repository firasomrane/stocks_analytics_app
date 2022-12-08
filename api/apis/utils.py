import logging
import os
from dataclasses import dataclass
from typing import Dict

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
