"""Generate the Code Reference > Backend and Frontend Markdown pages.

Writes plain Markdown into docs/code_reference/backend/ and
docs/code_reference/frontend/ (both folders are fully regenerated; don't edit
files in them by hand — edit the docstrings / JSDoc in the source instead).

- Backend: reads django/website/ statically with griffe (nothing is
  imported, so no Django setup is needed) and writes one page per module.
- Frontend: runs TypeDoc (`bun run docs:ts`, see typedoc.json) and copies its
  Markdown output from build/typedoc-md/.

Each section also gets an index.md landing page and a SUMMARY.md that
mkdocs-literate-nav turns into its sidebar.

Usage: python scripts/gen_code_reference.py [--skip-typedoc]
(or ./gen-code-reference.sh, which provides the Python dependencies via uv)
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import griffe

REPO = Path(__file__).resolve().parent.parent
BACKEND_SRC = REPO / "django" / "website"
TYPEDOC_OUT = REPO / "build" / "typedoc-md"
BACKEND_DIR = REPO / "docs" / "code_reference" / "backend"
FRONTEND_DIR = REPO / "docs" / "code_reference" / "frontend"

# Modules that aren't part of the reference.
EXCLUDE_PARTS = {"migrations", "__pycache__", "templates", "templatetags"}
EXCLUDE_FILES = {"tests.py", "views/_old.py"}


# ------------------------------------------------------------------- shared

def first_sentence(text: str | None) -> str:
	if not text:
		return ""
	text = " ".join(text.split())
	match = re.match(r"(.+?[.!?])(\s|$)", text)
	return match.group(1) if match else text


def section_title(name: str) -> str:
	return {"modelData": "Model Data", "api": "API", "filterTab": "Filter Tabs"}.get(
		name, name[:1].upper() + name[1:])


def write(path: Path, text: str) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text)


def write_summary(path: Path, root_title: str, entries: list[tuple[tuple[str, ...], str, str]]) -> None:
	"""Write a literate-nav SUMMARY.md, nesting entries by their folder parts."""
	lines = [f"* [{root_title}](index.md)"]
	open_parts: tuple[str, ...] = ()
	for parts, title, link in sorted(entries, key=lambda e: (e[0], e[1])):
		common = 0
		while common < min(len(parts), len(open_parts)) and parts[common] == open_parts[common]:
			common += 1
		for depth in range(common, len(parts)):
			lines.append(f"{'    ' * depth}* {section_title(parts[depth])}")
		lines.append(f"{'    ' * len(parts)}* [{title}]({link})")
		open_parts = parts
	write(path, "\n".join(lines) + "\n")


def front_matter(source: str) -> str:
	# `source` lets mkdocs_hooks/source_links.py point "Edit this page" at the
	# source file, since these pages are generated from it.
	return f"---\nsource: {source}\n---\n\n"


# ------------------------------------------------------------------ backend

def backend_modules():
	for path in sorted(BACKEND_SRC.rglob("*.py")):
		rel = path.relative_to(BACKEND_SRC)
		if EXCLUDE_PARTS & set(rel.parts) or rel.as_posix() in EXCLUDE_FILES:
			continue
		# test modules, and package __init__ files (they only re-export)
		if rel.name.startswith("test_") or rel.name == "__init__.py":
			continue
		yield path, rel


def load_module(path: Path) -> griffe.Module:
	"""Load a module with griffe, from the nearest directory that isn't a
	regular package (management/commands has no __init__.py)."""
	parts = [path.stem]
	parent = path.parent
	while (parent / "__init__.py").is_file():
		parts.insert(0, parent.name)
		parent = parent.parent
	package = griffe.load(parts[0], search_paths=[str(parent)], resolve_aliases=False)
	return package if len(parts) == 1 else package[".".join(parts[1:])]


def doc_text(obj) -> str:
	return obj.docstring.value.strip() if obj.docstring else ""


def cell(text: str) -> str:
	"""A docstring's first paragraph, on one line, safe inside a table cell."""
	para = text.split("\n\n", 1)[0]
	return " ".join(para.split()).replace("|", "\\|")


