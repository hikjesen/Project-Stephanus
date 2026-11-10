"""Acquire reference sources and datasets without checksums or retry loops."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.error
import urllib.request
import zipfile

from .paths import ROOT, DATA, VENDOR, MANIFEST

REPOS = [
    ("jmdict-simplified", "scriptin/jmdict-simplified", "Dictionary JSON conversion", ["ja"]),
    ("jinmei-dict", "s1r-J/jinmei-dict", "Homophonic Japanese names", ["ja"]),
    ("japanese-personal-name-dataset", "shuheilocale/japanese-personal-name-dataset", "Japanese names and native SQLite", ["ja"]),
    ("japanesenames", "flapBird/japanesenames", "Name dataset and application reference", ["ja"]),
    ("nihongo-mono", "stndaru/nihongo-mono", "Offline dictionary implementation reference", ["ja"]),
    ("yomikun-app", "richardjharris/yomikun-app", "Japanese name lookup application reference", ["ja"]),
    ("python-romkan", "soimort/python-romkan", "Kana and romaji conversion", ["ja"]),
    ("kuroshiro", "hexenq/kuroshiro", "Japanese script conversion", ["ja"]),
    ("wanakana", "WaniKani/WanaKana", "Kana and romaji utilities", ["ja"]),
    ("kuroshiro-analyzer-kuromoji", "hexenq/kuroshiro-analyzer-kuromoji", "Kuroshiro analyzer", ["ja"]),
    ("verba", "daniel-persigehl/verba", "Latin dictionaries and morphology", ["la", "en"]),
    ("smith-hall", "nikita-moor/latin-dictionary", "Smith and Hall digital dictionary", ["la", "en"]),
    ("perseus-lexica", "PerseusDL/lexica", "Lewis and Short TEI source", ["la", "grc"]),
    ("whitakers-words", "mk270/whitakers-words", "Whitaker morphology source", ["la"]),
    ("collatinus", "CIRCSE/collatinus", "Latin morphology application reference", ["la"]),
    ("latin-proper-names", "cltk/latin_proper_names_cltk", "Classical proper-name word list", ["la"]),
    ("onomaverse", "onomaverse/datasets", "Multilingual names and relations", ["mul"]),
    ("medieval-names", "ked66/Medieval-European-Name-Reference-Tool-", "DMNES-derived name tables", ["mul"]),
    ("wiktextract", "tatuylonen/wiktextract", "Multilingual extraction reference", ["mul"]),
    ("mcp-python-sdk", "modelcontextprotocol/python-sdk", "MCP implementation reference", []),
]

DOCUMENTS = [
    ("ninjal-romanization", "https://kotoba.ninjal.ac.jp/qa/yokuaru/qa-183/", "Historical romanization overview"),
    ("found-in-transliteration", "https://nichibun.repo.nii.ac.jp/record/2000509/files/jare_040_213.pdf", "Missionary Japanese name transliterations"),
    ("latinization-personal-names", "https://www.iapt-taxon.org/historic/Congress/IBC_1975/Prop030-032.pdf", "Nicolson 1974 latinization reference"),
    ("nippo-jisho", "https://ndlsearch.ndl.go.jp/search?keyword=%E6%97%A5%E8%91%A1%E8%BE%9E%E6%9B%B8", "Nippo Jisho public catalogue entry"),
    ("ontolex", "https://www.w3.org/2016/05/ontolex/", "OntoLex community report"),
    ("tei-dictionaries", "https://tei-c.org/release/doc/tei-p5-doc/en/html/DI.html", "TEI dictionary structure reference"),
    ("dmnes", "https://dmnes.org/", "Medieval names reference"),
    ("dmnes-guide", "https://dmnes.org/guide", "DMNES field guide"),
    ("behind-the-name", "https://www.behindthename.com/api/", "Optional API and download information"),
    ("behind-the-name-download", "https://www.behindthename.com/api/download.php", "Manual CAPTCHA-protected download entry"),
    ("morgan-owens", "https://neolatinlexicon.org/", "Optional Neo-Latin online lookup"),
    ("kaikki-downloads", "https://kaikki.org/dictionary/rawdata.html", "Wiktextract download catalogue"),
]

EDRDG = [
    ("jmnedict-xml", "http://ftp.edrdg.org/pub/Nihongo/JMnedict.xml.gz"),
    ("jmdict-xml", "http://ftp.edrdg.org/pub/Nihongo/JMdict.gz"),
    ("kanjidic2-xml", "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz"),
]

def read_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []

def save_manifest(records):
    MANIFEST.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Project-Stephanus/0.1"}), timeout=90)

def download(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    aria2 = VENDOR / "aria2" / "aria2-1.37.0-win-64bit-build1" / "aria2c.exe"
    if "raw-wiktextract-data.jsonl.gz" in url and aria2.exists():
        subprocess.run([str(aria2), "--continue=true", "--split=8", "--max-connection-per-server=8",
                        "--min-split-size=16M", "--max-tries=1", "--check-integrity=false", "--file-allocation=none",
                        "--auto-file-renaming=false", "--enable-color=false", "--console-log-level=warn",
                        "--dir=" + str(destination.parent), "--out=" + destination.name, url], check=True)
        return destination
    with request(url) as response, destination.open("wb") as target:
        shutil.copyfileobj(response, target, length=1024 * 1024)
    return destination

def record(identifier, group, url, local, purpose, languages=None, method="download"):
    return {"id": identifier, "group": group, "url": url, "local_path": str(local.relative_to(ROOT)),
            "purpose": purpose, "languages": languages or [], "method": method, "status": "pending"}

def acquire(item):
    item = dict(item)
    destination = ROOT / item["local_path"]
    try:
        if item["method"] == "git":
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and item.get("restore_subset"):
                commands = [["git", "init", str(destination)], ["git", "-C", str(destination), "remote", "add", "origin", item["url"]], ["git", "-C", str(destination), "fetch", "--depth", "1", "origin", item.get("revision") or "HEAD"], ["git", "-C", str(destination), "checkout", "--force", "--detach", "FETCH_HEAD"]]
            else:
                commands = [["git", "-c", "core.longpaths=true", "clone", "--depth", "1", "--single-branch", item["url"], str(destination)]]
            for command in commands:
                p = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
                if p.returncode:
                    raise RuntimeError(p.stderr[-1200:])
        else:
            download(item["url"], destination)
            if item.get("extract") or destination.name.endswith(".json.tgz"):
                if destination.suffix == ".zip":
                    with zipfile.ZipFile(destination) as archive:
                        archive.extractall(destination.parent)
                else:
                    with tarfile.open(destination, "r:gz") as archive:
                        archive.extractall(destination.parent, filter="data")
        item["status"] = "acquired"
    except Exception as exc:
        item["status"] = "unavailable"
        item["error"] = str(exc)
    item["acquired_at"] = datetime.now(timezone.utc).isoformat()
    return item

def source_items():
    return [record("repo-" + slug, "sources", "https://github.com/" + repo + ".git", VENDOR / slug, purpose, langs, "git") for slug, repo, purpose, langs in REPOS]

def document_items():
    return [record(slug, "references", url, DATA / "references" / (slug + (".pdf" if ".pdf" in url else ".html")), purpose) for slug, url, purpose in DOCUMENTS]

def release_assets(repo):
    try:
        with request("https://api.github.com/repos/" + repo + "/releases/latest") as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if repo != "onomaverse/datasets" or exc.code != 403:
            raise
        # Published snapshot also works when the anonymous GitHub API is rate-limited.
        names = ["given-name-frequency.csv", "surname-frequency.csv", "name-gender-inference.csv", "name-transliterations.csv", "name-equivalence.csv", "name-days.csv", "popular-names-by-country-2026.csv"]
        return {"tag_name": "v2026.10", "assets": [{"name": name, "browser_download_url": "https://github.com/onomaverse/datasets/releases/download/v2026.10/" + name} for name in names]}

def data_items():
    items = [record(slug, "data", url, DATA / "raw" / "edrdg" / url.rsplit("/", 1)[-1], "Original EDRDG XML", ["ja"]) for slug, url in EDRDG]
    releases = [
        ("scriptin/jmdict-simplified", lambda n: n.endswith(".json.zip") and n.startswith(("jmnedict-all-", "jmdict-all-", "kanjidic2-all-")), "jmdict-simplified"),
        ("shuheilocale/japanese-personal-name-dataset", lambda n: n.endswith(".sqlite"), "japanese-personal-name-dataset"),
        ("onomaverse/datasets", lambda n: n.endswith(".csv"), "onomaverse"),
    ]
    for repo, select, directory in releases:
        try:
            release = release_assets(repo)
            for asset in release["assets"]:
                name = asset["name"]
                if not select(name):
                    continue
                item = record(directory + "/" + name, "data", asset["browser_download_url"], DATA / "raw" / directory / name, "Released dataset", ["ja"] if directory != "onomaverse" else ["mul"])
                item["version"] = release["tag_name"]
                item["extract"] = name.endswith(".zip")
                items.append(item)
        except Exception as exc:
            failed = record(directory + "-release", "data", "https://github.com/" + repo + "/releases", DATA / "raw" / directory, "Release discovery")
            failed.update(status="unavailable", error=str(exc))
            items.append(failed)
    # Official compressed extraction; import selects ja/la while streaming.
    items.append(record("kaikki-extract", "data", "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz", DATA / "raw" / "kaikki" / "raw-wiktextract-data.jsonl.gz", "Compressed Wiktextract source; import Japanese and Latin only", ["ja", "la"]))
    return items

def fetch(group="all", only=None, workers=4, include_pruned=False):
    previous = {r["id"]: r for r in read_manifest()}
    items = []
    if group in ("all", "sources"):
        items.extend(source_items())
    if group in ("all", "references"):
        items.extend(document_items())
    if group in ("all", "data"):
        recorded = [dict(row) for row in previous.values() if row["group"] == "data"]
        items.extend(recorded or data_items())
    if only and only in previous and not any(item["id"] == only for item in items):
        items.append(dict(previous[only]))
    queue = []
    queued_paths = set()
    for item in items:
        if only and item["id"] != only:
            continue
        old = previous.get(item["id"])
        if old and old.get("storage_state") == "pruned" and not only and not include_pruned:
            continue
        if old and old["status"] == "unavailable" and not only:
            alternative = previous.get(old.get("resolved_by"))
            if not alternative:
                continue
            item, old = dict(alternative), alternative
        if old and old.get("storage_state") == "pruned" and not only and not include_pruned:
            continue
        restoring_subset = old and old.get("storage_state") == "runtime_subset" and (only or include_pruned)
        if old and old["status"] == "acquired" and (ROOT / old["local_path"]).exists() and not restoring_subset:
            continue
        if restoring_subset:
            item.update(restore_subset=True, revision=old.get("revision"))
        if item["local_path"] in queued_paths:
            continue
        item["status"] = "pending" if item["status"] != "unavailable" or only or old else "unavailable"
        item.pop("storage_state", None)
        previous[item["id"]] = item
        if item["status"] == "pending":
            queue.append(item)
            queued_paths.add(item["local_path"])
    save_manifest(list(previous.values()))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(acquire, item) for item in queue]
        for future in as_completed(futures):
            item = future.result()
            previous[item["id"]] = item
            save_manifest(list(previous.values()))
            print(item["status"], item["id"], item.get("error", "")[:220], flush=True)
    return list(previous.values())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=["all", "sources", "data", "references"], default="all")
    parser.add_argument("--only")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--include-pruned", action="store_true")
    args = parser.parse_args()
    fetch(args.group, args.only, args.workers, args.include_pruned)
