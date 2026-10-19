#!/usr/bin/env python3
"""Strip .md extensions from internal links in a directory of Markdown files.

GitHub's wiki (Gollum) treats a relative link ending in .md as a literal
file path and serves the raw file instead of the rendered page, so links
that work in a normal repo view break once mirrored into the wiki. This
rewrites only relative links to local .md files (preserving any #anchor);
absolute URLs and anchor-only links are left untouched.

Used by docs-to-wiki.yml against the wiki checkout only -- it never runs
against docs/ itself, so the repo's own source files (which need the real
.md extension to resolve correctly in GitHub's repo browser) are untouched.
"""
import re
import sys
from pathlib import Path

LINK_RE = re.compile(
    r"(\]\()((?:\.\./|[\w\-]+/)*[\w\-]+)\.md(#[\w\-]*)?(\))"
)


def strip_md(root: Path) -> None:
    for path in root.rglob("*.md"):
        text = path.read_text()
        new_text = LINK_RE.sub(r"\1\2\3\4", text)
        if new_text != text:
            path.write_text(new_text)


if __name__ == "__main__":
    strip_md(Path(sys.argv[1]))
