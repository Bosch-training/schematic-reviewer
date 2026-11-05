"""Tests for shared data models (ST-02)."""

import json

import pytest
from pydantic import ValidationError

from models import (
    Annotation,
    Category,
    ChangeRequestItem,
    ChangeType,
    Component,
    Decision,
    EbomEntry,
    Finding,
    ReviewSession,
    Status,
)

ENUM_VALUE_CASES = [
    pytest.param(Status, ["Pass", "Fail", "Unable to Verify"], id="ST-02-UT-001"),
    pytest.param(
        Category,
        [
            "Component",
            "Value",
            "Part number",
            "EBOM",
            "Connectivity",
            "Unintended change",
        ],
        id="ST-02-UT-004",
    ),
    pytest.param(
        ChangeType,
        ["Add", "Remove", "Replace", "Value change", "Part-number change"],
        id="ST-02-UT-006",
    ),
    pytest.param(
        Decision,
        ["Pending", "Approved", "Rejected", "Requires Investigation"],
        id="ST-02-UT-009",
    ),
]

ENUM_NAME_CASES = [
    pytest.param(Status, ["PASS", "FAIL", "UNABLE_TO_VERIFY"], id="ST-02-UT-002"),
    pytest.param(
        ChangeType,
        ["ADD", "REMOVE", "REPLACE", "VALUE_CHANGE", "PART_NUMBER_CHANGE"],
        id="ST-02-UT-007",
    ),
    pytest.param(
        Decision,
        ["PENDING", "APPROVED", "REJECTED", "REQUIRES_INVESTIGATION"],
        id="ST-02-UT-010",
    ),
]

ENUM_COUNT_CASES = [
    pytest.param(Status, 3, id="ST-02-UT-003"),
    pytest.param(Category, 6, id="ST-02-UT-005"),
    pytest.param(ChangeType, 5, id="ST-02-UT-008"),
    pytest.param(Decision, 4, id="ST-02-UT-011"),
]

ENUM_STR_CASES = [
    pytest.param(Status.PASS, "Pass", id="ST-02-UT-012-Status"),
    pytest.param(Category.EBOM, "EBOM", id="ST-02-UT-012-Category"),
    pytest.param(ChangeType.ADD, "Add", id="ST-02-UT-012-ChangeType"),
    pytest.param(Decision.PENDING, "Pending", id="ST-02-UT-012-Decision"),
]

NO_SOURCE_DOCUMENT_CASES = [
    pytest.param(Annotation, id="ST-02-UT-059-Annotation"),
    pytest.param(Component, id="ST-02-UT-059-Component"),
    pytest.param(EbomEntry, id="ST-02-UT-059-EbomEntry"),
    pytest.param(Finding, id="ST-02-UT-059-Finding"),
]

