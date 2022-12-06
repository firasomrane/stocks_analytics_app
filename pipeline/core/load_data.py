
from typing import List

import pandas as pd

from pipeline.core.constants import STOCK_MARKET_DATA
from pipeline.core.db_utils import create_database_if_not_exists, get_db_engine
from pipeline.core.populator import CsvFilePopulator, PandasDfPopulator
from pipeline.tables.stock import stock_table_definition


CSV_FILES = [
    'stocks-2010.csv',
    'stocks-2011.csv'
]

def get_pd_dataframe_with_dates_columns_formated(csv_files_l: List[str]) -> pd.DataFrame:
    dfs = []

    for filename in csv_files_l:
        df = pd.read_csv(filename, index_col=None, header=0)
        dfs.append(df)

    df_all = pd.concat(csv_files_l, axis=0, ignore_index=True)
    df_all['date'] = pd.to_datetime(df['date'])
    df_all['date'] = df_all['date'].dt.strftime('%Y-%m-%d')
    return df_all


if __name__ == "__main__":
    create_database_if_not_exists(STOCK_MARKET_DATA)
    db_engine = get_db_engine(STOCK_MARKET_DATA)

    df = get_pd_dataframe_with_dates_columns_formated(ficsv_files_lles=CSV_FILES)
    populator = PandasDfPopulator(
        table_definition=stock_table_definition,
        db_engine=db_engine,
        pandas_df=df,
    )
    populator.populate()