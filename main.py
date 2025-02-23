# -*- coding: utf-8 -*-
import argparse
import json

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from agents.market_data import market_data_agent
from agents.portfolio_manager import portfolio_management_agent
from agents.risk_manager import risk_management_agent
from graph.state import AgentState
from utils.analysts import get_analyst_nodes
from utils.datetime_util import get_start_end_date
from utils.display import print_trading_output
from utils.my_logging import get_logger, log_entry_exit

_log = get_logger(__name__)

load_dotenv()


@log_entry_exit
def parse_final_state_response(response):
    try:
        return json.loads(response)
    except Exception as e:
        _log.exception(f"Error parsing response: {e}")
        return None


def run_a_share(
    ticker: str, start_date: str, end_date: str, portfolio: dict, show_reasoning: bool = False, num_of_news: int = 5
):

    start_date, end_date = get_start_end_date(start_date, end_date)
    _log.info(f"start_date: {start_date}, end_date: {end_date}")

    workflow = create_workflow()
    app = workflow.compile()
    final_state = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Make a trading decision based on the provided data.",
                    name=run_a_share.__name__,
                )
            ],
            "data": {
                "ticker": ticker,
                "portfolio": portfolio,
                "start_date": start_date,
                "end_date": end_date,
                "num_of_news": num_of_news,
                "analyst_signals": {},
            },
            "metadata": {
                "show_reasoning": show_reasoning,
            },
        },
    )

    return {
        "decisions": {ticker: parse_final_state_response(final_state["messages"][-1].content)},
        "analyst_signals": final_state["data"]["analyst_signals"],
    }


def create_workflow():
    # Define the new workflow
    workflow = StateGraph(AgentState)

    # Start node
    workflow.add_node("market_data_agent", market_data_agent)
    workflow.set_entry_point("market_data_agent")

    # Get analyst nodes from the configuration
    analyst_nodes = get_analyst_nodes()
    selected_analysts = list(analyst_nodes.keys())
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("market_data_agent", node_name)

    # Always add risk and portfolio management
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_management_agent", portfolio_management_agent)

    # Connect selected analysts to risk management
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "risk_management_agent")

    workflow.add_edge("risk_management_agent", "portfolio_management_agent")
    workflow.add_edge("portfolio_management_agent", END)

    return workflow


# Add this at the bottom of the file
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD). Defaults to 1 year before end date")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to yesterday")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument(
        "--num-of-news", type=int, default=5, help="Number of news articles to analyze for sentiment (default: 5)"
    )
    parser.add_argument(
        "--initial-capital", type=float, default=100000.0, help="Initial cash amount (default: 100,000)"
    )
    parser.add_argument("--initial-position", type=int, default=0, help="Initial stock position (default: 0)")

    args = parser.parse_args()

    # Validate num_of_news
    if args.num_of_news < 1:
        raise ValueError("Number of news articles must be at least 1")
    if args.num_of_news > 100:
        raise ValueError("Number of news articles cannot exceed 100")

    # Configure portfolio
    portfolio = {"cash": args.initial_capital, "stock": args.initial_position}

    result = run_a_share(
        ticker=args.ticker,
        start_date=args.start_date,
        end_date=args.end_date,
        portfolio=portfolio,
        show_reasoning=args.show_reasoning,
        num_of_news=args.num_of_news,
    )
    _log.info(f"\nFinal Result:\n{result}")
    print_trading_output(result)
