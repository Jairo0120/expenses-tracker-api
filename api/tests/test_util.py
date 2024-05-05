import pytest
from .. import utils
from datetime import date


def test_first_day_month_invalid_date():
    with pytest.raises(AttributeError):
        utils.get_first_day_month('random')


def test_first_day_month_valid_date():
    result = utils.get_first_day_month(date(2024, 12, 13))
    assert result == date(2024, 12, 1)


def test_last_day_month_december():
    result = utils.get_last_day_month(date(2024, 12, 28))
    assert result == date(2024, 12, 31)


def test_last_day_month_leap():
    result = utils.get_last_day_month(date(2024, 2, 10))
    assert result == date(2024, 2, 29)


def test_last_day_month_no_leap():
    result = utils.get_last_day_month(date(2023, 2, 10))
    assert result == date(2023, 2, 28)


def test_last_day_month_invalid_date():
    with pytest.raises(AttributeError):
        utils.get_first_day_month('random')


def test_last_day_month_same_date():
    result = utils.get_last_day_month(date(2022, 12, 31))
    assert result == date(2022, 12, 31)
