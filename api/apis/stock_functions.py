import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional

import pandas as pd
from apis.schemas import StockMetric
from models.stock import Stock
from sqlalchemy.orm import Session
from validation.validation import ComparisonValidation, TwoElementsComparisonValidation, ValueBelongsToFieldValidation

logger = logging.getLogger(__name__)


ISO_DATE_FORMAT = '%Y-%m-%d'
START_DATE = '2010-01-04'
VALID_PRICE_COLUMN_VALUES = ['high_price', 'low_price', 'open_price', 'close_price']
MAX_ROLLING_WINDOW = 100
MIN_ROLLING_WINDOW = 1


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


def validate_query_parameters(start: str, end: str, price_column: str, metric: Metric, rolling_window: int):

    validations = [
        ComparisonValidation(field_name='start', field_value=start, min_value=START_DATE),
        ValueBelongsToFieldValidation(field_name='metric', field_value=metric, valid_values=Metric),
        ComparisonValidation(
            field_name='rolling_window',
            field_value=rolling_window,
            max_value=MAX_ROLLING_WINDOW,
            min_value=MIN_ROLLING_WINDOW,
        ),
        TwoElementsComparisonValidation(
            should_be_smaller_name='start',
            should_be_smaller_value=start,
            should_be_bigger_name='end',
            should_be_bigger_value=end,
        ),
        ValueBelongsToFieldValidation(
            field_name='price_column', field_value=price_column, valid_values=VALID_PRICE_COLUMN_VALUES
        ),
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

    # TODO check if pydantic validation is better https://docs.pydantic.dev/usage/validators/
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
