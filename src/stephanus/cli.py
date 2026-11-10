"""Management commands and JSON queries."""

import argparse
import json
import sys

def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="stephanus", description="Project Stephanus local name and lexicon tools")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="Acquire source code, datasets and references")
    fetch.add_argument("--group", choices=["all", "sources", "data", "references"], default="all")
    fetch.add_argument("--only")
    fetch.add_argument("--workers", type=int, default=4)
    fetch.add_argument("--include-pruned", action="store_true", help="Explicitly restore sources removed by the storage policy")
    importer = commands.add_parser("import", help="Build common indexes; completed sources are skipped")
    importer.add_argument("--source")
    sources = commands.add_parser("sources")
    sources.add_argument("--include-resources", action="store_true")
    commands.add_parser("targets")
    commands.add_parser("serve", help="Run the local stdio MCP server")
    for name in ["names", "words"]:
        command = commands.add_parser(name)
        command.add_argument("query")
        command.add_argument("--language")
        command.add_argument("--source")
        command.add_argument("--mode", choices=["auto", "text", "reading", "meaning"], default="auto")
        command.add_argument("--limit", type=int, default=20)
        command.add_argument("--offset", type=int, default=0)
        if name == "names":
            command.add_argument("--category")
    related = commands.add_parser("related")
    related.add_argument("identifier")
    related.add_argument("--relation")
    related.add_argument("--limit", type=int, default=20)
    related.add_argument("--offset", type=int, default=0)
    entry = commands.add_parser("entry")
    entry.add_argument("identifier")
    transliteration = commands.add_parser("transliterate")
    transliteration.add_argument("text")
    transliteration.add_argument("--scheme", default="hepburn", choices=["hepburn", "kunrei", "hiragana", "katakana"])
    latin = commands.add_parser("analyze")
    latin.add_argument("text")
    latin.add_argument("--limit", type=int, default=20)
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "fetch":
        from .resources import fetch
        fetch(**args)
        return
    if command == "import":
        from .importers import import_data
        emit(import_data(**args))
        return
    if command == "serve":
        from .server import run
        run()
        return
    if command == "targets":
        from dataclasses import asdict
        from .targets import load_targets
        emit([asdict(t) for t in load_targets().values()])
        return
    from .service import Service
    service = Service()
    function = {"sources": service.list_sources, "names": service.search_names, "words": service.lookup_words,
                "related": service.find_related_names, "entry": service.get_entry,
                "transliterate": service.transliterate_name, "analyze": service.analyze_latin}[command]
    emit(function(**args))

if __name__ == "__main__":
    main()
