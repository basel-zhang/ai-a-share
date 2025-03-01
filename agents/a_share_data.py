# -*- coding: utf-8 -*-
import pandas as pd

from graph.state import AgentState
from tools.api import get_financial_metrics, get_financial_statements, get_market_data, get_price_history
from utils.my_logging import get_logger

_log = get_logger(__name__)


def a_share_data_agent(state: AgentState):
    """Responsible for gathering and preprocessing market data"""
    messages = state["messages"]

    _log.debug(f"Received {len(messages)} messages")
    for msg in messages:
        _log.debug(f"Message from {msg.name}: {msg.content}")

    data = state["data"]

    # Get all required data
    tickers = data["tickers"]
    _log.info(f"tickers: {tickers}")

    start_date = data["start_date"]
    end_date = data["end_date"]

    a_share_data = {}

    for ticker in tickers:
        _log.info(f"Fetching data for {ticker}")
        # 获取价格数据并验证
        prices_df = get_price_history(ticker, start_date, end_date)
        if prices_df is None or prices_df.empty:
            _log.error(f"Unable to fetch price data for {ticker}, continuing with empty data")
            prices_df = pd.DataFrame(columns=["close", "open", "high", "low", "volume"])
        # 获取财务指标
        try:
            financial_metrics = get_financial_metrics(ticker)
        except Exception as e:
            _log.exception("获取财务指标失败:")
            financial_metrics = {}
        # 获取财务报表
        try:
            financial_line_items = get_financial_statements(ticker)
        except Exception as e:
            _log.exception("获取财务报表失败:")
            financial_line_items = {}
        # 获取市场数据
        try:
            market_data = get_market_data(ticker)
        except Exception as e:
            _log.exception("获取市场数据失败:")
            market_data = {"market_cap": 0}
        # 确保数据格式正确
        if not isinstance(prices_df, pd.DataFrame):
            prices_df = pd.DataFrame(columns=["close", "open", "high", "low", "volume"])
        a_share_data[ticker] = {
            "prices": prices_df,
            "financial_metrics": financial_metrics,
            "financial_line_items": financial_line_items,
            "market_cap": market_data.get("market_cap", 0),
            "market_data": market_data,
        }

    data[a_share_data_agent.__name__] = a_share_data

    _log.debug(f"messages[-1].content: {messages[-1].content}")

    return {
        "messages": [],
        "data": data,
    }
