# CSV Format

UTF-8, header row, comma delimiter, one case per row, no blank rows, no newlines inside fields (separate items with `; `). Quote fields containing a comma or quote, doubling inner quotes. All fields non-empty. The validator enforces this.

| Column | Content |
|---|---|
| `test_id` | `<ID>-UT-001`, sequential, unique |
| `story_id` | Story ID matching `test_id` |
| `unit_under_test` | Module path and function or class, e.g. `models.Finding` |
| `case_type` | `positive`, `negative`, `boundary` or `edge` |
| `scenario` | One-line behaviour |
| `preconditions` | State before the call, or `none` |
| `mocked_dependencies` | Each mock with its behaviour, or `none` |
| `input` | Exact synthetic values |
| `expected_result` | Observable outcome |
| `expected_status` | `Pass`, `Fail`, `Unable to Verify`, or `n/a` when the unit has no status |
| `source_ref` | LLD section and SRS, NFR or story acceptance ID |
| `suggested_test_name` | `test_<unit>_<behaviour>`, snake case, unique |

Example row:

```csv
ST-00-UT-002,ST-00,module.read,negative,Reader failure maps to Unable to Verify,none,"reader raises OSError","path 'missing.pdf'","finding status Unable to Verify",Unable to Verify,"LLD 5; SRS FR-00",test_read_oserror_unable_to_verify
```
