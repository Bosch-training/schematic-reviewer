# Software Requirements Specification (SRS)
## Automotive Electronics – Schematic Change Review MVP

**Document status:** Initial MVP baseline  
**Purpose:** One-day Software Development Life Cycle (SDLC) demonstration using GitHub Copilot  
**Domain:** Automotive electronic hardware  
**EDA source:** Zuken-generated schematic PDFs

---

## 1. Purpose

The system shall assist hardware engineers in reviewing a modified automotive electronic schematic against an annotated change request and the associated Engineering Bill of Materials (EBOM).

The system shall identify whether requested changes have been implemented, detect unintended modifications, reconcile component information with the EBOM, and produce an evidence-based engineering review report for mandatory human approval.

This is a demonstration MVP, not a production-certified engineering verification tool.

## 2. Scope

### 2.1 In scope

- Ingest the original schematic PDF containing change request comments/annotations.
- Ingest the modified schematic PDF.
- Ingest the EBOM Excel workbook.
- Extract available schematic text, component references, values, annotations and other relevant information.
- Compare the original and modified schematic content, even when page layouts, component positions, or page counts change.
- Validate requested component changes and identify unintended component changes.
- Validate electrical connectivity to the extent supported by the available source data.
- Reconcile component information between the modified schematic and EBOM.
- Generate detailed findings with evidence and schematic page/component references.
- Require an engineer to review and approve or reject the review outcome.

### 2.2 Out of scope for this MVP

- AI-based interpretation of ambiguous or descriptive engineering comments.
- Direct integration with the Zuken application or its APIs.
- Writing changes back into Zuken design files.
- Automated design correction or schematic generation.
- Full electrical rule checking (ERC), simulation, signal-integrity analysis or functional safety assessment.
- Production release authorization or replacement of the organization's formal engineering change process.
- Certification or claims of compliance with automotive standards.

## 3. Users and roles

| Role | Responsibility |
|---|---|
| Hardware Engineer / Requestor | Supplies the source documents and change request. |
| Reviewer | Examines automated findings and supporting evidence. |
| Approver | Records final approval or rejection of the review. |

For the demonstration, these roles may be represented by a single user.

## 4. Inputs

| Input | Format | Description |
|---|---|---|
| Original schematic and change request | Native/vector PDF | Original Zuken-generated schematic PDF containing comments/annotations that describe requested changes. |
| Modified schematic | Native/vector PDF | Updated schematic PDF produced after implementing the requested changes. |
| EBOM | XLSX | Engineering Bill of Materials containing component reference designators that map to the schematic. |

### 4.1 Known input characteristics

- Schematic PDFs are expected to be native/vector PDFs, not scanned documents.
- The source EDA tool is Zuken.
- Change request comments may contain explicit instructions or descriptive engineering language.
- Change request annotations always identify the affected schematic page and/or component reference.
- The schematic may be reorganized: page count, page layout and component positions may change.
- EBOM contains component reference designators such as `R101`, `C201` and `U101`.

### 4.2 Input validation

The system should:

- Validate file type and readability.
- Confirm that all required input files are supplied.
- Report missing, unsupported, password-protected or unreadable files.
- Identify whether expected annotations can be extracted from the original PDF.
- Identify whether the EBOM contains the expected reference-designator and component data fields.
- Avoid treating missing or unextractable information as a successful validation.

## 5. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The system shall allow the user to upload the original annotated schematic PDF. | Must |
| FR-02 | The system shall allow the user to upload the modified schematic PDF. | Must |
| FR-03 | The system shall allow the user to upload the EBOM XLSX workbook. | Must |
| FR-04 | The system shall extract available PDF annotations/comments and their page references. | Must |
| FR-05 | The system shall extract available schematic information, including component reference designators, values, part numbers, net names and pin connectivity where present and extractable. | Must |
| FR-06 | The system shall parse relevant EBOM fields, including reference designator, part number, description and quantity where available. | Must |
| FR-07 | The system shall identify differences between the original and modified schematics without relying solely on page position or component coordinates. | Must |
| FR-08 | The system shall assess whether each requested component addition, removal, replacement, value change or part-number change is reflected in the modified schematic. | Must |
| FR-09 | The system shall validate relevant connectivity changes, including net names, component pin-to-net connections, pin-to-pin connectivity and potential unintended disconnections or shorts, when sufficient structured information is available. | Must |
| FR-10 | The system shall reconcile modified schematic component references and applicable component attributes against the EBOM. | Must |
| FR-11 | The system shall identify potentially unintended component or design changes between the original and modified schematics. | Must |
| FR-12 | The system shall generate a review report containing findings, evidence and schematic page/component references. | Must |
| FR-13 | The system shall allow an engineer to review findings and record approval or rejection. | Must |
| FR-14 | The system should distinguish confirmed failures from items that cannot be verified because of insufficient or unavailable source data. | Should |

