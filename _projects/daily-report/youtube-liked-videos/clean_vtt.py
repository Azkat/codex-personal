#!/usr/bin/env python3
import re
import sys
from pathlib import Path


TAG_RE = re.compile(r"<[^>]+>")
TS_RE = re.compile(r"^(\d\d):(\d\d):(\d\d)\.")


def clean_line(line: str) -> str:
    line = TAG_RE.sub("", line)
    line = line.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return line.strip()


def main() -> None:
    for path_s in sys.argv[1:]:
        path = Path(path_s)
        seen = set()
        entries = []
        current_ts = ""
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if "-->" in line:
                current_ts = line.split("-->", 1)[0].strip()
                continue
            if not line or line == "WEBVTT" or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            if line.isdigit():
                continue
            text = clean_line(line)
            if not text or text in seen:
                continue
            seen.add(text)
            entries.append((current_ts, text))

        print(f"# {path.name}")
        for ts, text in entries:
            print(f"{ts}\t{text}")
        print()


if __name__ == "__main__":
    main()
