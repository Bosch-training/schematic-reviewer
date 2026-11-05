"""Manifest, spec and dataclass tests for the sanitized sample dataset (ST-04)."""

import ast
import dataclasses
import importlib
import re
from collections import Counter
from pathlib import Path

import pytest

from models import Status
from sample_dataset import (
    ANNOTATIONS,
    EBOM_HEADERS,
    EBOM_MATCH_ROWS,
    EBOM_MISMATCH_ROWS,
    EBOM_MISSING_COLUMN,
    EXPECTED_CHANGE_ITEMS,
    EXPECTED_CONNECTIVITY,
    EXPECTED_EBOM_ENTRY_MATCH,
    EXPECTED_EBOM_ENTRY_MISMATCH,
    EXPECTED_EBOM_QTY_MATCH,
    EXPECTED_EBOM_QTY_MISMATCH,
    EXPECTED_UNINTENDED,
    LAYOUT_ONLY_COMPONENTS,
    MODIFIED_COMPONENTS,
    ORIGINAL_COMPONENTS,
    PDF_OWNER_PASSWORD,
    PDF_USER_PASSWORD,
    ComponentSpec,
    EbomRow,
    SampleDataset,
)

# Change targets per change request item (LLD 4 and T-13); ref None means no reference.
# (change id, target reference, target value, target present after change)
CHANGE_TARGETS = (
    ("CR-001", "R101", "4.7K", True),
    ("CR-002", "R102", "2.2K", True),
    ("CR-003", "R103", None, False),
    ("CR-004", "C301", "100nF", True),
    ("CR-005", None, None, None),
)

# Mismatch EBOM edits relative to the match EBOM (LLD 4).
EBOM_EDITS = {"C201": {"part_number": "PN-CAP-999"}, "U101": {"quantity": 2}}
EBOM_REMOVED_REFS = frozenset({"R102"})

