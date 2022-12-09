# flake8

from apis.stock_functions import MetricValidation, StartDateValidation


def test_start_date_validation():

    assert StartDateValidation('2009-01-10').is_valid == False  # noqa

    assert StartDateValidation('2010-01-04').is_valid


def test_metric_validation():

    assert MetricValidation('median').is_valid

    assert MetricValidation('anything').is_valid == False  # noqa
