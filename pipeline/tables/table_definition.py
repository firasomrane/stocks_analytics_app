from dataclasses import dataclass
from typing import List

from sqlalchemy import Index, Table


@dataclass
class TableDefinition:
    """Class holding all information about a table:
    - table: Sqla table
    - indexes_list: List of sqla indexes to be created when the table is populated
    - post_copy_sql: Optional query to be run after the indexes and the table is populated
        can be for clustering.
    """

    table: Table
    indexes_list: List[Index]
    post_copy_sql: str = None
