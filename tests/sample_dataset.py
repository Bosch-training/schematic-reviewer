"""Sanitized sample dataset builders and expected-outcome manifest (ST-04)."""

from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import fitz
import openpyxl


@dataclass(frozen=True)
class ComponentSpec:
    ref_des: str
    value: str
    part_number: str
    description: str
    page: int  # 1-based


@dataclass(frozen=True)
class EbomRow:
    ref_des: str
    part_number: str
    description: str
    quantity: int


@dataclass(frozen=True)
class SampleDataset:
    original_pdf: Path
    modified_pdf: Path
    layout_only_pdf: Path
    ebom_match: Path
    ebom_mismatch: Path
    password_pdf: Path
    non_pdf: Path
    ebom_missing_column: Path


# Dummy test constants for password.pdf.
PDF_USER_PASSWORD: str = "user-pass-test"
PDF_OWNER_PASSWORD: str = "owner-pass-test"

# Statuses are strings equal to models.Status values.
_R101 = ComponentSpec("R101", "10K", "PN-RES-001", "Resistor 0603", 1)
_R102 = ComponentSpec("R102", "1K", "PN-RES-001", "Resistor 0603", 1)
_R103 = ComponentSpec("R103", "100R", "PN-RES-001", "Resistor 0603", 1)
_C201 = ComponentSpec("C201", "100nF", "PN-CAP-001", "Capacitor 0603", 2)
_C301 = ComponentSpec("C301", "100nF", "PN-CAP-002", "Capacitor 0603", 2)
_U101 = ComponentSpec("U101", "OPAMP", "PN-IC-001", "Dual op-amp 8-pin", 2)

ORIGINAL_COMPONENTS: tuple[ComponentSpec, ...] = (_R101, _R102, _R103, _C201, _U101)
MODIFIED_COMPONENTS: tuple[ComponentSpec, ...] = (
    replace(_R101, value="4.7K"),
    _R102,
    replace(_C201, value="220nF"),
    _C301,
    _U101,
)
LAYOUT_ONLY_COMPONENTS: tuple[ComponentSpec, ...] = (
    _R101,
    _R102,
    replace(_R103, page=2),
    _C201,
    replace(_U101, page=3),
)
EBOM_MATCH_ROWS: tuple[EbomRow, ...] = tuple(
    EbomRow(c.ref_des, c.part_number, c.description, 1) for c in MODIFIED_COMPONENTS
)
EBOM_MISMATCH_ROWS: tuple[EbomRow, ...] = tuple(
    replace(
        row,
        part_number="PN-CAP-999" if row.ref_des == "C201" else row.part_number,
        quantity=2 if row.ref_des == "U101" else row.quantity,
    )
    for row in EBOM_MATCH_ROWS
    if row.ref_des != "R102"
)
ANNOTATIONS: tuple[tuple[int, str], ...] = (  # (page 1-based, text)
    (1, "Replace R101 from 10K to 4.7K"),
    (1, "Replace R102 from 1K to 2.2K"),
    (1, "Remove R103"),
    (2, "Add C301 100nF"),
    (2, "Improve filtering on input stage"),
)
EXPECTED_CHANGE_ITEMS: tuple[tuple[str, str], ...] = (  # (item id, status)
    ("CR-001", "Pass"),
    ("CR-002", "Fail"),
    ("CR-003", "Pass"),
    ("CR-004", "Pass"),
    ("CR-005", "Unable to Verify"),
)
# (reference designator, field, original value, modified value)
EXPECTED_UNINTENDED: tuple[tuple[str, str, str, str], ...] = (
    ("C201", "value", "100nF", "220nF"),
)
# (reference designator, status)
EXPECTED_EBOM_ENTRY_MATCH: tuple[tuple[str, str], ...] = (
    ("R101", "Pass"),
    ("R102", "Pass"),
    ("C201", "Pass"),
    ("C301", "Pass"),
    ("U101", "Pass"),
)
EXPECTED_EBOM_ENTRY_MISMATCH: tuple[tuple[str, str], ...] = (
    ("C201", "Fail"),
    ("R102", "Fail"),
    ("R101", "Pass"),
    ("C301", "Pass"),
    ("U101", "Pass"),
)
# (part number, schematic quantity, EBOM quantity, status)
EXPECTED_EBOM_QTY_MATCH: tuple[tuple[str, int, int, str], ...] = (
    ("PN-RES-001", 2, 2, "Pass"),
    ("PN-CAP-001", 1, 1, "Pass"),
    ("PN-CAP-002", 1, 1, "Pass"),
    ("PN-IC-001", 1, 1, "Pass"),
)
EXPECTED_EBOM_QTY_MISMATCH: tuple[tuple[str, int, int, str], ...] = (
    ("PN-IC-001", 1, 2, "Fail"),
    ("PN-RES-001", 2, 1, "Fail"),
    ("PN-CAP-002", 1, 1, "Pass"),
)
EXPECTED_CONNECTIVITY: str = "Unable to Verify"  # status of the global result
EBOM_HEADERS: tuple[str, ...] = (
    "Reference Designator",
    "Part Number",
    "Description",
    "Quantity",
)
EBOM_MISSING_COLUMN: str = "Quantity"

