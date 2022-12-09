import logging
import os
from typing import List

import pandas as pd
from sqlalchemy.types import Date

from pipeline.core.constants import PIPELINE, STOCK_MARKET_DATA
from pipeline.core.db_utils import create_database_if_not_exists, get_db_engine
from pipeline.core.populator import PandasDfPopulator
from pipeline.tables.stock import stock_table_definition

logger = logging.getLogger(__name__)


CSV_FILES = ['stocks-2010.csv', 'stocks-2011.csv']


def get_pd_dataframe_with_dates_columns_formated(csv_files_l: List[str]) -> pd.DataFrame:
    """
    Loads the csv files and format the date columns to ISO format
    """
    dfs = []

    for filename in csv_files_l:
        base_dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)).split(PIPELINE)[0], PIPELINE)  # noqa
        csv_file_path = os.path.join(base_dir_path, 'data', filename)
        df = pd.read_csv(csv_file_path, index_col=None, header=0)
        dfs.append(df)

    df_all = pd.concat(dfs, axis=0, ignore_index=True)
    df_all['date'] = pd.to_datetime(df_all['date'])
    df_all['date'] = df_all['date'].dt.strftime('%Y-%m-%d')
    return df_all


if __name__ == '__main__':
    create_database_if_not_exists(STOCK_MARKET_DATA)
    db_engine = get_db_engine(STOCK_MARKET_DATA)

    df = get_pd_dataframe_with_dates_columns_formated(csv_files_l=CSV_FILES)

    populator = PandasDfPopulator(
        table_definition=stock_table_definition,
        db_engine=db_engine,
        pandas_df=df,
        columns_dtype={'date': Date()},  # noqa
    )
    populator.populate()

    logger.info('data is uploaded to the DB')
