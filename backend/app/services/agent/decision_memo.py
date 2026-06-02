from .base_agent import BaseAgent, _fmt


class DecisionMemoAgent(BaseAgent):
    agent_name = "decision_memo"

    def _build_prompt(self, context: dict) -> str:
        scoring_criteria = self.config.scoring_criteria or {}
        return (
            f"Ticker: {context['ticker']}\n"
            f"Current price: {context['financial_data'].get('current_price')}\n\n"
            f"Scoring criteria: {scoring_criteria}\n\n"
            f"=== AGENT OUTPUTS ===\n\n"
            f"1. Snapshot:\n{context.get('snapshot', {})}\n\n"
            f"2. Market belief:\n{context.get('market_belief', {})}\n\n"
            f"3. Variant perception:\n{context.get('variant_perception', {})}\n\n"
            f"4. Asymmetry:\n{context.get('asymmetry', {})}\n\n"
            f"5. Red flags:\n{context.get('red_flags', {})}"
        )
