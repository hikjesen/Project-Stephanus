"""Open output-language registry. Input-name resolution remains Japanese."""

from dataclasses import dataclass
import json

from .paths import ROOT

@dataclass
class TargetAdapter:
    code: str
    name: str
    capabilities: list[str]
    sources: list[str]

    def search_names(self, service, query, **options):
        return service.search_names(query, language=self.code, **options)

    def lookup_words(self, service, query, **options):
        return service.lookup_words(query, language=self.code, **options)

def load_targets():
    return {row["code"]: TargetAdapter(**row) for row in json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))}

def register_target(adapter):
    """Persist a new target without changing core tables or public tool signatures."""
    targets = load_targets()
    targets[adapter.code] = adapter
    from dataclasses import asdict
    (ROOT / "targets.json").write_text(json.dumps([asdict(t) for t in targets.values()], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
