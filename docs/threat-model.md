# Threat model

Scope: the lab pipeline and environment, **not** Juice Shop's own
application threat model (upstream ships one in `threat-model.json`).

## Assets

| Asset | Why it matters |
|---|---|
| Source, workflows, Terraform in this repo | Changing them changes what runs with CI privileges |
| `GITHUB_TOKEN` and runner | Can write to code scanning; could be abused to tamper with evidence |
| Scan reports / evidence pack | Used for release decisions; must be accurate and must not leak secrets |
| Running lab target | Intentionally exploitable. Exposure means a compromise of the host network |
| Developer workstation | Runs the same Terraform and scanners locally |

## Trust boundaries

```text
contributor workstation ─► GitHub repo ─► GitHub-hosted runner (ephemeral)
                                             │
                                             ├─► Docker engine
                                             │     ├─ lab net  ── juice-shop ── 127.0.0.1:3000 (host loopback only)
                                             │     └─ scan net (internal, no egress) ── juice-shop ◄── ZAP
                                             └─► registries (ghcr.io, Docker Hub) - digest-pinned pulls
```

## Threats and controls (STRIDE-style)

| # | Threat | Control in this repo | Verified by |
|---|---|---|---|
| T1 | **Information disclosure:** a secret committed to the repo | Gitleaks over full history, blocking | `ci-security/secrets` |
| T2 | **Elevation of privilege:** the vulnerable target is reachable from the LAN or internet | `ports.ip = 127.0.0.1`, policy `CKV2_LAB_001`, runtime assertion in DAST | LAN-IP curl refused; DAST job asserts `HostIp == 127.0.0.1` |
| T3 | **Elevation of privilege:** container breakout aided by capabilities or setuid | `drop ALL`, `no-new-privileges`, non-root UID, not privileged | `CKV2_LAB_002/003/006/007`, `docker inspect` |
| T4 | **Denial of service:** a runaway target starves the host | 1 GiB memory limit (`CKV2_LAB_004`) | Checkov |
| T5 | **Tampering:** a mutable tag is re-pointed to a malicious image | Images pinned by sha256 (`CKV2_LAB_005`), tool images pinned in workflows | Checkov, review |
| T6 | **Tampering:** a compromised third-party action | Actions pinned to commit SHA; Dependabot for updates | Semgrep `github-actions-mutable-action-tag` |
| T7 | **Elevation of privilege:** fork PR code runs with secrets | No `pull_request_target`; lab rule `gha-pull-request-target` | Semgrep (blocking) |
| T8 | **Elevation of privilege:** over-privileged `GITHUB_TOKEN` | `contents: read` default; `security-events: write` only on one job; `persist-credentials: false` | Workflow review |
| T9 | **Rules of engagement:** the scanner touches third-party systems | ZAP only on the `internal` network; CI fails if any other site is contacted | LAB-OPS-01 retest |
| T10 | **Repudiation / integrity:** wrong or partial evidence leads to a wrong decision | Fail-closed summary ("not run"), scope self-checks, verified upstream commit SHA | LAB-OPS-02, LAB-OPS-04 |
| T11 | **Information disclosure:** reports leak tokens or personal data | Gitleaks `--redact`; validation log records claims only (token redacted); git metadata stripped from committed reports | Gitleaks scan of `reports/` → 0 |
| T12 | **Tampering:** Terraform state leaks or drifts | Local state only, `.gitignore`d; no cloud credentials exist in this lab | `.gitignore` |

## Out of scope

Testing third-party systems or the public Juice Shop demo, credential
theft, persistence, denial-of-service, destructive actions, and anything
outside the isolated lab. Active ZAP scanning is out of scope as well:
only the passive baseline is run.
