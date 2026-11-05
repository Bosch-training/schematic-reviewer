"""Builder tests for the sanitized sample dataset (ST-04)."""

import dataclasses
import re
from datetime import datetime
from unittest.mock import patch

import fitz
import openpyxl
import pytest

from sample_dataset import (
    ANNOTATIONS,
    EBOM_HEADERS,
    EBOM_MATCH_ROWS,
    LAYOUT_ONLY_COMPONENTS,
    MODIFIED_COMPONENTS,
    ORIGINAL_COMPONENTS,
    PDF_OWNER_PASSWORD,
    PDF_USER_PASSWORD,
    SampleDataset,
    build_dataset,
    build_ebom_match,
    build_ebom_mismatch,
    build_ebom_missing_column,
    build_layout_only_pdf,
    build_modified_pdf,
    build_non_pdf_file,
    build_original_pdf,
    build_password_protected_pdf,
)

TITLE = "SANITIZED SAMPLE SCHEMATIC"
REF_TOKEN = re.compile(r"[A-Z]{1,3}\d+")

# (name, builder, file name, components, page count)
PDF_VARIANTS = (
    ("original", build_original_pdf, "original.pdf", ORIGINAL_COMPONENTS, 2),
    ("modified", build_modified_pdf, "modified.pdf", MODIFIED_COMPONENTS, 2),
    (
        "layout_only",
        build_layout_only_pdf,
        "layout_only.pdf",
        LAYOUT_ONLY_COMPONENTS,
        3,
    ),
)

# (name, builder, file name) for the four PDF builders.
PDF_BUILDERS = (
    ("original", build_original_pdf, "original.pdf"),
    ("modified", build_modified_pdf, "modified.pdf"),
    ("layout_only", build_layout_only_pdf, "layout_only.pdf"),
    ("password", build_password_protected_pdf, "password.pdf"),
)

# (name, builder, file name) for the three EBOM builders.
EBOM_BUILDERS = (
    ("match", build_ebom_match, "ebom_match.xlsx"),
    ("mismatch", build_ebom_mismatch, "ebom_mismatch.xlsx"),
    ("missing_column", build_ebom_missing_column, "ebom_missing_column.xlsx"),
)


def _variant_params(test_id):
    return [
        pytest.param(builder, filename, specs, pages, id=f"{test_id}-{name}")
        for name, builder, filename, specs, pages in PDF_VARIANTS
    ]


def _pdf_builder_params(test_id):
    return [
        pytest.param(builder, filename, id=f"{test_id}-{name}")
        for name, builder, filename in PDF_BUILDERS
    ]


def _ebom_params(test_id):
    return [
        pytest.param(builder, filename, id=f"{test_id}-{name}")
        for name, builder, filename in EBOM_BUILDERS
    ]


def _text_blocks(page):
    return [b for b in page.get_text("blocks") if b[6] == 0]


def _is_title(block):
    return block[4].splitlines() == [TITLE]


def _title_blocks(page):
    return [b for b in _text_blocks(page) if _is_title(b)]


def _component_blocks(page):
    return [b for b in _text_blocks(page) if not _is_title(b)]


def _component_lines(page):
    return [tuple(b[4].splitlines()) for b in _component_blocks(page)]


def _expected_lines(specs, page_no):
    return [
        (s.ref_des, s.value, f"PN: {s.part_number}", s.description)
        for s in specs
        if s.page == page_no
    ]


def _blocks_by_ref(doc):
    """Map reference to (1-based page, line tuple) for every component block."""
    found = {}
    for number, page in enumerate(doc, start=1):
        for block in _component_blocks(page):
            lines = tuple(block[4].splitlines())
            found[lines[0]] = (number, lines)
    return found


def _annotations(doc):
    return [
        (number, annot.info["content"])
        for number, page in enumerate(doc, start=1)
        for annot in page.annots()
    ]


def _content(path):
    with fitz.open(path) as doc:
        return [page.get_text("blocks") for page in doc], _annotations(doc)


