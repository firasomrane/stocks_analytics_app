import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from apis.schemas import StockMetric
from models.stock import Stock

logger = logging.getLogger(__name__)


class Metric(Enum):
    MEDIAN = 'median'
    MEAN = 'mean'
    MIN = 'min'
    MAX = 'max'
    STANDARD_DEVIATION = 'standard_deviation'

    @classmethod
    def keys(cls) -> List[str]:
        return [e.value for e in cls]


def get_agg_from_rolling_df(
    rolling_df: pd.core.window.rolling.Rolling,
    metric: Metric,
) -> pd.core.series.Series:
    if metric not in Metric.keys():
        raise HTTPException(
            status_code=400,
            detail=f'The metric {metric} is not supported, please choose one from {Metric.keys()} ',  # noqa
        )

    if metric == Metric.MEDIAN.value:
        return rolling_df.median()
    elif metric == Metric.MEAN.value:
        return rolling_df.mean()
    elif metric == Metric.MIN.value:
        return rolling_df.min()
    elif metric == Metric.MAX.value:
        return rolling_df.max()
    elif metric == Metric.STANDARD_DEVIATION.value:
        return rolling_df.std()


ISO_DATE_FORMAT = '%Y-%m-%d'


def get_date_timedelta(rolling_window: int) -> int:
    if rolling_window <= 5:
        return 7 * rolling_window
    else:
        return 3 * rolling_window


def get_stock_metric(
    db_session: Session,
    ticker: str,
    start: str,
    end: str,
    price_column: str,
    metric: Metric,
    rolling_window: int,
) -> List[StockMetric]:

    days_timedelta = get_date_timedelta(rolling_window=rolling_window)
    updated_start = (datetime.strptime(start, ISO_DATE_FORMAT).date() - timedelta(days=days_timedelta)).strftime(
        ISO_DATE_FORMAT
    )

    query = (
        db_session.query(Stock)
        .filter(Stock.name == ticker)
        .filter(Stock.date >= updated_start)
        .filter(Stock.date <= end)
    )

    df = pd.read_sql(query.statement, db_session.bind)

    df['metric'] = get_agg_from_rolling_df(df[price_column].rolling(rolling_window), metric)
    df = df.fillna('')
    # Keep only the desired data
    df = df[df['date'] >= datetime.strptime(start, ISO_DATE_FORMAT).date()]
    logger.info(f'Final output length is {len(df)}')

    # print(df[['date', 'metric']].head(100))

    # return [StockMetric(date=item[0], metric=item[1]) for item in df[['date', 'metric']].values.tolist()]  # noqa

    # tmp_l = [item_d for item_d in df[['date', 'metric']].to_dict(orient='records')]

    # return [StockMetric(**item_d) for item_d in df[['date', 'metric']].to_dict(orient='records')]

    return df[['date', 'metric']].values.tolist()