_FIXED_TIME = datetime(2026, 1, 1, 0, 0, 0)


def _insert_text(page: fitz.Page, rect: tuple, text: str) -> None:
    if page.insert_textbox(fitz.Rect(*rect), text, fontname="helv", fontsize=10) < 0:
        raise AssertionError("text does not fit its box")


def _build_pdf(
    components: tuple[ComponentSpec, ...],
    annotations: tuple[tuple[int, str], ...] = (),
) -> fitz.Document:
    doc = fitz.open()
    for number in range(1, max(c.page for c in components) + 1):
        page = doc.new_page(width=595, height=842)
        _insert_text(page, (72, 30, 472, 80), "SANITIZED SAMPLE SCHEMATIC")
        here = [c for c in components if c.page == number]
        for i, c in enumerate(here):
            x0, y0 = 72 + 200 * (i % 2), 100 + 100 * (i // 2)
            text = f"{c.ref_des}\n{c.value}\nPN: {c.part_number}\n{c.description}"
            _insert_text(page, (x0, y0, x0 + 160, y0 + 70), text)
    for k, (number, text) in enumerate(annotations):
        doc[number - 1].add_text_annot(fitz.Point(500, 60 + 30 * k), text)
    doc.set_metadata({"creationDate": "", "modDate": ""})
    return doc


def _save_pdf(doc: fitz.Document, path: Path, **options) -> Path:
    try:
        doc.save(path, **options)
    finally:
        doc.close()
    return path


def _build_ebom(
    path: Path, rows: tuple[EbomRow, ...], headers: tuple[str, ...] = EBOM_HEADERS
) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(list(headers))
    for row in rows:
        values = [row.ref_des, row.part_number, row.description, row.quantity]
        ws.append(values[: len(headers)])
    wb.properties.created = _FIXED_TIME
    wb.properties.modified = _FIXED_TIME
    with patch("openpyxl.writer.excel.datetime.datetime") as clock:
        clock.now.return_value = _FIXED_TIME
        wb.save(path)
    return path


def build_original_pdf(path: Path) -> Path:
    """Original schematic with five Text annotations."""
    return _save_pdf(_build_pdf(ORIGINAL_COMPONENTS, ANNOTATIONS), path)


def build_modified_pdf(path: Path) -> Path:
    """Modified schematic without annotations."""
    return _save_pdf(_build_pdf(MODIFIED_COMPONENTS), path)


def build_layout_only_pdf(path: Path) -> Path:
    """Original components redistributed over three pages."""
    return _save_pdf(_build_pdf(LAYOUT_ONLY_COMPONENTS), path)


def build_ebom_match(path: Path) -> Path:
    """EBOM matching the modified schematic."""
    return _build_ebom(path, EBOM_MATCH_ROWS)


def build_ebom_mismatch(path: Path) -> Path:
    """EBOM with wrong part number, missing reference and wrong quantity."""
    return _build_ebom(path, EBOM_MISMATCH_ROWS)


def build_password_protected_pdf(path: Path) -> Path:
    """Encrypted copy of the modified schematic."""
    return _save_pdf(
        _build_pdf(MODIFIED_COMPONENTS),
        path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=PDF_USER_PASSWORD,
        owner_pw=PDF_OWNER_PASSWORD,
    )


def build_non_pdf_file(path: Path) -> Path:
    """Plain text file with a .pdf name."""
    path.write_text("not a pdf\n", encoding="utf-8")
    return path


def build_ebom_missing_column(path: Path) -> Path:
    """Matching EBOM without the Quantity column."""
    headers = tuple(h for h in EBOM_HEADERS if h != EBOM_MISSING_COLUMN)
    return _build_ebom(path, EBOM_MATCH_ROWS, headers)


def build_dataset(directory: Path) -> SampleDataset:
    """Create every variant in directory and return their paths."""
    return SampleDataset(
        original_pdf=build_original_pdf(directory / "original.pdf"),
        modified_pdf=build_modified_pdf(directory / "modified.pdf"),
        layout_only_pdf=build_layout_only_pdf(directory / "layout_only.pdf"),
        ebom_match=build_ebom_match(directory / "ebom_match.xlsx"),
        ebom_mismatch=build_ebom_mismatch(directory / "ebom_mismatch.xlsx"),
        password_pdf=build_password_protected_pdf(directory / "password.pdf"),
        non_pdf=build_non_pdf_file(directory / "not_a_pdf.pdf"),
        ebom_missing_column=build_ebom_missing_column(
            directory / "ebom_missing_column.xlsx"
        ),
    )