def _protected_blocks(path):
    with fitz.open(path) as doc:
        assert doc.authenticate(PDF_USER_PASSWORD) != 0
        return [page.get_text("blocks") for page in doc]


def _sheet(path):
    return openpyxl.load_workbook(path).active


def _cells(path):
    return [tuple(row) for row in _sheet(path).iter_rows(values_only=True)]


def _header(path):
    return _cells(path)[0]


def _rows(path):
    return _cells(path)[1:]


def _inside(block, rect):
    x0, y0, x1, y1 = block[:4]
    rx0, ry0, rx1, ry1 = rect
    return rx0 <= x0 and ry0 <= y0 and x1 <= rx1 and y1 <= ry1


def _non_ref_lines(block):
    lines = block[4].splitlines()
    return lines if _is_title(block) else lines[1:]


def test_build_original_pdf_has_two_pages(tmp_path):
    """Covers ST-04-UT-001."""
    result = build_original_pdf(tmp_path / "original.pdf")
    with fitz.open(result) as doc:
        assert doc.page_count == 2


@pytest.mark.parametrize(
    "builder, filename",
    [
        pytest.param(build_original_pdf, "original.pdf", id="ST-04-UT-002"),
        pytest.param(build_modified_pdf, "modified.pdf", id="ST-04-UT-113-modified"),
        pytest.param(
            build_layout_only_pdf, "layout_only.pdf", id="ST-04-UT-113-layout_only"
        ),
        pytest.param(build_ebom_match, "ebom_match.xlsx", id="ST-04-UT-113-match"),
        pytest.param(
            build_ebom_mismatch, "ebom_mismatch.xlsx", id="ST-04-UT-113-mismatch"
        ),
        pytest.param(
            build_ebom_missing_column,
            "ebom_missing_column.xlsx",
            id="ST-04-UT-113-missing_column",
        ),
        pytest.param(
            build_password_protected_pdf, "password.pdf", id="ST-04-UT-113-password"
        ),
        pytest.param(build_non_pdf_file, "not_a_pdf.pdf", id="ST-04-UT-113-non_pdf"),
    ],
)
def test_builders_return_given_path_and_write_file(builder, filename, tmp_path):
    """Covers ST-04-UT-002 and ST-04-UT-113: return the given path and write a file."""
    path = tmp_path / filename
    result = builder(path)
    assert result == path
    assert path.is_file()
    assert path.stat().st_size > 0


def test_build_original_pdf_annotations_match_manifest(tmp_path):
    """Covers ST-04-UT-003."""
    with fitz.open(build_original_pdf(tmp_path / "original.pdf")) as doc:
        assert _annotations(doc) == list(ANNOTATIONS)


def test_build_original_pdf_five_text_annotations(tmp_path):
    """Covers ST-04-UT-004."""
    with fitz.open(build_original_pdf(tmp_path / "original.pdf")) as doc:
        types = [annot.type[1] for page in doc for annot in page.annots()]
    assert len(types) == 5
    assert all(kind == "Text" for kind in types)


def test_build_original_pdf_annotations_per_page(tmp_path):
    """Covers ST-04-UT-005."""
    with fitz.open(build_original_pdf(tmp_path / "original.pdf")) as doc:
        counts = [len(list(page.annots())) for page in doc]
    assert counts == [3, 2]


@pytest.mark.parametrize(
    "builder, filename, specs",
    [
        pytest.param(
            build_original_pdf, "original.pdf", ORIGINAL_COMPONENTS, id="ST-04-UT-006"
        ),
        pytest.param(
            build_modified_pdf, "modified.pdf", MODIFIED_COMPONENTS, id="ST-04-UT-025"
        ),
        pytest.param(
            build_layout_only_pdf,
            "layout_only.pdf",
            LAYOUT_ONLY_COMPONENTS,
            id="ST-04-UT-032",
        ),
    ],
)
def test_pdf_component_lines_match_specs(builder, filename, specs, tmp_path):
    """Covers ST-04-UT-006, ST-04-UT-025 and ST-04-UT-032."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        actual = [_component_lines(page) for page in doc]
    expected = [_expected_lines(specs, n) for n in range(1, len(actual) + 1)]
    assert len(actual) > 0
    assert actual == expected


@pytest.mark.parametrize(
    "builder, filename, specs, pages", _variant_params("ST-04-UT-007")
)
def test_schematic_pdfs_title_block_on_every_page(
    builder, filename, specs, pages, tmp_path
):
    """Covers ST-04-UT-007 over the three schematic PDFs."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.page_count == pages
        assert all(TITLE in page.get_text() for page in doc)


