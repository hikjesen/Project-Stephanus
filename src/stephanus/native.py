"""Query upstream Japanese formats directly and reuse upstream programs."""

from functools import lru_cache
import json
import os
import sqlite3
import subprocess
import sys

from .database import key
from .paths import DATA, VENDOR

JINMEI = "jinmei-dict"
PERSONAL = "japanese-personal-name-dataset"

def native_entry(identifier, source, text, readings, category, extra):
    return {"id": identifier, "source": source, "kind": "name", "language": "ja", "text": text,
            "readings": readings, "category": category, "description": "", "extra": extra}

@lru_cache(maxsize=2)
def jinmei_map(group):
    with (VENDOR / JINMEI / "jinmei" / (group + ".json")).open(encoding="utf-8") as f:
        return json.load(f)

def search_jinmei(query, amount, category=None, mode="auto"):
    result, normalized = [], key(query)
    for group in ("mei", "sei"):
        kind = "given" if group == "mei" else "surname"
        if category and category not in (kind, "name"):
            continue
        for reading, forms in jinmei_map(group).items():
            reading_match = mode in ("auto", "reading") and key(reading) == normalized
            for index, text in enumerate(forms):
                if reading_match or (mode in ("auto", "text") and key(text) == normalized):
                    result.append(native_entry(f"{JINMEI}:{group}:{reading}:{index}", JINMEI, text, [reading], kind, {}))
                    if len(result) >= amount:
                        return result
    return result

def personal_db():
    return sqlite3.connect((DATA / "raw" / PERSONAL / "japanese_names.sqlite").as_uri() + "?mode=ro", uri=True)

def search_personal(query, amount, category=None, mode="auto"):
    result = []
    normalized = key(query)
    with personal_db() as c:
        if category != "surname":
            condition, parameters = [], []
            if mode in ("auto", "text"):
                condition.append("k.kanji=?")
                parameters.append(query)
            if mode in ("auto", "reading"):
                condition.extend(["f.reading=?", "f.romaji=?"])
                parameters.extend([normalized, normalized])
            rows = c.execute("SELECT f.id,k.position,k.kanji,f.reading,f.romaji,f.gender,f.popular FROM first_names f JOIN first_name_kanji k ON k.first_name_id=f.id WHERE " + " OR ".join(condition) + " LIMIT ?", parameters + [amount])
            for row in rows:
                result.append(native_entry(f"{PERSONAL}:first:{row[0]}:{row[1]}", PERSONAL, row[2], [row[3]], "given", {"romaji": row[4], "gender": row[5], "popular": row[6]}))
        if category != "given" and len(result) < amount:
            condition, parameters = [], []
            if mode in ("auto", "text"):
                condition.append("kanji=?")
                parameters.append(query)
            if mode in ("auto", "reading"):
                condition.extend(["reading=?", "romaji=?"])
                parameters.extend([normalized, normalized])
            for row in c.execute("SELECT kanji,reading,romaji,count FROM last_names WHERE " + " OR ".join(condition) + " LIMIT ?", parameters + [amount - len(result)]):
                result.append(native_entry(f"{PERSONAL}:last:{row[0]}", PERSONAL, row[0], [row[1]], "surname", {"romaji": row[2], "population_estimate": row[3]}))
    return result

def get_native(identifier):
    if identifier.startswith(JINMEI + ":"):
        _, group, reading, position = identifier.split(":", 3)
        return native_entry(identifier, JINMEI, jinmei_map(group)[reading][int(position)], [reading], "given" if group == "mei" else "surname", {})
    if identifier.startswith(PERSONAL + ":"):
        parts = identifier.split(":")
        with personal_db() as c:
            if parts[1] == "first":
                row = c.execute("SELECT k.kanji,f.reading,f.romaji,f.gender,f.popular FROM first_names f JOIN first_name_kanji k ON k.first_name_id=f.id WHERE f.id=? AND k.position=?", (int(parts[2]), int(parts[3]))).fetchone()
                return native_entry(identifier, PERSONAL, row[0], [row[1]], "given", {"romaji": row[2], "gender": row[3], "popular": row[4]}) if row else None
            row = c.execute("SELECT kanji,reading,romaji,count FROM last_names WHERE kanji=?", (parts[2],)).fetchone()
            return native_entry(identifier, PERSONAL, row[0], [row[1]], "surname", {"romaji": row[2], "population_estimate": row[3]}) if row else None
    return None

def verba(query, mode="lat", limit=20):
    executable = VENDOR / "verba" / "verba.py"
    if not executable.exists():
        return {"status": "unavailable", "source": "verba", "description": "Download the verba source first: stephanus fetch --group sources"}
    command = [sys.executable, str(executable), mode, query, "-n", str(limit)]
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "NO_COLOR": "1"}
    process = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", env=environment)
    return {"id": "verba:" + mode + ":" + query, "source": "verba", "kind": "analysis" if mode == "parse" else "word",
            "text": query, "language": "la", "readings": [], "description": process.stdout.strip(),
            "extra": {"mode": mode}, "status": "available" if process.returncode == 0 else "error", **({"error": process.stderr.strip()} if process.returncode else {})}

def transliterate(text, scheme="hepburn"):
    # The upstream package's setup.py imports removed `imp`; its actual module works on Python 3.12.
    library = VENDOR / "python-romkan" / "src"
    if not library.exists():
        return {"status": "unavailable", "source": "python-romkan", "description": "Download python-romkan source first."}
    sys.path.insert(0, str(library)) if str(library) not in sys.path else None
    import romkan
    converters = {"hepburn": romkan.to_hepburn, "kunrei": romkan.to_kunrei, "hiragana": romkan.to_hiragana, "katakana": romkan.to_katakana}
    if scheme not in converters:
        raise ValueError("scheme must be hepburn, kunrei, hiragana, or katakana")
    converted = converters[scheme](text)
    return {"source": "python-romkan", "kind": "transliteration", "text": converted, "language": "ja",
            "description": scheme, "extra": {"input": text, "scheme": scheme}}
