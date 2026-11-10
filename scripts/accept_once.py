"""One real-data acceptance run: each scenario executes once, without a retry loop."""

import asyncio
from datetime import datetime, timezone
import json
import os
import subprocess
import sys

from mcp import Client, StdioServerParameters
from stephanus.paths import DATA, ROOT

REPORT = DATA / "acceptance.json"

async def main():
    if REPORT.exists():
        raise SystemExit("Acceptance already recorded. Project policy prohibits repeating it.")
    results = []
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    cli = subprocess.run([sys.executable, "-m", "stephanus.cli", "names", "佐藤", "--source", "jmnedict", "--limit", "2"], cwd=ROOT, env=environment, capture_output=True, encoding="utf-8")
    try:
        names = json.loads(cli.stdout)["items"]
        assert cli.returncode == 0 and names and names[0]["readings"]
        results.append({"scenario": "CLI kanji name to reading", "passed": True, "sample": {"text": names[0]["text"], "readings": names[0]["readings"]}})
    except Exception as exc:
        results.append({"scenario": "CLI kanji name to reading", "passed": False, "error": str(exc), "stderr": cli.stderr})

    async def call(client, name, args):
        response = await client.call_tool("stephanus_" + name, args)
        assert not response.is_error, str(response.content)
        return response.structured_content

    async def scenario(label, operation):
        try:
            detail = await operation()
            results.append({"scenario": label, "passed": True, "detail": detail})
        except Exception as exc:
            results.append({"scenario": label, "passed": False, "error": str(exc)})

    try:
        server = StdioServerParameters(command=sys.executable, args=["-m", "stephanus.cli", "serve"], env=environment, cwd=str(ROOT))
        async with Client(server) as client:
            tools = await client.list_tools()
            results.append({"scenario": "stdio MCP tool discovery", "passed": len(tools.tools) == 7, "tools": [t.name for t in tools.tools]})

            async def homophones():
                first = await call(client, "search_names", {"query": "あおい", "language": "ja", "mode": "reading", "limit": 2})
                second = await call(client, "search_names", {"query": "あおい", "language": "ja", "mode": "reading", "limit": 2, "offset": 2})
                assert len(first["items"]) == 2 and second["items"]
                assert {r["id"] for r in first["items"]}.isdisjoint(r["id"] for r in second["items"])
                return [r["text"] for r in first["items"] + second["items"]]
            await scenario("MCP homophones and pagination", homophones)

            async def word():
                response = await call(client, "lookup_words", {"query": "光", "language": "ja", "source": "jmdict", "limit": 2})
                assert response["items"]
                return response["items"][0]["description"][:250]
            await scenario("Japanese dictionary", word)

            async def character():
                response = await call(client, "lookup_words", {"query": "明", "source": "kanjidic2", "limit": 1})
                assert response["items"] and response["items"][0]["readings"]
                return response["items"][0]["description"]
            await scenario("Kanji meanings and readings", character)

            async def latin():
                response = await call(client, "lookup_words", {"query": "courage", "language": "la", "source": "verba", "mode": "meaning"})
                assert response["items"] and response["items"][0]["status"] == "available"
                return response["items"][0]["description"][:250]
            await scenario("English-to-Latin upstream lookup", latin)

            async def european():
                response = await call(client, "search_names", {"query": "John", "source": "onomaverse", "mode": "text", "limit": 1})
                identifier = response["items"][0]["id"]
                detail = await call(client, "get_entry", {"identifier": identifier})
                related = await call(client, "find_related_names", {"identifier": identifier, "limit": 3})
                assert detail and related["items"]
                return {"entry": identifier, "related": [r["text"] for r in related["items"]]}
            await scenario("European names, detail and relations", european)

            async def native():
                first = await call(client, "search_names", {"query": "はるか", "source": "jinmei-dict", "limit": 1})
                second = await call(client, "search_names", {"query": "たろう", "source": "japanese-personal-name-dataset", "limit": 1})
                assert first["items"] and second["items"]
                return {"jinmei": first["items"][0]["text"], "personal": second["items"][0]["text"]}
            await scenario("Native JSON and SQLite adapters", native)

            async def transliteration():
                response = await call(client, "transliterate_name", {"text": "しんじ", "scheme": "hepburn"})
                assert response["text"] == "shinji"
                return response["text"]
            await scenario("Upstream romanization", transliteration)

            async def morphology():
                response = await call(client, "analyze_latin", {"text": "amavit", "limit": 2})
                assert response["status"] == "available" and response["description"]
                return response["description"][:250]
            await scenario("Upstream Latin morphology", morphology)

            async def kaikki():
                response = await call(client, "lookup_words", {"query": "virtus", "source": "kaikki", "language": "la", "limit": 1})
                assert response["items"]
                return response["items"][0]["text"]
            await scenario("Kaikki local extraction", kaikki)

            async def empty_and_sources():
                empty = await call(client, "search_names", {"query": "__stephanus_no_match_20261110__"})
                sources = await call(client, "list_sources", {})
                assert empty["items"] == [] and sources["backends"] and sources["targets"]
                return {"empty": True, "backends": len(sources["backends"]), "targets": [r["code"] for r in sources["targets"]]}
            await scenario("Empty results and source/target registry", empty_and_sources)
    except Exception as exc:
        results.append({"scenario": "MCP connection", "passed": False, "error": str(exc)})
    REPORT.write_text(json.dumps({"executed_at": datetime.now(timezone.utc).isoformat(), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    for result in results:
        print("PASS" if result["passed"] else "FAIL", result["scenario"], result.get("error", ""), flush=True)
    return 0 if all(r["passed"] for r in results) else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(asyncio.run(main()))
