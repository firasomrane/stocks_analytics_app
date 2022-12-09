import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from apis.schemas import StockMetric
from models.stock import Stock
from validation.validation import Validation

logger = logging.getLogger(__name__)


ISO_DATE_FORMAT = '%Y-%m-%d'
START_DATE = '2010-01-04'


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

    """
    Given a rolling_df and a metric returns the appropriate metric computation
    """

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


class StartDateValidation(Validation):
    def __init__(self, start_date: str) -> None:
        super().__init__()
        self.start_date = start_date

    @property
    def is_valid(self) -> bool:
        return self.start_date >= START_DATE

    @property
    def error_message(self) -> str:
        return f'Start should be bigger or equal to {START_DATE}'


class MetricValidation(Validation):
    def __init__(self, metric: str) -> None:
        super().__init__()
        self.metric = metric

    @property
    def is_valid(self) -> bool:
        return self.metric in Metric.keys()

    @property
    def error_message(self) -> str:
        return f'The metric {self.metric} is not supported, please choose one from {Metric.keys()}'


MAX_ROLLING_WINDOW = 100
MIN_ROLLING_WINDOW = 1


class RollingWindowValidation(Validation):
    def __init__(self, rolling_window: int) -> None:
        super().__init__()
        self.rolling_window = rolling_window

    @property
    def is_valid(self) -> bool:
        return MIN_ROLLING_WINDOW <= self.rolling_window <= MAX_ROLLING_WINDOW

    @property
    def error_message(self) -> str:
        return f'rolling window should be between {MIN_ROLLING_WINDOW} and {MAX_ROLLING_WINDOW}'


class EndBiggerThanStartValidation(Validation):
    def __init__(self, start: str, end: str) -> None:
        super().__init__()
        self.start = start
        self.end = end

    @property
    def is_valid(self) -> bool:
        return self.start <= self.end

    @property
    def error_message(self) -> str:
        return 'Start date should be smaller or equal to end date'


class PriceColumnValidation(Validation):
    valid_price_column_values = ['high_price', 'low_price', 'open_price', 'close_price']

    def __init__(self, price_column: str) -> None:
        super().__init__()
        self.price_column = price_column

    @property
    def is_valid(self) -> bool:
        return self.price_column in self.valid_price_column_values

    @property
    def error_message(self) -> str:
        return f'Price column should be one of {self.valid_price_column_values}'


def validate_query_parameters(start: str, end: str, price_column: str, metric: Metric, rolling_window: int):

    validations = [
        StartDateValidation(start),
        MetricValidation(metric),
        RollingWindowValidation(rolling_window),
        EndBiggerThanStartValidation(start, end),
        PriceColumnValidation(price_column),
    ]

    for validation in validations:
        if not validation.is_valid:
            raise validation.http_exception


def format_to_float(input: str) -> Optional[float]:
    try:
        return round(float(input), 2)
    except ValueError:
        return None


def get_stock_metric(
    db_session: Session,
    ticker: str,
    start: str,
    end: str,
    price_column: str,
    metric: Metric,
    rolling_window: int,
) -> List[StockMetric]:

    validate_query_parameters(
        start=start,
        end=end,
        price_column=price_column,
        metric=metric,
        rolling_window=rolling_window,
    )

    query = db_session.query(Stock).filter(Stock.name == ticker).filter(Stock.date <= end).order_by(Stock.date.asc())

    df = pd.read_sql(query.statement, db_session.bind)

    df['metric'] = get_agg_from_rolling_df(df[price_column].rolling(rolling_window), metric)
    df = df.fillna('')

    # Keep only the desired data
    df = df[df['date'] >= datetime.strptime(start, ISO_DATE_FORMAT).date()]
    logger.info(f'Final output length is {len(df)}')

    df['metric'] = df['metric'].apply(format_to_float)
    df = df.fillna('')
    return df[['date', 'metric']].to_dict('records')
