# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import pytest

from utils.datetime_util import DATE_FORMAT, get_start_end_date


def test_get_start_end_date_with_both_dates_provided():
    # Act
    start, end = get_start_end_date("2023-01-01", "2023-01-07")

    # Assert
    assert start == "2023-01-01"
    assert end == "2023-01-07"


def test_get_start_end_date_with_only_start_date_provided():
    # Arrange
    test_start_date = "2023-01-01"

    # Act
    start, end = get_start_end_date(test_start_date, None)

    # Assert
    expected_end = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert start == test_start_date
    assert end == expected_end


def test_get_start_end_date_with_only_end_date_provided():
    # Arrange
    test_end_date = "2023-01-07"

    # Act
    start, end = get_start_end_date(None, test_end_date)

    # Assert
    expected_start = (datetime.strptime(test_end_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    assert start == expected_start
    assert end == test_end_date


def test_get_start_end_date_with_no_dates_provided():
    # Act
    start, end = get_start_end_date(None, None)

    # Assert
    expected_end = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    expected_start = (datetime.strptime(expected_end, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    assert start == expected_start
    assert end == expected_end


def test_end_date_adjustment_when_in_future():
    # Arrange
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Act
    start, end = get_start_end_date(None, future_date)

    # Assert
    expected_end = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    expected_start = (datetime.strptime(expected_end, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    assert end == expected_end
    assert start == expected_start


def test_invalid_start_date_format():
    with pytest.raises(ValueError) as exc_info:
        get_start_end_date("2023/01/01", "2023-01-07")
    assert f"Start date must be in {DATE_FORMAT} format" in str(exc_info.value)


def test_invalid_end_date_format():
    with pytest.raises(ValueError) as exc_info:
        get_start_end_date("2023-01-01", "07-01-2023")
    assert f"End date must be in {DATE_FORMAT} format" in str(exc_info.value)


def test_start_date_after_end_date():
    with pytest.raises(ValueError) as exc_info:
        get_start_end_date("2023-01-10", "2023-01-05")
    assert "Start date cannot be after end date" in str(exc_info.value)


def test_invalid_date_with_correct_format():
    with pytest.raises(ValueError) as exc_info:
        get_start_end_date("2023-02-30", "2023-03-01")  # February doesn't have 30 days
    assert f"Start date must be in {DATE_FORMAT} format" in str(exc_info.value)


def test_mixed_invalid_formats():
    # Test should expect only one error at a time
    with pytest.raises(ValueError) as exc_info:
        # First invalid format (start_date)
        get_start_end_date("01-01-2023", "2023-12-31")
    assert f"Start date must be in {DATE_FORMAT} format" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        # Second invalid format (end_date)
        get_start_end_date("2023-01-01", "2023/13/01")
    assert f"End date must be in {DATE_FORMAT} format" in str(exc_info.value)
