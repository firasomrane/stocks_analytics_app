import unittest
from dataclasses import dataclass
from typing import Any, List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tests.test_input import TEST_INPUT

from apis.dependencies import get_db_session
from apis.main import app
from database.utils import create_database_if_not_exists, create_table, drop_table, get_db_config
from models.stock import Stock

TC = unittest.TestCase()

create_database_if_not_exists('test')
test_db_config_uri = get_db_config(db_name='test').uri
print('test_db_config_uri: ', test_db_config_uri)
print(get_db_config(db_name='test'))

test_db_engine = create_engine(test_db_config_uri)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)


def get_db_test_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db_session] = get_db_test_session
client = TestClient(app)


@pytest.fixture()
def populate_db_test():

    create_table(test_db_engine, Stock.__table__)
    session = next(get_db_test_session())

    # TODO use add_all if big input
    for row in TEST_INPUT:
        table_row = Stock(**row)
        session.add(table_row)

    session.commit()

    yield

    drop_table(test_db_engine, Stock.__table__)


@dataclass
class TestCase:
    price_column: str
    metric: str
    rolling_window: int
    ticker: str
    start: str
    end: str
    expected_status_code: int
    expected_result: List[Any]


TEST_CASES = [
    TestCase(
        price_column='open_price',
        metric='max',
        rolling_window=10,
        ticker='AA',
        start='2010-01-14',
        end='2010-01-16',
        expected_status_code=200,
        expected_result=[
            {'date': '2010-01-14', 'metric': 10.00},
            {'date': '2010-01-15', 'metric': 10.00},
            {'date': '2010-01-16', 'metric': 10.00},
        ],
    ),
    TestCase(
        price_column='open_price',
        metric='max',
        rolling_window=10,
        ticker='AA',
        start='2010-01-13',
        end='2010-01-14',
        expected_status_code=200,
        expected_result=[
            {'date': '2010-01-13', 'metric': 10.00},
            {'date': '2010-01-14', 'metric': 10.00},
        ],
    ),
    TestCase(
        price_column='open_price',
        metric='mean',
        rolling_window=10,
        ticker='AA',
        start='2010-01-12',
        end='2010-01-13',
        expected_status_code=200,
        expected_result=[
            {'date': '2010-01-12', 'metric': ''},
            {'date': '2010-01-13', 'metric': 10.00},
        ],
    ),
    TestCase(
        price_column='high_price',
        metric='max',
        rolling_window=10,
        ticker='AA',
        start='2010-01-14',
        end='2010-01-16',
        expected_status_code=200,
        expected_result=[
            {'date': '2010-01-14', 'metric': 15.00},
            {'date': '2010-01-15', 'metric': 17.00},
            {'date': '2010-01-16', 'metric': 20.00},
        ],
    ),
    TestCase(
        price_column='high_price',
        metric='standard_deviation',
        rolling_window=10,
        ticker='AA',
        start='2010-01-04',
        end='2010-01-06',
        expected_status_code=200,
        expected_result=[
            {'date': '2010-01-04', 'metric': ''},
            {'date': '2010-01-05', 'metric': ''},
            {'date': '2010-01-06', 'metric': ''},
        ],
    ),
    TestCase(
        price_column='high_price',
        metric='max',
        rolling_window=10,
        ticker='AA',
        start='2010-01-01',
        end='2010-01-06',
        expected_status_code=422,
        expected_result={'detail': 'Start should be bigger or equal to 2010-01-04'},
    ),
    TestCase(
        price_column='high_price',
        metric='non_existing_metric',
        rolling_window=10,
        ticker='AA',
        start='2010-01-04',
        end='2010-01-06',
        expected_status_code=422,
        expected_result={
            'detail': "The metric non_existing_metric is not supported, please choose one from ['median', 'mean', 'min', 'max', 'standard_deviation']"  # noqa
        },
    ),
    TestCase(
        price_column='non_existing_column',
        metric='max',
        rolling_window=10,
        ticker='AA',
        start='2010-01-04',
        end='2010-01-06',
        expected_status_code=422,
        expected_result={
            'detail': "Price column should be one of ['high_price', 'low_price', 'open_price', 'close_price']"
        },
    ),
]
PATH = '/stock_metrics/?price_column={price_column}&metric={metric}&rolling_window={rolling_window}&ticker={ticker}&start={start}&end={end}'  # noqa


def test_read_main(populate_db_test):

    """"""
    # df = pd.read_sql_query("select * from stock", con=db_engine)
    # print(df.head(100))

    for test_case in TEST_CASES:
        path = PATH.format(
            price_column=test_case.price_column,
            metric=test_case.metric,
            rolling_window=test_case.rolling_window,
            ticker=test_case.ticker,
            start=test_case.start,
            end=test_case.end,
        )
        response = client.get(path)
        print(f'{path = }')
        print(f'{test_case.metric}')
        print(f'{response.status_code = }')
        print(f'{response.json() = }')
        print(f'{test_case.expected_result = }')
        assert response.status_code == test_case.expected_status_code
        assert response.json() == test_case.expected_result