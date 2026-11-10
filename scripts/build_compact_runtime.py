"""Build the independent candidate once; acceptance and deletion are separate steps."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
from stephanus.compact import build

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "data" / "runtime-candidate"

def main():
    if CANDIDATE.exists():
        raise SystemExit("Candidate already exists; do not silently rebuild an existing artifact.")
    CANDIDATE.mkdir(parents=True)
    manifest = json.loads((ROOT / "resources.json").read_text(encoding="utf-8"))
    for item in manifest:
        path = ROOT / item["local_path"]
        if item.get("method") == "git" and (path / ".git").exists():
            result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True)
            if result.returncode == 0:
                item["revision"] = result.stdout.strip()
    (ROOT / "resources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    policy = json.loads((ROOT / "data-policy.json").read_text(encoding="utf-8"))
    for relative in policy["runtime_assets"]:
        source, target = ROOT / relative, CANDIDATE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(source, target)
    for project in (ROOT / "vendor").iterdir():
        if not project.is_dir():
            continue
        for source in project.iterdir():
            if source.is_file() and (source.name.upper().startswith(("LICENSE", "COPYING", "NOTICE", "README", "ATTRIBUTION"))):
                target = CANDIDATE / "data" / "source-notices" / project.name / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    for name in ("resources.json", "targets.json", "data-policy.json"):
        shutil.copy2(ROOT / name, CANDIDATE / name)
    shutil.copytree(ROOT / "data" / "references", CANDIDATE / "data" / "references")
    report = build(ROOT / "data" / "stephanus.sqlite", CANDIDATE / "data" / "stephanus.sqlite", ROOT)
    inventory = {str(p.relative_to(CANDIDATE)).replace("\\", "/"): p.stat().st_size for p in CANDIDATE.rglob("*") if p.is_file()}
    size = sum(inventory.values())
    budget = policy["runtime_budget_bytes"]
    result = {"runtime_bytes": size, "budget_bytes": budget, "within_budget": size <= budget, "files": inventory}
    (CANDIDATE / "runtime-size.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Runtime data: {size / 1024 ** 2:.2f} MiB / {budget / 1024 ** 2:.0f} MiB", flush=True)
    if size > budget:
        raise SystemExit("Budget exceeded. Do not accept, switch, or clean old data.")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
