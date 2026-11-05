# Automotive Schematic Change Review MVP

Demo MVP: checks a modified Zuken schematic PDF against an annotated change request and the EBOM (XLSX). Outputs an evidence-based report for mandatory engineer approval. Not a certified verification tool. Spec: [docs/automotive_schematic_change_review_mvp_srs.md](docs/automotive_schematic_change_review_mvp_srs.md).

## Stack

- Python, FastAPI backend; Python frontend; single-host local run (uvicorn).
- PyMuPDF (PDF), openpyxl (EBOM), PDF report output.
- Inputs: native/vector PDFs (original, modified), XLSX EBOM.

## Layout

- `api/` routes, uploads
- `extraction/` PDF annotations/text, EBOM parsing
- `comparison/` original vs modified
- `validation/` requested-change, unintended-change, EBOM, connectivity checks
- `reporting/` findings, report
- `frontend/`
- `tests/`

## Scope

- In: three-file upload, extraction, page-independent comparison, change validation, unintended-change detection, EBOM reconciliation, connectivity checks where supported, report, engineer approve/reject.
- Out: AI interpretation of ambiguous comments, Zuken API/write-back, auto design correction, ERC/simulation/SI/functional safety, release authorization, compliance certification.

## Rules

- Every check is Pass, Fail or Unable to Verify. Missing or unextractable data is never a pass.
- Findings are advisory until an engineer approves or rejects them.
- Visual PDF comparison is not connectivity verification. Netlist is assumed unavailable, so connectivity is Unable to Verify.
- Do not infer ambiguous intent; require engineer clarification.
- Extraction and validation are deterministic.
- Trace every finding to source document, page and change request item.
- Do not invent performance targets, file-size limits, concurrency or retention periods.
- Assumed formats: EBOM fields are reference designator, part number, description, quantity; annotations are text/comment annotations with page reference.

## Tooling

- Before committing: `ruff check`, `ruff format --check`, `pytest`.
- Tests use a small sanitized dataset with known outcomes. Cover: valid inputs, missing/unsupported files, implemented vs missing/incorrect changes, unintended modification, layout change, EBOM match/mismatch, unverifiable connectivity.

## Confidentiality (NFR-07)

- Documents and EBOMs are confidential. Do not log their contents or extracted data.
- Do not commit real engineering files without approval.