CONSTRUCT_CASES = [
    pytest.param(
        Annotation,
        {"text": "Replace R1 with 10k", "page": 1},
        {"text": "Replace R1 with 10k", "page": 1, "component_ref": None},
        id="ST-02-UT-013",
    ),
    pytest.param(
        Annotation,
        {"text": "Replace R1 with 10k", "page": 2, "component_ref": "R1"},
        {"text": "Replace R1 with 10k", "page": 2, "component_ref": "R1"},
        id="ST-02-UT-014",
    ),
    pytest.param(
        Annotation,
        {"text": "note", "page": 0},
        {"text": "note", "page": 0},
        id="ST-02-UT-019",
    ),
    pytest.param(
        Annotation,
        {"text": "", "page": 1, "component_ref": ""},
        {"text": "", "component_ref": ""},
        id="ST-02-UT-020",
    ),
    pytest.param(
        Annotation,
        {"text": "  Ω 10kΩ ±1%  ", "page": 1},
        {"text": "  Ω 10kΩ ±1%  "},
        id="ST-02-UT-021",
    ),
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-1", "source_annotation": {"text": "t", "page": 1}},
        {
            "change_type": None,
            "component_ref": None,
            "old_value": None,
            "new_value": None,
            "structured": False,
        },
        id="ST-02-UT-024",
    ),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "change_type": None,
            "source_annotation": {"text": "t", "page": 1},
        },
        {"change_type": None},
        id="ST-02-UT-030",
    ),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "structured": True,
            "change_type": None,
            "source_annotation": {"text": "t", "page": 1},
        },
        {"structured": True, "change_type": None},
        id="ST-02-UT-031",
    ),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "structured": False,
            "change_type": "Add",
            "source_annotation": {"text": "t", "page": 1},
        },
        {"structured": False, "change_type": ChangeType.ADD},
        id="ST-02-UT-032",
    ),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "old_value": "",
            "new_value": "",
            "source_annotation": {"text": "t", "page": 1},
        },
        {"old_value": "", "new_value": ""},
        id="ST-02-UT-036",
    ),
    pytest.param(
        Component,
        {"ref_des": "R1", "page": 1},
        {"value": None, "part_number": None, "description": None},
        id="ST-02-UT-040",
    ),
    pytest.param(
        Component,
        {
            "ref_des": "R1",
            "value": "10k",
            "part_number": "P-100",
            "description": "Resistor",
            "page": 2,
        },
        {
            "ref_des": "R1",
            "value": "10k",
            "part_number": "P-100",
            "description": "Resistor",
            "page": 2,
        },
        id="ST-02-UT-041",
    ),
    pytest.param(
        Component,
        {
            "ref_des": "R1",
            "value": "",
            "part_number": "",
            "description": "",
            "page": 1,
        },
        {"value": "", "part_number": "", "description": ""},
        id="ST-02-UT-045",
    ),
    pytest.param(
        EbomEntry,
        {"ref_des": "R1"},
        {"part_number": None, "description": None, "quantity": None},
        id="ST-02-UT-048",
    ),
    pytest.param(
        EbomEntry,
        {
            "ref_des": "R1",
            "part_number": "P-100",
            "description": "Resistor",
            "quantity": 2,
        },
        {
            "ref_des": "R1",
            "part_number": "P-100",
            "description": "Resistor",
            "quantity": 2,
        },
        id="ST-02-UT-049",
    ),
    pytest.param(
        EbomEntry,
        {"ref_des": "R1", "quantity": 0},
        {"quantity": 0},
        id="ST-02-UT-052",
    ),
    pytest.param(
        EbomEntry,
        {"ref_des": "R1", "quantity": None},
        {"quantity": None},
        id="ST-02-UT-053",
    ),
    pytest.param(
        EbomEntry,
        {"ref_des": "R1", "part_number": "", "description": ""},
        {"part_number": "", "description": ""},
        id="ST-02-UT-056",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM", "status": "Pass"},
        {
            "reviewer_decision": Decision.PENDING,
            "severity": None,
            "reviewer_comment": None,
            "change_request_ref": None,
            "schematic_ref": None,
            "expected": None,
            "observed": None,
            "evidence": None,
        },
        id="ST-02-UT-060",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "status": Status.FAIL, "category": Category.VALUE},
        {"status": Status.FAIL, "category": Category.VALUE},
        id="ST-02-UT-072",
    ),
    pytest.param(
        Finding,
        {
            "id": "F-1",
            "category": "EBOM",
            "status": "Pass",
            "reviewer_comment": "Checked against drawing",
        },
        {"reviewer_comment": "Checked against drawing"},
        id="ST-02-UT-076",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM", "status": "Pass", "severity": "High"},
        {"severity": "High"},
        id="ST-02-UT-077",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "Value", "status": "Pass"},
        {"evidence": None},
        id="ST-02-UT-078",
    ),
    pytest.param(
        Finding,
        {
            "id": "F-1",
            "category": "EBOM",
            "status": "Pass",
            "change_request_ref": "",
            "schematic_ref": "",
            "expected": "",
            "observed": "",
            "evidence": "",
        },
        {
            "change_request_ref": "",
            "schematic_ref": "",
            "expected": "",
            "observed": "",
            "evidence": "",
        },
        id="ST-02-UT-079",
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1"},
        {
            "input_names": [],
            "change_items": [],
            "findings": [],
            "overall_decision": Decision.PENDING,
        },
        id="ST-02-UT-086",
    ),
]

