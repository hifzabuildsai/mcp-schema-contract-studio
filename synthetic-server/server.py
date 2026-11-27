#!/usr/bin/env python3
"""
Bundled Synthetic MCP Server for MCP Schema Contract & Silent-Failure Studio.

- State is persisted to a JSON file so schema version, records, and verifier
  availability survive stdio process restarts.
- The silent-failure write tool returns a normal success response with a
  generated record ID. It does not disclose that the write was not persisted.
- dynamic_record's schema is registered at process start from the persisted
  schema version, so a fresh process after control_schema_version reflects
  the new contract.
"""
from mcp.server.mcpserver import MCPServer
from mcp.server.apps import Apps
import json
import time
from pathlib import Path

STATE_FILE = Path("/tmp/mcp_studio_synthetic_state.json")

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "records": {},
        "schema_version": 1,
        "verifier_available": True,
    }

def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))

STATE = load_state()

apps = Apps()
mcp = MCPServer("synthetic-studio-server", extensions=[apps])

@mcp.tool()
def list_records() -> str:
    """List all records currently stored. Healthy read tool."""
    return json.dumps({"records": list(STATE["records"].keys()), "count": len(STATE["records"])})

@mcp.tool()
def create_record(name: str, value: int) -> str:
    """Create a new record. Healthy write that persists."""
    record_id = f"rec_{int(time.time()*1000)}"
    STATE["records"][record_id] = {"name": name, "value": value, "created": time.time()}
    save_state(STATE)
    return json.dumps({"id": record_id, "status": "created"})

@mcp.tool()
def create_record_silent_fail(name: str, value: int) -> str:
    """Create a new record. Returns a normal success response with a generated ID.
    Deliberately does not persist the record. The response does not disclose that."""
    record_id = f"rec_{int(time.time()*1000)}"
    # Intentionally do not write to STATE and do not save.
    return json.dumps({"id": record_id, "status": "created"})

@mcp.tool()
def get_record(record_id: str) -> str:
    """Independent read-back. Returns the actual stored record or missing."""
    if not STATE["verifier_available"]:
        raise Exception("Verifier temporarily unavailable")
    if record_id in STATE["records"]:
        return json.dumps({"found": True, "record": STATE["records"][record_id]})
    return json.dumps({"found": False, "record": None})

@mcp.tool()
def force_tool_error(reason: str = "demo") -> str:
    """Raises during tool execution. The SDK surfaces this as isError:true.
    This is a tool execution error, not a JSON-RPC protocol error."""
    raise ValueError(f"Tool execution failure: {reason}")

@mcp.tool()
def control_schema_version(version: int) -> str:
    """Studio control: change schema_version. Takes effect on the next process start."""
    STATE["schema_version"] = version
    save_state(STATE)
    return json.dumps({"schema_version": version, "note": "Schema contract changed and persisted"})

@mcp.tool()
def control_verifier(available: bool) -> str:
    """Studio control: make the verifier available or unavailable."""
    STATE["verifier_available"] = available
    save_state(STATE)
    return json.dumps({"verifier_available": available})

@mcp.tool()
def get_state() -> str:
    """Debug: dump current synthetic state."""
    return json.dumps(STATE)

# Registered at import time from persisted state so list_tools reflects the version.
if STATE.get("schema_version", 1) == 1:
    @mcp.tool(name="dynamic_record")
    def dynamic_record(name: str) -> str:
        """Create record (v1 schema: name only)."""
        return json.dumps({"id": "dyn1", "name": name, "schema_version": 1})
else:
    @mcp.tool(name="dynamic_record")
    def dynamic_record(name: str, priority: int) -> str:
        """Create record (v2 schema — priority now required). Breaking change from v1."""
        return json.dumps({"id": "dyn2", "name": name, "priority": priority, "schema_version": 2})

if __name__ == "__main__":
    mcp.run(transport="stdio")
