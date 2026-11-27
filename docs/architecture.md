# Architecture

User
  │
  ▼
HTML Dashboard (frontend/public/dashboard.html)
  │  fetch /api/*
  ▼
FastAPI Backend (official MCP Python SDK client)
  │  stdio (fresh process per session)
  ▼
Bundled Synthetic MCP Server
  │
  ▼
JSON state file (/tmp) + SQLite (snapshots, test runs, reviews)

React source exists under frontend/src/ but is not the running application.

MCP Apps are not implemented. The synthetic server does not serve a ui:// resource.
