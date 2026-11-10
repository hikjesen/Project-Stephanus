"""Package the installed database and minimal offline backends for a GitHub Release."""
import argparse
import json
from pathlib import Path
import zipfile
from stephanus.paths import ROOT

def package(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    policy = json.loads((ROOT / "data-policy.json").read_text(encoding="utf-8"))
    paths = {ROOT / name for name in ("data/stephanus.sqlite", "resources.json", "targets.json", "data-policy.json")}
    for relative in [*policy["runtime_assets"], "data/source-notices", "data/references"]:
        path = ROOT / relative
        if path.is_dir():
            paths.update(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
        else:
            paths.add(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    instructions = """Project Stephanus compact-v1 runtime data

This archive contains data/stephanus.sqlite, the native Japanese name backend,
jinmei JSON, the minimal verba/Whitaker and romkan files, source notices,
references, resources.json, targets.json and data-policy.json.

Get the matching compact-v1 source code from:
https://github.com/hikjesen/Project-Stephanus/releases/tag/compact-v1

Extract this archive into the source repository root, retaining data/ and vendor/.
Install Python 3.12+ and uv, then run:
  uv sync
  uv run stephanus names '佐藤' --limit 5
  uv run stephanus serve

Alternatively set STEPHANUS_HOME to this archive's extraction directory.
No fetch/import is needed when using this prebuilt data archive.
The Python environment, local paths, credentials and private configuration are excluded.
Data source and license notices are under data/source-notices/ and resources.json.
"""
    raw_bytes = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(paths):
            relative = str(path.relative_to(ROOT)).replace("\\", "/")
            raw_bytes += path.stat().st_size
            archive.write(path, relative)
            if relative == "data/stephanus.sqlite":
                print("Packaged SQLite database", flush=True)
        archive.writestr("RUNTIME_README.txt", instructions)
    result = {"path": str(output), "files": len(paths) + 1, "installed_bytes": raw_bytes,
              "archive_bytes": output.stat().st_size, "database_included": "data/stephanus.sqlite"}
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package(args.output)