ORIGINAL_EXPECTED = (
    ComponentSpec("R101", "10K", "PN-RES-001", "Resistor 0603", 1),
    ComponentSpec("R102", "1K", "PN-RES-001", "Resistor 0603", 1),
    ComponentSpec("R103", "100R", "PN-RES-001", "Resistor 0603", 1),
    ComponentSpec("C201", "100nF", "PN-CAP-001", "Capacitor 0603", 2),
    ComponentSpec("U101", "OPAMP", "PN-IC-001", "Dual op-amp 8-pin", 2),
)
MODIFIED_EXPECTED = (
    ComponentSpec("R101", "4.7K", "PN-RES-001", "Resistor 0603", 1),
    ComponentSpec("R102", "1K", "PN-RES-001", "Resistor 0603", 1),
    ComponentSpec("C201", "220nF", "PN-CAP-001", "Capacitor 0603", 2),
    ComponentSpec("C301", "100nF", "PN-CAP-002", "Capacitor 0603", 2),
    ComponentSpec("U101", "OPAMP", "PN-IC-001", "Dual op-amp 8-pin", 2),
)
LAYOUT_ONLY_EXPECTED = (
    ComponentSpec("R101", "10K", "PN-RES-001", "Resistor 0603", 1),
    ComponentSpec("R102", "1K", "PN-RES-001", "Resistor 0603", 1),
    ComponentSpec("R103", "100R", "PN-RES-001", "Resistor 0603", 2),
    ComponentSpec("C201", "100nF", "PN-CAP-001", "Capacitor 0603", 2),
    ComponentSpec("U101", "OPAMP", "PN-IC-001", "Dual op-amp 8-pin", 3),
)
EBOM_MATCH_EXPECTED = (
    EbomRow("R101", "PN-RES-001", "Resistor 0603", 1),
    EbomRow("R102", "PN-RES-001", "Resistor 0603", 1),
    EbomRow("C201", "PN-CAP-001", "Capacitor 0603", 1),
    EbomRow("C301", "PN-CAP-002", "Capacitor 0603", 1),
    EbomRow("U101", "PN-IC-001", "Dual op-amp 8-pin", 1),
)
EBOM_MISMATCH_EXPECTED = (
    EbomRow("R101", "PN-RES-001", "Resistor 0603", 1),
    EbomRow("C201", "PN-CAP-999", "Capacitor 0603", 1),
    EbomRow("C301", "PN-CAP-002", "Capacitor 0603", 1),
    EbomRow("U101", "PN-IC-001", "Dual op-amp 8-pin", 2),
)
ANNOTATIONS_EXPECTED = (
    (1, "Replace R101 from 10K to 4.7K"),
    (1, "Replace R102 from 1K to 2.2K"),
    (1, "Remove R103"),
    (2, "Add C301 100nF"),
    (2, "Improve filtering on input stage"),
)
CHANGE_ITEMS_EXPECTED = {
    ("CR-001", Status.PASS),
    ("CR-002", Status.FAIL),
    ("CR-003", Status.PASS),
    ("CR-004", Status.PASS),
    ("CR-005", Status.UNABLE_TO_VERIFY),
}
UNINTENDED_EXPECTED = (("C201", "value", "100nF", "220nF"),)
ENTRY_MATCH_EXPECTED = {
    ("R101", Status.PASS),
    ("R102", Status.PASS),
    ("C201", Status.PASS),
    ("C301", Status.PASS),
    ("U101", Status.PASS),
}
ENTRY_MISMATCH_EXPECTED = {
    ("C201", Status.FAIL),
    ("R102", Status.FAIL),
    ("R101", Status.PASS),
    ("C301", Status.PASS),
    ("U101", Status.PASS),
}
QTY_MATCH_EXPECTED = {
    ("PN-RES-001", 2, 2, Status.PASS),
    ("PN-CAP-001", 1, 1, Status.PASS),
    ("PN-CAP-002", 1, 1, Status.PASS),
    ("PN-IC-001", 1, 1, Status.PASS),
}
QTY_MISMATCH_EXPECTED = {
    ("PN-IC-001", 1, 2, Status.FAIL),
    ("PN-RES-001", 2, 1, Status.FAIL),
    ("PN-CAP-002", 1, 1, Status.PASS),
}

# (name, value, documented length, element shape: a type or a tuple of types)
MANIFEST_TUPLES = (
    ("ORIGINAL_COMPONENTS", ORIGINAL_COMPONENTS, 5, ComponentSpec),
    ("MODIFIED_COMPONENTS", MODIFIED_COMPONENTS, 5, ComponentSpec),
    ("LAYOUT_ONLY_COMPONENTS", LAYOUT_ONLY_COMPONENTS, 5, ComponentSpec),
    ("EBOM_MATCH_ROWS", EBOM_MATCH_ROWS, 5, EbomRow),
    ("EBOM_MISMATCH_ROWS", EBOM_MISMATCH_ROWS, 4, EbomRow),
    ("ANNOTATIONS", ANNOTATIONS, 5, (int, str)),
    ("EXPECTED_CHANGE_ITEMS", EXPECTED_CHANGE_ITEMS, 5, (str, str)),
    ("EXPECTED_UNINTENDED", EXPECTED_UNINTENDED, 1, (str, str, str, str)),
    ("EXPECTED_EBOM_ENTRY_MATCH", EXPECTED_EBOM_ENTRY_MATCH, 5, (str, str)),
    ("EXPECTED_EBOM_ENTRY_MISMATCH", EXPECTED_EBOM_ENTRY_MISMATCH, 5, (str, str)),
    ("EXPECTED_EBOM_QTY_MATCH", EXPECTED_EBOM_QTY_MATCH, 4, (str, int, int, str)),
    (
        "EXPECTED_EBOM_QTY_MISMATCH",
        EXPECTED_EBOM_QTY_MISMATCH,
        3,
        (str, int, int, str),
    ),
    ("EBOM_HEADERS", EBOM_HEADERS, 4, str),
)