@pytest.mark.parametrize(
    "builder, filename, specs, pages", _variant_params("ST-04-UT-008")
)
def test_schematic_pdfs_pages_are_a4(builder, filename, specs, pages, tmp_path):
    """Covers ST-04-UT-008 over the three schematic PDFs."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.page_count == pages
        assert all(p.rect.width == 595 and p.rect.height == 842 for p in doc)


@pytest.mark.parametrize(
    "builder, filename, specs, pages", _variant_params("ST-04-UT-009")
)
def test_schematic_pdfs_one_block_per_component(
    builder, filename, specs, pages, tmp_path
):
    """Covers ST-04-UT-009 over the three schematic PDFs."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.page_count == pages
        for number, page in enumerate(doc, start=1):
            components_here = [s for s in specs if s.page == number]
            assert len(_text_blocks(page)) == len(components_here) + 1


@pytest.mark.parametrize(
    "builder, filename, specs, pages", _variant_params("ST-04-UT-010")
)
def test_schematic_pdfs_no_reference_token_outside_ref_lines(
    builder, filename, specs, pages, tmp_path
):
    """Covers ST-04-UT-010 over the three schematic PDFs."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.page_count == pages
        for page in doc:
            for block in _text_blocks(page):
                for line in _non_ref_lines(block):
                    assert not REF_TOKEN.search(line), line


@pytest.mark.parametrize(
    "builder, filename, specs, pages", _variant_params("ST-04-UT-011")
)
def test_schematic_pdfs_blocks_inside_documented_rects(
    builder, filename, specs, pages, tmp_path
):
    """Covers ST-04-UT-011 over the three schematic PDFs."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.page_count == pages
        for number, page in enumerate(doc, start=1):
            components = _component_blocks(page)
            assert len(components) == len([s for s in specs if s.page == number])
            for i, block in enumerate(components):
                x0 = 72 + 200 * (i % 2)
                y0 = 100 + 100 * (i // 2)
                assert _inside(block, (x0, y0, x0 + 160, y0 + 70))
            titles = _title_blocks(page)
            assert len(titles) == 1
            assert _inside(titles[0], (72, 30, 472, 80))


def test_build_original_pdf_annotation_points(tmp_path):
    """Covers ST-04-UT-012."""
    with fitz.open(build_original_pdf(tmp_path / "original.pdf")) as doc:
        rects = [annot.rect for page in doc for annot in page.annots()]
    assert len(rects) == 5
    for k, rect in enumerate(rects):
        assert rect.x0 <= 500 <= rect.x1
        assert rect.y0 <= 60 + 30 * k <= rect.y1


@pytest.mark.parametrize(
    "builder, filename, specs, pages", _variant_params("ST-04-UT-013")
)
def test_schematic_pdfs_text_is_ascii(builder, filename, specs, pages, tmp_path):
    """Covers ST-04-UT-013 over the three schematic PDFs."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.page_count == pages
        texts = [page.get_text() for page in doc]
        texts += [content for _, content in _annotations(doc)]
    assert texts
    assert all(text.isascii() for text in texts)


@pytest.mark.parametrize(
    "builder, filename, specs, pages", _variant_params("ST-04-UT-014")
)
def test_schematic_pdfs_metadata_dates_empty(builder, filename, specs, pages, tmp_path):
    """Covers ST-04-UT-014 over the three schematic PDFs."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.metadata["creationDate"] == ""
        assert doc.metadata["modDate"] == ""


@pytest.mark.parametrize(
    "builder, filename",
    [
        pytest.param(build_original_pdf, "original.pdf", id="ST-04-UT-015"),
        pytest.param(build_modified_pdf, "modified.pdf", id="ST-04-UT-026"),
        pytest.param(build_layout_only_pdf, "layout_only.pdf", id="ST-04-UT-033"),
    ],
)
def test_pdf_builders_deterministic_content(builder, filename, tmp_path):
    """Covers ST-04-UT-015, ST-04-UT-026 and ST-04-UT-033."""
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    first = builder(tmp_path / "d1" / filename)
    second = builder(tmp_path / "d2" / filename)
    assert _content(first) == _content(second)


@pytest.mark.parametrize("builder, filename", _pdf_builder_params("ST-04-UT-016"))
def test_pdf_builders_raise_assertion_error_when_text_does_not_fit(
    builder, filename, tmp_path
):
    """Covers ST-04-UT-016 over the four PDF builders."""
    with patch.object(fitz.Page, "insert_textbox", return_value=-1):
        with pytest.raises(AssertionError):
            builder(tmp_path / filename)


@pytest.mark.parametrize("builder, filename", _pdf_builder_params("ST-04-UT-017"))
def test_pdf_builders_propagate_save_error(builder, filename, tmp_path):
    """Covers ST-04-UT-017 over the four PDF builders."""
    with patch.object(fitz.Document, "save", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            builder(tmp_path / filename)


@pytest.mark.parametrize(
    "builder, filename",
    [
        pytest.param(build_original_pdf, "original.pdf", id="ST-04-UT-018"),
        pytest.param(build_password_protected_pdf, "password.pdf", id="ST-04-UT-112"),
    ],
)
def test_builder_writes_only_given_path(builder, filename, tmp_path):
    """Covers ST-04-UT-018 and ST-04-UT-112."""
    builder(tmp_path / filename)
    assert [p.name for p in tmp_path.iterdir()] == [filename]


@pytest.mark.parametrize(
    "builder, filename, pages",
    [
        pytest.param(build_modified_pdf, "modified.pdf", 2, id="ST-04-UT-019"),
        pytest.param(build_layout_only_pdf, "layout_only.pdf", 3, id="ST-04-UT-027"),
    ],
)
def test_pdf_page_count_and_no_annotations(builder, filename, pages, tmp_path):
    """Covers ST-04-UT-019 and ST-04-UT-027."""
    with fitz.open(builder(tmp_path / filename)) as doc:
        assert doc.page_count == pages
        assert sum(len(list(page.annots())) for page in doc) == 0


def test_build_modified_pdf_r101_changed_r102_unchanged(tmp_path):
    """Covers ST-04-UT-020."""
    with fitz.open(build_modified_pdf(tmp_path / "modified.pdf")) as doc:
        blocks = _blocks_by_ref(doc)
    assert blocks["R101"][0] == 1
    assert blocks["R101"][1][1] == "4.7K"
    assert blocks["R102"][0] == 1
    assert blocks["R102"][1][1] == "1K"


@pytest.mark.parametrize(
    "ref, page, lines",
    [
        pytest.param(
            "C301",
            2,
            ("C301", "100nF", "PN: PN-CAP-002", "Capacitor 0603"),
            id="ST-04-UT-021",
        ),
        pytest.param(
            "U101",
            2,
            ("U101", "OPAMP", "PN: PN-IC-001", "Dual op-amp 8-pin"),
            id="ST-04-UT-024",
        ),
    ],
)
def test_build_modified_pdf_component_block(ref, page, lines, tmp_path):
    """Covers ST-04-UT-021 and ST-04-UT-024."""
    with fitz.open(build_modified_pdf(tmp_path / "modified.pdf")) as doc:
        assert _blocks_by_ref(doc)[ref] == (page, lines)


def test_build_modified_pdf_r103_absent(tmp_path):
    """Covers ST-04-UT-022."""
    with fitz.open(build_modified_pdf(tmp_path / "modified.pdf")) as doc:
        assert doc.page_count == 2
        assert all(page.search_for("R103") == [] for page in doc)


def test_build_modified_pdf_c201_value_changed(tmp_path):
    """Covers ST-04-UT-023."""
    with fitz.open(build_modified_pdf(tmp_path / "modified.pdf")) as doc:
        page, lines = _blocks_by_ref(doc)["C201"]
    assert page == 2
    assert lines[1] == "220nF"
    assert lines[2] == "PN: PN-CAP-001"


def test_build_layout_only_pdf_same_components_as_original(tmp_path):
    """Covers ST-04-UT-028."""
    original = build_original_pdf(tmp_path / "original.pdf")
    layout = build_layout_only_pdf(tmp_path / "layout_only.pdf")
    with fitz.open(original) as orig_doc, fitz.open(layout) as layout_doc:
        original_lines = {
            lines for page in orig_doc for lines in _component_lines(page)
        }
        layout_lines = {
            lines for page in layout_doc for lines in _component_lines(page)
        }
    assert layout_lines == original_lines


def test_build_layout_only_pdf_components_on_documented_pages(tmp_path):
    """Covers ST-04-UT-029."""
    original = build_original_pdf(tmp_path / "original.pdf")
    layout = build_layout_only_pdf(tmp_path / "layout_only.pdf")
    with fitz.open(layout) as layout_doc:
        layout_pages = {
            ref: page for ref, (page, _) in _blocks_by_ref(layout_doc).items()
        }
    with fitz.open(original) as orig_doc:
        original_pages = {
            ref: page for ref, (page, _) in _blocks_by_ref(orig_doc).items()
        }
    assert layout_pages == {"R101": 1, "R102": 1, "R103": 2, "C201": 2, "U101": 3}
    assert layout_pages != original_pages


def test_build_layout_only_pdf_last_page_single_component(tmp_path):
    """Covers ST-04-UT-030."""
    with fitz.open(build_layout_only_pdf(tmp_path / "layout_only.pdf")) as doc:
        assert doc.page_count == 3
        blocks = [list(b[4].splitlines()) for b in _text_blocks(doc[2])]
    assert blocks == [
        [TITLE],
        ["U101", "OPAMP", "PN: PN-IC-001", "Dual op-amp 8-pin"],
    ]


def test_build_layout_only_pdf_derives_from_original(tmp_path):
    """Covers ST-04-UT-031."""
    with fitz.open(build_layout_only_pdf(tmp_path / "layout_only.pdf")) as doc:
        blocks = _blocks_by_ref(doc)
        texts = [page.get_text() for page in doc]
    assert blocks["R101"][1][1] == "10K"
    assert "R103" in blocks
    assert blocks["C201"][1][1] == "100nF"
    assert "C301" not in blocks
    assert not any("C301" in text for text in texts)


@pytest.mark.parametrize(
    "builder, filename, expected",
    [
        pytest.param(
            build_ebom_match,
            "ebom_match.xlsx",
            ("Reference Designator", "Part Number", "Description", "Quantity"),
            id="ST-04-UT-034",
        ),
        pytest.param(
            build_ebom_mismatch, "ebom_mismatch.xlsx", EBOM_HEADERS, id="ST-04-UT-046"
        ),
        pytest.param(
            build_ebom_missing_column,
            "ebom_missing_column.xlsx",
            ("Reference Designator", "Part Number", "Description"),
            id="ST-04-UT-047",
        ),
    ],
)
def test_ebom_header_row(builder, filename, expected, tmp_path):
    """Covers ST-04-UT-034, ST-04-UT-046 and ST-04-UT-047."""
    assert _header(builder(tmp_path / filename)) == expected


def test_build_ebom_match_rows_match_specs(tmp_path):
    """Covers ST-04-UT-035."""
    rows = _rows(build_ebom_match(tmp_path / "ebom_match.xlsx"))
    assert rows == [
        (r.ref_des, r.part_number, r.description, r.quantity) for r in EBOM_MATCH_ROWS
    ]


def test_build_ebom_match_references_equal_modified_pdf(tmp_path):
    """Covers ST-04-UT-036."""
    ebom = build_ebom_match(tmp_path / "ebom_match.xlsx")
    modified = build_modified_pdf(tmp_path / "modified.pdf")
    ebom_refs = {row[0] for row in _rows(ebom)}
    with fitz.open(modified) as doc:
        pdf_refs = set(_blocks_by_ref(doc))
    expected = {"R101", "R102", "C201", "C301", "U101"}
    assert ebom_refs == expected
    assert pdf_refs == expected


def test_build_ebom_match_quantity_is_integer(tmp_path):
    """Covers ST-04-UT-037."""
    rows = _rows(build_ebom_match(tmp_path / "ebom_match.xlsx"))
    quantities = [row[3] for row in rows]
    assert len(quantities) == 5
    assert all(isinstance(q, int) and q == 1 for q in quantities)


def test_build_ebom_match_single_sheet_six_rows(tmp_path):
    """Covers ST-04-UT-038."""
    wb = openpyxl.load_workbook(build_ebom_match(tmp_path / "ebom_match.xlsx"))
    assert len(wb.sheetnames) == 1
    assert wb.active.max_row == 6
    assert wb.active.max_column == 4


@pytest.mark.parametrize("builder, filename", _ebom_params("ST-04-UT-039"))
def test_ebom_builders_fixed_timestamps(builder, filename, tmp_path):
    """Covers ST-04-UT-039 over the three EBOM builders."""
    wb = openpyxl.load_workbook(builder(tmp_path / filename))
    assert wb.properties.created == datetime(2026, 1, 1, 0, 0, 0)
    assert wb.properties.modified == datetime(2026, 1, 1, 0, 0, 0)


def test_build_ebom_match_deterministic_cells(tmp_path):
    """Covers ST-04-UT-040."""
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    first = build_ebom_match(tmp_path / "d1" / "ebom_match.xlsx")
    second = build_ebom_match(tmp_path / "d2" / "ebom_match.xlsx")
    assert _cells(first) == _cells(second)


@pytest.mark.parametrize("builder, filename", _ebom_params("ST-04-UT-041"))
def test_ebom_builders_propagate_save_error(builder, filename, tmp_path):
    """Covers ST-04-UT-041 over the three EBOM builders."""
    with patch.object(openpyxl.Workbook, "save", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            builder(tmp_path / filename)


def test_build_ebom_mismatch_differs_only_by_three_edits(tmp_path):
    """Covers ST-04-UT-042."""
    match = {r[0]: r for r in _rows(build_ebom_match(tmp_path / "ebom_match.xlsx"))}
    mismatch_rows = _rows(build_ebom_mismatch(tmp_path / "ebom_mismatch.xlsx"))
    mismatch = {r[0]: r for r in mismatch_rows}
    fields = ("ref_des", "part_number", "description", "quantity")
    assert set(match) - set(mismatch) == {"R102"}
    assert set(mismatch) - set(match) == set()
    diffs = {
        ref: [
            fields[i]
            for i, (a, b) in enumerate(zip(match[ref], mismatch[ref]))
            if a != b
        ]
        for ref in set(match) & set(mismatch)
    }
    assert {ref: names for ref, names in diffs.items() if names} == {
        "C201": ["part_number"],
        "U101": ["quantity"],
    }


def test_build_ebom_mismatch_r102_missing(tmp_path):
    """Covers ST-04-UT-043."""
    path = build_ebom_mismatch(tmp_path / "ebom_mismatch.xlsx")
    rows = _rows(path)
    assert [row[0] for row in rows] == ["R101", "C201", "C301", "U101"]
    assert _sheet(path).max_row == 5


@pytest.mark.parametrize(
    "ref, expected",
    [
        pytest.param("C201", ("PN-CAP-999", "Capacitor 0603", 1), id="ST-04-UT-044"),
        pytest.param("U101", ("PN-IC-001", "Dual op-amp 8-pin", 2), id="ST-04-UT-045"),
    ],
)
def test_build_ebom_mismatch_row_edits(ref, expected, tmp_path):
    """Covers ST-04-UT-044 and ST-04-UT-045."""
    rows = _rows(build_ebom_mismatch(tmp_path / "ebom_mismatch.xlsx"))
    assert {r[0]: r[1:] for r in rows}[ref] == expected


def test_build_ebom_missing_column_rows_match_without_quantity(tmp_path):
    """Covers ST-04-UT-048."""
    rows = _rows(build_ebom_missing_column(tmp_path / "ebom_missing_column.xlsx"))
    assert all(len(row) == 3 for row in rows)
    assert rows == [(r.ref_des, r.part_number, r.description) for r in EBOM_MATCH_ROWS]


def test_build_password_protected_pdf_needs_pass(tmp_path):
    """Covers ST-04-UT-049."""
    with fitz.open(build_password_protected_pdf(tmp_path / "password.pdf")) as doc:
        assert bool(doc.needs_pass) is True
        assert doc.is_encrypted is True


@pytest.mark.parametrize(
    "password",
    [
        pytest.param(PDF_USER_PASSWORD, id="ST-04-UT-050"),
        pytest.param(PDF_OWNER_PASSWORD, id="ST-04-UT-051"),
    ],
)
def test_build_password_protected_pdf_password_authenticates(password, tmp_path):
    """Covers ST-04-UT-050 and ST-04-UT-051."""
    with fitz.open(build_password_protected_pdf(tmp_path / "password.pdf")) as doc:
        assert doc.authenticate(password) != 0


def test_build_password_protected_pdf_wrong_password_fails(tmp_path):
    """Covers ST-04-UT-052."""
    with fitz.open(build_password_protected_pdf(tmp_path / "password.pdf")) as doc:
        assert doc.authenticate("wrong-password") == 0
        assert bool(doc.needs_pass) is True


def test_build_password_protected_pdf_empty_password_fails(tmp_path):
    """Covers ST-04-UT-053."""
    with fitz.open(build_password_protected_pdf(tmp_path / "password.pdf")) as doc:
        assert doc.authenticate("") == 0


def test_build_password_protected_pdf_content_equals_modified(tmp_path):
    """Covers ST-04-UT-054."""
    protected = build_password_protected_pdf(tmp_path / "password.pdf")
    modified_blocks, modified_annots = _content(
        build_modified_pdf(tmp_path / "modified.pdf")
    )
    assert _protected_blocks(protected) == modified_blocks
    assert modified_annots == []


def test_build_password_protected_pdf_uses_aes_256(tmp_path):
    """Covers ST-04-UT-055."""
    with fitz.open(build_password_protected_pdf(tmp_path / "password.pdf")) as doc:
        encryption = doc.xref_get_key(-1, "Encrypt")[1]
    assert "AES" in encryption
    assert "256" in encryption


def test_build_password_protected_pdf_deterministic_content(tmp_path):
    """Covers ST-04-UT-056."""
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    first = build_password_protected_pdf(tmp_path / "d1" / "password.pdf")
    second = build_password_protected_pdf(tmp_path / "d2" / "password.pdf")
    assert _protected_blocks(first) == _protected_blocks(second)


def test_build_non_pdf_file_content(tmp_path):
    """Covers ST-04-UT-057."""
    path = build_non_pdf_file(tmp_path / "not_a_pdf.pdf")
    assert path.read_bytes().decode("utf-8").rstrip() == "not a pdf"


def test_build_non_pdf_file_has_no_pdf_header(tmp_path):
    """Covers ST-04-UT-058."""
    data = build_non_pdf_file(tmp_path / "not_a_pdf.pdf").read_bytes()
    assert not data.startswith(b"%PDF")
    assert b"%PDF" not in data


def test_build_non_pdf_file_keeps_pdf_name(tmp_path):
    """Covers ST-04-UT-059."""
    path = tmp_path / "not_a_pdf.pdf"
    result = build_non_pdf_file(path)
    assert result.suffix == ".pdf"
    assert result == path


def test_build_non_pdf_file_deterministic_bytes(tmp_path):
    """Covers ST-04-UT-060."""
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    first = build_non_pdf_file(tmp_path / "d1" / "not_a_pdf.pdf")
    second = build_non_pdf_file(tmp_path / "d2" / "not_a_pdf.pdf")
    assert first.read_bytes() == second.read_bytes()


def test_build_dataset_returns_fixed_file_names(tmp_path):
    """Covers ST-04-UT-061."""
    dataset = build_dataset(tmp_path)
    assert isinstance(dataset, SampleDataset)
    names = {
        f.name: getattr(dataset, f.name).name for f in dataclasses.fields(SampleDataset)
    }
    assert names == {
        "original_pdf": "original.pdf",
        "modified_pdf": "modified.pdf",
        "layout_only_pdf": "layout_only.pdf",
        "ebom_match": "ebom_match.xlsx",
        "ebom_mismatch": "ebom_mismatch.xlsx",
        "password_pdf": "password.pdf",
        "non_pdf": "not_a_pdf.pdf",
        "ebom_missing_column": "ebom_missing_column.xlsx",
    }


def test_build_dataset_all_files_exist_non_empty(tmp_path):
    """Covers ST-04-UT-062."""
    dataset = build_dataset(tmp_path)
    for f in dataclasses.fields(SampleDataset):
        path = getattr(dataset, f.name)
        assert path.is_file()
        assert path.stat().st_size > 0


def test_build_dataset_creates_exactly_eight_files(tmp_path):
    """Covers ST-04-UT-063."""
    build_dataset(tmp_path)
    expected = [
        "original.pdf",
        "modified.pdf",
        "layout_only.pdf",
        "ebom_match.xlsx",
        "ebom_mismatch.xlsx",
        "password.pdf",
        "not_a_pdf.pdf",
        "ebom_missing_column.xlsx",
    ]
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(expected)


def test_build_dataset_paths_distinct_in_directory(tmp_path):
    """Covers ST-04-UT-064."""
    dataset = build_dataset(tmp_path)
    paths = [getattr(dataset, f.name) for f in dataclasses.fields(SampleDataset)]
    assert len(set(paths)) == 8
    assert all(path.parent == tmp_path for path in paths)


def test_build_dataset_deterministic_across_directories(tmp_path):
    """Covers ST-04-UT-065."""
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    first = build_dataset(tmp_path / "d1")
    second = build_dataset(tmp_path / "d2")
    for name in ("original_pdf", "modified_pdf", "layout_only_pdf"):
        assert _content(getattr(first, name)) == _content(getattr(second, name))
    for name in ("ebom_match", "ebom_mismatch", "ebom_missing_column"):
        assert _cells(getattr(first, name)) == _cells(getattr(second, name))
    assert first.non_pdf.read_bytes() == second.non_pdf.read_bytes()
    modified_blocks, _ = _content(first.modified_pdf)
    assert _protected_blocks(first.password_pdf) == modified_blocks
    assert _protected_blocks(second.password_pdf) == modified_blocks


def test_build_dataset_propagates_builder_error(tmp_path):
    """Covers ST-04-UT-066."""
    with patch("sample_dataset.build_original_pdf", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            build_dataset(tmp_path)


def test_sample_dataset_fixture_creates_all_files(sample_dataset):
    """Covers ST-04-UT-067."""
    assert isinstance(sample_dataset, SampleDataset)
    for f in dataclasses.fields(SampleDataset):
        assert getattr(sample_dataset, f.name).is_file()


def test_sample_dataset_fixture_uses_tmp_path(sample_dataset, tmp_path):
    """Covers ST-04-UT-068."""
    for f in dataclasses.fields(SampleDataset):
        assert getattr(sample_dataset, f.name).parent == tmp_path


@pytest.mark.parametrize("builder, filename", _pdf_builder_params("ST-04-UT-114"))
def test_pdf_builders_accept_zero_insert_textbox_return(builder, filename, tmp_path):
    path = tmp_path / filename
    with patch.object(fitz.Page, "insert_textbox", return_value=0):
        builder(path)
    assert path.is_file()
