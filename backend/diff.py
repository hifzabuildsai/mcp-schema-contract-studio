"""Schema contract comparison for MCP tool inventories.

Classifies changes as breaking or non-breaking. Pure function: no I/O.
"""
from __future__ import annotations

from typing import Any


def diff_schemas(old_tools: list[dict], new_tools: list[dict]) -> dict:
    """Compare two tool inventories. Returns classified changes."""
    old = {t["name"]: t for t in old_tools}
    new = {t["name"]: t for t in new_tools}
    changes: list[dict[str, Any]] = []
    for name in sorted(set(old) | set(new)):
        if name not in old:
            changes.append({
                "tool": name, "path": name, "type": "tool_added",
                "breaking": False, "detail": "Tool added",
            })
        elif name not in new:
            changes.append({
                "tool": name, "path": name, "type": "tool_removed",
                "breaking": True, "detail": "Tool removed",
            })
        else:
            changes.extend(_compare_schema(
                name,
                old[name].get("inputSchema") or {},
                new[name].get("inputSchema") or {},
                path="$",
            ))
    breaking = [c for c in changes if c["breaking"]]
    return {
        "changes": changes,
        "breaking_count": len(breaking),
        "non_breaking_count": len(changes) - len(breaking),
    }


def _compare_schema(tool: str, s1: dict, s2: dict, path: str) -> list[dict]:
    changes: list[dict] = []
    t1 = s1.get("type")
    t2 = s2.get("type")
    if t1 != t2 and (t1 or t2):
        changes.append({
            "tool": tool, "path": path, "type": "type_changed",
            "breaking": True, "from": t1, "to": t2,
        })

    e1 = s1.get("enum")
    e2 = s2.get("enum")
    if e1 is not None or e2 is not None:
        set1 = set(e1 or [])
        set2 = set(e2 or [])
        for v in sorted(set1 - set2, key=str):
            changes.append({
                "tool": tool, "path": path, "type": "enum_value_removed",
                "breaking": True, "value": v,
            })
        for v in sorted(set2 - set1, key=str):
            changes.append({
                "tool": tool, "path": path, "type": "enum_value_added",
                "breaking": False, "value": v,
            })

    p1 = s1.get("properties") or {}
    p2 = s2.get("properties") or {}
    r1 = set(s1.get("required") or [])
    r2 = set(s2.get("required") or [])

    for prop in sorted(set(p1) | set(p2)):
        ppath = f"{path}.properties.{prop}"
        if prop not in p1:
            breaking = prop in r2
            changes.append({
                "tool": tool, "path": ppath, "type": "property_added",
                "breaking": breaking, "required": prop in r2,
            })
        elif prop not in p2:
            changes.append({
                "tool": tool, "path": ppath, "type": "property_removed",
                "breaking": True,
            })
        else:
            changes.extend(_compare_schema(tool, p1[prop], p2[prop], ppath))

    for req in sorted(r2 - r1):
        if req in p1:
            changes.append({
                "tool": tool, "path": f"{path}.required.{req}",
                "type": "required_added", "breaking": True, "property": req,
            })
    for req in sorted(r1 - r2):
        changes.append({
            "tool": tool, "path": f"{path}.required.{req}",
            "type": "required_removed", "breaking": False, "property": req,
        })

    if "items" in s1 or "items" in s2:
        changes.extend(_compare_schema(tool, s1.get("items") or {}, s2.get("items") or {}, f"{path}.items"))

    return changes
