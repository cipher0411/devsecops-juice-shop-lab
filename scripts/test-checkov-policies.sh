#!/usr/bin/env bash
# Unit-tests the custom Checkov policies:
#   * every CKV2_LAB_* policy must FAIL on the insecure fixture
#   * every CKV2_LAB_* policy must PASS on the real lab Terraform
# Requires: docker. Usage: scripts/test-checkov-policies.sh
set -euo pipefail

CHECKOV_IMAGE="${CHECKOV_IMAGE:-bridgecrew/checkov:3.4.5}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
POLICY_DIR="security/checkov/policies"
expected=$(grep -h '^  id:' "$ROOT/$POLICY_DIR"/*.yaml | sed 's/.*"\(.*\)"/\1/' | tr -d '\r' | sort)

scan() {
  docker run --rm -v "$ROOT:/repo" -w /repo "$CHECKOV_IMAGE" \
    -d "$1" --framework terraform --external-checks-dir "$POLICY_DIR" \
    --check "$(echo "$expected" | paste -sd, -)" -o json --soft-fail
}

ids() { "${PYTHON:-python3}" -c "
import json,sys
d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d
print('\n'.join(sorted({c['check_id'] for c in d['results']['$1']})))" | tr -d '\r'; }

failed_on_bad=$(scan security/checkov/tests/insecure | ids failed_checks)
passed_on_good=$(scan terraform | ids passed_checks)

status=0
if [ "$failed_on_bad" != "$expected" ]; then
  echo "FAIL: policies that did not fire on the insecure fixture:"
  comm -23 <(echo "$expected") <(echo "$failed_on_bad"); status=1
fi
if [ "$passed_on_good" != "$expected" ]; then
  echo "FAIL: policies that did not pass on terraform/:"
  comm -23 <(echo "$expected") <(echo "$passed_on_good"); status=1
fi
[ $status -eq 0 ] && echo "OK: $(echo "$expected" | wc -l) policies fail on insecure fixture and pass on terraform/"
exit $status
