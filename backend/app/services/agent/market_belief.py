from .base_agent import BaseAgent, _fmt


class MarketBeliefAgent(BaseAgent):
    agent_name = "market_belief"

    def _build_prompt(self, context: dict) -> str:
        return (
            f"Ticker: {context['ticker']}\n\n"
            f"Financial data:\n{_fmt(context['financial_data'])}\n\n"
            f"Company snapshot:\n{context.get('snapshot', {})}"
        )
