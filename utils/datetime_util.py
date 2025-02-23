# -*- coding: utf-8 -*-
from datetime import datetime, timedelta


def get_start_end_date(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Get the start and end dates for the market data
    If the end_date is not provided, use yesterday's date
    If the start_date is not provided, use one year before the end_date
    Return the start and end dates in the format of YYYY-MM-DD
    """

    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    end_date = end_date or yesterday.strftime("%Y-%m-%d")

    # Ensure end_date is not in the future
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    if end_date_obj > yesterday:
        end_date = yesterday.strftime("%Y-%m-%d")
        end_date_obj = yesterday

    if not start_date:
        # Calculate 1 year before end_date
        start_date = end_date_obj - timedelta(days=365)
        start_date = start_date.strftime("%Y-%m-%d")

    return start_date, end_date
