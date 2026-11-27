# Engineering Audit — MCP Schema Contract & Silent-Failure Studio

Audit date: 27 November 2026. Based on code inspection and automated tests run against the bundled synthetic server.

## 1. Frontend

The running dashboard is `frontend/public/dashboard.html`, served as static HTML. It calls the backend API for snapshots, individual tool schema inspection, classified diffs (breaking / non-breaking), scenario runs with full details, review notes and status, and the reliability report. Loading, success, and failure states are shown in the banner.

The React source under `frontend/src/` is not the running application. Vite could not be started in this environment.

## 2. MCP Apps

**Not implemented.** The synthetic server imports `Apps()` but registers no `ui://` resource, sets no `_meta.ui.resourceUri`, and serves no MCP App HTML. This is a standalone web application that uses an MCP client.

## 3. Automated verification

`python3 tests/test_studio.py` — 18 checks, 18 passed, 0 failed (27 November 2026).

Diff engine (fixtures):
- tool added (non-breaking) / tool removed (breaking)
- property added (non-breaking when optional) / property removed (breaking)
- required added (breaking) / required removed (non-breaking)
- enum value removed (breaking) / enum value added (non-breaking)
- nested type change (breaking) / nested required added (breaking)

Live scenarios against the synthetic server:
- A PASS — live tools/list (9 tools)
- B PASS — baseline snapshot, version change, fresh process, detected breaking required-field change (`priority`) on `dynamic_record`
- C FAIL — write returned normal success `{"id": "...", "status": "created"}` with no disclosure of failure; independent read-back of that exact ID returned `{"found": false}`
- D PASS — healthy write plus independent read-back confirmed the record exists with expected data
- E FAIL — tool execution error (`isError: true` from server exception), classified separately from protocol errors
- P PASS — JSON-RPC method-not-found, code -32601
- F UNKNOWN — verifier unavailable on 3 repeated attempts; verifier restored safely in finally block

## 4. Before / after

Before this pass:
- C returned `persisted: false` and a note explaining the failure, and the verdict was hardcoded FAIL.
- D hardcoded FAIL on a missing ID with no write.
- B reported FAIL because the control tool set the version, without capturing and comparing schemas in the same test.
- E was labelled a protocol error but tested a tool execution error (`isError: true`).

After this pass:
- C returns a normal success with a generated ID, extracts that ID, and the verdict comes only from independent read-back of that exact ID (FAIL on missing, PASS on found, UNKNOWN if read-back unavailable).
- B captures a baseline, changes the version, starts a fresh process, captures the updated schema, and the verdict comes from the detected classified diff (required field `priority`).
- E is labelled Tool Execution Error Handling (`isError: true`). P is the independent JSON-RPC protocol-error test (code -32601).
- F repeats the unavailable-verifier condition three times, produces UNKNOWN, and restores the verifier even on exception.

## 5. Release status

**Implemented and tested:**
- Backend MCP client connection to the synthetic server (stdio)
- Snapshot storage, listing, and individual tool schema inspection
- Classified schema diff (breaking / non-breaking) covering tools, properties, required fields, types, enums, nested schemas
- Silent-failure detection with independent read-back (C)
- Healthy write with independent read-back (D)
- Tool execution error handling (E)
- JSON-RPC protocol error (P)
- Verifier unavailable → UNKNOWN, with safe restore (F)
- SQLite persistence for snapshots, test runs, reviews
- HTML dashboard with loading, success, and failure states, schema inspection, diffs, run details, and reviews
- Automated test suite (diff fixtures + live scenarios)

**Not implemented:**
- MCP Apps (`ui://` resource, `_meta.ui.resourceUri`, host embedding)
- Running React application
- Arbitrary server connection (intentionally excluded)
- Production deployment or authentication

## Known limitations
- Only the bundled synthetic server is supported.
- Token estimates are character-based approximations.
- Schema changes take effect on the next server process start. Scenario B starts that process itself.
- Tool execution errors appear as `isError: true` tool results. JSON-RPC protocol errors are a separate response type, tested by scenario P.
- MCP Apps is not implemented.
- Primary UI is the static HTML dashboard.
- Disk I/O errors can occur under concurrent SQLite writes in constrained environments; clean DB runs pass consistently.
