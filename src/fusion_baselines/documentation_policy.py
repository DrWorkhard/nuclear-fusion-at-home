"""Small editorial checks; no judgement of scientific truth or prose language."""

import re
from pathlib import Path

WORD_LIMITS = {
    "README.md": 1500,
    "README_agents.md": 1500,
    "AGENTS.md": 700,
    "docs/README.md": 600,
    "docs/STATUS.md": 600,
    "docs/PROJECT_PLAN.md": 600,
    "docs/steps/STEP_4_PLASMA_AND_COILS.md": 900,
}
STATUS_ROW_LIMIT = 8
ROADMAP_HOMES = ("README_agents.md", "docs/PROJECT_PLAN.md")
ROADMAP_NAMES = (
    "1. Establish a reliable foundation",
    "2. Make design iteration reproducible",
    "3. Improve our own plasma target",
    "4. Develop plasma and coils together",
    "5. Demonstrate a meaningful design advantage",
    "MS0. Publish a useful open coil benchmark",
    "MS1. Contact Proxima Fusion with strong evidence",
    "MSX. Our end goal",
)


def table_rows(text):
    """Return data rows of pipe tables, excluding headers, rules and code blocks."""
    text = re.sub(r"```.*?```|~~~.*?~~~", "", text, flags=re.DOTALL)
    previous = None
    in_table = False
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            previous, in_table = None, False
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            in_table = previous is not None
        elif in_table:
            yield [cell.replace("**", "") for cell in cells]
        previous = cells


def overview_sizes(root):
    """Words are whitespace-delimited Markdown tokens, including code/URLs."""
    return {name: len((root / name).read_text(encoding="utf-8").split())
            for name in WORD_LIMITS if (root / name).is_file()}


def check_overview_policy(root: Path) -> list[str]:
    root = root.resolve()
    errors = []
    for name, size in overview_sizes(root).items():
        if size > WORD_LIMITS[name]:
            errors.append(f"overview word budget: {name}: {size} > {WORD_LIMITS[name]}")
    roadmap = {}
    for name in ("README.md", *ROADMAP_HOMES, "docs/STATUS.md", "docs/README.md"):
        path = root / name
        if not path.is_file():
            errors.append(f"missing overview: {name}")
            continue
        rows = list(table_rows(path.read_text(encoding="utf-8")))
        milestones = [row for row in rows if re.match(r"(?:[1-5]|MS\w*)\. ", row[0])]
        if name in ROADMAP_HOMES:
            if tuple(row[0] for row in milestones) != ROADMAP_NAMES:
                errors.append(f"incomplete or changed roadmap names/order: {name}")
            if any(len(row) < 3 for row in milestones):
                errors.append(f"missing roadmap status column: {name}")
            roadmap[name] = [(row[0], row[2] if len(row) >= 3 else None) for row in milestones]
        elif milestones:
            errors.append(f"duplicated roadmap table outside its two homes: {name}")
        if name == "docs/STATUS.md" and len(rows) > STATUS_ROW_LIMIT:
            errors.append(f"scientific status row budget: {len(rows)} > {STATUS_ROW_LIMIT}")
    if len(roadmap) == 2 and roadmap[ROADMAP_HOMES[0]] != roadmap[ROADMAP_HOMES[1]]:
        errors.append("README_agents and project plan roadmap statuses differ")
    return errors
