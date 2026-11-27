# MCP Schema Contract & Silent-Failure Studio

Local-first interactive web application for inspecting MCP servers, tracking schema changes, testing tool contracts, and verifying actual tool outcomes.

**Current status (honest):**  
This is a working vertical slice. Scenarios A, B, C, D, E, and F are implemented and tested with live MCP calls against the bundled synthetic server. MCP Apps support is not implemented. The React frontend exists as source but is not the running application in this environment.

## What it does
- Connects to a bundled synthetic MCP server via the official Python MCP SDK (stdio).
- Takes persistent schema snapshots and shows tool inventory.
- Visual schema comparison (diff endpoint).
- Runs scenarios A–F with PASS / FAIL / UNKNOWN verdicts where the logic is complete.
- Independent read-back verification (scenario D).
- Test history and JSON reliability report.
- Token counts are explicitly labelled as estimates.

## Architecture
```
┌─────────────────────────┐     REST      ┌─────────────────┐     stdio     ┌─────────────────────┐
│ HTML Dashboard           │ ────────────► │ FastAPI Backend  │ ────────────► │ Synthetic MCP Server│
│ (frontend/public/        │               │ (MCP Client)     │               │ (Official SDK)      │
│  dashboard.html)         │               │                  │               │                     │
│                          │               └────────┬─────────┘               └──────────────────────┘
│ React source exists      │                        │
│ (not running here)       │                        ▼
└─────────────────────────┘                 SQLite (snapshots, runs, reviews)
```

## Quick Start (local only)

### 1. Backend
```bash
cd backend
python3 -m pip install mcp fastapi uvicorn
python3 main.py
```
Backend listens on http://127.0.0.1:8000

### 2. Dashboard (working entry point)
```bash
cd frontend/public
python3 -m http.server 5173
```
Open http://localhost:5173/dashboard.html

### 3. React frontend (optional, not required for demo)
The React source is present under `frontend/src/`. In this environment Vite could not be started due to install issues. On a normal machine:
```bash
cd frontend
npm install
npm run dev
```

### 4. Use the app
1. Click “Connect & Take Snapshot” (Scenario A).
2. Run Scenario C and D to exercise silent failure and independent read-back.
3. Diff two snapshots.
4. Copy the reliability report JSON.

## Mandatory Scenarios

| Scenario | Status | Notes |
|----------|--------|-------|
| A — Healthy connection + tool list | Implemented and tested | Live `tools/list` |
| B — Schema change detection | Implemented and tested | `control_schema_version` persists state; next process registers `dynamic_record` with required `priority` (breaking change). Diff shows schema change. |
| C — Silent failure (`is_error: false` but no persist) | Implemented and tested | Correctly flags FAIL |
| D — Independent read-back | Implemented and tested | Confirms missing record |
| E — Protocol-level error vs outcome failure | Implemented and tested | Server exception surfaces as `is_error=True` tool result (SDK behavior). Scenario checks the flag. |
| F — Verifier unavailable → UNKNOWN | Implemented and tested | Control sets verifier off; `get_record` returns `is_error=True`; scenario reports UNKNOWN. |

## Limitations (explicit)
- Only the bundled synthetic server is supported. Arbitrary user-provided commands are not executed.
- Token estimates are character-based approximations.
- **MCP Apps are not implemented.** The synthetic server imports `Apps()` but registers no `ui://` resource, sets no `_meta.ui.resourceUri`, and serves no MCP App HTML. This is a standalone web application that uses an MCP client.
- Schema changes (Scenario B) take effect on the next server process start (stdio client starts a fresh process per API call). After running B, take a new snapshot to observe the drift.
- Single-user local application. No authentication. Not deployed to production.
- The React interface is source only in this package; the running dashboard is the plain HTML file.

## Disclosure
All demonstration results come from live MCP protocol calls against the included synthetic server. No hardcoded metrics are shown in the UI after a real run.

See `docs/AUDIT.md` for the full engineering audit (27 Nov 2026).