NONEMPTY_CASES = [
    pytest.param(value, id=f"ST-04-UT-090-{name}")
    for name, value, _, _ in MANIFEST_TUPLES
]
LENGTH_CASES = [
    pytest.param(value, length, id=f"ST-04-UT-091-{name}")
    for name, value, length, _ in MANIFEST_TUPLES
]
TYPE_CASES = [
    pytest.param(value, shape, id=f"ST-04-UT-093-{name}")
    for name, value, _, shape in MANIFEST_TUPLES
]


def _has_shape(item, shape):
    if isinstance(shape, type):
        return isinstance(item, shape)
    return (
        isinstance(item, tuple)
        and len(item) == len(shape)
        and all(isinstance(v, t) for v, t in zip(item, shape))
    )


def _spec_status(before, after):
    """Return (kind, original value, modified value) for one reference."""
    if before is None:
        return "added", None, after.value
    if after is None:
        return "removed", before.value, None
    kind = "changed" if before.value != after.value else "unchanged"
    return kind, before.value, after.value


def _entry_outcome(ebom_rows, ref, part_number):
    part_by_ref = {r.ref_des: r.part_number for r in ebom_rows}
    return Status.PASS if part_by_ref.get(ref) == part_number else Status.FAIL


def test_module_importable_top_level():
    """Covers ST-04-UT-069."""
    module = importlib.import_module("sample_dataset")
    assert all(
        hasattr(module, name)
        for name in ("ComponentSpec", "EbomRow", "SampleDataset", "build_dataset")
    )
    assert callable(module.build_dataset)


def test_module_does_not_import_models():
    """Covers ST-04-UT-070."""
    source = Path(__file__).with_name("sample_dataset.py").read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not any(name == "models" or name.startswith("models.") for name in imported)


FROZEN_CASES = [
    pytest.param(
        ComponentSpec("R1", "1K", "PN-X", "Resistor", 1),
        "ref_des",
        id="ST-04-UT-071-ComponentSpec",
    ),
    pytest.param(
        EbomRow("R1", "PN-X", "Resistor", 1), "ref_des", id="ST-04-UT-071-EbomRow"
    ),
    pytest.param(
        SampleDataset(*([Path("x.pdf")] * 8)),
        "original_pdf",
        id="ST-04-UT-071-SampleDataset",
    ),
]


