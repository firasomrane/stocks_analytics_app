from apis.stock_functions import format_to_float


def test_format_to_float():
    assert format_to_float('43.43') == 43.43

    assert format_to_float('11.1111') == 11.11

    assert format_to_float('anything') is None
