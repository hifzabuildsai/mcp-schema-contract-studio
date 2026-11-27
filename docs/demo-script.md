# Video Demonstration Script (60–90 seconds)

**0–10s**  
“MCP servers change schemas and can return success when the operation never happened. Agents keep going.”

**10–25s**  
Open the Studio dashboard → click “Connect & Take Snapshot” → show live tool inventory and token estimate.

**25–45s**  
Run Scenario B (schema change) then Scenario C (silent failure). Show the FAIL verdict and the explanation that isError was false but nothing was persisted.

**45–65s**  
Run Scenario D (independent read-back) and Scenario F (verifier unavailable). Show FAIL and UNKNOWN with clear explanations.

**65–80s**  
Open the reliability report → point out live snapshots, verdicts, and the disclosure note.

**80–90s**  
“Complete local application. Full source, setup instructions, and architecture on GitHub. Built in one day.”

# X Caption

Shipped MCP Schema Contract & Silent-Failure Studio.

A local-first interactive dashboard that connects to a real MCP server, snapshots schemas, detects breaking changes, and verifies outcomes with PASS / FAIL / UNKNOWN.

- Live stdio MCP protocol (official SDK)
- Silent-failure simulation (isError:false but no persist)
- Independent read-back
- Visual diffs + reliability report
- Zero arbitrary command execution

Full source + run instructions in the repo. Demo below.

# Limitations
- Bundled synthetic server only in this version
- Token estimates are approximate
- Standalone dashboard is fully functional; MCP Apps host embedding is prepared for compatible clients
