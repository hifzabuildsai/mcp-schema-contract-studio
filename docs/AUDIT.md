# Engineering Audit — MCP Schema Contract & Silent-Failure Studio
Audit date: 27 November 2026. Based on code inspection and live execution against the running backend.

## 1. Frontend Audit

**Is `frontend/src/App.tsx` used by the running application?**  
No. The React application is not the running entry point.

**Current running dashboard:**  
Plain HTML + JavaScript in `frontend/public/dashboard.html`, served by `python3 -m http.server`.

**Why:**  
Vite binary is missing (`node_modules/.bin/vite` does not exist). npm install failed with EPERM/EIO errors in this environment. The React source exists (`App.tsx`, `main.tsx`, `index.html`) but cannot be compiled or served.

**Primary entry point:**  
`frontend/public/dashboard.html` (documented in README). The React scaffolding is unused for the current demo.

## 2. MCP Apps Compatibility Audit

**Status: NOT IMPLEMENTED.**

Evidence from `synthetic-server/server.py`:
- Imports `Apps()` and passes `extensions=[apps]` to `MCPServer`.
- Does **not** register any `ui://` resource.
- Does **not** set `_meta.ui.resourceUri` on any tool.
- Does **not** serve HTML with MIME type `text/html;profile=mcp-app`.
- No embedded UI communication with an MCP host.
- No compatible host testing was performed.

This is a standalone web application that uses an MCP client (in the FastAPI backend) to talk to an MCP server. It is not an MCP App.

## 3. Functional Test Audit (live runs)

### Scenario A — Implemented and tested
- Request: `POST /api/scenarios/A`
- Result: `{"verdict":"PASS","details":[{"tools":8}]}`
- Evidence: Live `tools/list` returned 8 tools.

### Scenario C — Implemented and tested
- Request: `POST /api/scenarios/C` → calls `create_record_silent_fail`
- Response: `isError: false`, content contains `"persisted": false`
- Verdict: FAIL
- Correctly does not treat `isError: false` as proof of business success.

### Scenario D — Implemented and tested
- Request: `POST /api/scenarios/D` → calls `get_record` with missing ID
- Response: `{"found": false, "record": null}`
- Verdict: FAIL
- Independent read-back confirmed absence.

### Scenario B — Implemented and tested
- `control_schema_version` persists state to `/tmp/mcp_studio_synthetic_state.json`.
- Next server process (new stdio connection) loads the version and registers `dynamic_record` with different input schema (`priority` required when version > 1).
- Snapshot hashes differ; diff endpoint reports schema_changed with breaking=true.

### Scenario E — Implemented and tested
- `force_protocol_error` raises ValueError.
- Official SDK converts the exception into a `CallToolResult` with `is_error=True` and content describing the error.
- Scenario checks `res.is_error` and correctly classifies as protocol-level error (FAIL).

### Scenario F — Implemented and tested
- `control_verifier(available=False)` persists the flag.
- Subsequent `get_record` raises; SDK returns `is_error=True`.
- Scenario detects the flag and returns UNKNOWN. Verifier is reset afterward.

### Persistence
- SQLite file `backend/studio.db` survives process restart.
- Snapshots and test_runs rows remain after backend restart.
- Diff endpoint previously crashed on key mismatch (`input_schema` vs `inputSchema`); fixed in this audit. Now returns 200.

### Database evidence (after test suite)
- Snapshots: 3 rows, hashes identical.
- Test runs: 8+ rows with A/PASS, C/FAIL, D/FAIL, E/FAIL, B/FAIL, F/UNKNOWN.

## 4. Product Quality Audit

**Working:**
- Health endpoint
- Snapshot creation and listing
- Scenario A, B, C, D, E, F end-to-end
- SQLite persistence across restart
- Synthetic state persistence (schema version, records)
- Report endpoint
- Diff endpoint (after key fix)

**Bugs found and fixed:**
- Diff endpoint KeyError on `input_schema` (stored JSON uses `inputSchema`). Fixed.
- Scenarios B/E/F incomplete — fixed by persisting state and checking `is_error` on tool results.

**Remaining issues:**
- React frontend cannot be started in this environment.
- No automated test suite beyond manual runs.
- Empty states and connection-failure paths are not fully exercised in the UI.
- MCP Apps not implemented.

## 5. Release Status

**Implemented and tested:**
- Backend MCP client connection to synthetic server
- Snapshot storage and listing
- Silent-failure detection (C)
- Independent read-back (D)
- Schema drift detection (B) via persisted state + dynamic tool registration
- Protocol error distinction via `is_error=True` (E)
- Reliable UNKNOWN path via verifier control (F)
- SQLite persistence
- HTML dashboard that calls the API
- Report JSON

**Implemented but not correctly tested / incomplete:**
- Diff visualization of real breaking changes (now functional after B)

**Not implemented:**
- MCP Apps (`ui://` resource, `_meta.ui.resourceUri`, host embedding, host testing)
- Running React application
- Automated test suite
- Arbitrary server connection (intentionally excluded)

## Known Limitations (accurate)
- Only the bundled synthetic server is supported.
- Token estimates are character-based approximations.
- Schema changes (Scenario B) take effect on the next server process start.
- SDK exception handling means protocol errors appear as tool results with `is_error=True` rather than raised client exceptions.
- MCP Apps is not implemented.
- Primary UI is the static HTML dashboard.

## Demo Recording Plan (honest)
1. Start backend and serve `dashboard.html`.
2. Click Connect & Take Snapshot (A).
3. Run Scenario B, then take a new snapshot and show the diff (dynamic_record now requires priority).
4. Run Scenario C — show FAIL with `is_error: false` and `persisted: false`.
5. Run Scenario D — show FAIL with `found: false`.
6. Run Scenario E — show protocol error via `is_error=True`.
7. Run Scenario F — show UNKNOWN when verifier unavailable.
8. Show report JSON. Note MCP Apps is not implemented.
