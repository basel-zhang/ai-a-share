# -*- coding: utf-8 -*-

import ast
import json
import math

from langchain_core.messages import HumanMessage

from agents.a_share_data import a_share_data_agent
from agents.fundamentals import fundamentals_agent
from agents.sentiment import sentiment_agent
from agents.technicals import technical_analyst_agent
from agents.valuation import valuation_agent
from graph.state import AgentState, show_agent_reasoning
from utils.my_logging import get_logger

_log = get_logger(__name__)


##### Risk Management Agent #####


def risk_management_agent(state: AgentState):
    """Evaluates portfolio risk and sets position limits based on comprehensive risk analysis."""

    _log.debug(f"Received {len(state['messages'])} messages")
    for msg in state["messages"]:
        _log.debug(f"Message from {msg.name}: {msg.content}")

    show_reasoning = state["metadata"]["show_reasoning"]
    portfolio = state["data"]["portfolio"]
    data = state["data"]
    tickers = data["tickers"]

    risk_analysis = {}
    for ticker in tickers:
        prices_df = data[a_share_data_agent.__name__][ticker]["prices"]

        # Fetch messages from other agents
        technical_message = next(msg for msg in state["messages"] if msg.name == technical_analyst_agent.__name__)
        fundamentals_message = next(msg for msg in state["messages"] if msg.name == fundamentals_agent.__name__)
        sentiment_message = next(msg for msg in state["messages"] if msg.name == sentiment_agent.__name__)
        valuation_message = next(msg for msg in state["messages"] if msg.name == valuation_agent.__name__)

        # Parse messages into dictionaries
        try:
            fundamental_signals = json.loads(fundamentals_message.content)[ticker]
            technical_signals = json.loads(technical_message.content)[ticker]
            sentiment_signals = json.loads(sentiment_message.content)[ticker]
            valuation_signals = json.loads(valuation_message.content)[ticker]
        except Exception as e:
            _log.exception("Error parsing message content:")
            fundamental_signals = ast.literal_eval(fundamentals_message.content)
            technical_signals = ast.literal_eval(technical_message.content)
            sentiment_signals = ast.literal_eval(sentiment_message.content)
            valuation_signals = ast.literal_eval(valuation_message.content)

        agent_signals = {
            "fundamental": fundamental_signals,
            "technical": technical_signals,
            "sentiment": sentiment_signals,
            "valuation": valuation_signals,
        }

        # 1. Calculate Risk Metrics
        returns = prices_df["close"].pct_change().dropna()
        daily_vol = returns.std()
        # Annualized volatility approximation
        volatility = daily_vol * (252**0.5)

        # 计算波动率的历史分布
        rolling_std = returns.rolling(window=120).std() * (252**0.5)
        volatility_mean = rolling_std.mean()
        volatility_std = rolling_std.std()
        volatility_percentile = (volatility - volatility_mean) / volatility_std

        # Simple historical VaR at 95% confidence
        var_95 = returns.quantile(0.05)
        # 使用60天窗口计算最大回撤
        max_drawdown = (prices_df["close"] / prices_df["close"].rolling(window=60).max() - 1).min()

        # 2. Market Risk Assessment
        market_risk_score = 0

        # Volatility scoring based on percentile
        if volatility_percentile > 1.5:  # 高于1.5个标准差
            market_risk_score += 2
        elif volatility_percentile > 1.0:  # 高于1个标准差
            market_risk_score += 1

        # VaR scoring
        # Note: var_95 is typically negative. The more negative, the worse.
        if var_95 < -0.03:
            market_risk_score += 2
        elif var_95 < -0.02:
            market_risk_score += 1

        # Max Drawdown scoring
        if max_drawdown < -0.20:  # Severe drawdown
            market_risk_score += 2
        elif max_drawdown < -0.10:
            market_risk_score += 1

        # 3. Position Size Limits
        # Consider total portfolio value, not just cash
        current_stock_value = portfolio["stock"] * prices_df["close"].iloc[-1]
        total_portfolio_value = portfolio["cash"] + current_stock_value

        # Start with 25% max position of total portfolio
        base_position_size = total_portfolio_value * 0.25

        if market_risk_score >= 4:
            # Reduce position for high risk
            max_position_size = base_position_size * 0.5
        elif market_risk_score >= 2:
            # Slightly reduce for moderate risk
            max_position_size = base_position_size * 0.75
        else:
            # Keep base size for low risk
            max_position_size = base_position_size

        # 4. Stress Testing
        stress_test_scenarios = {"market_crash": -0.20, "moderate_decline": -0.10, "slight_decline": -0.05}

        stress_test_results = {}
        current_position_value = current_stock_value

        for scenario, decline in stress_test_scenarios.items():
            potential_loss = current_position_value * decline
            portfolio_impact = (
                potential_loss / (portfolio["cash"] + current_position_value)
                if (portfolio["cash"] + current_position_value) != 0
                else math.nan
            )
            stress_test_results[scenario] = {"potential_loss": potential_loss, "portfolio_impact": portfolio_impact}

        # 5. Risk-Adjusted Signals Analysis
        low_confidence = any(signal["confidence"] < 30 for signal in agent_signals.values())

        # Check the diversity of signals. If all three differ, add to risk score
        # (signal divergence can be seen as increased uncertainty)
        unique_signals = set(signal["signal"] for signal in agent_signals.values())
        signal_divergence = 2 if len(unique_signals) == 3 else 0

        # Market risk contributes up to ~6 points total when doubled
        risk_score = market_risk_score + (2 if low_confidence else 0)
        risk_score += signal_divergence

        # Cap risk score at 10
        risk_score = min(round(risk_score), 10)

        # 6. Generate Trading Action
        # If risk is very high, hold. If moderately high, consider reducing.
        # Else, follow valuation signal as a baseline.
        if risk_score >= 9:
            trading_action = "hold"
        elif risk_score >= 7:
            trading_action = "reduce"
        else:
            # Consider both valuation and price drop signals
            if agent_signals["technical"]["signal"] == "bullish" and agent_signals["technical"]["confidence"] > 50:
                trading_action = "buy"
            else:
                trading_action = agent_signals["valuation"]["signal"]

        risk_analysis[ticker] = {
            "max_position_size": float(max_position_size),
            "risk_score": risk_score,
            "trading_action": trading_action,
            "risk_metrics": {
                "volatility": float(volatility),
                "value_at_risk_95": float(var_95),
                "max_drawdown": float(max_drawdown),
                "market_risk_score": market_risk_score,
                "stress_test_results": stress_test_results,
            },
            "reasoning": f"Risk Score {risk_score}/10: Market Risk={market_risk_score}, "
            f"Volatility={volatility:.2%}, VaR={var_95:.2%}, "
            f"Max Drawdown={max_drawdown:.2%}",
        }

    # Create the risk management message
    message = HumanMessage(
        content=json.dumps(risk_analysis),
        name=risk_management_agent.__name__,
    )

    if show_reasoning:
        show_agent_reasoning(risk_analysis, "Risk Management Agent")

    state["data"]["analyst_signals"][risk_management_agent.__name__] = risk_analysis

    _log.debug(f"message.content: {message.content}")
    _log.debug(f"state['messages'][-1].content: {state['messages'][-1].content}")

    return {
        "messages": state["messages"] + [message],
        "data": data,
    }
