# Architecture Diagram (text)

User
  │
  ▼
React Dashboard (Vite + React + Tailwind)
  │  fetch /api/*
  ▼
FastAPI Backend (official MCP Python SDK client)
  │  stdio
  ▼
Bundled Synthetic MCP Server
  │
  ▼
In-memory state + SQLite persistence of snapshots / test runs / reviews

MCP Apps: synthetic server can serve a ui:// resource; the standalone web app is the primary interactive surface for this version.
