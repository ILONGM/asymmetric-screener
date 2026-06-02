from .base_agent import BaseAgent, _fmt


class SnapshotAgent(BaseAgent):
    agent_name = "snapshot"

    def _build_prompt(self, context: dict) -> str:
        return (
            f"Ticker: {context['ticker']}\n\n"
            f"Financial data:\n{_fmt(context['financial_data'])}"
        )
