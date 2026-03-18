"""NODUS MCP Server — Model Context Protocol implementation.

Exposes NODUS workflows and validation tools to other AI agents via MCP.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .nodus import run_workflow

# ═══════════════════════════════════════════════════════════════════════════
# SERVER INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

mcp = FastMCP("Nodus")


# ───────────────────────────────────────────────────────────────────────────
# TOOLS
# ───────────────────────────────────────────────────────────────────────────


@mcp.tool()
def execute_workflow(path: str, input_data: str = "{}") -> str:
    """Execute a NODUS workflow file.

    Args:
        path: Path to the .nodus file (e.g., 'workflows/reply.nodus').
        input_data: JSON string containing input variables for the workflow.

    Returns:
        JSON string containing the NODUS:RESULT (status, output, and logs).
    """
    try:
        data = json.loads(input_data)
    except json.JSONDecodeError as exc:
        return json.dumps(
            {"status": "failed", "errors": [f"Invalid input JSON: {exc}"]}, indent=2
        )

    result = run_workflow(path, data)
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


@mcp.tool()
def list_available_workflows() -> str:
    """List all .nodus workflows in the project.

    Returns:
        List of workflow paths relative to the project root.
    """
    # Look in workflows/ and current directory
    paths = list(Path("workflows").glob("**/*.nodus")) + list(Path(".").glob("*.nodus"))
    # Filter out .nodus/ internal files
    filtered = [str(p) for p in paths if ".nodus" not in str(p)]
    return "\n".join(sorted(set(filtered)))


# ───────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ───────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