def describe(member) -> str:
	"""The member's docstring; for an undocumented short constant or class
	attribute (e.g. an enum value), its value instead."""
	text = cell(doc_text(member))
	if text or not member.is_attribute or member.value is None:
		return text
	value = " ".join(str(member.value).split())
	if len(value) > 60 or re.search(r"(models\.\w+|\w*Field)\(", value):
		return ""
	return f"Value: `{value}`".replace("|", "\\|")


def is_public(name: str) -> bool:
	return not name.startswith("_")


def signature(func: griffe.Function) -> str:
	names = []
	for param in func.parameters:
		if param.name in ("self", "cls"):
			continue
		prefix = {"var-positional": "*", "var-keyword": "**"}.get(param.kind.value, "")
		names.append(prefix + param.name)
	return f"{func.name}({', '.join(names)})"


def member_kind(member) -> str:
	if member.is_function:
		labels = member.labels
		if "property" in labels:
			return "property"
		if "classmethod" in labels:
			return "class method"
		if "staticmethod" in labels:
			return "static method"
		return "constructor" if member.name == "__init__" else "method"
	value = str(member.value) if member.value is not None else ""
	if not value or re.search(r"(models\.\w+|\w*Field)\(", value):
		return "field"
	return "class attribute"


def member_name(member) -> str:
	if member.is_function and "property" not in member.labels:
		return signature(member)
	return member.name


def public_members(obj):
	for name, member in obj.members.items():
		if member.is_alias:
			continue
		if not (is_public(name) or name == "__init__"):
			continue
		yield member


def render_class(cls: griffe.Class) -> str:
	out = [f"### `{cls.name}`", ""]
	line = cell(doc_text(cls)) if doc_text(cls) else ""
	bases = [str(b) for b in cls.bases]
	if bases:
		line += (" " if line else "") + "**Extends:** " + ", ".join(f"`{b}`" for b in bases)
	if line:
		out += [line, ""]
	rest = doc_text(cls).split("\n\n")[1:]
	for para in rest:
		out += [" ".join(para.split()), ""]
	rows = []
	for member in public_members(cls):
		if member.is_class:
			continue  # inner classes (e.g. Django's Meta)
		rows.append(f"| `{member_name(member)}` | {member_kind(member)} | {describe(member)} |")
	if rows:
		out += ["| Member | Kind | Description |", "|---|---|---|", *rows, ""]
	return "\n".join(out)


def render_module(module: griffe.Module, rel: Path) -> str:
	source = f"django/website/{rel.as_posix()}"
	constants, classes, functions = [], [], []
	for member in public_members(module):
		if member.is_class:
			classes.append(member)
		elif member.is_function:
			functions.append(member)
		elif member.is_attribute:
			constants.append(member)

	sections = []
	if constants:
		rows = [f"| `{m.name}` | {describe(m)} |" for m in constants]
		sections.append(("Constants", "| Name | Description |\n|---|---|\n" + "\n".join(rows) + "\n"))
	if classes:
		sections.append(("Classes", "\n".join(render_class(c) for c in classes)))
	if functions:
		rows = [f"| `{signature(f)}` | {cell(doc_text(f))} |" for f in functions]
		sections.append(("Functions", "| Function | Description |\n|---|---|\n" + "\n".join(rows) + "\n"))

	out = [front_matter(source) + "[← Back to Backend](index.md)", "", f"# {rel.as_posix()}", ""]
	if doc_text(module):
		out += [doc_text(module), ""]
	out += [f"**Source:** [{source}](../../../{source})", ""]
	if sections:
		out += ["## Contents", ""]
		out += [f"- [{title}](#{title.lower()})" for title, _ in sections]
		out += ["", "---", ""]
		for title, body in sections:
			out += [f"## {title}", "", body.rstrip(), ""]
	return "\n".join(out)


