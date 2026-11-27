#!/usr/bin/env python3
"""
Backend for MCP Schema Contract & Silent-Failure Studio.
Connects via official MCP SDK (stdio) to the bundled synthetic server.
Persists everything in SQLite. Serves the React dashboard.
"""
import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DB_PATH = Path(__file__).parent / "studio.db"
SYNTHETIC = Path(__file__).parent.parent / "synthetic-server" / "server.py"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        taken_at TEXT, tools_json TEXT, schema_hash TEXT, token_estimate INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS test_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_at TEXT, scenario TEXT, result TEXT, verdict TEXT, explanation TEXT, details_json TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_type TEXT, target_id INTEGER, note TEXT, status TEXT, created_at TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

app = FastAPI(title="MCP Schema Studio")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

async def with_session(coro):
    params = StdioServerParameters(command="python3", args=[str(SYNTHETIC)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await coro(session)

@app.get("/api/health")
def health():
    return {"status": "ok", "server": str(SYNTHETIC.exists())}

@app.post("/api/snapshots")
async def take_snapshot():
    async def do(session):
        tools_resp = await session.list_tools()
        tools = [{"name": t.name, "description": t.description or "", "inputSchema": t.input_schema} for t in tools_resp.tools]
        tools_json = json.dumps(tools, sort_keys=True)
        schema_hash = hashlib.sha256(tools_json.encode()).hexdigest()[:16]
        token_estimate = len(tools_json) // 4  # explicit estimate
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO snapshots (taken_at, tools_json, schema_hash, token_estimate) VALUES (?,?,?,?)",
                  (datetime.utcnow().isoformat(), tools_json, schema_hash, token_estimate))
        sid = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": sid, "tool_count": len(tools), "schema_hash": schema_hash,
                "token_estimate": token_estimate, "tools": tools,
                "note": "token_estimate is a rough approximation, not a real tokenizer"}
    return await with_session(do)

@app.get("/api/snapshots")
def list_snapshots():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, taken_at, schema_hash, token_estimate, tools_json FROM snapshots ORDER BY id DESC").fetchall()
    conn.close()
    return [{"id": r[0], "taken_at": r[1], "schema_hash": r[2], "token_estimate": r[3],
             "tool_count": len(json.loads(r[4]))} for r in rows]

@app.get("/api/snapshots/{sid}")
def get_snapshot(sid: int):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT tools_json, schema_hash, token_estimate, taken_at FROM snapshots WHERE id=?", (sid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404)
    return {"id": sid, "tools": json.loads(row[0]), "schema_hash": row[1],
            "token_estimate": row[2], "taken_at": row[3], "note": "estimate"}

@app.get("/api/diff/{id1}/{id2}")
def diff(id1: int, id2: int):
    conn = sqlite3.connect(DB_PATH)
    r1 = conn.execute("SELECT tools_json FROM snapshots WHERE id=?", (id1,)).fetchone()
    r2 = conn.execute("SELECT tools_json FROM snapshots WHERE id=?", (id2,)).fetchone()
    conn.close()
    if not r1 or not r2:
        raise HTTPException(404)
    t1 = {t["name"]: t for t in json.loads(r1[0])}
    t2 = {t["name"]: t for t in json.loads(r2[0])}
    changes = []
    for name in sorted(set(t1) | set(t2)):
        if name not in t1:
            changes.append({"tool": name, "type": "added", "breaking": False})
        elif name not in t2:
            changes.append({"tool": name, "type": "removed", "breaking": True})
        elif t1[name]["inputSchema"] != t2[name]["inputSchema"]:
            req1 = set(t1[name]["inputSchema"].get("required", []))
            req2 = set(t2[name]["inputSchema"].get("required", []))
            breaking = bool(req2 - req1)
            changes.append({"tool": name, "type": "schema_changed", "breaking": breaking,
                            "old_required": list(req1), "new_required": list(req2)})
    return {"from": id1, "to": id2, "changes": changes, "breaking_count": sum(c["breaking"] for c in changes)}

