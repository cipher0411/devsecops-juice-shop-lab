# Test plan and baseline record

## Baseline record

| Item | Value |
|---|---|
| Date (UTC) | 2026-11-15 |
| Target | OWASP Juice Shop **v20.4.0** |
| Target source | `github.com/juice-shop/juice-shop` tag `v20.4.0`, commit `266448aba68cd8ba5915f526a128da4fa7bc3f9f` (verified in CI) |
| Target image | `bkimminich/juice-shop:v20.4.0@sha256:9bbaecc41791f00b002bc65931cc5ff355fbdb941fa72b06558c18dace43197b` (Debian 13.7) |
| Target URL | `http://127.0.0.1:3000` in CI. Locally `http://127.0.0.1:3001` because port 3000 was taken by another service; set with `-var host_port=3001` |
| Scanner URL | `http://juice-shop:3000` over the internal `juice-shop-lab-scan` network |
| Environment | Docker Desktop 29.6.2 (local) and GitHub-hosted `ubuntu-24.04` (CI) |
| Scan profile | Passive only (ZAP baseline). No active scan, no authenticated scan |

## Tools

| Tool | Version | Image digest |
|---|---|---|
| Gitleaks | 8.30.1 | `ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0…` |
| Semgrep | 1.185.0 | `semgrep/semgrep@sha256:67518c17…` |
| Trivy | 0.76.2 | `aquasec/trivy@sha256:8f6bb947…` |
| Checkov | 3.4.5 | `bridgecrew/checkov@sha256:122602cf…` |
| Terraform | 1.17.2, provider `kreuzwerker/docker` 4.7.x (lockfile) | `hashicorp/terraform@sha256:6e9c1e64…` |
| OWASP ZAP | 2.17.0 + `pscanrulesBeta` (baked in) | base `ghcr.io/zaproxy/zaproxy@sha256:9624669d…` |

## Test cases

| # | Control | Procedure | Pass criterion | Result |
|---|---|---|---|---|
| TC-01 | Secrets in repo | `gitleaks git` over full history | 0 leaks | **Pass** (0) |
| TC-02 | Secrets in target | `gitleaks dir target/juice-shop` | Report produced and triaged | 75 hits, triaged (LAB-SEC-01) |
| TC-03 | SAST on repo | Semgrep, 4 registry packs + lab rules, `--error` | 0 findings | **Pass** (28 files, 0) |
| TC-04 | Custom Semgrep rules | `scripts/test-semgrep-rules.py` on fixtures | All `ruleid` hit, no `ok` hit | **Pass** (3 / 3). Negative test: empty input → exit 1 |
| TC-05 | SAST on target | Semgrep OWASP / JS / TS / nodejsscan | Report produced and in scope | 923 files, 90 findings, 0 out of scope |
| TC-06 | Terraform hygiene | `fmt -check`, `init -backend=false`, `validate` | All succeed | **Pass** |
| TC-07 | IaC policy | Checkov + `CKV2_LAB_*` on `terraform/` | 0 failed | Baseline 6 failed → retest **7/7 pass** |
| TC-08 | Policy correctness | `scripts/test-checkov-policies.sh` | 7 fail on fixture, 7 pass on `terraform/` | **Pass** |
| TC-09 | IaC misconfiguration | `trivy config`, HIGH/CRITICAL gate | exit 0 | Failed (DS-0002) → fixed → **Pass** |
| TC-10 | Container SCA | `trivy image` on the digest | Report and release decision | 7C / 24H / 65M / 15L / 2U → **BLOCKED** |
| TC-11 | Loopback isolation | `terraform apply`, then curl the LAN IP and 127.0.0.1 | LAN refused, loopback 200 | **Pass** |
| TC-12 | Scan-network isolation | curl `https://github.com` from the scan network | Fails | **Pass** (curl exit 6) |
| TC-13 | DAST | ZAP baseline on the scan network | Report, only the target contacted | **Pass**: 1 site, 17 alert types, 0 FAIL |
| TC-14 | Finding validation | Manual safe reproduction on the local target | Documented with control requests | SQLi, open redirect, CSP, CORS validated |

## Reproduce locally

```bash
git clone https://github.com/cipher0411/devsecops-juice-shop-lab && cd devsecops-juice-shop-lab
git clone --depth 1 --branch v20.4.0 https://github.com/juice-shop/juice-shop target/juice-shop

# IaC + policy tests
bash scripts/test-checkov-policies.sh
docker run --rm -v "$PWD:/repo" -w /repo bridgecrew/checkov:3.4.5 \
  -d terraform --framework terraform --external-checks-dir security/checkov/policies

# Deploy target (loopback only) with Terraform
TF='docker run --rm -v '"$PWD"'/terraform:/tf -v /var/run/docker.sock:/var/run/docker.sock -w /tf hashicorp/terraform:1.17.2'
$TF init && $TF apply -auto-approve

# DAST from the no-egress network with the hermetic ZAP image
docker build -t juice-shop-lab/zap:local security/zap
mkdir -p reports/zap && cp security/zap/rules.tsv reports/zap/
docker run --rm --network juice-shop-lab-scan -v "$PWD/reports/zap:/zap/wrk:rw" juice-shop-lab/zap:local \
  zap-baseline.py -t http://juice-shop:3000 -m 3 -j -I -c rules.tsv -J zap-baseline.json -r zap-baseline.html

# Summary + teardown
python3 scripts/summarize_reports.py reports
$TF destroy -auto-approve
```

On Windows Git Bash, prefix `docker run` commands with `MSYS_NO_PATHCONV=1`.
