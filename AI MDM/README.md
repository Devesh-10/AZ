# Agentic MDM POC

Conversational interface for Master Data Management with enforced governance
(search-before-create, duplicate detection, controlled merges).

Built with: **Claude (Bedrock) + LangGraph + FastAPI + React**.
Backend talks to a **mock Reltio** service that mirrors Reltio's REST API shape, so
swapping to a real Reltio tenant requires only changing `RELTIO_BASE_URL` and adding
`RELTIO_AUTH_TOKEN`.

## Architecture

```
React chat (5180)  →  LangGraph backend (3010)  →  Mock Reltio (8765)
                         ↑                              ↑
                      Bedrock                       in-memory store
                      Claude Sonnet 4.5             + JSON persist
```

## Run the stack

Three terminals.

**1. Mock Reltio**
```bash
cd mock-reltio
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn app.main:app --port 8765
```

**2. LangGraph backend** (needs AWS creds for Bedrock — same profile as mia-langgraph)
```bash
cd backend
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn app.main:app --port 3010
```

**3. Frontend**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5180

## Demo prompts

- `Add Dr. Sara Chen, oncologist in Boston MA` — finds 3 duplicates, asks for confirmation
- `Find all oncologists in Boston` — pure discovery query
- `Add Dr. Alex Kowalski, neurosurgeon in Pittsburgh PA, NPI 9988776655` — no duplicates, creates
- `Add a new hospital called Mass General Hospital in Boston MA` — HCO fuzzy match

## Switching to real Reltio

When the trial tenant is provisioned, set in `backend/.env`:
```
RELTIO_BASE_URL=https://<your-env>.reltio.com/reltio/api/<tenantId>
RELTIO_AUTH_TOKEN=<bearer token>
```
No code changes required. The mock and real Reltio share the same request/response shape.

## Reseed mock data

```bash
curl -X POST http://127.0.0.1:8765/_admin/reseed
```
