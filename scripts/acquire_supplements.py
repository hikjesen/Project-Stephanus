"""Published alternative endpoints for resources whose initial endpoint failed."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from stephanus.resources import acquire, record, read_manifest, save_manifest
from stephanus.paths import DATA, ROOT

items = []
for filename in ["given-name-frequency.csv", "surname-frequency.csv", "name-gender-inference.csv", "name-transliterations.csv", "name-equivalence.csv", "name-days.csv", "popular-names-by-country-2026.csv"]:
    r = record("onomaverse/" + filename, "data", "https://github.com/onomaverse/datasets/releases/download/v2026.10/" + filename, DATA / "raw" / "onomaverse" / filename, "Full released name dataset", ["mul"])
    r["version"] = "v2026.10"
    items.append(r)
version = "3.6.2+20261109214828"
filename = "jmdict-all-" + version + ".json.tgz"
items.append(record("jmdict-full-alternative", "data", "https://github.com/scriptin/jmdict-simplified/releases/download/" + version.replace("+", "%2B") + "/" + filename.replace("+", "%2B"), DATA / "raw" / "jmdict-simplified" / filename, "Alternative full JMdict archive", ["ja"]))
for slug, url, filename in [
    ("jmnedict-xml-http", "http://ftp.edrdg.org/pub/Nihongo/JMnedict.xml.gz", "JMnedict.xml.gz"),
    ("jmdict-xml-http", "http://ftp.edrdg.org/pub/Nihongo/JMdict.gz", "JMdict.gz"),
    ("found-in-transliteration-jstage", "https://www.jstage.jst.go.jp/article/japanreview/40/0/40_2025.Gonzalez-Bolado/_pdf", "found-in-transliteration-jstage.pdf"),
    ("tei-alternative", "https://www.tei-c.org/release/doc/tei-p5-doc/en/html/DI.html", "tei-dictionaries-alternative.html"),
]:
    items.append(record(slug, "references" if filename.endswith((".pdf", ".html")) else "data", url, DATA / ("references" if filename.endswith((".pdf", ".html")) else "raw/edrdg") / filename, "Published alternative source"))

report = DATA / "supplementary-resources.json"
results = json.loads(report.read_text(encoding="utf-8")) if report.exists() else []
manifest = {row["id"]: row for row in read_manifest()}
completed = {row["id"] for row in results + list(manifest.values()) if row["status"] == "acquired" and (ROOT / row["local_path"]).exists()}
with ThreadPoolExecutor(max_workers=5) as pool:
    for result in as_completed([pool.submit(acquire, item) for item in items if item["id"] not in completed]):
        row = result.result()
        results.append(row)
        manifest[row["id"]] = row
        save_manifest(list(manifest.values()))
        (DATA / "supplementary-resources.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(row["status"], row["id"], row.get("error", "")[:180], flush=True)
