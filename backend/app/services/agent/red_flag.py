from .base_agent import BaseAgent, _fmt


class RedFlagAgent(BaseAgent):
    agent_name = "red_flag"

    def _build_prompt(self, context: dict) -> str:
        return (
            f"Ticker: {context['ticker']}\n\n"
            f"Financial data:\n{_fmt(context['financial_data'])}\n\n"
            f"Snapshot:\n{context.get('snapshot', {})}\n\n"
            f"Market belief:\n{context.get('market_belief', {})}\n\n"
            f"Variant perception:\n{context.get('variant_perception', {})}\n\n"
            f"Asymmetry analysis:\n{context.get('asymmetry', {})}"
        )
