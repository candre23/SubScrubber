#!/usr/bin/env python3
"""
subscrub.py — sanitize SRT subtitles that show weird “Â” characters or invisible spaces
and fix common mojibake like â€™ for apostrophes.

See usage at bottom of file docstring.
"""
import argparse
from pathlib import Path
import re
from typing import Dict, Tuple

# Characters to normalize
MOJIBAKE_REMAP = {
    "â€™": "'",  # right single quote
    "â€˜": "'",  # left single quote
    "â€œ": '"',   # left double quote
    "â€\x9d": '"', # right double quote (appears as â€\x9d)
    "â€“": "-",  # en dash
    "â€”": "-",  # em dash
    "â€¦": "...", # ellipsis
}
SPACE_SUBS = {
    "\u00A0": " ",  # NBSP
    "\u202F": " ",  # NARROW NO-BREAK SPACE
    "\u2007": " ",  # FIGURE SPACE
    "\u2008": " ",  # PUNCTUATION SPACE
    "\u2009": " ",  # THIN SPACE
    "\u200A": " ",  # HAIR SPACE
}
REMOVE_CHARS = [
    "\u200B",  # ZERO WIDTH SPACE
    "\u200C",  # ZWNJ
    "\u200D",  # ZWJ
    "\uFEFF",  # ZERO WIDTH NO-BREAK SPACE / BOM (if appears inside text)
]

def try_decode(data: bytes) -> Tuple[str, str]:
    """Decode with utf-8-sig, fallback to cp1252 then latin-1. Return text and codec used."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8(replace)"

def sanitize(text: str) -> Tuple[str, Dict[str, int]]:
    counts: Dict[str, int] = {}
    # Replace variant spaces with normal space
    for ch, rep in SPACE_SUBS.items():
        n = text.count(ch)
        if n:
            counts[f"replaced {hex(ord(ch))}"] = n
            text = text.replace(ch, rep)
    # Remove zero-width and BOM-in-text
    for ch in REMOVE_CHARS:
        n = text.count(ch)
        if n:
            counts[f"removed {hex(ord(ch))}"] = n
            text = text.replace(ch, "")
    # Fix common mojibake sequences (UTF-8 decoded as cp1252)
    for bad, good in MOJIBAKE_REMAP.items():
        n = text.count(bad)
        if n:
            counts[f"mojibake {bad!r} -> {good!r}"] = n
            text = text.replace(bad, good)

    # Repair truncated right double-quote mojibake: a bare 'â€' with missing trailing byte
    # often appears at end-of-line or right before whitespace/punctuation.
    new_text, nfix = re.subn(r"â€(?=$|\s|[)\]\}\"'».,!?;:])", '"', text)
    if nfix:
        counts["mojibake truncated right dbl quote â€ -> \""] = nfix
        text = new_text

    # Remove stray “Â” only when it directly precedes whitespace
    before = text
    text = re.sub(r"\u00C2(?=\s)", "", text)  # drop Â when followed by whitespace
    n = len(before) - len(text)
    if n:
        counts["removed stray Â (U+00C2) before space"] = n
    # Normalize line endings to \n and strip trailing spaces
    lines = [ln.rstrip() for ln in text.splitlines()]
    text = "\n".join(lines) + ("\n" if text.endswith(("\n", "\r")) else "")
    return text, counts

def process_file(path: Path, in_place: bool, backup: bool, bom: bool, quiet: bool=False) -> bool:
    data = path.read_bytes()
    original_text, used_enc = try_decode(data)
    cleaned_text, counts = sanitize(original_text)
    changed = cleaned_text != original_text
    if not changed:
        if not quiet:
            print(f"✓ {path} (clean) — no changes needed [{used_enc}]")
        return False
    if in_place:
        if backup:
            path.with_suffix(path.suffix + ".bak").write_bytes(data)
        out_path = path
    else:
        out_path = path.with_suffix(".clean.srt")
    encoding = "utf-8-sig" if bom else "utf-8"
    out_path.write_bytes(cleaned_text.encode(encoding))
    if not quiet:
        stats = ", ".join(f"{k}: {v}" for k, v in counts.items()) or "changes made"
        mode = "overwrote" if in_place else "wrote"
        print(f"• {mode} {out_path} [{encoding}] — {stats}")
    return True

def iter_srt_paths(root: Path):
    if root.is_file() and root.suffix.lower() == ".srt":
        yield root
        return
    if root.is_dir():
        for p in root.rglob("*.srt"):
            if p.is_file():
                yield p

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Clean weird spaces (Â, NBSP, zero-width) and mojibake (â€™) from SRT files.")
    ap.add_argument("paths", nargs="+", help="Files or folders to process")
    ap.add_argument("--in-place", action="store_true", help="Overwrite original files (default writes .clean.srt)")
    ap.add_argument("--backup", action="store_true", help="When --in-place, create a .bak backup")
    ap.add_argument("--utf8-bom", action="store_true", help="Write UTF-8 with BOM (helps some older players)")
    ap.add_argument("--quiet", action="store_true", help="Less console output")
    args = ap.parse_args(argv)

    total = changed = 0
    for raw in args.paths:
        for path in iter_srt_paths(Path(raw)):
            total += 1
            if process_file(path, in_place=args.in_place, backup=args.backup, bom=args.utf8_bom, quiet=args.quiet):
                changed += 1
    if not args.quiet:
        print(f"Done. {changed}/{total} file(s) updated.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