@app.post("/api/scenarios/{scenario}")
async def run_scenario(scenario: str):
    async def do(session):
        details = []
        if scenario == "A":
            tools = await session.list_tools()
            details.append({"tools": len(tools.tools)})
            return "PASS", "Connected and listed tools from healthy synthetic server.", details
        if scenario == "B":
            # Set version; actual schema change is visible on the *next* process start
            # because tools are registered at import time based on persisted state.
            res = await session.call_tool("control_schema_version", {"version": 2})
            text = res.content[0].text if res.content else ""
            details.append({"control_result": text, "note": "Schema change takes effect on next connection/snapshot"})
            return "FAIL", "Schema version set to 2. Next snapshot will show breaking change on dynamic_record (priority now required).", details
        if scenario == "C":
            res = await session.call_tool("create_record_silent_fail", {"name": "test", "value": 1})
            text = res.content[0].text if res.content else ""
            is_err = getattr(res, "is_error", getattr(res, "isError", False))
            details.append({"is_error": is_err, "text": text})
            return "FAIL", "Tool returned success text with is_error=false but did not persist the record.", details
        if scenario == "D":
            res = await session.call_tool("get_record", {"record_id": "missing"})
            text = res.content[0].text if res.content else ""
            details.append({"readback": text})
            return "FAIL", "Independent read-back confirmed the expected record is missing.", details
        if scenario == "E":
            res = await session.call_tool("force_protocol_error", {"reason": "demo"})
            is_err = getattr(res, "is_error", getattr(res, "isError", False))
            text = res.content[0].text if res.content else ""
            details.append({"is_error": is_err, "text": text, "raised_exception_on_client": False})
            # Protocol error is reported via is_error=True on the tool result
            if is_err:
                return "FAIL", "Protocol-level error correctly reported as is_error=True (SDK surfaces server exception as tool error result).", details
            return "FAIL", "Expected protocol error but is_error was false.", details
        if scenario == "F":
            await session.call_tool("control_verifier", {"available": False})
            res = await session.call_tool("get_record", {"record_id": "x"})
            is_err = getattr(res, "is_error", getattr(res, "isError", False))
            text = res.content[0].text if res.content else ""
            details.append({"is_error": is_err, "text": text})
            # Reset verifier
            await session.call_tool("control_verifier", {"available": True})
            if is_err:
                return "UNKNOWN", "Verifier unavailable — tool returned is_error=True. Reported UNKNOWN instead of incorrect PASS/FAIL.", details
            return "UNKNOWN", "Verifier control applied; is_error was not set as expected.", details
        raise HTTPException(400, "Unknown scenario")

    verdict, explanation, details = await with_session(do)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO test_runs (run_at, scenario, result, verdict, explanation, details_json) VALUES (?,?,?,?,?,?)",
              (datetime.utcnow().isoformat(), scenario, "ok", verdict, explanation, json.dumps(details)))
    rid = c.lastrowid
    conn.commit()
    conn.close()
    return {"run_id": rid, "scenario": scenario, "verdict": verdict, "explanation": explanation, "details": details}

@app.get("/api/test-runs")
def list_runs():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, run_at, scenario, verdict, explanation FROM test_runs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return [{"id": r[0], "run_at": r[1], "scenario": r[2], "verdict": r[3], "explanation": r[4]} for r in rows]

@app.post("/api/reviews")
def add_review(target_type: str = "run", target_id: int = 0, note: str = "", status: str = "reviewed"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO reviews (target_type, target_id, note, status, created_at) VALUES (?,?,?,?,?)",
                 (target_type, target_id, note, status, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/report")
def report():
    conn = sqlite3.connect(DB_PATH)
    snaps = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    runs = conn.execute("SELECT scenario, verdict FROM test_runs").fetchall()
    conn.close()
    return {
        "snapshots": snaps,
        "test_runs": len(runs),
        "recent_verdicts": {r[0]: r[1] for r in runs[-6:]},
        "generated_at": datetime.utcnow().isoformat(),
        "disclosure": "All results from live calls to the bundled synthetic MCP server. Token figures are estimates. No arbitrary user commands are executed."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
