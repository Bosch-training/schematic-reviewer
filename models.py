"""Shared enums and data models used by all modules (ST-02)."""

from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    PASS = "Pass"
    FAIL = "Fail"
    UNABLE_TO_VERIFY = "Unable to Verify"


class Category(str, Enum):
    COMPONENT = "Component"
    VALUE = "Value"
    PART_NUMBER = "Part number"
    EBOM = "EBOM"
    CONNECTIVITY = "Connectivity"
    UNINTENDED_CHANGE = "Unintended change"


class ChangeType(str, Enum):
    ADD = "Add"
    REMOVE = "Remove"
    REPLACE = "Replace"
    VALUE_CHANGE = "Value change"
    PART_NUMBER_CHANGE = "Part-number change"


class Decision(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    REQUIRES_INVESTIGATION = "Requires Investigation"


class Annotation(BaseModel):
    text: str
    page: int
    component_ref: str | None = None


class ChangeRequestItem(BaseModel):
    id: str
    change_type: ChangeType | None = None
    component_ref: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    source_annotation: Annotation
    structured: bool = False


class Component(BaseModel):
    ref_des: str
    value: str | None = None
    part_number: str | None = None
    description: str | None = None
    page: int


class EbomEntry(BaseModel):
    ref_des: str
    part_number: str | None = None
    description: str | None = None
    quantity: int | None = None


class Finding(BaseModel):
    id: str
    change_request_ref: str | None = None
    category: Category
    schematic_ref: str | None = None
    expected: str | None = None
    observed: str | None = None
    status: Status
    severity: str | None = None
    evidence: str | None = None
    reviewer_decision: Decision = Decision.PENDING
    reviewer_comment: str | None = None


class ReviewSession(BaseModel):
    id: str
    input_names: list[str] = Field(default_factory=list)
    change_items: list[ChangeRequestItem] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    overall_decision: Decision = Decision.PENDING
