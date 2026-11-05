---
name: unit-test-design
description: "Use when designing unit test cases for a story (ST-nn) or its LLD before test code exists: derive positive, negative, boundary and edge cases with mocked dependencies, write docs/design/tests/ST-nn-unit-tests.csv, and validate it. Triggers: unit test design, test cases csv, test matrix, ST-nn unit tests, validate test csv."
argument-hint: "Story ID or LLD path, e.g. ST-02 or docs/design/lld/ST-02.md"
---

# Unit Test Design

Turn one LLD (or story) into a unit-scoped test case CSV. Design only: no pytest or production code.

## Input

Story ID or LLD path; an ID resolves to `docs/design/lld/<ID>.md`.
- No LLD: use the story section in `docs/stories.md` (heading `### <ID> `), say so, and list missing signatures as open questions.
- Malformed ID: stop and list nearby valid IDs from the section 3 table of `docs/stories.md`.

## Procedure

1. Read the LLD, the unit's source file if it exists, only the SRS and story acceptance lines the LLD cites (search by ID), and existing tests in `tests/`. On conflict: SRS, then architecture, then stories; report conflicts.
2. List each public function, method, class and endpoint; note its inputs, outputs, branches, error paths and dependencies.
3. Derive cases per [case rules](./references/case-rules.md).
4. Mock every dependency (other modules, file/network I/O, PyMuPDF, openpyxl, FastAPI clients, clock, randomness, logging sinks) and state its behaviour in the row. Plain `models.py` enums and dataclasses are data: use real instances. Where a unit logs, add a case asserting no document content is logged (NFR-07).
5. Map every LLD step, error rule, test-plan row and acceptance line to at least one case; add cases until none is uncovered. One behaviour and one observable result per row; no duplicates.
6. Write `docs/design/tests/<ID>-unit-tests.csv` per [CSV format](./references/csv-format.md). Ask before replacing an existing file.
7. Run `python3 .github/skills/unit-test-design/scripts/validate_csv.py <csv>`; fix errors until it exits 0.

## Rules

- Do not test another module or story; list it as out of scope.
- Do not invent behaviour, limits, names or messages. Ambiguity is an open question, not a guessed expected result.
- Synthetic data only; no real engineering files or `.env*` files.
- Results are `Pass`, `Fail` or `Unable to Verify`; missing or unextractable data is never `Pass`.

## Reply

CSV path, total count and count per `case_type`; coverage per LLD section or acceptance line (row IDs or gap); out-of-scope items; numbered open questions with sources, or "None".
