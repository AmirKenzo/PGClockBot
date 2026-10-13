"""Search over the Telegram settings catalogue (labels and subsection titles)."""

from __future__ import annotations

from dataclasses import dataclass

SEARCH_QUERY_MAX_LEN = 60
SEARCH_RESULT_LIMIT = 8

_ARABIC_TO_PERSIAN = str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"})
_STRIPPED_CHARS = "\u200c\u200f\u200e\u0640"


@dataclass(frozen=True, slots=True)
class SettingsSearchEntry:
    """One searchable place: a field (or a whole subsection) and where it lives."""

    label: str
    section_id: str
    section_title: str
    sub_id: str
    sub_title: str
    key: str = ""


def normalize_search_text(text: str) -> str:
    """Fold Arabic letter variants and drop joiners so «کارت‌به‌کارت» matches «کارت به کارت»."""
    folded = (text or "").translate(_ARABIC_TO_PERSIAN).casefold()
    for ch in _STRIPPED_CHARS:
        folded = folded.replace(ch, " " if ch == "\u200c" else "")
    return " ".join(folded.split())


def search_settings(
    entries: list[SettingsSearchEntry],
    query: str,
    *,
    limit: int = SEARCH_RESULT_LIMIT,
) -> list[SettingsSearchEntry]:
    """Entries whose label, key or location contains every word of the query."""
    words = normalize_search_text(query[:SEARCH_QUERY_MAX_LEN]).split()
    if not words:
        return []
    hits: list[tuple[int, int, SettingsSearchEntry]] = []
    for order, entry in enumerate(entries):
        label = normalize_search_text(entry.label)
        where = normalize_search_text(
            f"{entry.section_title} {entry.sub_title} {entry.key}"
        )
        if not all(w in label or w in where for w in words):
            continue
        in_label = all(w in label for w in words)
        hits.append((0 if in_label else 1, order, entry))
    hits.sort(key=lambda item: (item[0], item[1]))
    return [entry for _, _, entry in hits[:limit]]
