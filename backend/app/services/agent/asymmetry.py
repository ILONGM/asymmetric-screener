from .base_agent import BaseAgent, _fmt


class AsymmetryAgent(BaseAgent):
    agent_name = "asymmetry"

    def _build_prompt(self, context: dict) -> str:
        return (
            f"Ticker: {context['ticker']}\n"
            f"Current price: {context['financial_data'].get('current_price')}\n"
            f"Market cap: {context['financial_data'].get('market_cap')}\n"
            f"EV: {context['financial_data'].get('enterprise_value')}\n\n"
            f"Financial data:\n{_fmt(context['financial_data'])}\n\n"
            f"Snapshot:\n{context.get('snapshot', {})}\n\n"
            f"Market belief:\n{context.get('market_belief', {})}\n\n"
            f"Variant perception:\n{context.get('variant_perception', {})}"
        )
