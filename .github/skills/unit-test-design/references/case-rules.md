# Case Rules

Apply per unit; omit a category only where it cannot apply.

- **Positive:** every documented happy path, enum member, branch and default.
- **Negative:** invalid types; unknown enum values; missing required fields; malformed or unsupported input; dependency failure (mock raises the error the LLD names); unextractable data, which maps to `Unable to Verify`.
- **Boundary:** empty, one, many; min and max of documented ranges; first and last page; off-by-one at each documented limit; `None` versus empty string.
- **Edge:** duplicates; whitespace and case variants; Unicode; ordering; determinism on repeated calls; shared mutable defaults; serialization round trips.

`expected_result` must be checkable: a return value, exception type, finding fields, status, or a mock call assertion. Never "works correctly".
