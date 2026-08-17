#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

def score_text(text: str, input_text: str | None = None) -> dict:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    list_lines = sum(1 for ln in lines if re.match(r"^\s*(?:[-*]|\d+[\.)])\s+", ln))
    # rough prose without code fences
    prose = re.sub(r"```.*?```", " ", text, flags=re.S)
    semis = prose.count(";")
    sentences = [s.strip() for s in SENT_SPLIT.split(prose) if s.strip() and not s.strip().startswith("#")]
    words = re.findall(r"\w+", prose, flags=re.U)
    sw = [len(re.findall(r"\w+", s, flags=re.U)) for s in sentences] or [0]
    out = {
        "chars": len(text),
        "words": len(words),
        "semicolon_count": semis,
        "sentence_n": len(sentences),
        "avg_sentence_words": round(sum(sw)/len(sw), 2),
        "max_sentence_words": max(sw),
        "list_line_ratio": round(list_lines / max(len(lines),1), 3),
        "lines": len(lines),
    }
    if input_text is not None:
        out["delta_chars_vs_input"] = len(text) - len(input_text)
        out["delta_words_vs_input"] = len(words) - len(re.findall(r"\w+", input_text, flags=re.U))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--input", type=Path)
    args = ap.parse_args()
    text = args.path.read_text(encoding="utf-8")
    inp = args.input.read_text(encoding="utf-8") if args.input else None
    print(json.dumps(score_text(text, inp), ensure_ascii=False))

if __name__ == "__main__":
    main()