def generate_backend() -> int:
	shutil.rmtree(BACKEND_DIR, ignore_errors=True)
	entries = []
	index_rows: dict[str, list[str]] = {}
	for path, rel in backend_modules():
		module = load_module(path)
		dotted = ".".join(rel.with_suffix("").parts)
		write(BACKEND_DIR / f"{dotted}.md", render_module(module, rel))

		folder = rel.parent.parts
		entries.append((folder, rel.name, f"{dotted}.md"))
		summary = first_sentence(doc_text(module))
		group = section_title(folder[0]) if folder else "Shared"
		index_rows.setdefault(group, []).append(
			f"- [{rel.as_posix()}]({dotted}.md)" + (f" — {summary}" if summary else ""))

	index = [
		"[← Back to Code Reference](../overview.md)", "", "# Backend", "",
		"Reference for the Django app (`django/website/`), generated from the "
		"source docstrings by `scripts/gen_code_reference.py`. To change a "
		"description, edit the docstring in the source file.", ""]
	for group in sorted(index_rows, key=lambda g: (g == "Shared", g)):
		index += [f"## {group}", "", *index_rows[group], ""]
	write(BACKEND_DIR / "index.md", "\n".join(index))
	write_summary(BACKEND_DIR / "SUMMARY.md", "Backend", entries)
	return len(entries)


# ----------------------------------------------------------------- frontend

# TypeDoc writes its module list to modules.md and frontend/index.ts to
# index.md; swap them so the module list is the section's landing page.
RENAMES = {"index.md": "index_ts.md", "modules.md": "index.md"}


def rewrite_links(text: str) -> str:
	def repl(match: re.Match) -> str:
		return f"]({match.group(1)}{RENAMES[match.group(2)]}{match.group(3)}"
	return re.sub(r"\]\(((?:\.\./)*)(index\.md|modules\.md)([#)])", repl, text)


def generate_frontend(run_typedoc: bool) -> int:
	if run_typedoc:
		shutil.rmtree(TYPEDOC_OUT, ignore_errors=True)
		subprocess.run(["bun", "run", "docs:ts"], cwd=REPO, check=True)
	if not (TYPEDOC_OUT / "modules.md").is_file():
		sys.exit(f"No TypeDoc output in {TYPEDOC_OUT}; run `bun run docs:ts` first.")

	shutil.rmtree(FRONTEND_DIR, ignore_errors=True)
	entries = []
	for path in sorted(TYPEDOC_OUT.rglob("*.md")):
		rel = path.relative_to(TYPEDOC_OUT)
		name = RENAMES.get(rel.as_posix(), rel.as_posix())
		text = rewrite_links(path.read_text())
		if name == "index.md":
			text = re.sub(r"^# .*\n", "", text, count=1)
			text = (
				"[← Back to Code Reference](../overview.md)\n\n# Frontend\n\n"
				"Reference for the TypeScript frontend (`frontend/`), generated by "
				"TypeDoc from the source JSDoc comments by "
				"`scripts/gen_code_reference.py`. To change a description, edit "
				"the comment in the source file.\n\n" + text)
		else:
			source = "index.ts" if name == "index_ts.md" else Path(name).with_suffix(".ts").as_posix()
			back = "../" * (len(Path(name).parts) - 1) + "index.md"
			text = front_matter(f"frontend/{source}") + f"[← Back to Frontend]({back})\n\n" + text
			entries.append((Path(name).parent.parts, Path(source).name, name))
		write(FRONTEND_DIR / name, text)
	write_summary(FRONTEND_DIR / "SUMMARY.md", "Frontend", entries)
	return len(entries)


if __name__ == "__main__":
	backend = generate_backend()
	frontend = generate_frontend(run_typedoc="--skip-typedoc" not in sys.argv)
	print(f"Wrote {backend} backend and {frontend} frontend module pages to docs/code_reference/.")
