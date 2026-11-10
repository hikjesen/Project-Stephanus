"""Shared read-only service for CLI and MCP."""

from dataclasses import asdict
import json
import sqlite3

from . import database as db
from .native import JINMEI, PERSONAL, get_native, search_jinmei, search_personal, transliterate, verba
from .paths import DATABASE, DATA, VENDOR
from .resources import read_manifest
from .targets import load_targets

def page(items, limit, offset):
    return {"items": items[offset:offset + limit], "limit": limit, "offset": offset,
            "has_more": len(items) > offset + limit, "next_offset": offset + limit if len(items) > offset + limit else None}

class Service:
    def source_unavailable(self, source, limit, offset):
        if not source:
            return None
        if DATABASE.exists():
            with db.connect() as c:
                if c.execute("SELECT 1 FROM imports WHERE source=?", (source,)).fetchone():
                    return None
        return {**page([], limit, offset), "status": "unavailable", "description": f"Source '{source}' is not indexed. See list_sources or run stephanus import."}

    def list_sources(self):
        imports = {}
        languages = []
        if DATABASE.exists():
            with db.connect() as c:
                imports = {r["source"]: dict(r) for r in c.execute("SELECT * FROM imports")}
                languages = [r[0] for r in c.execute("SELECT DISTINCT language FROM entries ORDER BY language")]
        capabilities = {
            "jmnedict": (["ja"], ["name_lookup"]),
            "jmdict": (["ja"], ["lexicon_lookup"]),
            "kanjidic2": (["ja"], ["lexicon_lookup"]),
            "medieval-names": (["und"], ["name_lookup", "name_relations"]),
            "onomaverse": (["mul"], ["name_lookup", "name_relations"]),
            "latin-proper-names": (["la"], ["name_lookup"]),
            "kaikki": (["ja", "la"], ["name_lookup", "lexicon_lookup"]),
        }
        backends = [{"source": source, "status": "indexed", "languages": capabilities[source][0],
                     "capabilities": capabilities[source][1], **value} for source, value in imports.items()]
        for source, available, native_capabilities in [
            (JINMEI, (VENDOR / JINMEI / "jinmei" / "mei.json").exists(), ["name_lookup"]),
            (PERSONAL, (DATA / "raw" / PERSONAL / "japanese_names.sqlite").exists(), ["name_lookup"]),
            ("verba", (VENDOR / "verba" / "verba.py").exists(), ["lexicon_lookup", "morphology"]),
            ("python-romkan", (VENDOR / "python-romkan" / "src" / "romkan").exists(), ["transliteration"]),
        ]:
            backends.append({"source": source, "status": "native" if available else "unavailable", "languages": ["la"] if source == "verba" else ["ja"], "capabilities": native_capabilities})
        return {"backends": backends, "targets": [asdict(t) for t in load_targets().values()], "indexed_languages": languages,
                "resources": read_manifest()}

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
        result = page(items, limit, offset)
        if missing:
            result["unavailable_sources"] = missing
        return result

    def lookup_words(self, query, language=None, source=None, mode="auto", limit=20, offset=0):
        if source == "verba":
            if offset:
                return page([], limit, offset)
            item = verba(query, "eng" if mode == "meaning" else "lat", limit)
            return page([item] if item.get("description") else [], limit, 0)
        unavailable = self.source_unavailable(source, limit, offset)
        if unavailable:
            return unavailable
        items = db.search(query, ["word", "character"], language, source, mode=mode, amount=offset + limit + 1) if DATABASE.exists() else []
        if not items and language == "la" and not source and offset == 0:
            item = verba(query, "eng" if mode == "meaning" else "lat", limit)
            if item.get("description"):
                items.append(item)
        return page(items, limit, offset)

    def get_entry(self, identifier):
        if identifier.startswith((JINMEI + ":", PERSONAL + ":")):
            return get_native(identifier)
        if identifier.startswith("verba:"):
            _, mode, query = identifier.split(":", 2)
            return verba(query, mode)
        if not DATABASE.exists():
            return None
        with db.connect() as c:
            row = c.execute("SELECT * FROM entries WHERE id=?", (identifier,)).fetchone()
            if not row:
                return None
            result = db.unpack(row)
            supplements = [{"dataset": r[0], "data": json.loads(r[1])} for r in c.execute("SELECT dataset,data FROM supplements WHERE entry_id=?", (identifier,))]
            if supplements:
                result["extra"]["supplements"] = supplements
            return result

    def find_related_names(self, identifier, relation=None, limit=20, offset=0):
        if not DATABASE.exists():
            return page([], limit, offset)
        with db.connect() as c:
            sql = """SELECT e.*,r.relation AS relation_type,r.source AS relation_source FROM relations r JOIN entries e
              ON e.id=CASE WHEN r.left_id=? THEN r.right_id ELSE r.left_id END
              WHERE (r.left_id=? OR r.right_id=?)"""
            params = [identifier] * 3
            if relation:
                sql += " AND r.relation=?"
                params.append(relation)
            sql += " ORDER BY e.text_key,e.id LIMIT ? OFFSET ?"
            params.extend([limit + 1, offset])
            items = []
            for row in c.execute(sql, params):
                item = db.unpack(row)
                item["extra"]["relation"] = item.pop("relation_type")
                item["extra"]["relation_source"] = item.pop("relation_source")
                items.append(item)
        result = page(items, limit, 0)
        result.update(offset=offset, next_offset=offset + limit if result["has_more"] else None)
        return result

    def transliterate_name(self, text, scheme="hepburn"):
        return transliterate(text, scheme)

    def analyze_latin(self, text, limit=20):
        return verba(text, "parse", limit)
