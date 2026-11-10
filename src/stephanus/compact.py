"""One-pass purpose-specific extraction; no raw-record archive, hashing or acceptance."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata
from .database import encode, decode, key, split_id, pack_description, description_text, register_blocks

SCHEMA = """
PRAGMA page_size=4096;
PRAGMA journal_mode=OFF;
PRAGMA synchronous=OFF;
PRAGMA temp_store=MEMORY;
PRAGMA cache_size=-196608;
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
CREATE TABLE sources(id INTEGER PRIMARY KEY,name TEXT UNIQUE,version TEXT);
CREATE TABLE languages(id INTEGER PRIMARY KEY,code TEXT UNIQUE);
CREATE TABLE labels(id INTEGER PRIMARY KEY,value TEXT);
CREATE TABLE strings(id INTEGER PRIMARY KEY,text TEXT,search_key TEXT);
CREATE TABLE records(id INTEGER PRIMARY KEY,record_key,description TEXT,data BLOB);
CREATE TABLE entries(id INTEGER PRIMARY KEY,source INTEGER,variant INTEGER,legacy_key,
 form INTEGER,language INTEGER,kind INTEGER,category INTEGER,record INTEGER);
CREATE TABLE readings(entry INTEGER,ordinal INTEGER,reading INTEGER,PRIMARY KEY(entry,ordinal)) WITHOUT ROWID;
CREATE TABLE aliases(entry INTEGER,target INTEGER,tags INTEGER,relation INTEGER,
 PRIMARY KEY(entry,target,tags,relation)) WITHOUT ROWID;
CREATE TABLE relations(left_id INTEGER,right_id INTEGER,relation INTEGER,source INTEGER,
 PRIMARY KEY(left_id,right_id,relation,source)) WITHOUT ROWID;
CREATE TABLE supplements(entry INTEGER,dataset INTEGER,ordinal INTEGER,data BLOB,
 PRIMARY KEY(entry,dataset,ordinal)) WITHOUT ROWID;
