#!/usr/bin/env python3
"""Validate a unit test design CSV. Usage: validate_csv.py <csv>. Exit 0 valid, 1 errors, 2 usage."""

import csv
import re
import sys
from pathlib import Path

COLUMNS = [
    "test_id",
    "story_id",
    "unit_under_test",
    "case_type",
    "scenario",
    "preconditions",
    "mocked_dependencies",
    "input",
    "expected_result",
    "expected_status",
    "source_ref",
    "suggested_test_name",
]
CASE_TYPES = {"positive", "negative", "boundary", "edge"}
STATUSES = {"Pass", "Fail", "Unable to Verify", "n/a"}
ID_RE = re.compile(r"^(ST-\d{2,})-UT-\d{3,}$")
NAME_RE = re.compile(r"^test_[a-z0-9]+(_[a-z0-9]+)*$")


def validate(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
        rows = list(csv.reader(text.splitlines(keepends=True), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        return [f"unreadable CSV: {exc}"]
    if not rows:
        return ["file is empty"]

    errors = [] if rows[0] == COLUMNS else [f"header must be: {','.join(COLUMNS)}"]
    if len(rows) == 1:
        errors.append("no data rows")

    names: set[str] = set()
    for n, row in enumerate(rows[1:], start=1):
        where = f"row {n}"
        if len(row) != len(COLUMNS):
            errors.append(f"{where}: {len(row)} fields, expected {len(COLUMNS)}")
            continue
        rec = dict(zip(COLUMNS, row))
        for col, val in rec.items():
            if not val.strip():
                errors.append(f"{where}: empty '{col}'")
            elif "\n" in val or "\r" in val:
                errors.append(f"{where}: newline in '{col}'")

        m = ID_RE.match(rec["test_id"])
        if not m or m.group(1) != rec["story_id"]:
            errors.append(f"{where}: test_id/story_id mismatch or bad format")
        elif rec["test_id"] != f"{m.group(1)}-UT-{n:03d}":
            errors.append(f"{where}: test_id '{rec['test_id']}' not sequential")
        if rec["case_type"] not in CASE_TYPES:
            errors.append(f"{where}: bad case_type '{rec['case_type']}'")
        if rec["expected_status"] not in STATUSES:
            errors.append(f"{where}: bad expected_status '{rec['expected_status']}'")
        name = rec["suggested_test_name"]
        if not NAME_RE.match(name):
            errors.append(f"{where}: test name not snake case '{name}'")
        elif name in names:
            errors.append(f"{where}: duplicate test name '{name}'")
        names.add(name)
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not Path(argv[1]).is_file():
        print(__doc__, file=sys.stderr)
        return 2
    errors = validate(Path(argv[1]))
    for err in errors:
        print(f"ERROR {err}")
    print(f"{len(errors)} error(s)" if errors else f"OK {argv[1]}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
