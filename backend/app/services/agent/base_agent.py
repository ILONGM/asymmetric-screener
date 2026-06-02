"""
BaseAgent — parent class for all 6 sub-agents.

Each sub-agent:
  1. Loads its active system_prompt from agent_configs (versioned in DB)
  2. Builds a user message from the shared context dict
  3. Calls Claude
  4. Parses the response (JSON expected)
  5. Persists raw + parsed output to agent_step_outputs (full audit trail)
  6. Returns parsed dict to the orchestrator
"""
from __future__ import annotations

import json
import re
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.models.tables import AgentConfig, AgentStepOutput

CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


class BaseAgent(ABC):
    agent_name: str  # must be defined on each subclass

    def __init__(self, db: Session, client: Anthropic, recommendation_id: uuid.UUID):
        self.db = db
        self.client = client
        self.recommendation_id = recommendation_id
        self.config = self._load_config()

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def _load_config(self) -> AgentConfig:
        config = (
            self.db.query(AgentConfig)
            .filter(
                AgentConfig.agent_name == self.agent_name,
                AgentConfig.is_active == True,
            )
            .order_by(AgentConfig.created_at.desc())
            .first()
        )
        if not config:
            raise ValueError(
                f"No active config in agent_configs for agent_name='{self.agent_name}'. "
                "Run scripts/seed_agent_configs.py first."
            )
        return config

    # ------------------------------------------------------------------
    # Claude call
    # ------------------------------------------------------------------

    def _call_claude(self, user_content: str) -> tuple[str, int]:
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=self.config.system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        text = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist(
        self,
        raw_output: str,
        parsed_output: Optional[dict],
        tokens: int,
        duration_ms: int,
    ) -> None:
        step = AgentStepOutput(
            id=uuid.uuid4(),
            recommendation_id=self.recommendation_id,
            agent_name=self.agent_name,
            agent_config_id=self.config.id,
            raw_output=raw_output,
            parsed_output=parsed_output,
            tokens_used=tokens,
            duration_ms=duration_ms,
            created_at=datetime.utcnow(),
        )
        self.db.add(step)
        self.db.commit()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, context: dict) -> dict:
        t0 = time.time()
        user_content = self._build_prompt(context)
        raw, tokens = self._call_claude(user_content)
        parsed = _extract_json(raw)
        duration_ms = int((time.time() - t0) * 1000)
        self._persist(raw, parsed, tokens, duration_ms)
        return parsed

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_prompt(self, context: dict) -> str:
        """Build the user message from the shared context dict."""
        ...


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Extract JSON from Claude's response, handling optional ```json fences."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    return {"raw": text}


def _fmt(data: dict) -> str:
    """Format a dict as a readable block for injection into prompts."""
    lines = []
    for k, v in data.items():
        if v is not None:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)
