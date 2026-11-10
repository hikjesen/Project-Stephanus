"""Compact knowledge index with integer references and source-local public IDs."""
import json
import sqlite3
import unicodedata
import zlib
from functools import lru_cache
import re
from .paths import DATABASE

KINDS = {1: "name", 2: "word", 3: "character"}
MATCHES = {0: "text_exact", 1: "reading_exact", 2: "prefix", 3: "meaning"}
JSON_DICTIONARY = (b'{"senses":[{"id":0,"glosses":[],"tags":[],"pos":[],"written_forms":[],"readings":[],'
 b'"field":[],"dialect":[],"source_words":[],"related":[],"notes":[],"antonyms":[]}],'
 b'"etymology":"","forms":[],"related_words":[{"text":"","relation":"","grammar":""}],'
 b'"attestations":[{"NAME":"","CNF":"","ORIGIN":"","AREA":"","EARLIEST":"","LATEST":"","CASE":"","GENDER":"","CITATION":"","LINK":""}],'
 b'"pronunciations":[],"principal_parts":[],"grammar":{},"latin_equivalents":[],"headings":[],"name_id":"","country":"","frequency":0')

def description_text(value):
    return zlib.decompress(value).decode("utf-8") if isinstance(value, bytes) else value

def pack_description(value):
    raw = value.encode("utf-8")
    packed = zlib.compress(raw)
    return packed if len(packed) < len(raw) else value

def key(text):
    text = unicodedata.normalize("NFKC", str(text)).casefold().strip()
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)

def connect(write=False):
    if write:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(DATABASE)
    else:
        c = sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    c.create_function("stephanus_description", 1, description_text, deterministic=True)
    register_blocks(c)
    return c

