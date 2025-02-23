# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from common.datetime_util import get_start_end_date


def test_get_start_end_date_with_both_dates_provided():
    # Arrange
    state = {"messages": [], "data": {"start_date": "2023-01-01", "end_date": "2023-01-07"}, "metadata": {}}

    # Act
    start, end = get_start_end_date(state)

    # Assert
    assert start == "2023-01-01"
    assert end == "2023-01-07"


def test_get_start_end_date_with_only_start_date_provided():
    # Arrange
    state = {"messages": [], "data": {"start_date": "2023-01-01", "end_date": None}, "metadata": {}}

    # Act
    start, end = get_start_end_date(state)

    # Assert
    assert start == "2023-01-01"
    assert end == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def test_get_start_end_date_with_only_end_date_provided():
    # Arrange
    state = {"messages": [], "data": {"start_date": None, "end_date": "2023-01-07"}, "metadata": {}}

    # Act
    start, end = get_start_end_date(state)

    # Assert
    expected_start = (datetime.strptime("2023-01-07", "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    assert start == expected_start
    assert end == "2023-01-07"


def test_get_start_end_date_with_no_dates_provided():
    # Arrange
    state = {"messages": [], "data": {"start_date": None, "end_date": None}, "metadata": {}}

    # Act
    start, end = get_start_end_date(state)

    # Assert
    expected_end = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    expected_start = (datetime.now() - timedelta(days=366)).strftime("%Y-%m-%d")
    assert start == expected_start
    assert end == expected_end
