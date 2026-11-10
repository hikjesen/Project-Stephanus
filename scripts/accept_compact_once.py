"""The single functional acceptance of the independent compact runtime."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data/runtime-candidate"
REPORT = ROOT / "data/reports/compact-acceptance.json"

async def main():
    if REPORT.exists():
        raise SystemExit("This phase has already recorded acceptance; repeating it is prohibited.")
    size = json.loads((STAGE / "runtime-size.json").read_text(encoding="utf-8"))
    if not size["within_budget"]:
        raise SystemExit("Do not accept a runtime over the storage budget.")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running", "resource_root": str(STAGE), "runtime_bytes": size["runtime_bytes"], "results": []}
    def save():
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    environment = {**os.environ, "STEPHANUS_HOME": str(STAGE), "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    async def scenario(label, operation):
        try:
            detail = await operation()
            item = {"scenario": label, "passed": True, "detail": detail}
        except Exception as exc:
            item = {"scenario": label, "passed": False, "error": str(exc)}
        report["results"].append(item)
        save()
        print("PASS" if item["passed"] else "FAIL", label, item.get("error", ""), flush=True)
    async def cli():
        result = subprocess.run([sys.executable, "-m", "stephanus.cli", "names", "佐藤", "--source", "jmnedict", "--limit", "1"], cwd=ROOT, env=environment, capture_output=True, encoding="utf-8")
        assert result.returncode == 0, result.stderr
        item = json.loads(result.stdout)["items"][0]
        assert item["readings"]
        return {"id": item["id"], "text": item["text"], "readings": item["readings"]}
    await scenario("CLI name and reading", cli)
    try:
        server = StdioServerParameters(command=sys.executable, args=["-m", "stephanus.cli", "serve"], cwd=str(ROOT), env=environment)
        async with Client(server) as client:
            async def call(name, **args):
                response = await client.call_tool("stephanus_" + name, args)
                assert not response.is_error, str(response.content)
                assert isinstance(response.structured_content, dict), "Missing structured object"
                return response.structured_content
            async def discovery():
                response = await client.list_tools()
                assert len(response.tools) == 7
                return [t.name for t in response.tools]
            await scenario("Seven structured MCP tools", discovery)
            async def pagination():
                first = await call("search_names", query="あおい", mode="reading", limit=3)
                second = await call("search_names", query="あおい", mode="reading", limit=3, offset=3)
                assert len(first["items"]) == 3 and second["items"]
                assert {r["id"] for r in first["items"]}.isdisjoint(r["id"] for r in second["items"])
                assert all("match" in i["extra"] and "_sort" not in i for i in first["items"])
                return [i["id"] for i in first["items"] + second["items"]]
            await scenario("Merged-source homophones and pagination", pagination)
            async def japanese():
                response = await call("lookup_words", query="光", language="ja", source="jmdict", limit=1)
                item = response["items"][0]
                assert len(item["description"]) <= 240
                detail = await call("get_entry", identifier=item["id"])
                assert detail["extra"]["knowledge"]["senses"] and detail["extra"]["provenance"]
                assert "kanji" not in detail["extra"]
                return {"id": item["id"], "senses": len(detail["extra"]["knowledge"]["senses"])}
            await scenario("Japanese senses, summary and retained details", japanese)
            async def character():
                response = await call("lookup_words", query="明", source="kanjidic2", limit=1)
                assert response["items"][0]["readings"]
                return response["items"][0]["description"]
            await scenario("Kanji readings and meaning", character)
            async def english_latin():
                response = await call("lookup_words", query="courage", source="verba", language="la", mode="meaning", limit=1)
                item = response["items"][0]
                detail = await call("get_entry", identifier=item["id"])
                equivalents = detail["extra"]["knowledge"]["senses"][0].get("latin_equivalents", [])
                assert equivalents, "No extracted English-Latin equivalents"
                return {"id": item["id"], "equivalents": [e["text"] for e in equivalents[:5]]}
            await scenario("Compact English-to-Latin dictionary", english_latin)
            async def latin_english():
                response = await call("lookup_words", query="virtus", source="verba", language="la", limit=1)
                assert response["items"] and response["items"][0]["description"]
                return response["items"][0]["id"]
            await scenario("Latin lemma with quantity-insensitive search keys", latin_english)
            async def form():
                build = json.loads((STAGE / "data/compact-build.json").read_text(encoding="utf-8"))
                identifier = build["samples"]["form_id"]
                detail = await call("get_entry", identifier=identifier)
                assert detail["id"] == identifier and detail["extra"]["knowledge"]["lemma_links"]
                return {"id": identifier, "links": detail["extra"]["knowledge"]["lemma_links"][:2]}
            await scenario("Original form ID resolves to compact lemma links", form)
            async def european():
                response = await call("search_names", query="John", source="onomaverse", mode="text", limit=1)
                identifier = response["items"][0]["id"]
                detail = await call("get_entry", identifier=identifier)
                related = await call("find_related_names", identifier=identifier, limit=3)
                assert detail["id"] == identifier and related["items"]
                return {"id": identifier, "related": [i["id"] for i in related["items"]]}
            await scenario("European public IDs and name relations", european)
            async def medieval():
                response = await call("search_names", query="John", source="medieval-names", limit=1)
                detail = await call("get_entry", identifier=response["items"][0]["id"])
                assert detail["language"] == "und" and detail["extra"]["knowledge"]["attestations"]
                return detail["id"]
            await scenario("Historical names, und and source notes", medieval)
            async def native():
                first = await call("search_names", query="はるか", source="jinmei-dict", limit=1)
                second = await call("search_names", query="たろう", source="japanese-personal-name-dataset", limit=1)
                assert first["items"] and second["items"]
                return [first["items"][0]["id"], second["items"][0]["id"]]
            await scenario("Independent native JSON and SQLite", native)
            async def transliteration():
                result = await call("transliterate_name", text="しんじ", scheme="hepburn")
                assert result["text"] == "shinji"
                return result["text"]
            await scenario("Romkan conversion", transliteration)
            async def morphology():
                result = await call("analyze_latin", text="amavit", limit=2)
                assert result["status"] == "available" and result["description"]
                return result["description"][:240]
            await scenario("Whitaker analysis without full Latin articles", morphology)
            async def sources():
                result = await call("list_sources")
                empty = await call("search_names", query="__stephanus_no_match_compact_20261110__")
                assert "resources" not in result and len(result["indexed_languages"]) >= 95
                assert empty["items"] == []
                return {"languages": len(result["indexed_languages"]), "backends": len(result["backends"])}
            await scenario("Compact source list, language coverage and empty result", sources)
    except Exception as exc:
        report["results"].append({"scenario": "MCP connection", "passed": False, "error": str(exc)})
    report.update(status="complete", completed_at=datetime.now(timezone.utc).isoformat(), passed=all(r["passed"] for r in report["results"]))
    save()
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(asyncio.run(main()))
