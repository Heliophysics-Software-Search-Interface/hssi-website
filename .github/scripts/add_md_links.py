#!/usr/bin/env python3
"""Re-append .md extensions to internal links pulled in from the wiki.

The inverse of strip_md_links.py: wiki pages link to each other without
a .md extension, but the same link needs the real extension once it lands
back in docs/ to resolve correctly in GitHub's repo browser. A link is
only rewritten if <link-target-resolved-relative-to-this-file>.md actually
exists on disk under the given root; absolute URLs, anchor-only links, and
links that don't resolve to a real file are left untouched rather than
guessed at.
"""
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\]\((?!https?://)([^)#]+)(#[^)]*)?\)")


def add_md(root: Path) -> None:
    root = root.resolve()
    for path in root.rglob("*.md"):
        text = path.read_text()

        def repl(m: re.Match) -> str:
            target, anchor = m.group(1), m.group(2) or ""
            if not target or target.endswith(".md"):
                return m.group(0)
            candidate = (path.parent / f"{target}.md").resolve()
            if candidate != root and root not in candidate.parents:
                return m.group(0)
            if candidate.is_file():
                return f"]({target}.md{anchor})"
            return m.group(0)

        new_text = LINK_RE.sub(repl, text)
        if new_text != text:
            path.write_text(new_text)


if __name__ == "__main__":
    add_md(Path(sys.argv[1]))