NEGATIVE_CASES = [
    pytest.param(Annotation, {"text": "note"}, id="ST-02-UT-015"),
    pytest.param(Annotation, {"page": 1}, id="ST-02-UT-016"),
    pytest.param(Annotation, {"text": None, "page": 1}, id="ST-02-UT-017"),
    pytest.param(Annotation, {"text": "note", "page": "abc"}, id="ST-02-UT-018"),
    pytest.param(
        ChangeRequestItem,
        {"source_annotation": {"text": "t", "page": 1}},
        id="ST-02-UT-025",
    ),
    pytest.param(ChangeRequestItem, {"id": "CR-1"}, id="ST-02-UT-026"),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "change_type": "add",
            "source_annotation": {"text": "t", "page": 1},
        },
        id="ST-02-UT-028",
    ),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "change_type": "Part number change",
            "source_annotation": {"text": "t", "page": 1},
        },
        id="ST-02-UT-029",
    ),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "structured": "maybe",
            "source_annotation": {"text": "t", "page": 1},
        },
        id="ST-02-UT-033",
    ),
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-1", "source_annotation": {"text": "t"}},
        id="ST-02-UT-035",
    ),
    pytest.param(Component, {"page": 1}, id="ST-02-UT-042"),
    pytest.param(Component, {"ref_des": "R1"}, id="ST-02-UT-043"),
    pytest.param(Component, {"ref_des": None, "page": 1}, id="ST-02-UT-044"),
    pytest.param(EbomEntry, {"part_number": "P-100"}, id="ST-02-UT-050"),
    pytest.param(EbomEntry, {"ref_des": None}, id="ST-02-UT-051"),
    pytest.param(EbomEntry, {"ref_des": "R1", "quantity": 1.5}, id="ST-02-UT-054"),
    pytest.param(EbomEntry, {"ref_des": "R1", "quantity": "abc"}, id="ST-02-UT-055"),
    pytest.param(Finding, {"id": "F-1", "category": "EBOM"}, id="ST-02-UT-061"),
    pytest.param(Finding, {"id": "F-1", "status": "Pass"}, id="ST-02-UT-062"),
    pytest.param(Finding, {"category": "EBOM", "status": "Pass"}, id="ST-02-UT-063"),
    pytest.param(
        Finding, {"id": "F-1", "category": "EBOM", "status": "pass"}, id="ST-02-UT-064"
    ),
    pytest.param(
        Finding, {"id": "F-1", "category": "EBOM", "status": "Maybe"}, id="ST-02-UT-065"
    ),
    pytest.param(
        Finding, {"id": "F-1", "category": "EBOM", "status": None}, id="ST-02-UT-066"
    ),
    pytest.param(
        Finding, {"id": "F-1", "category": "EBOM", "status": " Pass"}, id="ST-02-UT-067"
    ),
    pytest.param(
        Finding, {"id": "F-1", "category": "EBOM", "status": ""}, id="ST-02-UT-068"
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "component", "status": "Pass"},
        id="ST-02-UT-069",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM", "status": "Pass", "reviewer_decision": ""},
        id="ST-02-UT-073",
    ),
    pytest.param(
        Finding,
        {
            "id": "F-1",
            "category": "EBOM",
            "status": "Pass",
            "reviewer_decision": "approved",
        },
        id="ST-02-UT-074",
    ),
    pytest.param(ReviewSession, {}, id="ST-02-UT-087"),
    pytest.param(
        ReviewSession, {"id": "s1", "overall_decision": "Done"}, id="ST-02-UT-091"
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1", "findings": [{"id": "F-1", "category": "EBOM"}]},
        id="ST-02-UT-093",
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1", "change_items": [{"id": "CR-1"}]},
        id="ST-02-UT-094",
    ),
    pytest.param(ReviewSession, {"id": "s1", "findings": None}, id="ST-02-UT-095"),
    pytest.param(
        ReviewSession, {"id": "s1", "input_names": "x.pdf"}, id="ST-02-UT-096"
    ),
]

