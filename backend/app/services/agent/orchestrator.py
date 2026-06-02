"""
AgentOrchestrator — runs the 6-agent pipeline for a single ticker.

Flow:
  1. Fetch financial data (yfinance)
  2. Create a placeholder Recommendation in DB (needed for FK in agent_step_outputs)
  3. Run agents in sequence, accumulating context
  4. Handle vetos: VariantPerception (no variant) and RedFlag (fatal issue)
  5. Fill the Recommendation with the final Decision Memo output
"""
from __future__ import annotations

import uuid
from datetime import datetime

from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.models.tables import Recommendation
from . import data_fetcher
from .asymmetry import AsymmetryAgent
from .decision_memo import DecisionMemoAgent
from .market_belief import MarketBeliefAgent
from .red_flag import RedFlagAgent
from .snapshot import SnapshotAgent
from .variant_perception import VariantPerceptionAgent


class AgentOrchestrator:
    def __init__(self, db: Session, client: Anthropic):
        self.db = db
        self.client = client

    def analyze(
        self,
        ticker: str,
        run_id: uuid.UUID,
        sector_id: uuid.UUID,
        workflow_version: str = "v1.0",
    ) -> Recommendation:
        # ── 1. Fetch financial data ───────────────────────────────────────
        financial_data = data_fetcher.fetch(ticker)
        context: dict = {
            "ticker": ticker,
            "financial_data": financial_data,
        }

        # ── 2. Create placeholder recommendation ─────────────────────────
        rec = Recommendation(
            id=uuid.uuid4(),
            run_id=run_id,
            sector_id=sector_id,
            workflow_version=workflow_version,
            ticker=ticker,
            company_name=financial_data.get("name") or ticker,
            price_at_analysis=financial_data.get("current_price"),
            created_at=datetime.utcnow(),
        )
        self.db.add(rec)
        self.db.commit()

        # ── 3. Agent pipeline ─────────────────────────────────────────────
        def make(cls):
            return cls(self.db, self.client, rec.id)

        # Agent 1 — Snapshot
        context["snapshot"] = make(SnapshotAgent).run(context)

        # Agent 2 — Market Belief
        context["market_belief"] = make(MarketBeliefAgent).run(context)

        # Agent 3 — Variant Perception (can trigger NO-GO)
        vp = make(VariantPerceptionAgent).run(context)
        context["variant_perception"] = vp
        if vp.get("no_go"):
            return self._finalize(rec, verdict="NO-GO", one_liner=vp.get("no_go_reason"))

        # Agent 4 — Asymmetry Engine
        context["asymmetry"] = make(AsymmetryAgent).run(context)

        # Agent 5 — Red Flag Killer (can trigger NO-GO veto)
        flags = make(RedFlagAgent).run(context)
        context["red_flags"] = flags
        if flags.get("fatal_veto"):
            return self._finalize(
                rec,
                verdict="NO-GO",
                one_liner=flags.get("veto_reason"),
                red_flags_fatal=flags.get("fatal_flags"),
            )

        # Agent 6 — Decision Memo
        memo = make(DecisionMemoAgent).run(context)
        return self._finalize(rec, memo=memo, flags=flags, vp=vp, context=context)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _finalize(
        self,
        rec: Recommendation,
        verdict: str = "NO-GO",
        one_liner: str | None = None,
        red_flags_fatal: str | None = None,
        memo: dict | None = None,
        flags: dict | None = None,
        vp: dict | None = None,
        context: dict | None = None,
    ) -> Recommendation:
        if memo:
            score = memo.get("score_breakdown", {})
            rec.verdict = memo.get("verdict", verdict)
            rec.one_liner = memo.get("one_liner")
            rec.why_now = memo.get("why_now")
            rec.thesis = memo.get("thesis")
            rec.score_total = memo.get("score_total")
            rec.score_breakdown = score
            rec.next_analyses = memo.get("next_analyses")
        else:
            rec.verdict = verdict
            rec.one_liner = one_liner

        if vp:
            rec.variant_perception_candidates = vp.get("candidates")
            rec.variant_perception_best = vp.get("best")

        if flags:
            rec.red_flags_fatal = flags.get("fatal_flags")
            rec.red_flags_non_fatal = str(flags.get("non_fatal_flags", ""))
            rec.information_missing = str(flags.get("information_missing", ""))

        if context:
            asym = context.get("asymmetry", {})
            rec.scenarios = asym.get("scenarios")
            if asym.get("scenarios"):
                bull = next(
                    (s for s in asym["scenarios"] if s.get("label") == "Bull"), None
                )
                if bull:
                    rec.target_multiplier = round(
                        (100 + bull.get("upside_pct", 0)) / 100, 1
                    )
            mb = context.get("market_belief", {})
            rec.market_belief = mb.get("market_belief")

        if red_flags_fatal:
            rec.red_flags_fatal = red_flags_fatal

        self.db.commit()
        return rec
