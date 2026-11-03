"""Rewrite docs links to repo source files into GitHub URLs.

Docs can link to source files with normal relative paths (e.g.
`../django/website/models/base.py`), which resolve in GitHub's repo
browser. MkDocs only knows about files inside docs/, so on the built site
those links would 404 and fail `mkdocs build --strict`. This hook runs
before MkDocs validates links and rewrites any relative link that resolves
outside docs/ (but still inside the repo) to `<repo_url>/blob/main/<path>`,
keeping any #anchor (so `#L42` line links work).

A link whose target doesn't exist in the repo is left alone and logged as
a warning, so typos still fail the strict build.
"""
import logging
import posixpath
import re
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.source_links")

LINK_RE = re.compile(r"\]\((?!https?://|mailto:|#|/)([^)#\s]+)(#[^)\s]*)?\)")
BRANCH = "main"


def on_page_markdown(markdown, page, config, **kwargs):
    repo_root = Path(config.config_file_path).parent.resolve()
    docs_dir = Path(config.docs_dir).resolve()
    docs_rel = docs_dir.relative_to(repo_root).as_posix()
    page_dir = posixpath.dirname(f"{docs_rel}/{page.file.src_uri}")
    blob_base = config.repo_url.rstrip("/") + f"/blob/{BRANCH}/"

    def repl(m: re.Match) -> str:
        target, anchor = m.group(1), m.group(2) or ""
        rel = posixpath.normpath(posixpath.join(page_dir, target))
        if rel == docs_rel or rel.startswith(docs_rel + "/") or rel.startswith(".."):
            # Inside docs/ (MkDocs handles it) or outside the repo entirely.
            return m.group(0)
        if not (repo_root / rel).exists():
            log.warning(
                f"Doc file '{page.file.src_uri}' links to '{target}', "
                f"but '{rel}' does not exist in the repository."
            )
            return m.group(0)
        return f"]({blob_base}{rel}{anchor})"

    # Generated reference pages name their source file in front matter;
    # point "Edit this page" there instead of at the generated Markdown.
    source = page.meta.get("source")
    if source:
        page.edit_url = config.repo_url.rstrip("/") + f"/edit/{BRANCH}/{source}"

    return LINK_RE.sub(repl, markdown)
