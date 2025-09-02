#!/usr/bin/env python3
"""
make_publications_qmd.py
----------------------------------
Generate a standalone `publications.qmd` from BibTeX files.
- No external dependencies (pure Python stdlib).
- Groups into: Journal Articles, Conference Papers, Book Chapters & Books, Theses, Other.
- Sorts newest -> oldest in each group.
- Titles italicised, your name bold in author list.
- Produces numbered lists per section.
- Writes a complete Quarto page with YAML header.

USAGE
-----
# If your split bibs are in ./files/:
python make_publications_qmd.py --out publications.qmd
"""

import os, re, argparse
from typing import List, Dict

DEFAULT_NAME_PATTERNS = [
    r"Rostampour,\s*Vahab",
    r"Vahab\s+Rostampour",
    r"Rostampour,\s*V\.",
    r"V\.\s*Rostampour",
]

def bold_name(s, pats):
    s = (s or "").replace(" and ", ", ")
    for pat in pats:
        s = re.sub(pat, lambda m: f"**{m.group(0)}**", s, flags=re.IGNORECASE)
    return s

def strip_wrap(v):
    v = (v or "").strip().strip(',').strip()
    if (v.startswith('{') and v.endswith('}')) or (v.startswith('"') and v.endswith('"')):
        v = v[1:-1]
    return v.strip()

def parse_bib_entry(txt):
    fields = {}
    mtype = re.match(r'@(\w+)\s*{', txt)
    fields['ENTRYTYPE'] = (mtype.group(1).lower() if mtype else 'misc')
    body = re.sub(r'^@\w+\s*{\s*[^,]+,\s*', '', txt.strip(), flags=re.DOTALL)
    if body.endswith('}'): body = body[:-1]
    parts = re.split(r',\s*(?=\w+\s*=)', body)
    for p in parts:
        m = re.match(r'(\w+)\s*=\s*(.+)$', p.strip(), flags=re.DOTALL)
        if m:
            k, v = m.group(1).lower(), strip_wrap(m.group(2))
            fields[k] = v
    return fields

def read_bib(path):
    if not path or not os.path.exists(path): return []
    t = open(path, 'r', encoding='utf-8').read()
    entries = re.split(r'(?=@\w+\s*{)', t)
    return [parse_bib_entry(e.strip()) for e in entries if e.strip()]

def sort_entries(es):
    def key(e):
        m = re.search(r'\d{4}', e.get('year',''))
        y = int(m.group(0)) if m else -1
        return (-y, (e.get('title') or '').lower())
    return sorted(es, key=key)

def fmt_entry(e, pats):
    authors = bold_name(e.get('author',''), pats)
    title = strip_wrap(e.get('title','')).strip('{} ')
    title_md = f"*{title}*"
    venue = (e.get('journal') or e.get('booktitle') or e.get('publisher') or e.get('school') or '').strip()
    vol = (e.get('volume') or '').strip()
    no = (e.get('number') or e.get('issue') or '').strip()
    pages = (e.get('pages') or '').strip()
    year = (e.get('year') or '').strip()
    doi = (e.get('doi') or '').strip()
    url = (e.get('url') or e.get('eprint') or '').strip()
    parts = [f"{authors}. {title_md}."]
    venue_bits = []
    if venue: venue_bits.append(venue)
    if vol:
        venue_bits.append(f"{vol}" + (f"({no})" if no else ""))
    elif no:
        venue_bits.append(f"({no})")
    if pages: venue_bits.append(pages)
    if venue_bits: parts.append(", ".join(venue_bits) + ".")
    if year: parts.append(year + ".")
    if doi: parts.append(f"https://doi.org/{doi}")
    elif url: parts.append(url)
    return " ".join(parts)

def build_section(heading, entries, pats):
    lines = [f"## {heading}", ""]
    for i, e in enumerate(sort_entries(entries), 1):
        lines.append(f"{i}. {fmt_entry(e, pats)}")
    lines.append("")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="publications.qmd")
    ap.add_argument("--journal"); ap.add_argument("--conference")
    ap.add_argument("--books"); ap.add_argument("--thesis"); ap.add_argument("--other")
    ap.add_argument("--name", action="append")
    ap.add_argument("--title", default="Publications")
    args = ap.parse_args()

    def or_default(p, d):
        return p if p else (os.path.join("files", d) if os.path.exists("files") else None)

    paths = {
        "Journal Articles": or_default(args.journal, "journal.bib"),
        "Conference Papers": or_default(args.conference, "conference.bib"),
        "Book Chapters & Books": or_default(args.books, "books.bib"),
        "Theses": or_default(args.thesis, "thesis.bib"),
        "Other": or_default(args.other, "other.bib"),
    }

    pats = args.name if args.name else DEFAULT_NAME_PATTERNS

    sections = []
    for heading, p in paths.items():
        entries = read_bib(p) if p else []
        if entries: sections.append((heading, entries))

    qmd = ["---", f'title: "{args.title}"', "---", "", "# Publications", ""]
    for heading, entries in sections:
        qmd.append(build_section(heading, entries, pats))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(qmd) + "\n")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
