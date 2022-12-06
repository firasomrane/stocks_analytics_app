from abc import ABC, abstractmethod
import os
from typing import List, Tuple, Union

from sqlalchemy.sql.expression import Executable
from sqlalchemy.engine import Engine
import pandas as pd

from pipeline.core.db_utils import copy_csv_to_table, copy_pandas_df_to_table, get_db_conn
from pipeline.tables.table_definition import TableDefinition
from pipeline.core.constants import PIPELINE, STOCK_MARKET_DATA


class BasePostgresTablePopulator(ABC):
    def __init__(
        self,
        table_definition: TableDefinition,
        db_engine: Engine,
        target_db: str = STOCK_MARKET_DATA,
        drop_table_if_exits: bool = True,
    ) -> None:

        self.table_definition = table_definition
        self.target_db = target_db
        self.db_conn = get_db_conn(self.target_db)
        self.tablename = self.table_definition.table
        self.db_engine = db_engine
        self.drop_table_if_exits = drop_table_if_exits

    def create_table(self):
        self.table_definition.table.create(self.db_engine)

    def drop_table(self):
        self.table_definition.table.drop(self.db_engine, checkfirst=True)

    @abstractmethod
    def upload_data(self):
        """
        Implements uploading the target data
        """
        pass

    def execute(
        self,
        stmt: Union[str, Executable],
        autocommit: bool = True,
        **execution_option,
    ):
        return self.db_engine.execution_options(autocommit=autocommit, **execution_option).execute(stmt)  # noqa

    def create_indexes(self):
        """
        Create indexes
        """
        for index in self.table_definition.indexes_list:
            index.create(bind=self.db_engine)

    def analyze(self):
        """Executes an `ANALYZE table` query to collect statistics about the table and indexes for better queries execution plans"""  # noqa
        self.execute(f'ANALYZE {self.tablename}')

    def execute_additional_sql(self):
        if self.table_definition.post_copy_sql:
            self.execute(self.table_definition.post_copy_sql)

    def populate(self):
        if self.drop_table_if_exits:
            self.drop_table()
        self.create_table()
        self.upload_data()
        self.create_indexes()
        self.execute_additional_sql()
        self.analyze()


class CsvFilePopulator(BasePostgresTablePopulator):
    def __init__(
        self,
        table_definition: TableDefinition,
        csv_file_names: List[str],
        csv_files_dir_path: str = 'data',
        csv_separator: str = ',',
        **kwargs,
    ) -> None:
        super().__init__(
            table_definition=table_definition,
            **kwargs,
        )
        self.csv_file_names = csv_file_names
        self.csv_files_dir_path = csv_files_dir_path
        self.csv_separator = csv_separator

    def upload_data(self):
        # TODO Use asycio for faster upload
        for csv_file in self.csv_file_names:
            base_dir_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)).split(PIPELINE)[0], PIPELINE
            )  # noqa
            csv_file_path = os.path.join(base_dir_path, self.csv_files_dir_path, csv_file)
            copy_csv_to_table(
                csv_file_path=csv_file_path,
                table_name=self.table_definition.table.name,
                db_engine=self.db_engine,
                csv_sep=self.csv_separator,
            )


class PandasDfPopulator(BasePostgresTablePopulator):
    def __init__(
        self,
        table_definition: TableDefinition,
        pandas_df: pd.DataFrame,
        **kwargs,
    ) -> None:
        super().__init__(
            table_definition=table_definition,
            **kwargs,
        )
        self.pandas_df = pandas_df

    def upload_data(self):

        copy_pandas_df_to_table(
            pandas_df=self.pandas_df,
            table_name=self.table_definition.table.name,
            db_engine=self.db_engine,
        )
