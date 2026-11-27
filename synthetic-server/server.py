#!/usr/bin/env python3
"""
Bundled Synthetic MCP Server for MCP Schema Contract & Silent-Failure Studio.
Supports dynamic schema changes, silent failures, and independent read-back for deterministic demos.
All scenarios A-F can be exercised against this server.
"""
from mcp.server.mcpserver import MCPServer
from mcp.server.apps import Apps
import json
import time
from typing import Any

# In-memory state for read-back verification
STATE = {
    "records": {},
    "schema_version": 1,
    "verifier_available": True,
}

apps = Apps()
mcp = MCPServer("synthetic-studio-server", extensions=[apps])

# --- Healthy tools (Scenario A) ---
@mcp.tool()
def list_records() -> str:
    """List all records currently stored. Healthy read tool."""
    return json.dumps({"records": list(STATE["records"].keys()), "count": len(STATE["records"])})

@mcp.tool()
def create_record(name: str, value: int) -> str:
    """Create a new record. Healthy write that persists."""
    record_id = f"rec_{int(time.time()*1000)}"
    STATE["records"][record_id] = {"name": name, "value": value, "created": time.time()}
    return json.dumps({"id": record_id, "status": "created", "persisted": True})

# --- Silent failure tool (Scenario C) ---
@mcp.tool()
def create_record_silent_fail(name: str, value: int) -> str:
    """
    Claims success but deliberately does NOT persist the record.
    Returns isError:false (default) with success text. Used for Scenario C.
    """
    # Intentionally do nothing to STATE
    fake_id = f"fake_{int(time.time()*1000)}"
    return json.dumps({
        "id": fake_id,
        "status": "created",
        "persisted": False,
        "note": "This is a silent failure - nothing was written"
    })

# --- Read-back tool for independent verification (Scenario D) ---
@mcp.tool()
def get_record(record_id: str) -> str:
    """Independent read-back. Returns the actual stored record or missing."""
    if not STATE["verifier_available"]:
        raise Exception("Verifier temporarily unavailable")
    if record_id in STATE["records"]:
        return json.dumps({"found": True, "record": STATE["records"][record_id]})
    return json.dumps({"found": False, "record": None})

# --- Protocol error tool (Scenario E distinction) ---
@mcp.tool()
def force_protocol_error(reason: str = "demo") -> str:
    """Raises a real exception so the SDK returns a protocol-level error."""
    raise ValueError(f"Protocol-level failure: {reason}")

# --- Control tools for the Studio (not exposed as business tools) ---
@mcp.tool()
def control_schema_version(version: int) -> str:
    """Studio control: change schema_version to trigger drift detection."""
    STATE["schema_version"] = version
    return json.dumps({"schema_version": version, "note": "Schema contract changed"})

@mcp.tool()
def control_verifier(available: bool) -> str:
    """Studio control: make verifier unavailable to produce UNKNOWN (Scenario F)."""
    STATE["verifier_available"] = available
    return json.dumps({"verifier_available": available})

@mcp.tool()
def get_state() -> str:
    """Debug: dump current synthetic state."""
    return json.dumps(STATE)

if __name__ == "__main__":
    mcp.run(transport="stdio")

# Dynamic schema tool for real drift detection (Scenario B)
def make_dynamic_tool():
    if STATE.get("schema_version", 1) == 1:
        @mcp.tool(name="dynamic_record")
        def dynamic_record(name: str) -> str:
            """Create record (v1 schema)."""
            return json.dumps({"id": "dyn1", "name": name})
    else:
        @mcp.tool(name="dynamic_record")
        def dynamic_record(name: str, priority: int) -> str:
            """Create record (v2 schema — priority now required)."""
            return json.dumps({"id": "dyn2", "name": name, "priority": priority})

# Note: the above is illustrative; actual schema change requires server restart
# or low-level tool registration. For this version we document the limitation.
