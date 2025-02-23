# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"


def get_start_end_date(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Get the start and end dates for the market data
    If the end_date is not provided, use yesterday's date
    If the start_date is not provided, use one year before the end_date
    Return the start and end dates in the format of YYYY-MM-DD
    """

    # Validate dates
    if start_date:
        try:
            datetime.strptime(start_date, DATE_FORMAT)
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format")

    if end_date:
        try:
            datetime.strptime(end_date, DATE_FORMAT)
        except ValueError:
            raise ValueError("End date must be in YYYY-MM-DD format")

    # If both dates are given, and start date is later then end date, raise error
    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date cannot be after end date")

    # If end date is not provided, use yesterday's date
    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    end_date = end_date or yesterday.strftime(DATE_FORMAT)

    # Ensure end_date is not in the future
    end_date_obj = datetime.strptime(end_date, DATE_FORMAT)
    if end_date_obj > yesterday:
        end_date = yesterday.strftime(DATE_FORMAT)
        end_date_obj = yesterday

    if not start_date:
        # Calculate 1 year before end_date
        start_date = end_date_obj - timedelta(days=365)
        start_date = start_date.strftime(DATE_FORMAT)

    return start_date, end_date
