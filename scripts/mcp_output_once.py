"""One focused confirmation of the repaired MCP output contract."""

import asyncio
from datetime import datetime, timezone
import json
import os
import sys

from mcp import Client, StdioServerParameters
from stephanus.paths import DATA, ROOT

REPORT = DATA / "mcp-output-fix.json"

async def main():
    if REPORT.exists():
        raise SystemExit("This repair's output contract has already been recorded.")
    report = {"scope": "Structured output repair only; original acceptance suite not repeated", "executed_at": datetime.now(timezone.utc).isoformat(), "results": []}
    server = StdioServerParameters(command=sys.executable, args=["-m", "stephanus.cli", "serve"], env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}, cwd=str(ROOT))
    try:
        async with Client(server) as client:
            for name, args in [
                ("stephanus_get_entry", {"identifier": "onomaverse:john-fn"}),
                ("stephanus_find_related_names", {"identifier": "onomaverse:john-fn", "limit": 3}),
            ]:
                result = await client.call_tool(name, args)
                assert not result.is_error, str(result.content)
                assert isinstance(result.structured_content, dict), "Expected structured JSON object"
                report["results"].append({"tool": name, "passed": True, "result": result.structured_content})
        report["passed"] = True
    except Exception as exc:
        report.update(passed=False, error=str(exc))
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "tools": [r["tool"] for r in report["results"]], "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(asyncio.run(main()))