ENUM_ACCEPT_CASES = [
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-1", "source_annotation": {"text": "t", "page": 1}},
        "change_type",
        ChangeType,
        "Add",
        id="ST-02-UT-027-Add",
    ),
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-1", "source_annotation": {"text": "t", "page": 1}},
        "change_type",
        ChangeType,
        "Remove",
        id="ST-02-UT-027-Remove",
    ),
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-1", "source_annotation": {"text": "t", "page": 1}},
        "change_type",
        ChangeType,
        "Replace",
        id="ST-02-UT-027-Replace",
    ),
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-1", "source_annotation": {"text": "t", "page": 1}},
        "change_type",
        ChangeType,
        "Value change",
        id="ST-02-UT-027-Value change",
    ),
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-1", "source_annotation": {"text": "t", "page": 1}},
        "change_type",
        ChangeType,
        "Part-number change",
        id="ST-02-UT-027-Part-number change",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "status": "Pass"},
        "category",
        Category,
        "Component",
        id="ST-02-UT-070-Component",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "status": "Pass"},
        "category",
        Category,
        "Value",
        id="ST-02-UT-070-Value",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "status": "Pass"},
        "category",
        Category,
        "Part number",
        id="ST-02-UT-070-Part number",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "status": "Pass"},
        "category",
        Category,
        "EBOM",
        id="ST-02-UT-070-EBOM",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "status": "Pass"},
        "category",
        Category,
        "Connectivity",
        id="ST-02-UT-070-Connectivity",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "status": "Pass"},
        "category",
        Category,
        "Unintended change",
        id="ST-02-UT-070-Unintended change",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM"},
        "status",
        Status,
        "Pass",
        id="ST-02-UT-071-Pass",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM"},
        "status",
        Status,
        "Fail",
        id="ST-02-UT-071-Fail",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM"},
        "status",
        Status,
        "Unable to Verify",
        id="ST-02-UT-071-Unable to Verify",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM", "status": "Pass"},
        "reviewer_decision",
        Decision,
        "Pending",
        id="ST-02-UT-075-Pending",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM", "status": "Pass"},
        "reviewer_decision",
        Decision,
        "Approved",
        id="ST-02-UT-075-Approved",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM", "status": "Pass"},
        "reviewer_decision",
        Decision,
        "Rejected",
        id="ST-02-UT-075-Rejected",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "EBOM", "status": "Pass"},
        "reviewer_decision",
        Decision,
        "Requires Investigation",
        id="ST-02-UT-075-Requires Investigation",
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1"},
        "overall_decision",
        Decision,
        "Pending",
        id="ST-02-UT-092-Pending",
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1"},
        "overall_decision",
        Decision,
        "Approved",
        id="ST-02-UT-092-Approved",
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1"},
        "overall_decision",
        Decision,
        "Rejected",
        id="ST-02-UT-092-Rejected",
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1"},
        "overall_decision",
        Decision,
        "Requires Investigation",
        id="ST-02-UT-092-Requires Investigation",
    ),
]

ROUND_TRIP_CASES = [
    pytest.param(
        Annotation,
        {"text": "t", "page": 3, "component_ref": "C5"},
        id="ST-02-UT-022",
    ),
    pytest.param(Annotation, {"text": "t", "page": 3}, id="ST-02-UT-023"),
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "change_type": "Value change",
            "component_ref": "R1",
            "old_value": "1k",
            "new_value": "10k",
            "structured": True,
            "source_annotation": {"text": "t", "page": 1},
        },
        id="ST-02-UT-037",
    ),
    pytest.param(
        ChangeRequestItem,
        {"id": "CR-2", "source_annotation": {"text": "t", "page": 1}},
        id="ST-02-UT-038",
    ),
    pytest.param(
        Component,
        {
            "ref_des": "R1",
            "value": "10k",
            "part_number": "P-100",
            "description": "Resistor",
            "page": 2,
        },
        id="ST-02-UT-046",
    ),
    pytest.param(Component, {"ref_des": "R1", "page": 1}, id="ST-02-UT-047"),
    pytest.param(
        EbomEntry,
        {
            "ref_des": "R1",
            "part_number": "P-100",
            "description": "Resistor",
            "quantity": 2,
        },
        id="ST-02-UT-057",
    ),
    pytest.param(EbomEntry, {"ref_des": "R1"}, id="ST-02-UT-058"),
    pytest.param(
        Finding,
        {
            "id": "F-1",
            "change_request_ref": "CR-1",
            "category": "Part number",
            "schematic_ref": "p2 R1",
            "expected": "P-100",
            "observed": "P-200",
            "status": "Fail",
            "severity": "High",
            "evidence": "Annotation p1",
            "reviewer_decision": "Rejected",
            "reviewer_comment": "Wrong part",
        },
        id="ST-02-UT-081",
    ),
    pytest.param(
        Finding, {"id": "F-1", "category": "EBOM", "status": "Pass"}, id="ST-02-UT-082"
    ),
    pytest.param(
        Finding,
        {
            "id": "F-1",
            "category": "EBOM",
            "status": "Pass",
            "expected": "10kΩ ±1%",
            "observed": "4.7µF",
            "evidence": "Seite 2: Widerstand R1",
        },
        id="ST-02-UT-084",
    ),
    pytest.param(
        ReviewSession,
        {"id": "s1", "input_names": [], "change_items": [], "findings": []},
        id="ST-02-UT-098",
    ),
    pytest.param(
        ReviewSession,
        {
            "id": "s1",
            "input_names": ["a.pdf"],
            "change_items": [
                {"id": "CR-1", "source_annotation": {"text": "t", "page": 1}}
            ],
            "findings": [{"id": "F-1", "category": "EBOM", "status": "Pass"}],
        },
        id="ST-02-UT-099",
    ),
    pytest.param(
        ReviewSession,
        {
            "id": "s1",
            "findings": [
                {"id": f"F-{i:03d}", "category": "EBOM", "status": "Pass"}
                for i in range(1, 101)
            ],
        },
        id="ST-02-UT-100",
    ),
]

