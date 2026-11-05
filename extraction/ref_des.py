"""Reference designator parser (ST-09)."""

import re

_REF_DES = re.compile(r"(?<![A-Za-z0-9_])[A-Z]{1,3}[0-9]+(?![A-Za-z0-9_]|\.[0-9])")


def find_ref_des(text: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    return list(dict.fromkeys(_REF_DES.findall(text)))
