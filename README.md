# Asymmetric Returns Stock Screener

An AI-powered investment analysis agent that identifies disruptive technology sectors and companies with asymmetric return potential — stocks where a realistic path to 5–10x exists, even if the probability is low.

> Think venture capital logic applied to public markets: nine bets may fail, but one transformational win covers everything.

---

## What it does

Every week, the agent produces a report of **5 stock picks**, each with:
- A full investment thesis (why this company, why now)
- The disruption vector it's exposed to (e.g. robotics, photonics, space economy)
- The blockers that previously limited this technology and why they're now unlocked
- A realistic scenario where the stock reaches 5–10x

Recommendations are stored historically so you can track how theses perform over time.

---

## Architecture

```
Asym_AI/
├── backend/          # Python + FastAPI
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── services/     # Business logic + AI agent
│   │   ├── repositories/ # Database access layer
│   │   ├── models/       # SQLAlchemy models
│   │   └── core/         # Config, auth, scheduler
│   └── migrations/       # Alembic DB migrations
├── frontend/         # React
│   └── src/
└── docs/             # Architecture decisions, rules config
```

**Stack:**
- Backend: Python 3.11, FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL
- AI: Claude API (Anthropic) for thesis generation
- Auth: Google OAuth
- Frontend: React
- Deployment: Railway (backend + DB), Vercel (frontend)
- Scheduler: Cron job (weekly, Monday morning)

---

## How the agent works

The agent runs in two phases:

**Phase 1 — Sector identification** (v1: manually configured, v2: automated)
Define which disruption sectors are active (e.g. robotics, photonics, space economy). For each sector, understand what previously blocked it and what recent factor unlocked it.

**Phase 2 — Company analysis**
For each sector, find listed companies positioned to benefit. Evaluate whether a realistic 5–10x path exists given the company's market position, R&D, and the size of the addressable market if the disruption succeeds.

**Phase 3 — Thesis generation**
Pass the top candidates to Claude API. It writes a structured investment thesis for each pick.

This architecture allows the business rules in Phase 1 and 2 to evolve independently — from manual config today to fully automated detection later — without touching the thesis generation or storage logic.

---

## Roadmap

| Version | What's included |
|---------|----------------|
| v1 | Manual sector input, basic company analysis, Claude-generated theses, web dashboard |
| v2 | Automated disruption sector detection (news, patents, R&D signals) |
| v3 | Backtesting layer — track how past recommendations performed |

---

## Getting started (local development)

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL

```bash
# Clone
git clone https://github.com/<your-handle>/asym-ai.git
cd asym-ai

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Environment variables

```
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SECRET_KEY=...
```
