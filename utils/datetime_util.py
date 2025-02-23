# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"
TUSHARE_DATE_FORMAT = "%Y%m%d"


def get_start_end_date(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Get the start and end dates for the market data
    If the end_date is not provided, use yesterday's date
    If the start_date is not provided, use one year before the end_date
    Return the start and end dates in the format of YYYY-MM-DD
    """
    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    start_date_obj = None
    end_date_obj = None

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, DATE_FORMAT)
            if end_date_obj > yesterday:
                end_date_obj = yesterday
        except ValueError:
            raise ValueError(f"End date must be in {DATE_FORMAT} format")
    else:
        end_date_obj = yesterday

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, DATE_FORMAT)
        except ValueError:
            raise ValueError(f"Start date must be in {DATE_FORMAT} format")
    else:
        start_date_obj = end_date_obj - timedelta(days=365)

    if start_date_obj > end_date_obj:
        raise ValueError("Start date cannot be after end date")

    return start_date_obj.strftime(DATE_FORMAT), end_date_obj.strftime(DATE_FORMAT)


def get_tushare_date(date: str) -> str:
    """
    Convert a date string in the format of YYYY-MM-DD to a date string in the format of YYYYMMDD
    """
    try:
        return datetime.strptime(date, DATE_FORMAT).strftime(TUSHARE_DATE_FORMAT)
    except ValueError:
        raise ValueError(f"Date must be in {DATE_FORMAT} format")
