from .base_agent import BaseAgent, _fmt


class VariantPerceptionAgent(BaseAgent):
    agent_name = "variant_perception"

    def _build_prompt(self, context: dict) -> str:
        return (
            f"Ticker: {context['ticker']}\n\n"
            f"Financial data:\n{_fmt(context['financial_data'])}\n\n"
            f"Company snapshot:\n{context.get('snapshot', {})}\n\n"
            f"Market belief:\n{context.get('market_belief', {})}"
        )
