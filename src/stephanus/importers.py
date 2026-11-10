"""Source-specific imports; native datasets are queried by their own adapters."""

import csv
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import re
import sys

import ijson

from .database import Writer, connect, initialize
from .paths import DATA, VENDOR

def json_items(pattern, prefix):
    path = next((DATA / "raw" / "jmdict-simplified").glob(pattern), None)
    if path is None:
        raise FileNotFoundError("Dataset not downloaded: " + pattern)
    with path.open("rb") as f:
        yield from ijson.items(f, prefix + ".item", use_float=True)

def jmnedict(w):
    name_types = {"surname", "given", "masc", "fem", "person", "unclass", "full", "male", "female"}
    for row in json_items("jmnedict-*.json", "words"):
        types = [t for tr in row["translation"] for t in tr["type"]]
        if not name_types.intersection(types):
            continue
        categories = list(types)
        if set(types).intersection({"given", "masc", "fem", "male", "female"}) and "given" not in categories:
            categories.append("given")
        forms = row["kanji"] or row["kana"]
        description = "; ".join(t["text"] if isinstance(t, dict) else t for tr in row["translation"] for t in tr["translation"])
        for i, form in enumerate(forms):
            readings = [r["text"] for r in row["kana"] if not row["kanji"] or "*" in r["appliesToKanji"] or form["text"] in r["appliesToKanji"]]
            w.add(f"jmnedict:{row['id']}:{i}", form["text"], "ja", readings=readings, category=",".join(categories), description=description, extra=row)

def jmdict(w):
    for row in json_items("jmdict-*.json", "words"):
        description = "; ".join(g["text"] for s in row["sense"] for g in s["gloss"] if g["lang"] == "eng")
        for i, form in enumerate(row["kanji"] or row["kana"]):
            readings = [r["text"] for r in row["kana"] if not row["kanji"] or "*" in r["appliesToKanji"] or form["text"] in r["appliesToKanji"]]
            w.add(f"jmdict:{row['id']}:{i}", form["text"], "ja", "word", readings, description, extra=row)

def kanjidic(w):
    for row in json_items("kanjidic2-*.json", "characters"):
        rm = row.get("readingMeaning") or {}
        groups = rm.get("groups", [])
        readings = [r["value"] for g in groups for r in g["readings"] if r["type"].startswith("ja_")] + rm.get("nanori", [])
        description = "; ".join(m["value"] for g in groups for m in g["meanings"] if m["lang"] == "en")
        w.add("kanjidic2:" + row["literal"], row["literal"], "ja", "character", readings, description, extra=row)

def medieval(w):
    for filename in ["app_name_data.csv", "app_variations.csv"]:
        with (VENDOR / "medieval-names" / filename).open(encoding="utf-8-sig", newline="") as f:
            for index, row in enumerate(csv.DictReader(f)):
                name = row["NAME"]
                # CNF groups supply stable links without inventing a language for a citation.
                canonical = row.get("CNF") or name
                root = w.add("medieval-names:canonical:" + canonical, canonical, description=row.get("ETYMOLOGY", ""), category="given", extra={"LINK": row.get("LINK"), "ORIGIN": row.get("ORIGIN")})
                identifier = w.add(f"medieval-names:{filename}:{index}", name, description="; ".join(row.get(k, "") for k in ("MEANING", "ETYMOLOGY", "NOTES") if row.get(k) not in (None, "NA", "")), category="given", extra=row)
                w.relation(root, identifier, "historical_variant")

def onomaverse(w):
    directory = DATA / "raw" / "onomaverse"
    paths = list(directory.glob("*.csv"))
    if not paths:
        raise FileNotFoundError("Onomaverse CSV release not downloaded")
    for path in sorted(paths):
        with path.open(encoding="utf-8-sig", newline="") as f:
            for index, row in enumerate(csv.DictReader(f)):
                base = "onomaverse:" + row["name_id"]
                name_type = row.get("type") or ("surname" if row["name_id"].endswith("-sn") else "given")
                name_type = "given" if name_type == "forename" else name_type
                w.add(base, row["name"], category=name_type, extra={"name_id": row["name_id"]})
                if path.name == "name-equivalence.csv":
                    target = w.add("onomaverse:" + row["related_id"], row["related_name"], category="surname" if row["related_id"].endswith("-sn") else "given", extra={"name_id": row["related_id"]})
                    w.relation(base, target, row["relation"])
                elif path.name == "name-transliterations.csv":
                    localized = w.add(f"onomaverse:localized:{index}", row["localized_form"], row["lang_code"], category=name_type, extra=row)
                    w.relation(base, localized, "transliteration")
                else:
                    w.supplement(base, path.stem, row)

def cltk(w):
    with (VENDOR / "latin-proper-names" / "proper_names.txt").open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            text = line.strip()
            if text:
                w.add(f"latin-proper-names:{i}", text, "la", category="proper_name", description="PHI5 classical proper-name word list; persons and places.")

def kaikki(w):
    path = DATA / "raw" / "kaikki" / "raw-wiktextract-data.jsonl.gz"
    extracted = DATA / "raw" / "kaikki" / "ja-la.jsonl"
    use_extracted = extracted.exists()
    if not path.exists() and not use_extracted:
        raise FileNotFoundError("Kaikki extraction not downloaded")
    reader = extracted.open(encoding="utf-8") if use_extracted else gzip.open(path, "rt", encoding="utf-8")
    out = None if use_extracted else extracted.open("w", encoding="utf-8")
    selected_language = re.compile(r'"lang_code"\s*:\s*"(?:ja|la)"')
    try:
        for i, line in enumerate(reader):
            if not use_extracted and not selected_language.search(line):
                continue
            row = json.loads(line)
            language = row.get("lang_code")
            if language not in ("ja", "la"):
                continue
            if out:
                out.write(line)
            word = row.get("word", "")
            description = "; ".join(g for s in row.get("senses", []) for g in s.get("glosses", []))
            description += ("; " + row["etymology_text"]) if row.get("etymology_text") else ""
            readings = [r.get("roman", "") for r in row.get("sounds", []) if r.get("roman")]
            kind = "name" if row.get("pos") in ("name", "proper-noun") else "word"
            w.add(f"kaikki:{i}", word, language, kind, readings, description, row.get("pos", ""), row)
            if w.count and w.count % 100000 == 0:
                print(f"kaikki: {w.count} selected entries", file=sys.stderr, flush=True)
    finally:
        reader.close()
        if out:
            out.close()

IMPORTERS = {"jmnedict": jmnedict, "jmdict": jmdict, "kanjidic2": kanjidic, "medieval-names": medieval, "onomaverse": onomaverse, "latin-proper-names": cltk, "kaikki": kaikki}

def import_data(source=None):
    summary = []
    with connect(write=True) as c:
        initialize(c)
        completed = {r[0] for r in c.execute("SELECT source FROM imports")}
        for name, importer in IMPORTERS.items():
            if source and name != source:
                continue
            if name in completed:
                continue
            w = Writer(c, name)
            try:
                importer(w)
                c.execute("INSERT INTO imports VALUES (?,?,?)", (name, w.count, datetime.now(timezone.utc).isoformat()))
                c.commit()
                result = {"source": name, "status": "imported", "entries": w.count}
            except (FileNotFoundError, OSError, ValueError) as exc:
                c.commit()
                result = {"source": name, "status": "unavailable", "entries": w.count, "error": str(exc)}
            summary.append(result)
            report_path = DATA / "import-summary.json"
            previous = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else []
            previous = [r for r in previous if r["source"] != name] + [result]
            report_path.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, ensure_ascii=False), file=sys.stderr, flush=True)
    return summary
