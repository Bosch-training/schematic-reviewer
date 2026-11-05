"""Tests for the reference designator parser (ST-09)."""

import logging

import pytest

from extraction.ref_des import find_ref_des

# Rows whose act is a single find_ref_des(text) call and whose expected result is a list.
RESULT_CASES = [
    # Positive
    pytest.param("R101", ["R101"], id="UT-001"),
    pytest.param("C201", ["C201"], id="UT-002"),
    pytest.param("U101", ["U101"], id="UT-003"),
    pytest.param(
        "Replace R101 with C201 near U101", ["R101", "C201", "U101"], id="UT-007"
    ),
    pytest.param("(R101)", ["R101"], id="UT-027"),
    pytest.param("R101,", ["R101"], id="UT-028"),
    pytest.param("R101.", ["R101"], id="UT-029"),
    pytest.param("R101-R105", ["R101", "R105"], id="UT-030"),
    pytest.param("R101/R102", ["R101", "R102"], id="UT-031"),
    pytest.param("NET-R101", ["R101"], id="UT-032"),
    # Negative
    pytest.param("10K", [], id="UT-004"),
    pytest.param("4.7K", [], id="UT-005"),
    pytest.param("100nF", [], id="UT-006"),
    pytest.param("change value to 4.7K", [], id="UT-011"),
    pytest.param("R101A", [], id="UT-018"),
    pytest.param("xR101", [], id="UT-019"),
    pytest.param("1R101", [], id="UT-020"),
    pytest.param("R_101", [], id="UT-021"),
    pytest.param("AB1234X", [], id="UT-022"),
    pytest.param("R1.5", [], id="UT-033"),
    pytest.param("U101.1", [], id="UT-034"),
    pytest.param("V3.3V", [], id="UT-035"),
    pytest.param("R", [], id="UT-039"),
    pytest.param("ABC", [], id="UT-040"),
    pytest.param("R\u0661\u0662\u0663", [], id="UT-041"),
    pytest.param("\uff32101", [], id="UT-045"),
    # Boundary
    pytest.param("", [], id="UT-012"),
    pytest.param("R1", ["R1"], id="UT-015"),
    pytest.param("RRR1", ["RRR1"], id="UT-016"),
    pytest.param("RRRR1", [], id="UT-017"),
    pytest.param("R101.12", [], id="UT-036"),
    pytest.param("R101.A", ["R101"], id="UT-037"),
    pytest.param("R007", ["R007"], id="UT-046"),
    pytest.param("R0", ["R0"], id="UT-047"),
    pytest.param("R1234567890", ["R1234567890"], id="UT-048"),
    pytest.param(
        " ".join(f"R{i}" for i in range(1, 51)),
        [f"R{i}" for i in range(1, 51)],
        id="UT-051",
    ),
    # Edge
    pytest.param("U1 R2 C3", ["U1", "R2", "C3"], id="UT-008"),
    pytest.param("R101 and R101, then C1 R101", ["R101", "C1"], id="UT-009"),
    pytest.param("R1 R01 R1", ["R1", "R01"], id="UT-010"),
    pytest.param("r101 R102 c201 C201", ["R102", "C201"], id="UT-014"),
    pytest.param("XR101", ["XR101"], id="UT-026"),
    pytest.param("R101R102", [], id="UT-023"),
    pytest.param("R101_", [], id="UT-024"),
    pytest.param("_R101", [], id="UT-025"),
    pytest.param("R101.\u0665", ["R101"], id="UT-038"),
    pytest.param("R101\u00e9", ["R101"], id="UT-042"),
    pytest.param("R101\u0661", ["R101"], id="UT-043"),
    pytest.param("\u00e9R101", ["R101"], id="UT-044"),
    pytest.param("R101\nPN: 123\nC201", ["R101", "C201"], id="UT-049"),
    pytest.param("R101\tC201\r\nU1", ["R101", "C201", "U1"], id="UT-050"),
    pytest.param(
        "ECN12 USB2 LM358 C0603", ["ECN12", "USB2", "LM358", "C0603"], id="UT-052"
    ),
]

# Rows whose act is find_ref_des(<non-str>) and whose expected result is TypeError.
TYPE_ERROR_CASES = [
    pytest.param(None, id="UT-054"),
    pytest.param(123, id="UT-055"),
    pytest.param(b"R1", id="UT-056"),
]

# Rows whose act is two calls with lowercase input; each must return [].
LOWERCASE_CASES = [
    pytest.param("r101", id="UT-013a"),
    pytest.param("c201", id="UT-013b"),
]


@pytest.mark.parametrize("text, expected", RESULT_CASES)
def test_find_ref_des_returns_expected_designators(text, expected):
    """Covers UT-001 to UT-052: list result, order, de-duplication and token boundaries."""
    assert find_ref_des(text) == expected


@pytest.mark.parametrize("text", LOWERCASE_CASES)
def test_find_ref_des_lowercase_designator_no_match(text):
    """Covers UT-013: lowercase designators are not matched (L1)."""
    assert find_ref_des(text) == []


@pytest.mark.parametrize("value", TYPE_ERROR_CASES)
def test_find_ref_des_non_str_raises_type_error(value):
    """Covers UT-054 to UT-056: non-str input raises TypeError (L5)."""
    with pytest.raises(TypeError):
        find_ref_des(value)


def test_find_ref_des_type_error_message_omits_value():
    """Covers UT-057: TypeError names the type and does not echo the input (NFR-07)."""
    with pytest.raises(TypeError) as excinfo:
        find_ref_des(b"R101-confidential")
    message = str(excinfo.value)
    assert "bytes" in message
    assert "R101" not in message
    assert "confidential" not in message


def test_find_ref_des_repeated_calls_are_equal():
    """Covers UT-053: repeated calls with the same input return equal results."""
    first = find_ref_des("U1 R2 C3 R2")
    second = find_ref_des("U1 R2 C3 R2")
    assert first == second == ["U1", "R2", "C3"]


def test_find_ref_des_success_does_not_log_content(caplog):
    """Covers UT-058: a successful call emits no log records (NFR-07)."""
    caplog.set_level(logging.DEBUG)
    find_ref_des("R101 confidential note")
    assert len(caplog.records) == 0


def test_find_ref_des_type_error_does_not_log_content(caplog):
    """Covers UT-059: a TypeError path emits no log records (NFR-07)."""
    caplog.set_level(logging.DEBUG)
    with pytest.raises(TypeError):
        find_ref_des(None)
    assert len(caplog.records) == 0
