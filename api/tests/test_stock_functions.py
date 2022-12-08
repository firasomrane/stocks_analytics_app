from api.apis.stock_functions import get_date_timedelta


def test_get_date_timedelta():
    assert get_date_timedelta(4) == 28
    assert get_date_timedelta(10) == 30