JSON_VALUE_CASES = [
    pytest.param(
        ChangeRequestItem,
        {
            "id": "CR-1",
            "change_type": ChangeType.VALUE_CHANGE,
            "source_annotation": {"text": "t", "page": 1},
        },
        {"change_type": "Value change"},
        id="ST-02-UT-039",
    ),
    pytest.param(
        Finding,
        {"id": "F-1", "category": "Unintended change", "status": "Fail"},
        {
            "status": "Fail",
            "category": "Unintended change",
            "reviewer_decision": "Pending",
        },
        id="ST-02-UT-085",
    ),
]

SHARED_DEFAULT_CASES = [
    pytest.param("input_names", "x.pdf", id="ST-02-UT-088"),
    pytest.param(
        "change_items",
        ChangeRequestItem(id="CR-1", source_annotation=Annotation(text="t", page=1)),
        id="ST-02-UT-089",
    ),
    pytest.param(
        "findings",
        Finding(id="F-1", category="EBOM", status="Pass"),
        id="ST-02-UT-090",
    ),
]


@pytest.mark.parametrize("enum_cls, expected_values", ENUM_VALUE_CASES)
def test_enum_values_match_wording(enum_cls, expected_values):
    """Covers ST-02-UT-001, 004, 006 and 009: enum values equal the documented wording."""
    assert [member.value for member in enum_cls] == expected_values


@pytest.mark.parametrize("enum_cls, expected_names", ENUM_NAME_CASES)
def test_enum_member_names_upper_snake_case(enum_cls, expected_names):
    """Covers ST-02-UT-002, 007 and 010: enum member names are upper snake case."""
    assert [member.name for member in enum_cls] == expected_names


@pytest.mark.parametrize("enum_cls, expected_count", ENUM_COUNT_CASES)
def test_enum_has_exact_member_count(enum_cls, expected_count):
    """Covers ST-02-UT-003, 005, 008 and 011: enums have no extra members."""
    assert len(list(enum_cls)) == expected_count


@pytest.mark.parametrize("member, expected_value", ENUM_STR_CASES)
def test_enums_are_str_subclasses(member, expected_value):
    """Covers ST-02-UT-012: each enum member is a str equal to its value."""
    assert isinstance(member, str)
    assert member == expected_value


@pytest.mark.parametrize("model", NO_SOURCE_DOCUMENT_CASES)
def test_models_have_no_source_document_field(model):
    """Covers ST-02-UT-059: no model defines a source_document field."""
    assert "source_document" not in model.model_fields


