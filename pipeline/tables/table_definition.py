from dataclasses import dataclass
from typing import List

from sqlalchemy import Table, Index


@dataclass
class TableDefinition:
    table: Table
    indexes_list: List[Index]
    post_copy_sql: str = None
