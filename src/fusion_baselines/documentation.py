"""Check the project's deliberately shallow, fully indexed documentation tree."""

import ast
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT_DOCUMENTS = {"README.md", "STATUS.md", "PROJECT_PLAN.md"}


def local_links(path: Path) -> set[Path]:
    """Resolve inline local Markdown file links; fragments are not validated."""
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    targets = re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text)
    links = set()
    for target in targets:
        target = target.strip().strip("<>")
        parts = urlsplit(target)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        links.add((path.parent / unquote(parts.path)).resolve())
    return links


def check_documentation(root: Path) -> list[str]:
    """Return structural/navigation errors, never a scientific validity claim."""
    root = root.resolve()
    docs = root / "docs"
    if not docs.is_dir():
        return ["missing docs directory"]
    errors = []
    root_files = {p.name for p in docs.iterdir() if p.is_file()}
    if root_files != ROOT_DOCUMENTS:
        errors.append(f"root documents must be {sorted(ROOT_DOCUMENTS)}; got {sorted(root_files)}")
    for path in docs.rglob("*"):
        if path.is_symlink():
            errors.append(f"documentation symlink is not allowed: {path.relative_to(root)}")
        depth = len(path.relative_to(docs).parts)
        if (path.is_dir() and depth > 1) or (path.is_file() and depth > 2):
            errors.append(f"documentation hierarchy too deep: {path.relative_to(root)}")
    root_index = docs / "README.md"
    root_links = local_links(root_index) if root_index.is_file() else set()
    for folder in sorted(p for p in docs.iterdir() if p.is_dir()):
        index = folder / "README.md"
        if not index.is_file():
            errors.append(f"missing overview: {index.relative_to(root)}")
            continue
        if index.resolve() not in root_links:
            errors.append(f"folder not in root overview: {folder.name}")
        indexed = local_links(index)
        for path in folder.glob("*.md"):
            if path != index and path.resolve() not in indexed:
                errors.append(f"unindexed document: {path.relative_to(root)}")
    markdown = sorted(docs.rglob("*.md"))
    markdown += sorted(root.glob("*.md"))
    for folder in (root / "examples", root / "submissions", root / ".github"):
        markdown += sorted(folder.rglob("*.md"))
    for path in markdown:
        for target in sorted(local_links(path)):
            if not target.exists():
                errors.append(f"broken local link in {path.relative_to(root)}: {target}")
    for folder in (root / "scripts", root / "src"):
        for path in sorted(folder.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    value = node.value
                    if value.startswith("docs/") and value.endswith(".md"):
                        if not (root / value).is_file():
                            errors.append(
                                f"stale script document path: {path.relative_to(root)}: {value}"
                            )
    return errors
