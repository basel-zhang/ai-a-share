# -*- coding: utf-8 -*-

import tushare as ts
import os
from dotenv import load_dotenv


def get_pro_api():
    """Get Tushare API"""

    # Get Tushare token from environment variables
    tushare_token = os.getenv("TUSHARE_TOKEN")
    if not tushare_token:
        raise ValueError("Tushare token not found in .env file. Please add TUSHARE_TOKEN=your_token")

    # Initialize tushare with token from .env
    ts.set_token(tushare_token)
    pro = ts.pro_api()
    return pro


# Convert regular stock code to tushare format
def convert_to_tushare_code(code: str) -> str:
    """
    Convert regular stock code to tushare format.
    Args:
        code: str, the regular stock code
    Returns:
        str, the tushare stock code
    """

    # Remove any existing suffixes
    code = code.split(".")[0]

    # Add appropriate suffix
    if code.startswith("6"):
        return f"{code}.SH"
    elif code.startswith(("0", "3")):
        return f"{code}.SZ"
    else:
        raise ValueError(f"Unsupported stock code format: {code}")