### 5.1 Component validation details

The review shall consider:

- Component reference designator.
- Component presence or absence.
- Component value.
- Manufacturer part number, where available.
- Component description, where available.
- Component quantity, where applicable.
- Additions, removals, replacements and modifications.

Example:

**Change request:** Replace `R101` from `10K` to `4.7K`.

The review should check:

1. Whether `R101` exists in the modified schematic.
2. Whether its value is `4.7K`.
3. Whether its connectivity remains unchanged unless the change request also requests a connectivity modification.
4. Whether the corresponding EBOM entry reflects the applicable updated component information.

### 5.2 Connectivity validation details

The review scope includes:

- Net-name changes.
- Component pin-to-net mapping.
- Pin-to-pin connectivity.
- Potential unintended disconnections or shorts.

**Technical constraint:** A vector PDF is not guaranteed to contain enough semantic information to reconstruct a complete electrical netlist. Visual PDF comparison alone must not be represented as definitive electrical connectivity verification.

For reliable connectivity validation, a structured netlist or equivalent connectivity export from Zuken is recommended as an optional engineering input/enhancement. If the required connectivity information cannot be extracted or supplied, the system shall report the relevant checks as **Unable to Verify** and route them for engineering review.

### 5.3 Change interpretation

For the MVP:

- Extract and present the available comments/annotations.
- Capture their page and component references.
- Support explicit instructions that can be mapped to structured checks.
- Allow an engineer to clarify or structure descriptive instructions before validation.
- Do not silently infer ambiguous engineering intent.

**Future enhancement:** AI-assisted interpretation of natural-language comments, with engineer confirmation of the interpreted change before validation.

## 6. Review findings and report

Each finding should contain, where applicable:

| Field | Description |
|---|---|
| Finding ID | Unique identifier for the finding. |
| Change request reference | Related annotation or change request item. |
| Finding category | Component, value, part number, EBOM, connectivity or unintended change. |
| Schematic reference | Page and component/net/pin reference, where available. |
| Expected result | What the change request or comparison expects. |
| Observed result | What was extracted from the modified schematic or EBOM. |
| Status | Pass, Fail or Unable to Verify. |
| Severity | Suggested impact classification for engineering review. |
| Evidence | Relevant extracted text, comparison detail or source-page reference. |
| Reviewer decision | Pending, Approved, Rejected or Requires Investigation. |
| Reviewer comments | Optional explanation or disposition. |

The report should include:

- Input document names.
- Review summary and counts by status.
- Requested-change validation results.
- Unintended-change findings.
- EBOM reconciliation findings.
- Connectivity findings and verification limitations.
- Evidence and source references.
- Engineer review and approval outcome.

**Report format:** PDF or Excel is a recommended implementation choice; the final format can be selected during implementation.

## 7. Review and approval workflow

1. User uploads the original annotated schematic, modified schematic and EBOM.
2. System validates the input files.
3. System extracts available annotations, schematic information and EBOM data.
4. System identifies and structures reviewable change requests.
5. System compares original and modified schematic information.
6. System validates requested changes, unintended changes, EBOM consistency and supported connectivity checks.
7. System generates findings and the review report.
8. Engineer reviews the findings and evidence.
9. Engineer records approval, rejection or a request for further investigation.

Automated findings are advisory until reviewed by an authorized engineer. The system shall not represent an unverified result as an approved engineering change.