def register_blocks(c):
    @lru_cache(maxsize=32)
    def block(identifier):
        return decode(c.execute("SELECT data FROM knowledge_blocks WHERE id=?", (identifier,)).fetchone()[0])
    def record(identifier, field):
        if identifier is None:
            return None
        item = block((identifier - 1) // 256)[(identifier - 1) % 256]
        value = item[field]
        return json.dumps(value, ensure_ascii=False, separators=(",", ":")) if field == 2 and value else None if field == 2 else value
    c.create_function("stephanus_record", 2, record, deterministic=True)

def split_id(identifier):
    source, value = identifier.split(":", 1)
    variant = 0
    if source in ("jmnedict", "jmdict"):
        record, form = value.rsplit(":", 1)
        value = (int(record) << 16) | int(form)
    elif source == "onomaverse" and value.startswith("localized:"):
        variant, value = 1, int(value.split(":", 1)[1])
    elif source == "medieval-names":
        prefix, value = value.split(":", 1)
        variant = {"canonical": 0, "app_name_data.csv": 1, "app_variations.csv": 2}[prefix]
        if variant:
            value = int(value)
    elif source in ("kaikki", "latin-proper-names"):
        value = int(value)
    elif source == "verba":
        prefix, value = value.split(":", 1)
        variant = {"ls": 1, "sh": 2}[prefix]
        if variant == 2:
            value = int(value)
    return source, variant, value

def public_id(source, variant, value):
    if source in ("jmnedict", "jmdict"):
        value = f"{value >> 16}:{value & 65535}"
    elif source == "onomaverse" and variant:
        value = f"localized:{value}"
    elif source == "medieval-names":
        value = f"{('canonical', 'app_name_data.csv', 'app_variations.csv')[variant]}:{value}"
    elif source == "verba":
        value = f"{('unused', 'ls', 'sh')[variant]}:{value}"
    return f"{source}:{value}"

def encode(data):
    if not data:
        return None
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressor = zlib.compressobj(level=9, zdict=JSON_DICTIONARY)
    packed = compressor.compress(raw) + compressor.flush()
    return b"d" + packed if len(packed) < len(raw) else b"j" + raw

def decode(blob):
    if not blob:
        return {}
    if isinstance(blob, str):
        return json.loads(blob)
    if blob[:1] == b"d":
        decoder = zlib.decompressobj(zdict=JSON_DICTIONARY)
        return json.loads(decoder.decompress(blob[1:]) + decoder.flush())
    return json.loads(zlib.decompress(blob[1:]) if blob[:1] == b"z" else blob[1:])

SELECT = """SELECT e.id,e.source,e.variant,e.legacy_key,e.form,e.kind,e.record,
 e.language AS language_id,s.name AS source_name,s.version AS source_version,l.code AS language,
 t.text,coalesce(t.search_key,t.text) AS search_key,coalesce(stephanus_description(r.description),'') AS description,r.data,r.record_key,
 cat.value AS category FROM entries e JOIN sources s ON s.id=e.source
 JOIN languages l ON l.id=e.language JOIN strings t ON t.id=e.form
 LEFT JOIN records r ON r.id=e.record LEFT JOIN labels cat ON cat.id=e.category"""

def entry_row(c, identifier):
    try:
        source, variant, value = split_id(identifier)
    except (ValueError, KeyError):
        return None
    return c.execute(SELECT + " WHERE s.name=? AND e.variant=? AND e.legacy_key=?", (source, variant, value)).fetchone()

def unpack(c, row, detail=False):
    source = row["source_name"]
    readings = [r[0] for r in c.execute("SELECT t.text FROM readings r JOIN strings t ON t.id=r.reading WHERE r.entry=? ORDER BY r.ordinal", (row["id"],))]
    result = {"id": public_id(source, row["variant"], row["legacy_key"]), "source": source,
              "kind": KINDS[row["kind"]], "language": row["language"], "text": row["text"],
              "category": row["category"] or "", "readings": readings,
              "description": row["description"] if detail else row["description"][:240], "extra": {}}
    if "priority" in row.keys():
        result["extra"]["match"] = MATCHES[row["priority"]]
        result["_sort"] = (row["priority"], row["search_key"], source, row["variant"], str(row["legacy_key"]))
    if not detail:
        if source == "kaikki" and not row["record"]:
            result["extra"]["is_form"] = True
        return result
    knowledge = {"senses": [], "etymology": None, "forms": [], "related_words": [], "attestations": []}
    knowledge.update(decode(row["data"]))
    if knowledge["forms"]:
        labels = {r[0]: r[1] for r in c.execute("SELECT id,value FROM labels")}
        knowledge["forms"] = [{"text": f[0], "tags": labels.get(f[1], "").split("|") if f[1] else []} for f in knowledge["forms"]]
    aliases = [{"text": r[0], "language": row["language"], "tags": r[1].split("|") if r[1] else [], "relation": {1: "form_of", 2: "alt_of"}[r[2]]}
               for r in c.execute("SELECT t.text,coalesce(g.value,''),a.relation FROM aliases a JOIN strings t ON t.id=a.target LEFT JOIN labels g ON g.id=a.tags WHERE a.entry=?", (row["id"],))]
    if aliases:
        knowledge["lemma_links"] = aliases
        for alias in aliases:
            targets = c.execute(SELECT + " WHERE t.text=? AND e.language=? AND e.source=? AND e.record>0 LIMIT 5", (alias["text"], row["language_id"], row["source"])).fetchall()
            alias["entry_ids"] = [public_id(source, r["variant"], r["legacy_key"]) for r in targets]
            for target in targets:
                data = decode(target["data"])
                knowledge["senses"].extend(data.get("senses", []))
                if not knowledge["etymology"]:
                    knowledge["etymology"] = data.get("etymology")
        result["description"] = "; ".join(f"{a['relation']} {a['text']} ({', '.join(a['tags'])})" for a in aliases)
    supplements = [{"dataset": r[0], "data": decode(r[1])} for r in c.execute("SELECT g.value,p.data FROM supplements p JOIN labels g ON g.id=p.dataset WHERE p.entry=?", (row["id"],))]
    if supplements:
        knowledge["supplements"] = supplements
    result["extra"] = {"knowledge": knowledge, "provenance": {"source": source,
        "version": row["source_version"], "record": row["record_key"] or result["id"],
        "retention": "purpose-specific knowledge; source full text removed"}}
    return result

def search(query, kinds, language=None, source=None, category=None, mode="auto", amount=21):
    normalized = key(query)
    if not normalized:
        return []
    clauses, params = [], []
    if mode in ("auto", "text"):
        clauses += ["SELECT e.id,0 AS priority FROM strings t JOIN entries e ON e.form=t.id WHERE coalesce(t.search_key,t.text)=?",
                    "SELECT e.id,2 AS priority FROM strings t JOIN entries e ON e.form=t.id WHERE coalesce(t.search_key,t.text)>=? AND coalesce(t.search_key,t.text)<?"]
        params += [normalized, normalized, normalized + "\U0010ffff"]
    if mode in ("auto", "reading"):
        clauses.append("SELECT r.entry AS id,1 AS priority FROM strings t JOIN readings r ON r.reading=t.id WHERE coalesce(t.search_key,t.text)=?")
        params.append(normalized)
    if mode in ("auto", "meaning"):
        terms = re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", query), flags=re.UNICODE)
        if not terms:
            return []
        # Indexed records have positive IDs; spell this out to use the partial index.
        clauses.append("SELECT e.id,3 AS priority FROM record_fts f JOIN entries e ON e.record=f.rowid WHERE record_fts MATCH ? AND e.record>0")
        params.append(" AND ".join('"' + t + '"' for t in terms))
    if not clauses:
        raise ValueError("mode must be auto, text, reading, or meaning")
    kind_ids = [i for i, name in KINDS.items() if name in kinds]
    predicates = ["e.kind IN (" + ",".join("?" for _ in kind_ids) + ")"]
    params += kind_ids
    for column, value in [("l.code", language), ("s.name", source)]:
        if value:
            predicates.append(column + "=?")
            params.append(value)
    if category:
        predicates.append("instr(','||cat.value||',',','||?||',')>0")
        params.append(category)
    sql = "WITH matches AS (" + " UNION ALL ".join(clauses) + "), best AS (SELECT id,min(priority) AS priority FROM matches GROUP BY id) "
    listing = SELECT.replace("r.data,r.record_key", "NULL AS data,NULL AS record_key")
    sql += listing.replace("SELECT e.id", "SELECT best.priority,e.id", 1) + " JOIN best ON best.id=e.id WHERE " + " AND ".join(predicates)
    sql += " ORDER BY best.priority,coalesce(t.search_key,t.text),s.name,e.variant,cast(e.legacy_key AS TEXT) LIMIT ?"
    params.append(amount)
    with connect() as c:
        return [unpack(c, r) for r in c.execute(sql, params)]
