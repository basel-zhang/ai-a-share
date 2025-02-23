import os

from dotenv import load_dotenv

from utils.my_tushare import convert_to_tushare_code, get_pro_api

load_dotenv()
print(os.getenv("TUSHARE_TOKEN"))

pro = get_pro_api()

ts_code = convert_to_tushare_code("301157")

print(
    pro.bak_daily(
        ts_code=ts_code,
        start_date="20250220",
        end_date="20250221",
        fields="trade_date,open,high,low,close,vol,amount,swing,pct_change,change,turn_over",
    )
)
