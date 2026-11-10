"""Small common index; original records remain in extra."""

import json
import sqlite3
import unicodedata

from .paths import DATABASE

def key(text):
    text = unicodedata.normalize("NFKC", str(text)).casefold().strip()
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)

def connect(write=False):
    if write:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DATABASE)
    else:
        connection = sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection

def initialize(c):
    c.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS entries (
      id TEXT PRIMARY KEY, source TEXT NOT NULL, kind TEXT NOT NULL,
      language TEXT NOT NULL, text TEXT NOT NULL, text_key TEXT NOT NULL,
      category TEXT NOT NULL, readings TEXT NOT NULL, description TEXT NOT NULL, extra TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS entries_text ON entries(text_key);
    CREATE INDEX IF NOT EXISTS entries_filter ON entries(kind,language,source);
    CREATE TABLE IF NOT EXISTS readings (entry_id TEXT NOT NULL, reading_key TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS readings_key ON readings(reading_key);
    CREATE TABLE IF NOT EXISTS relations (left_id TEXT NOT NULL, right_id TEXT NOT NULL, relation TEXT NOT NULL, source TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS relations_left ON relations(left_id);
    CREATE INDEX IF NOT EXISTS relations_right ON relations(right_id);
    CREATE VIRTUAL TABLE IF NOT EXISTS entry_fts USING fts5(entry_id UNINDEXED,text,description,tokenize='unicode61 remove_diacritics 2');
    CREATE TABLE IF NOT EXISTS imports (source TEXT PRIMARY KEY, entries INTEGER NOT NULL, imported_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS supplements (entry_id TEXT NOT NULL, dataset TEXT NOT NULL, data TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS supplements_entry ON supplements(entry_id);
    """)

def unpack(row):
    item = dict(row)
    item.pop("text_key", None)
    for field in ("readings", "extra"):
        item[field] = json.loads(item[field])
    return item

class Writer:
    def __init__(self, connection, source):
        self.c, self.source, self.count = connection, source, 0

    def add(self, identifier, text, language="und", kind="name", readings=None, description="", category="", extra=None):
        identifier = str(identifier)
        readings = list(dict.fromkeys(readings or []))
        cursor = self.c.execute("INSERT OR IGNORE INTO entries VALUES (?,?,?,?,?,?,?,?,?,?)",
            (identifier, self.source, kind, language or "und", text, key(text), category,
             json.dumps(readings, ensure_ascii=False), description, json.dumps(extra or {}, ensure_ascii=False)))
        if cursor.rowcount:
            self.c.executemany("INSERT INTO readings VALUES (?,?)", [(identifier, key(r)) for r in readings])
            self.c.execute("INSERT INTO entry_fts(entry_id,text,description) VALUES (?,?,?)", (identifier, text, description))
            self.count += 1
            if self.count % 10000 == 0:
                self.c.commit()
        return identifier

    def relation(self, left, right, relation):
        if left != right:
            self.c.execute("INSERT INTO relations VALUES (?,?,?,?)", (left, right, relation, self.source))

    def supplement(self, identifier, dataset, data):
        self.c.execute("INSERT INTO supplements VALUES (?,?,?)", (identifier, dataset, json.dumps(data, ensure_ascii=False)))

def search(query, kinds, language=None, source=None, category=None, mode="auto", amount=21):
    normalized = key(query)
    if not normalized:
        return []
    selections, params = [], []
    if mode in ("auto", "text"):
        selections.append("SELECT id,0 AS priority FROM entries WHERE text_key=?")
        params.append(normalized)
        selections.append("SELECT id,1 AS priority FROM entries WHERE text_key>=? AND text_key<?")
        params.extend([normalized, normalized + "\uffff"])
    if mode in ("auto", "reading"):
        selections.append("SELECT entry_id AS id,0 AS priority FROM readings WHERE reading_key=?")
        params.append(normalized)
    if mode in ("auto", "meaning"):
        terms = [t.replace('"', '""') for t in query.split() if t.strip()]
        selections.append("SELECT entry_id AS id,2 AS priority FROM entry_fts WHERE entry_fts MATCH ?")
        params.append(" AND ".join('"' + t + '"' for t in terms))
    if not selections:
        raise ValueError("mode must be auto, text, reading, or meaning")
    predicates = ["e.kind IN (" + ",".join("?" for _ in kinds) + ")"]
    params.extend(kinds)
    for column, value in [("language", language), ("source", source), ("category", category)]:
        if value:
            predicates.append("instr(','||e.category||',',','||?||',')>0" if column == "category" else "e." + column + "=?")
            params.append(value)
    params.append(amount)
    sql = "WITH matches AS (" + " UNION ALL ".join(selections) + ") SELECT e.* FROM matches m JOIN entries e ON e.id=m.id WHERE " + " AND ".join(predicates) + " GROUP BY e.id ORDER BY MIN(m.priority),e.text_key,e.id LIMIT ?"
    with connect() as c:
        return [unpack(r) for r in c.execute(sql, params)]