## 8. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | The system should use a modular design so document extraction, comparison, validation and reporting can be developed and tested independently. |
| NFR-02 | The system shall provide clear error messages for invalid, missing or unsupported inputs. |
| NFR-03 | The system shall preserve traceability from a finding to its source document, page and change request item where available. |
| NFR-04 | The system shall distinguish Pass, Fail and Unable to Verify outcomes. |
| NFR-05 | The system should record reviewer decisions and comments. |
| NFR-06 | The system should avoid silently discarding extraction or validation errors. |
| NFR-07 | The system should protect uploaded engineering documents from unauthorized access. |
| NFR-08 | The system should maintain consistent results for identical inputs and validation rules. |

Performance targets, supported file-size limits, user concurrency and retention periods are not yet specified. They should not be invented for this demonstration.

## 9. Acceptance criteria

The MVP demonstration is successful when:

1. The user can upload all three required input files.
2. The system can extract the available annotations from the original schematic PDF.
3. The system can parse the relevant EBOM fields and map entries by reference designator.
4. The system can demonstrate at least one requested component change being correctly identified as implemented.
5. The system can demonstrate at least one requested change being identified as missing or incorrectly implemented.
6. The system can identify at least one unintended modification in the demonstration dataset.
7. The system can demonstrate EBOM reconciliation for component references and applicable attributes.
8. The system can report connectivity results when structured connectivity data is available, or explicitly mark unsupported checks as Unable to Verify.
9. The system generates a report with findings and traceable evidence.
10. An engineer can record an approval or rejection.

## 10. Assumptions and recommendations

These are implementation recommendations, not additional confirmed business requirements.

- Use a small, controlled demonstration dataset with known expected outcomes.
- Include representative examples of component addition, removal, replacement, value change and connectivity change.
- Include at least one page/layout change to demonstrate that comparison is not based only on visual coordinates.
- Use a Zuken-exported netlist or equivalent structured connectivity data for the connectivity demonstration if available.
- If structured connectivity data is unavailable, demonstrate the Unable to Verify path rather than claiming complete connectivity validation.
- Keep extraction and validation deterministic for the MVP.
- Use AI-assisted interpretation as a later enhancement, not as a dependency for the initial demonstration.
- Treat severity and confidence classifications as reviewer aids; define their detailed rules only when agreed by the engineering team.

## 11. Future enhancements

- AI-assisted interpretation of descriptive and ambiguous change request comments.
- Direct ingestion of structured Zuken exports.
- More robust schematic semantic comparison and symbol/net recognition.
- Configurable engineering validation rules.
- Integration with PLM, requirements management or engineering change management systems.
- Role-based access, audit history and controlled report release.
- Expanded electrical design checks and formal verification integrations.

## 12. One-day GitHub Copilot SDLC demonstration plan

| Stage | Demonstration activity | Expected artifact |
|---|---|---|
| 1. Requirement analysis | Review this SRS, identify actors, scope, assumptions and acceptance criteria. | Reviewed requirements |
| 2. Design | Define modules, data models and processing workflow. | Architecture/design notes |
| 3. Implementation | Build upload, extraction, basic comparison, EBOM reconciliation and report workflow. | Working MVP |
| 4. Testing | Test valid inputs, missing files, expected changes, unintended changes and unverifiable connectivity. | Test cases and results |
| 5. Review | Inspect generated findings and evidence; record engineer decision. | Review report and approval state |
| 6. Demonstration | Walk through one representative change request end to end. | Demonstrable SDLC outcome |

The one-day target is a demonstrable prototype using a controlled dataset. It is not a commitment to deliver complete Zuken PDF semantic extraction or production-grade electrical verification in one day.

---

## 13. Open implementation decisions

The following are intentionally left open rather than assumed:

- Whether the demonstration dataset will include a structured Zuken netlist export.
- Which exact EBOM column names and worksheet structure will be used.
- Which PDF annotation types must be supported.
- Whether the generated report will be PDF, Excel or both.
- Which technology stack and deployment approach will be used.

These decisions can be finalized during design and implementation without changing the agreed business objective.
