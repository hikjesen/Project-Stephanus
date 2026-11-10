"""Seven read-only tools over the same service used by the CLI."""

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from typing import Any

from .service import Service

mcp = MCPServer("stephanus_mcp")
service = Service()
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)

@mcp.tool(annotations=READ_ONLY, structured_output=True)
def stephanus_list_sources() -> dict[str, Any]:
    """List local resources, connected backends, indexed languages and output targets."""
    return service.list_sources()

@mcp.tool(annotations=READ_ONLY, structured_output=True)
def stephanus_search_names(query: str, language: str | None = None, category: str | None = None, source: str | None = None, mode: str = "auto", limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """Search written names, kana readings or meanings. Modes: auto/text/reading/meaning. Language is an open code, e.g. ja/la/de; unknown medieval citation languages are und. Categories include given/surname/proper_name. Paginate with limit and offset."""
    return service.search_names(query, language, category, source, mode, limit, offset)

@mcp.tool(annotations=READ_ONLY, structured_output=True)
def stephanus_lookup_words(query: str, language: str | None = None, source: str | None = None, mode: str = "auto", limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """Search word forms or meanings (auto/text/reading/meaning). For English-to-Latin use language=la,source=verba,mode=meaning. Source may be jmdict/kanjidic2/kaikki/verba."""
    return service.lookup_words(query, language, source, mode, limit, offset)

@mcp.tool(annotations=READ_ONLY, structured_output=True)
def stephanus_find_related_names(identifier: str, relation: str | None = None, limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """Find recorded name variants, similar names and transliterations for an entry ID returned by search."""
    return service.find_related_names(identifier, relation, limit, offset)

@mcp.tool(annotations=READ_ONLY, structured_output=True)
def stephanus_get_entry(identifier: str) -> dict[str, Any]:
    """Retrieve a complete record with original fields and supplementary source data."""
    return service.get_entry(identifier) or {}

@mcp.tool(annotations=READ_ONLY, structured_output=True)
def stephanus_transliterate_name(text: str, scheme: str = "hepburn") -> dict[str, Any]:
    """Convert Japanese kana/romaji using upstream romkan. Schemes: hepburn/kunrei/hiragana/katakana. Resolve kanji readings with search_names first."""
    return service.transliterate_name(text, scheme)

@mcp.tool(annotations=READ_ONLY, structured_output=True)
def stephanus_analyze_latin(text: str, limit: int = 20) -> dict[str, Any]:
    """Use verba/Whitaker to analyze Latin inflected forms and return lemma and morphology."""
    return service.analyze_latin(text, limit)

def run():
    mcp.run(transport="stdio")
