#!/usr/bin/env python3
import os, re, sys
from collections import defaultdict
try:
    import bibtexparser
except ImportError:
    sys.stderr.write("ERROR: bibtexparser not found. Install with: pip install bibtexparser\n")
    sys.exit(1)

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(ROOT, ".."))
FILES_DIR = os.path.join(PROJECT, "files")
OUT_MD = os.path.join(PROJECT, "publications_rendered.md")

BIB_MAP = [
    ("Journal Articles",       os.path.join(FILES_DIR, "journal.bib"),      ["article"]),
    ("Conference Papers",      os.path.join(FILES_DIR, "conference.bib"),   ["inproceedings"]),
    ("Book Chapters & Books",  os.path.join(FILES_DIR, "books.bib"),        ["book","incollection"]),
    ("Theses",                 os.path.join(FILES_DIR, "thesis.bib"),       ["phdthesis","mastersthesis"]),
    ("Other",                  os.path.join(FILES_DIR, "other.bib"),        []),
]

ME_PATTERNS = [
    r"Rostampour,\s*Vahab",
    r"Vahab\s+Rostampour",
    r"Rostampour,\s*V\\?\\.?",
    r"V\\?\\.?\\s*Rostampour",
]

def bold_me(author_str: str) -> str:
    s = author_str or ""
    s = s.replace(" and ", ", ")
    for pat in ME_PATTERNS:
        s = re.sub(pat, lambda m: f"**{m.group(0)}**", s, flags=re.IGNORECASE)
    return s

def norm(s):
    return (s or "").strip()

def format_entry(e: dict) -> str:
    authors = bold_me(e.get("author",""))
    title = norm(e.get("title","")).strip("{} ")
    title_md = f"*{title}*"

    venue = norm(e.get("journal") or e.get("booktitle") or e.get("publisher") or e.get("school"))
    vol = norm(e.get("volume"))
    no = norm(e.get("number") or e.get("issue"))
    pages = norm(e.get("pages"))
    year = norm(e.get("year"))
    doi = norm(e.get("doi"))
    url = norm(e.get("url") or e.get("eprint"))

    parts = [f"{authors}. {title_md}."]

    venue_bits = []
    if venue: venue_bits.append(venue)
    if vol:
        venue_bits.append(f"{vol}" + (f"({no})" if no else ""))
    elif no:
        venue_bits.append(f"({no})")
    if pages: venue_bits.append(pages)

    if venue_bits:
        parts.append(", ".join(venue_bits) + ".")
    if year: parts.append(year + ".")
    if doi:
        parts.append(f"doi:{doi}")
    elif url:
        parts.append(url)

    return " ".join(parts)

def load_entries(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return db.entries

def sort_entries(entries):
    def key(e):
        y = e.get("year")
        try:
            yv = int(re.findall(r"\\d{4}", y or "")[0])
        except Exception:
            yv = -1
        t = (e.get("title") or "").lower()
        return (-yv, t)
    import re
    return sorted(entries, key=key)

def main():
    lines = ["# Publications", ""]

    for section, bibpath, _types in BIB_MAP:
        ents = load_entries(bibpath)
        if not ents:
            continue
        ents = sort_entries(ents)

        # Section header
        lines.append(f"## {section}")
        lines.append("")  # blank line

        # Ordered list with numbers
        for i, e in enumerate(ents, 1):
            item = format_entry(e)
            lines.append(f"{i}. {item}")
        lines.append("")  # blank line between sections

    # Write with proper line breaks
    with open(OUT_MD, "w", encoding="utf-8") as out:
        out.write("\n".join(lines) + "\n")

    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
