"""Shared compact, read-only queries for CLI and MCP."""
from dataclasses import asdict
import sqlite3
from . import database as db
from .native import JINMEI, PERSONAL, get_native, search_jinmei, search_personal, transliterate, verba
from .paths import DATABASE, DATA, VENDOR
from .resources import read_manifest
from .targets import load_targets

def page(items, limit, offset):
    selected = items[offset:offset + limit]
    for item in selected:
        item.pop("_sort", None)
    more = len(items) > offset + limit
    return {"items": selected, "limit": limit, "offset": offset, "has_more": more,
            "next_offset": offset + limit if more else None}

def sort_key(item):
    return item.get("_sort", (0, db.key(item["text"]), item["source"], 0, item["id"]))

class Service:
    def source_unavailable(self, source, limit, offset):
        if not source:
            return None
        if DATABASE.exists():
            with db.connect() as c:
                if c.execute("SELECT 1 FROM imports WHERE source=?", (source,)).fetchone():
                    return None
        return {**page([], limit, offset), "status": "unavailable", "description": f"Source '{source}' is not indexed. See list_sources."}

    def list_sources(self, include_resources=False):
        backends, languages = [], []
        if DATABASE.exists():
            with db.connect() as c:
                languages = [r[0] for r in c.execute("SELECT code FROM languages ORDER BY code")]
                for row in c.execute("SELECT i.*,s.version FROM imports i JOIN sources s ON s.name=i.source"):
                    name = row["source"]
                    capabilities = ["lexicon_lookup"] if name in ("jmdict", "kanjidic2", "verba") else ["name_lookup"]
                    if name == "kaikki":
                        capabilities.append("lexicon_lookup")
                    if name in ("onomaverse", "medieval-names"):
                        capabilities.append("name_relations")
                    if name == "verba":
                        capabilities.append("morphology")
                    backends.append({"status": "indexed", "capabilities": capabilities, **dict(row)})
        for name, path, capabilities in [
            (JINMEI, VENDOR / JINMEI / "jinmei/mei.json", ["name_lookup"]),
            (PERSONAL, DATA / "raw" / PERSONAL / "japanese_names.sqlite", ["name_lookup"]),
            ("python-romkan", VENDOR / "python-romkan/src/romkan", ["transliteration"]),
        ]:
            backends.append({"source": name, "status": "native" if path.exists() else "unavailable", "languages": ["ja"], "capabilities": capabilities})
        result = {"backends": backends, "targets": [asdict(t) for t in load_targets().values()], "indexed_languages": languages, "format": "compact-v1"}
        if include_resources:
            result["resources"] = read_manifest()
        return result

    def search_names(self, query, language=None, category=None, source=None, mode="auto", limit=20, offset=0):
        if source and source not in (JINMEI, PERSONAL):
            unavailable = self.source_unavailable(source, limit, offset)
            if unavailable:
                return unavailable
        amount = offset + limit + 1
        items = db.search(query, ["name"], language, source, category, mode, amount) if DATABASE.exists() else []
        missing = []
        if language in (None, "ja") and mode in ("auto", "text", "reading"):
            for name, function in [(JINMEI, search_jinmei), (PERSONAL, search_personal)]:
                if source and source != name:
                    continue
                try:
                    items.extend(function(query, amount, category, mode))
                except (FileNotFoundError, sqlite3.OperationalError) as exc:
                    missing.append({"source": name, "status": "unavailable", "description": str(exc)})
        unique = {i["id"]: i for i in items}
        result = page(sorted(unique.values(), key=sort_key), limit, offset)
        if missing:
            result["unavailable_sources"] = missing
        return result

    def lookup_words(self, query, language=None, source=None, mode="auto", limit=20, offset=0):
        unavailable = self.source_unavailable(source, limit, offset)
        if unavailable:
            return unavailable
        # English headwords in Smith & Hall get exact/prefix precedence over broad gloss hits.
        effective_mode = "auto" if source == "verba" and mode == "meaning" else mode
        items = db.search(query, ["word", "character"], language, source, mode=effective_mode, amount=offset + limit + 1) if DATABASE.exists() else []
        return page(items, limit, offset)

    def get_entry(self, identifier):
        if identifier.startswith((JINMEI + ":", PERSONAL + ":")):
            item = get_native(identifier)
            if item:
                item["extra"]["knowledge"] = {"senses": [], "etymology": None, "forms": [], "related_words": [], "attestations": []}
                item["extra"]["provenance"] = {"source": item["source"], "record": identifier, "version": next((r.get("version") or r.get("revision") or r.get("acquired_at") for r in read_manifest() if item["source"] in r.get("local_path", "")), None)}
            return item
        if identifier.startswith(("verba:lat:", "verba:eng:", "verba:parse:")):
            _, mode, query = identifier.split(":", 2)
            if mode == "parse":
                return self.analyze_latin(query)
            items = self.lookup_words(query, "la", "verba", "meaning" if mode == "eng" else "auto", 20)["items"]
            return {"id": identifier, "source": "verba", "kind": "word", "language": "la", "text": query,
                    "readings": [], "description": "\n".join(i["description"] for i in items),
                    "extra": {"entries": [self.get_entry(i["id"]) for i in items]}, "status": "available"}
        if not DATABASE.exists():
            return None
        with db.connect() as c:
            row = db.entry_row(c, identifier)
            return db.unpack(c, row, detail=True) if row else None

    def find_related_names(self, identifier, relation=None, limit=20, offset=0):
        if not DATABASE.exists():
            return page([], limit, offset)
        with db.connect() as c:
            entry = db.entry_row(c, identifier)
            if not entry:
                return page([], limit, offset)
            sql = db.SELECT.replace("SELECT e.id", "SELECT rel.value AS relation_type,origin.name AS relation_source,e.id", 1)
            sql += " JOIN relations edge ON e.id=CASE WHEN edge.left_id=? THEN edge.right_id ELSE edge.left_id END JOIN labels rel ON rel.id=edge.relation JOIN sources origin ON origin.id=edge.source WHERE (edge.left_id=? OR edge.right_id=?)"
            params = [entry["id"]] * 3
            if relation:
                sql += " AND rel.value=?"
                params.append(relation)
            sql += " ORDER BY coalesce(t.search_key,t.text),s.name,e.variant,cast(e.legacy_key AS TEXT),rel.value LIMIT ? OFFSET ?"
            items = []
            for row in c.execute(sql, params + [limit + 1, offset]):
                item = db.unpack(c, row)
                item["extra"].update(relation=row["relation_type"], relation_source=row["relation_source"])
                items.append(item)
        result = page(items, limit, 0)
        result.update(offset=offset, next_offset=offset + limit if result["has_more"] else None)
        return result

    def transliterate_name(self, text, scheme="hepburn"):
        return transliterate(text, scheme)

    def analyze_latin(self, text, limit=20):
        return verba(text, "parse", limit)
