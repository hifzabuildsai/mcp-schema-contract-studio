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

### Scenario B — Partially implemented, not correctly tested
- `control_schema_version` only mutates in-memory `STATE["schema_version"]`.
- The actual `tools/list` schemas do not change.
- Snapshot hashes before and after are identical (`3c1733de929b1c1e`).
- Diff of snapshots 2 and 3 returns `{"changes":[],"breaking_count":0}`.
- The FAIL verdict is based on the control call, not on detected schema drift.

### Scenario E — Implemented but behavior differs from intent
- `force_protocol_error` raises `ValueError` on the server.
- The official SDK converts this into a tool result containing the text `"Error executing tool force_protocol_error"`.
- The client does not receive a raised exception or `isError: true`.
- Current scenario logic records `raised: false` and still returns FAIL.
- Does not cleanly distinguish protocol-level error from business-outcome failure.

### Scenario F — Implemented but unreliable
- Setting `verifier_available = False` causes `get_record` to raise.
- The SDK converts the exception into tool content (`"Error executing tool get_record"`).
- The endpoint previously returned 500 on DB write under load; later runs can succeed with UNKNOWN.
- Does not reliably produce a clean UNKNOWN based on verifier unavailability.

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
- Scenario A, C, D end-to-end
- SQLite persistence across restart
- Report endpoint
- Diff endpoint (after key fix)

**Bugs found and fixed:**
- Diff endpoint KeyError on `input_schema` (stored JSON uses `inputSchema`). Fixed.

**Remaining issues:**
- Scenario B does not produce real schema drift.
- Scenario E/F do not match the intended protocol-error vs UNKNOWN semantics because the SDK converts exceptions into tool content.
- Scenario F previously caused 500 on concurrent DB writes (disk I/O error under load).
- React frontend cannot be started in this environment.
- No automated test suite beyond manual curl runs.
- Empty states and connection-failure paths are not fully exercised in the UI.

## 5. Release Status

**Implemented and tested:**
- Backend MCP client connection to synthetic server
- Snapshot storage and listing
- Silent-failure detection (C)
- Independent read-back (D)
- SQLite persistence
- HTML dashboard that calls the API
- Report JSON

**Implemented but not correctly tested / incomplete:**
- Schema drift detection (B) — control exists, actual schema does not change
- Protocol error distinction (E)
- Reliable UNKNOWN path (F)
- Diff visualization of real breaking changes

**Not implemented:**
- MCP Apps (`ui://` resource, `_meta.ui.resourceUri`, host embedding, host testing)
- Running React application
- Automated test suite
- Arbitrary server connection (intentionally excluded)

## Known Limitations (accurate)
- Only the bundled synthetic server is supported.
- Token estimates are character-based approximations.
- Schema drift in Scenario B is simulated via a control tool, not by actual tool schema mutation.
- SDK exception handling means protocol errors appear as tool content rather than raised exceptions or `isError: true`.
- MCP Apps is not implemented.
- Primary UI is the static HTML dashboard.

## Demo Recording Plan (honest)
1. Start backend and serve `dashboard.html`.
2. Click Connect & Take Snapshot (A).
3. Run Scenario C — show FAIL with `isError: false` and `persisted: false`.
4. Run Scenario D — show FAIL with `found: false`.
5. Show report JSON and note the limitations (B does not change schema, MCP Apps not present).
6. Do not claim MCP Apps compatibility or real schema drift detection.
