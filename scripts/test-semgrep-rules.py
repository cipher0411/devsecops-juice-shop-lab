#!/usr/bin/env python3
"""Unit-test the custom Semgrep rules in security/semgrep/lab-rules.yaml.

Reads Semgrep JSON (stdin) produced by scanning security/semgrep/fixtures
and compares it with the annotations in the fixtures:

    # ruleid: <rule-id>   -> the next line MUST be reported by <rule-id>
    # ok: <rule-id>       -> the next line MUST NOT be reported by <rule-id>

Exit code 0 when every expectation holds, 1 otherwise.
"""
import json
import pathlib
import re
import sys

FIXTURES = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "security/semgrep/fixtures")
ANNOTATION = re.compile(r"#\s*(ruleid|ok):\s*([\w-]+)")

expected, forbidden = set(), set()
for path in FIXTURES.rglob("*"):
    if not path.is_file():
        continue
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        match = ANNOTATION.search(line)
        if match:
            key = (path.as_posix(), idx + 2, match.group(2))  # annotated line is the next one
            (expected if match.group(1) == "ruleid" else forbidden).add(key)

report = json.load(sys.stdin)
actual = {
    (r["path"], r["start"]["line"], r["check_id"].split(".")[-1])
    for r in report["results"]
}

missed = expected - actual
false_positives = forbidden & actual
for item in sorted(missed):
    print(f"MISSED          {item[0]}:{item[1]}  {item[2]}")
for item in sorted(false_positives):
    print(f"FALSE POSITIVE  {item[0]}:{item[1]}  {item[2]}")

if not expected:
    print("No ruleid annotations found - refusing to pass an empty test.")
    sys.exit(1)
if missed or false_positives:
    sys.exit(1)
print(f"OK: {len(expected)} expected matches found, {len(forbidden)} ok-cases clean")