@pytest.mark.parametrize("instance, field", FROZEN_CASES)
def test_dataclasses_are_frozen(instance, field):
    """Covers ST-04-UT-071 over the three dataclasses."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, field, "changed")


FIELD_CASES = [
    pytest.param(
        ComponentSpec,
        ("ref_des", "value", "part_number", "description", "page"),
        id="ST-04-UT-072-ComponentSpec",
    ),
    pytest.param(
        EbomRow,
        ("ref_des", "part_number", "description", "quantity"),
        id="ST-04-UT-072-EbomRow",
    ),
    pytest.param(
        SampleDataset,
        (
            "original_pdf",
            "modified_pdf",
            "layout_only_pdf",
            "ebom_match",
            "ebom_mismatch",
            "password_pdf",
            "non_pdf",
            "ebom_missing_column",
        ),
        id="ST-04-UT-072-SampleDataset",
    ),
]


@pytest.mark.parametrize("cls, names", FIELD_CASES)
def test_dataclass_fields_match_lld(cls, names):
    """Covers ST-04-UT-072 over the three dataclasses."""
    assert tuple(f.name for f in dataclasses.fields(cls)) == names


EXACT_CASES = [
    pytest.param(ORIGINAL_COMPONENTS, ORIGINAL_EXPECTED, id="ST-04-UT-073"),
    pytest.param(MODIFIED_COMPONENTS, MODIFIED_EXPECTED, id="ST-04-UT-074"),
    pytest.param(LAYOUT_ONLY_COMPONENTS, LAYOUT_ONLY_EXPECTED, id="ST-04-UT-075"),
    pytest.param(EBOM_MATCH_ROWS, EBOM_MATCH_EXPECTED, id="ST-04-UT-076"),
    pytest.param(EBOM_MISMATCH_ROWS, EBOM_MISMATCH_EXPECTED, id="ST-04-UT-077"),
    pytest.param(ANNOTATIONS, ANNOTATIONS_EXPECTED, id="ST-04-UT-078"),
    pytest.param(EXPECTED_UNINTENDED, UNINTENDED_EXPECTED, id="ST-04-UT-081"),
]


@pytest.mark.parametrize("actual, expected", EXACT_CASES)
def test_manifest_constant_matches_lld_table(actual, expected):
    """Covers ST-04-UT-073 to ST-04-UT-078 and ST-04-UT-081 (order significant)."""
    assert actual == expected


SET_CASES = [
    pytest.param(EXPECTED_CHANGE_ITEMS, CHANGE_ITEMS_EXPECTED, id="ST-04-UT-079"),
    pytest.param(EXPECTED_EBOM_ENTRY_MATCH, ENTRY_MATCH_EXPECTED, id="ST-04-UT-082"),
    pytest.param(
        EXPECTED_EBOM_ENTRY_MISMATCH, ENTRY_MISMATCH_EXPECTED, id="ST-04-UT-083"
    ),
    pytest.param(EXPECTED_EBOM_QTY_MATCH, QTY_MATCH_EXPECTED, id="ST-04-UT-084"),
    pytest.param(EXPECTED_EBOM_QTY_MISMATCH, QTY_MISMATCH_EXPECTED, id="ST-04-UT-085"),
]


@pytest.mark.parametrize("actual, expected", SET_CASES)
def test_manifest_constant_matches_lld_set(actual, expected):
    """Covers ST-04-UT-079 and ST-04-UT-082 to ST-04-UT-085 (order not asserted)."""
    assert set(actual) == expected


def test_expected_change_item_cr005_unable_to_verify():
    """Covers ST-04-UT-080."""
    assert dict(EXPECTED_CHANGE_ITEMS)["CR-005"] == Status.UNABLE_TO_VERIFY
    assert dict(EXPECTED_CHANGE_ITEMS)["CR-005"] != Status.PASS


def test_expected_connectivity_unable_to_verify():
    """Covers ST-04-UT-087."""
    assert EXPECTED_CONNECTIVITY == Status.UNABLE_TO_VERIFY


def test_ebom_header_constants_match_lld():
    """Covers ST-04-UT-088."""
    assert EBOM_HEADERS == (
        "Reference Designator",
        "Part Number",
        "Description",
        "Quantity",
    )
    assert EBOM_MISSING_COLUMN == "Quantity"
    assert EBOM_MISSING_COLUMN in EBOM_HEADERS


def test_pdf_passwords_non_empty_and_distinct():
    """Covers ST-04-UT-089."""
    assert isinstance(PDF_USER_PASSWORD, str) and len(PDF_USER_PASSWORD) > 0
    assert isinstance(PDF_OWNER_PASSWORD, str) and len(PDF_OWNER_PASSWORD) > 0
    assert PDF_USER_PASSWORD != PDF_OWNER_PASSWORD


@pytest.mark.parametrize("value", NONEMPTY_CASES)
def test_manifest_tuples_are_not_empty(value):
    """Covers ST-04-UT-090 over every manifest tuple."""
    assert len(value) > 0


@pytest.mark.parametrize("value, length", LENGTH_CASES)
def test_manifest_tuples_have_documented_lengths(value, length):
    """Covers ST-04-UT-091 over every manifest tuple."""
    assert len(value) == length


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(EXPECTED_CONNECTIVITY, id="ST-04-UT-092-EXPECTED_CONNECTIVITY"),
        pytest.param(EBOM_MISSING_COLUMN, id="ST-04-UT-092-EBOM_MISSING_COLUMN"),
        pytest.param(PDF_USER_PASSWORD, id="ST-04-UT-092-PDF_USER_PASSWORD"),
        pytest.param(PDF_OWNER_PASSWORD, id="ST-04-UT-092-PDF_OWNER_PASSWORD"),
    ],
)
def test_manifest_string_constants_not_empty(value):
    assert isinstance(value, str)
    assert len(value) > 0


@pytest.mark.parametrize("value, shape", TYPE_CASES)
def test_manifest_element_types(value, shape):
    """Covers ST-04-UT-093 over every manifest tuple."""
    assert len(value) > 0
    assert all(_has_shape(item, shape) for item in value)


@pytest.mark.parametrize(
    "rows",
    [
        pytest.param(EBOM_MATCH_ROWS, id="ST-04-UT-093-quantity-EBOM_MATCH_ROWS"),
        pytest.param(EBOM_MISMATCH_ROWS, id="ST-04-UT-093-quantity-EBOM_MISMATCH_ROWS"),
    ],
)
def test_manifest_ebom_quantity_fields_are_int(rows):
    assert len(rows) > 0
    assert all(isinstance(row.quantity, int) for row in rows)


def test_manifest_status_strings_match_models_status():
    """Covers ST-04-UT-094."""
    allowed = {s.value for s in Status}
    statuses = (
        [status for _, status in EXPECTED_CHANGE_ITEMS]
        + [status for _, status in EXPECTED_EBOM_ENTRY_MATCH]
        + [status for _, status in EXPECTED_EBOM_ENTRY_MISMATCH]
        + [row[3] for row in EXPECTED_EBOM_QTY_MATCH]
        + [row[3] for row in EXPECTED_EBOM_QTY_MISMATCH]
        + [EXPECTED_CONNECTIVITY]
    )
    assert statuses
    assert all(status in allowed for status in statuses)


def test_manifest_pages_are_one_based():
    """Covers ST-04-UT-095."""
    pages = [s.page for s in (*ORIGINAL_COMPONENTS, *MODIFIED_COMPONENTS)]
    pages += [s.page for s in LAYOUT_ONLY_COMPONENTS]
    pages += [page for page, _ in ANNOTATIONS]
    assert min(pages) >= 1
    assert max(s.page for s in ORIGINAL_COMPONENTS) == 2
    assert max(s.page for s in MODIFIED_COMPONENTS) == 2
    assert max(page for page, _ in ANNOTATIONS) == 2
    assert max(s.page for s in LAYOUT_ONLY_COMPONENTS) == 3


REF_CASES = [
    pytest.param(ORIGINAL_COMPONENTS, id="ST-04-UT-096-ORIGINAL_COMPONENTS"),
    pytest.param(MODIFIED_COMPONENTS, id="ST-04-UT-096-MODIFIED_COMPONENTS"),
    pytest.param(LAYOUT_ONLY_COMPONENTS, id="ST-04-UT-096-LAYOUT_ONLY_COMPONENTS"),
    pytest.param(EBOM_MATCH_ROWS, id="ST-04-UT-096-EBOM_MATCH_ROWS"),
    pytest.param(EBOM_MISMATCH_ROWS, id="ST-04-UT-096-EBOM_MISMATCH_ROWS"),
]


@pytest.mark.parametrize("rows", REF_CASES)
def test_manifest_reference_designators_unique(rows):
    """Covers ST-04-UT-096 over the component and EBOM tuples."""
    refs = [row.ref_des for row in rows]
    assert refs
    assert len(set(refs)) == len(refs)


def test_expected_change_item_ids_sequential():
    """Covers ST-04-UT-097."""
    ids = [item_id for item_id, _ in EXPECTED_CHANGE_ITEMS]
    assert sorted(ids) == ["CR-001", "CR-002", "CR-003", "CR-004", "CR-005"]


def test_expected_change_items_count_equals_annotations():
    """Covers ST-04-UT-098."""
    assert len(EXPECTED_CHANGE_ITEMS) == 5
    assert len(ANNOTATIONS) == 5
    items = dict(EXPECTED_CHANGE_ITEMS)
    for k in range(1, 6):
        assert f"CR-00{k}" in items
        # Pairing by index is the open question; only the annotation lookup is checked.
        assert ANNOTATIONS[k - 1]


def test_spec_text_is_ascii_without_reference_tokens():
    """Covers ST-04-UT-099."""
    specs = (*ORIGINAL_COMPONENTS, *MODIFIED_COMPONENTS, *LAYOUT_ONLY_COMPONENTS)
    strings = []
    for spec in specs:
        strings += [spec.ref_des, spec.part_number]
    for row in (*EBOM_MATCH_ROWS, *EBOM_MISMATCH_ROWS):
        strings += [row.ref_des, row.part_number]
    assert strings
    assert all(text.isascii() for text in strings)
    for spec in specs:
        assert not re.search(r"[A-Z]{1,3}\d+", spec.value)
        assert not re.search(r"[A-Z]{1,3}\d+", spec.description)


def test_spec_fields_well_formed():
    """Covers ST-04-UT-100."""
    rows = (*ORIGINAL_COMPONENTS, *MODIFIED_COMPONENTS, *LAYOUT_ONLY_COMPONENTS)
    rows += (*EBOM_MATCH_ROWS, *EBOM_MISMATCH_ROWS)
    assert rows
    for row in rows:
        assert re.fullmatch(r"[A-Z]{1,3}\d+", row.ref_des)
        for field in dataclasses.fields(row):
            value = getattr(row, field.name)
            if isinstance(value, str):
                assert value.strip()


def test_part_number_identifies_family():
    """Covers ST-04-UT-101."""
    descriptions = {}
    for spec in (*ORIGINAL_COMPONENTS, *MODIFIED_COMPONENTS):
        descriptions.setdefault(spec.part_number, set()).add(spec.description)
    assert all(len(found) == 1 for found in descriptions.values())
    values = {s.value for s in MODIFIED_COMPONENTS if s.part_number == "PN-RES-001"}
    assert values == {"4.7K", "1K"}


def test_manifest_spec_diff_per_reference():
    """Covers ST-04-UT-102."""
    original = {s.ref_des: s for s in ORIGINAL_COMPONENTS}
    modified = {s.ref_des: s for s in MODIFIED_COMPONENTS}
    derived = {
        ref: _spec_status(original.get(ref), modified.get(ref))
        for ref in original.keys() | modified.keys()
    }
    assert derived == {
        "R101": ("changed", "10K", "4.7K"),
        "R102": ("unchanged", "1K", "1K"),
        "R103": ("removed", "100R", None),
        "C201": ("changed", "100nF", "220nF"),
        "C301": ("added", None, "100nF"),
        "U101": ("unchanged", "OPAMP", "OPAMP"),
    }


def test_manifest_unintended_derived_from_specs():
    """Covers ST-04-UT-103."""
    original = {s.ref_des: s for s in ORIGINAL_COMPONENTS}
    modified = {s.ref_des: s for s in MODIFIED_COMPONENTS}
    diffs = {
        (ref, "value", original[ref].value, modified[ref].value)
        for ref in original.keys() & modified.keys()
        if original[ref].value != modified[ref].value
    }
    targeted = {ref for _, ref, _, _ in CHANGE_TARGETS if ref is not None}
    unintended = {diff for diff in diffs if diff[0] not in targeted}
    assert unintended == {("C201", "value", "100nF", "220nF")}
    assert set(EXPECTED_UNINTENDED) == unintended


def test_manifest_layout_only_has_no_content_diff():
    """Covers ST-04-UT-104."""
    original = {s.ref_des: s for s in ORIGINAL_COMPONENTS}
    layout = {s.ref_des: s for s in LAYOUT_ONLY_COMPONENTS}
    content = {
        ref: (s.value, s.part_number, s.description) for ref, s in original.items()
    }
    layout_content = {
        ref: (s.value, s.part_number, s.description) for ref, s in layout.items()
    }
    assert content == layout_content
    assert {ref: s.page for ref, s in original.items()} != {
        ref: s.page for ref, s in layout.items()
    }


def test_manifest_change_items_derived_from_specs():
    """Covers ST-04-UT-105."""
    modified = {s.ref_des: s for s in MODIFIED_COMPONENTS}
    derived = set()
    for cr_id, ref, value, present in CHANGE_TARGETS:
        if ref is None:
            derived.add((cr_id, Status.UNABLE_TO_VERIFY))
            continue
        spec = modified.get(ref)
        matches = (spec is not None) == present and (
            spec is None or spec.value == value
        )
        derived.add((cr_id, Status.PASS if matches else Status.FAIL))
    assert derived == set(EXPECTED_CHANGE_ITEMS)


def test_manifest_ebom_match_derived_from_modified():
    """Covers ST-04-UT-106."""
    derived = [
        EbomRow(s.ref_des, s.part_number, s.description, 1) for s in MODIFIED_COMPONENTS
    ]
    assert EBOM_MATCH_ROWS
    assert derived == list(EBOM_MATCH_ROWS)


def test_manifest_ebom_mismatch_derived_from_match():
    """Covers ST-04-UT-107."""
    derived = [
        dataclasses.replace(row, **EBOM_EDITS.get(row.ref_des, {}))
        for row in EBOM_MATCH_ROWS
        if row.ref_des not in EBOM_REMOVED_REFS
    ]
    assert EBOM_MISMATCH_ROWS
    assert derived == list(EBOM_MISMATCH_ROWS)


ENTRY_CASES = [
    pytest.param(EBOM_MATCH_ROWS, EXPECTED_EBOM_ENTRY_MATCH, id="ST-04-UT-108"),
    pytest.param(EBOM_MISMATCH_ROWS, EXPECTED_EBOM_ENTRY_MISMATCH, id="ST-04-UT-109"),
]


@pytest.mark.parametrize("ebom_rows, expected", ENTRY_CASES)
def test_manifest_ebom_entry_outcomes_derived(ebom_rows, expected):
    """Covers ST-04-UT-108 and ST-04-UT-109 (same-part-number rule)."""
    derived = {
        (s.ref_des, _entry_outcome(ebom_rows, s.ref_des, s.part_number))
        for s in MODIFIED_COMPONENTS
    }
    assert expected
    assert derived == set(expected)


QTY_CASES = [
    pytest.param(
        EBOM_MATCH_ROWS, EXPECTED_EBOM_QTY_MATCH, frozenset(), id="ST-04-UT-110"
    ),
    pytest.param(
        EBOM_MISMATCH_ROWS,
        EXPECTED_EBOM_QTY_MISMATCH,
        frozenset({"PN-CAP-001", "PN-CAP-999"}),
        id="ST-04-UT-111",
    ),
]


@pytest.mark.parametrize("ebom_rows, expected, excluded", QTY_CASES)
def test_manifest_ebom_qty_outcomes_derived(ebom_rows, expected, excluded):
    """Covers ST-04-UT-110 and ST-04-UT-111 (unspecified part numbers excluded)."""
    schematic = Counter(s.part_number for s in MODIFIED_COMPONENTS)
    ebom = Counter()
    for row in ebom_rows:
        ebom[row.part_number] += row.quantity
    derived = {
        (pn, count, ebom[pn], Status.PASS if ebom[pn] == count else Status.FAIL)
        for pn, count in schematic.items()
        if pn not in excluded
    }
    assert expected
    assert derived == set(expected)


def test_expected_ebom_qty_mismatch_excludes_unspecified_parts():
    """Covers ST-04-UT-086: PN-CAP-001 and PN-CAP-999 are not asserted on quantity."""
    parts = {row[0] for row in EXPECTED_EBOM_QTY_MISMATCH}
    assert parts
    assert "PN-CAP-001" not in parts
    assert "PN-CAP-999" not in parts
