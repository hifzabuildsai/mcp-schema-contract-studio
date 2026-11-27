# Video Demonstration Script (60–90 seconds)

**0–10s**
“MCP servers can change their schema, and a tool can return success when the write never happened. Agents keep going.”

**10–25s**
Open the Studio dashboard. Click “Connect & take snapshot”. Show the live tool inventory and open one tool’s schema.

**25–45s**
Run Scenario B. Show the baseline and updated snapshots, and the classified breaking change: `dynamic_record` gained a required `priority` field.

**45–65s**
Run Scenario C. Show the write response: a normal success with a generated ID, no failure disclosure. Then show the independent read-back of that exact ID returning found:false, and the FAIL verdict that came from the read-back.

**65–80s**
Run Scenario P and Scenario F. P shows a JSON-RPC method-not-found (code -32601). F shows UNKNOWN because the verifier was unavailable, and note that the verifier was restored.

**80–90s**
Open the reliability report. “Local application. Full source and setup on GitHub. MCP Apps are not implemented in this version.”

# X Caption

Shipped MCP Schema Contract & Silent-Failure Studio.

A local-first dashboard that connects to a real MCP server, snapshots schemas, classifies breaking changes, and verifies outcomes with independent read-back.

- Live stdio MCP protocol (official SDK)
- Silent-failure test: success response with an ID, no disclosure, read-back decides the verdict
- Schema drift detected across a fresh server process
- Tool execution error and JSON-RPC protocol error kept separate
- UNKNOWN when the verifier is unavailable

Full source and run instructions in the repo.

# Limitations to state on camera
- Bundled synthetic server only
- Token estimates are approximate
- MCP Apps are not implemented
- The running UI is the HTML dashboard; React source is present but not the running app