@pytest.mark.parametrize("model, kwargs, attrs", CONSTRUCT_CASES)
def test_model_builds_with_expected_attributes(model, kwargs, attrs):
    """Covers ST-02-UT-013, 014, 019-021, 024, 030-032, 036, 040, 041, 045, 048, 049,
    052, 053, 056, 060, 072, 076-079 and 086: valid input keeps the documented values."""
    obj = model(**kwargs)
    for name, value in attrs.items():
        assert getattr(obj, name) == value


@pytest.mark.parametrize("model, kwargs", NEGATIVE_CASES)
def test_model_rejects_invalid_input(model, kwargs):
    """Covers ST-02-UT-015-018, 025, 026, 028, 029, 033, 035, 042-044, 050, 051,
    054, 055, 061-069, 073, 074, 087, 091, 093-096: invalid input raises ValidationError."""
    with pytest.raises(ValidationError):
        model(**kwargs)


@pytest.mark.parametrize("model, base, field, enum_cls, value", ENUM_ACCEPT_CASES)
def test_enum_field_accepts_value_string(model, base, field, enum_cls, value):
    """Covers ST-02-UT-027, 070, 071, 075 and 092: each documented value string is accepted."""
    obj = model(**base, **{field: value})
    assert getattr(obj, field) is enum_cls(value)


@pytest.mark.parametrize("model, kwargs", ROUND_TRIP_CASES)
def test_json_round_trip_restores_equal_model(model, kwargs):
    """Covers ST-02-UT-022, 023, 037, 038, 046, 047, 057, 058, 081, 082, 084, 098-100:
    JSON round trip returns an equal model."""
    original = model(**kwargs)
    restored = model.model_validate_json(original.model_dump_json())
    assert restored == original


@pytest.mark.parametrize("model, kwargs, expected_json", JSON_VALUE_CASES)
def test_dumped_json_holds_value_strings(model, kwargs, expected_json):
    """Covers ST-02-UT-039 and 085: enums serialise to their value strings."""
    payload = json.loads(model(**kwargs).model_dump_json())
    for key, value in expected_json.items():
        assert payload[key] == value


@pytest.mark.parametrize("field, item", SHARED_DEFAULT_CASES)
def test_review_session_default_lists_not_shared(field, item):
    """Covers ST-02-UT-088, 089 and 090: default list fields are per-instance."""
    first = ReviewSession(id="a")
    second = ReviewSession(id="b")
    getattr(first, field).append(item)
    assert getattr(first, field) == [item]
    assert getattr(second, field) == []


def test_change_request_item_source_annotation_from_dict():
    item = ChangeRequestItem(id="CR-1", source_annotation={"text": "t", "page": 1})
    assert isinstance(item.source_annotation, Annotation)
    assert item.source_annotation.text == "t"
    assert item.source_annotation.page == 1


def test_finding_unable_to_verify_round_trip():
    original = Finding(id="F-1", category="Connectivity", status="Unable to Verify")
    restored = Finding.model_validate_json(original.model_dump_json())
    assert restored == original
    assert original.status.value == "Unable to Verify"
    assert "Unable to Verify" in original.model_dump_json()


def test_finding_invalid_status_json_raises():
    with pytest.raises(ValidationError):
        Finding.model_validate_json(
            '{"id": "F-1", "category": "EBOM", "status": "pass"}'
        )


def test_review_session_nested_json_round_trip():
    original = ReviewSession(
        id="s1",
        input_names=["orig.pdf", "mod.pdf", "ebom.xlsx"],
        change_items=[
            ChangeRequestItem(id="CR-1", source_annotation={"text": "t", "page": 1})
        ],
        findings=[Finding(id="F-1", category="EBOM", status="Pass")],
        overall_decision="Requires Investigation",
    )
    restored = ReviewSession.model_validate_json(original.model_dump_json())
    assert restored == original
    assert isinstance(restored.change_items[0], ChangeRequestItem)
    assert isinstance(restored.findings[0], Finding)


def test_review_session_input_names_order_preserved():
    session = ReviewSession(id="s1", input_names=["c.xlsx", "a.pdf", "b.pdf"])
    assert session.input_names == ["c.xlsx", "a.pdf", "b.pdf"]
    restored = ReviewSession.model_validate_json(session.model_dump_json())
    assert restored.input_names == ["c.xlsx", "a.pdf", "b.pdf"]