"""

def clean(value):
    return re.sub(r"[\x00-\x1f]", "", str(value or "")).strip()

def pack_records(c):
    """Share compression context across 256 extracted records, with a small read cache."""
    c.executescript("CREATE TABLE knowledge_blocks(id INTEGER PRIMARY KEY,data BLOB); CREATE TABLE record_ids(id INTEGER PRIMARY KEY);")
    chunk = []
    block_id = 0
    for identifier, record_key, description, payload in c.execute("SELECT id,record_key,description,data FROM records ORDER BY id"):
        chunk.append([record_key, description_text(description), decode(payload)])
        c.execute("INSERT INTO record_ids VALUES (?)", (identifier,))
        if len(chunk) == 256:
            c.execute("INSERT INTO knowledge_blocks VALUES (?,?)", (block_id, encode(chunk)))
            block_id += 1
            chunk = []
    if chunk:
        c.execute("INSERT INTO knowledge_blocks VALUES (?,?)", (block_id, encode(chunk)))
    c.executescript("""
    DROP TABLE records;
    CREATE VIEW records AS SELECT id,stephanus_record(id,0) AS record_key,
      stephanus_record(id,1) AS description,stephanus_record(id,2) AS data FROM record_ids;
    """)
    register_blocks(c)

def create_fts(c):
    c.executescript("""
    CREATE VIEW record_search AS SELECT id,description FROM records;
    CREATE VIRTUAL TABLE record_fts USING fts5(description,content='record_search',content_rowid='id',columnsize=0,detail=none,tokenize='unicode61 remove_diacritics 2');
    INSERT INTO record_fts(rowid,description) SELECT id,description FROM record_search WHERE description<>'';
    INSERT INTO record_fts(record_fts) VALUES ('optimize');
    """)

class Builder:
    def __init__(self, c, manifest):
        self.c = c
        self.manifest = manifest
        self.strings, self.labels, self.languages, self.sources = {}, {}, {}, {}
        self.record_ids, self.identifiers = {}, {}
        self.counts = Counter()
        self.dropped = defaultdict(Counter)
        self.samples = {}
        self.next_entry = 0

    def intern(self, table, cache, value):
        if value not in cache:
            identifier = len(cache) + 1
            if table == "strings":
                normalized = key(value)
                self.c.execute("INSERT INTO strings VALUES (?,?,?)", (identifier, value, normalized if normalized != value else None))
            else:
                self.c.execute(f"INSERT INTO {table} VALUES (?,?)", (identifier, value))
            cache[value] = identifier
        return cache[value]

    def text(self, value):
        return self.intern("strings", self.strings, str(value))

    def label(self, value):
        return self.intern("labels", self.labels, value) if value else 0

    def source(self, name):
        if name not in self.sources:
            source_id = len(self.sources) + 1
            prefix = "jmdict-simplified" if name in ("jmdict", "jmnedict", "kanjidic2") else name
            versions = list(dict.fromkeys(r.get("version") or r.get("revision") or r.get("acquired_at", "") for r in self.manifest if prefix in r.get("local_path", "").replace("\\", "/")))
            self.c.execute("INSERT INTO sources VALUES (?,?,?)", (source_id, name, "; ".join(v for v in versions if v) or "2026-11-10 local snapshot"))
            self.sources[name] = source_id
        return self.sources[name]

    def omitted(self, source, data, allowed):
        self.dropped[source].update(k for k in data if k not in allowed)

    def project(self, source, row, extra):
        data, description, aliases = {}, row["description"], []
        if source == "jmnedict":
            self.omitted(source, extra, {"id", "kanji", "kana", "translation"})
        elif source == "jmdict":
            self.omitted(source, extra, {"id", "kanji", "kana", "sense"})
            senses = []
            for index, sense in enumerate(extra.get("sense", [])):
                self.omitted(source + ".sense", sense, {"gloss", "partOfSpeech", "appliesToKanji", "appliesToKana", "related", "antonym", "field", "dialect", "misc", "info", "languageSource"})
                glosses = [g["text"] for g in sense.get("gloss", []) if g.get("lang") == "eng"]
                self.dropped[source]["non_English_gloss"] += sum(g.get("lang") != "eng" for g in sense.get("gloss", []))
                item = {"id": index, "glosses": glosses}
                for field, target in [("partOfSpeech", "pos"), ("field", "field"), ("dialect", "dialect"), ("misc", "tags"), ("info", "notes"), ("languageSource", "source_words"), ("related", "related"), ("antonym", "antonyms")]:
                    if sense.get(field):
                        item[target] = sense[field]
                for field, target in [("appliesToKanji", "written_forms"), ("appliesToKana", "readings")]:
                    if sense.get(field) not in (None, [], ["*"]):
                        item[target] = sense[field]
                senses.append(item)
            data["senses"] = senses
        elif source == "kanjidic2":
            self.omitted(source, extra, {"literal", "readingMeaning", "misc"})
            rm = extra.get("readingMeaning") or {}
            data["senses"] = [{"glosses": [v["value"] for v in g.get("meanings", []) if v.get("lang") == "en"]} for g in rm.get("groups", [])]
            data["pronunciations"] = [v for g in rm.get("groups", []) for v in g.get("readings", []) if v.get("type", "").startswith("ja_")]
            data["nanori"] = rm.get("nanori", [])
            variants = (extra.get("misc") or {}).get("variants")
            if variants:
                data["variants"] = variants
        elif source == "medieval-names":
            allowed = {"NAME", "CNF", "ORIGIN", "AREA", "EARLIEST", "LATEST", "CASE", "GENDER", "CITATION", "LINK", "ETYMOLOGY", "MEANING"}
            self.omitted(source, extra, allowed)
            history = {k: v for k, v in extra.items() if k in allowed - {"ETYMOLOGY", "MEANING"} and v not in (None, "", "NA")}
            data["attestations"] = [history] if history else []
            etymology = extra.get("ETYMOLOGY")
            meaning = extra.get("MEANING")
            data["etymology"] = etymology if etymology not in (None, "", "NA") else None
            data["senses"] = [{"glosses": [meaning]}] if meaning not in (None, "", "NA") else []
            description = "; ".join(v for v in (meaning, etymology) if v not in (None, "", "NA"))
        elif source == "onomaverse":
            self.omitted(source, extra, {"name_id", "name", "localized_form", "lang_code", "type"})
            description = ""
        elif source == "latin-proper-names":
            description = ""
        elif source == "kaikki":
            allowed = {"word", "lang_code", "pos", "senses", "etymology_text", "etymology_links", "sounds", "forms", "related", "synonyms", "antonyms", "derived", "descendants", "hypernyms", "hyponyms"}
            self.omitted(source, extra, allowed)
            senses = extra.get("senses", [])
            pure_form = bool(senses) and all(s.get("form_of") or s.get("alt_of") for s in senses)
            for sense in senses:
                for field, relation in [("form_of", 1), ("alt_of", 2)]:
                    for link in sense.get(field, []):
                        if link.get("word"):
                            aliases.append((self.text(link["word"]), self.label("|".join(sense.get("tags", []))), relation))
            if pure_form:
                self.counts["compact_form_records"] += 1
                self.samples.setdefault("form_id", row["id"])
                return {}, "", aliases, True
            normalized_senses = []
            for index, sense in enumerate(senses):
                self.omitted(source + ".sense", sense, {"glosses", "tags", "topics", "form_of", "alt_of", "senseid", "qualifier"})
                item = {"id": index, "glosses": sense.get("glosses", [])}
                for field in ("tags", "topics", "qualifier", "form_of", "alt_of"):
                    if sense.get(field):
                        item[field] = sense[field]
                normalized_senses.append(item)
            data["senses"] = normalized_senses
            data["pos"] = extra.get("pos", "")
            if extra.get("etymology_text"):
                data["etymology"] = extra["etymology_text"]
            if extra.get("etymology_links"):
                data["source_words"] = extra["etymology_links"]
            forms = set()
            for form in extra.get("forms", []):
                if form.get("form"):
                    forms.add((form["form"], self.label("|".join(form.get("tags", [])))))
            if forms:
                data["forms"] = sorted(forms)
                self.counts["retained_paradigm_forms"] += len(forms)
            related = []
            for field in ("related", "synonyms", "antonyms", "derived", "descendants", "hypernyms", "hyponyms"):
                for word in extra.get(field, []):
                    if word.get("word"):
                        item = {"text": word["word"], "relation": field}
                        for k in ("lang_code", "sense", "tags"):
                            if word.get(k):
                                item[k] = word[k]
                        related.append(item)
            if related:
                data["related_words"] = related
            pronunciations = [{k: v for k, v in sound.items() if k in ("ipa", "roman", "other", "tags")} for sound in extra.get("sounds", [])]
            if any(pronunciations):
                data["pronunciations"] = [p for p in pronunciations if p]
            description = "; ".join(g for s in normalized_senses for g in s["glosses"])
            if data.get("etymology"):
                description += ("; " if description else "") + data["etymology"]
        return data, description, aliases, False

    def add(self, row, data=None, description=None):
        self.next_entry += 1
        eid = self.next_entry
        source, variant, legacy = split_id(row["id"])
        sid = self.source(source)
        record_key = legacy >> 16 if source in ("jmnedict", "jmdict") else legacy
        cache_key = (sid, variant, record_key)
        aliases = []
        if cache_key in self.record_ids:
            rid = self.record_ids[cache_key]
        else:
            if data is None:
                data, description, aliases, pure = self.project(source, row, json.loads(row["extra"]))
            if description or data:
                cur = self.c.execute("INSERT INTO records(record_key,description,data) VALUES (?,?,?)", (record_key, pack_description(description or ""), encode(data)))
                rid = cur.lastrowid
            else:
                rid = 0
            if source in ("jmnedict", "jmdict"):
                self.record_ids[cache_key] = rid
        language = self.intern("languages", self.languages, row["language"])
        self.c.execute("INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?)", (eid, sid, variant, legacy, self.text(row["text"]), language, {"name": 1, "word": 2, "character": 3}[row["kind"]], self.label(row["category"]), rid))
        self.c.executemany("INSERT INTO readings VALUES (?,?,?)", [(eid, i, self.text(r)) for i, r in enumerate(dict.fromkeys(json.loads(row["readings"])))])
        if aliases:
            self.c.executemany("INSERT OR IGNORE INTO aliases VALUES (?,?,?,?)", [(eid, *a) for a in aliases])
        self.identifiers[row["id"]] = eid
        self.counts[source] += 1
        return eid

    def verba(self, root):
        source = root / "vendor" / "verba" / "source"
        if not all((source / name).exists() for name in ("ls_schema.jsonl", "smithhall_schema.jsonl")):
            print("Latin lexical inputs unavailable; explicitly restore the verba source for a full rebuild.", file=sys.stderr)
            return
        for line_number, line in enumerate((source / "ls_schema.jsonl").open(encoding="utf-8")):
            node = json.loads(line)
            gloss = clean(node.get("gloss"))[:240]
            senses = []
            if gloss:
                senses.append({"id": "lead", "glosses": [gloss]})
            else:
                def collect(nodes, path=""):
                    for i, sense in enumerate(nodes):
                        location = path + "/" + str(i)
                        if sense.get("gloss"):
                            senses.append({"id": location, "glosses": [clean(sense["gloss"])[:240]]})
                        collect(sense.get("children", []), location)
                collect(node.get("senses", []))
            data = {"senses": senses}
            for field, target in [("etym", "etymology"), ("pos", "pos"), ("morph", "grammar"), ("principal_parts", "principal_parts"), ("alt_keys", "alternative_keys"), ("xref", "cross_reference")]:
                if node.get(field):
                    data[target] = node[field]
            row = {"id": "verba:ls:" + (node.get("id") or str(line_number)), "language": "la", "text": node.get("display") or node.get("lemma") or node["key"], "kind": "word", "category": "", "readings": json.dumps(list(dict.fromkeys([node["key"]] + node.get("alt_keys", []))))}
            self.add(row, data, "; ".join(g for s in senses for g in s["glosses"]))
            self.omitted("verba.ls", node, {"id", "lemma", "display", "key", "alt_keys", "pos", "morph", "principal_parts", "etym", "gloss", "xref", "senses"})
            self.dropped["verba.ls"]["article_examples_and_body"] += 1
        for line_number, line in enumerate((source / "smithhall_schema.jsonl").open(encoding="utf-8")):
            node = json.loads(line)
            equivalents = []
            def collect(nodes, headings=()):
                for s in nodes:
                    path = headings + ((clean(s["heading"]),) if s.get("heading") else ())
                    if s.get("latin"):
                        equivalents.append({"text": clean(s["latin"]), "grammar": clean(s.get("gram")), "headings": path})
                    collect(s.get("children", []), path)
            collect(node.get("senses", []))
            data = {"senses": [{"glosses": [node["head"]], "latin_equivalents": equivalents}], "related_words": [{"text": e["text"], "relation": "English-Latin equivalent", "grammar": e["grammar"]} for e in equivalents]}
            row = {"id": f"verba:sh:{line_number}", "language": "la", "text": node["head"], "kind": "word", "category": "", "readings": "[]"}
            self.add(row, data, node["head"] + "; " + "; ".join(e["text"] for e in equivalents))
            self.dropped["verba.sh"]["article_body_and_examples"] += 1

def build(old_path, output, root):
    old_path, output, root = Path(old_path).resolve(), Path(output).resolve(), Path(root).resolve()
    if output.exists():
        raise FileExistsError(f"Candidate already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    old = sqlite3.connect(old_path.as_uri() + "?mode=ro", uri=True)
    old.row_factory = sqlite3.Row
    c = sqlite3.connect(output)
    c.create_function("stephanus_description", 1, description_text, deterministic=True)
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "input": str(old_path), "output": str(output), "policy": "compact-v1"}
    try:
        c.executescript(SCHEMA)
        builder = Builder(c, json.loads((root / "resources.json").read_text(encoding="utf-8")))
        for row in old.execute("SELECT * FROM entries ORDER BY rowid"):
            builder.add(row)
            if builder.next_entry % 100000 == 0:
                c.commit()
                print(f"Extracted {builder.next_entry:,} entries", file=sys.stderr, flush=True)
        report["migrated_entries"] = builder.next_entry
        print("Extracting compact Latin dictionaries", file=sys.stderr, flush=True)
        builder.verba(root)
        print("Converting relations and supplementary attributes", file=sys.stderr, flush=True)
        relation_count = 0
        for row in old.execute("SELECT * FROM relations"):
            left, right = builder.identifiers.get(row["left_id"]), builder.identifiers.get(row["right_id"])
            if left and right:
                cursor = c.execute("INSERT OR IGNORE INTO relations VALUES (?,?,?,?)", (left, right, builder.label(row["relation"]), builder.source(row["source"])))
                relation_count += cursor.rowcount
            else:
                raise ValueError("Missing relation endpoint: " + str(dict(row)))
        sequence = Counter()
        supplement_count = 0
        for row in old.execute("SELECT * FROM supplements"):
            eid, dataset = builder.identifiers[row["entry_id"]], builder.label(row["dataset"])
            group = (eid, dataset)
            content = {k: v for k, v in json.loads(row["data"]).items() if k not in ("name_id", "name", "type")}
            c.execute("INSERT INTO supplements VALUES (?,?,?,?)", (eid, dataset, sequence[group], encode(content)))
            sequence[group] += 1
            supplement_count += 1
        c.execute("CREATE TABLE imports(source TEXT PRIMARY KEY,entries INTEGER,imported_at TEXT)")
        now = datetime.now(timezone.utc).isoformat()
        c.executemany("INSERT INTO imports VALUES (?,?,?)", [(s, builder.counts[s], now) for s in builder.sources])
        print("Building compact search indexes", file=sys.stderr, flush=True)
        c.commit()
        c.executescript("""
        CREATE INDEX strings_key ON strings(coalesce(search_key,text));
        CREATE UNIQUE INDEX entries_identity ON entries(source,variant,legacy_key);
        CREATE INDEX entries_form ON entries(form);
        CREATE INDEX entries_record ON entries(record) WHERE record>0;
        CREATE INDEX readings_reading ON readings(reading);
        CREATE INDEX relations_right ON relations(right_id,left_id,relation,source);
        """)
        print("Packing shared knowledge blocks", file=sys.stderr, flush=True)
        pack_records(c)
        create_fts(c)
        c.execute("INSERT INTO meta VALUES ('format','compact-v1')")
        c.commit()
        print("Packing database pages", file=sys.stderr, flush=True)
        c.execute("VACUUM")
        report.update(completed_at=now, database_bytes=output.stat().st_size, sources={s: builder.counts[s] for s in builder.sources}, languages=list(builder.languages), relations=relation_count, supplements=supplement_count, conversion_counters=dict(builder.counts), omitted_fields={s: dict(v) for s, v in builder.dropped.items()}, samples=builder.samples)
    finally:
        old.close()
        c.close()
    report_path = output.parent / "compact-build.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("migrated_entries", "database_bytes", "sources", "relations")}, ensure_ascii=False), flush=True)
    return report
