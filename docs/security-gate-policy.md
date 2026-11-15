# Security gate policy

## Principle

**Gate what you own; evidence what you don't.**

| Scope | Examples | Pipeline behaviour |
|---|---|---|
| Code and config in this repository | Terraform, workflows, Dockerfile, Compose, scripts, scanner config | **Blocking.** Any finding fails the job |
| Third-party lab target (OWASP Juice Shop) | Source, image, running app | **Evidence.** Reports are retained and a release decision is computed and printed to the job summary. CI does not fail, because the target is never promoted |

A pipeline that is always red trains people to ignore it. A pipeline that
is green because nothing is checked is worse. Splitting by ownership keeps
the gate meaningful.

## Blocking controls (this repository)

| Control | Workflow / job | Fails when |
|---|---|---|
| Gitleaks (full history, `fetch-depth: 0`) | `ci-security` / secrets | any leak (exit 1) |
| Semgrep `p/github-actions`, `p/terraform`, `p/secrets`, `p/dockerfile`, lab rules | `ci-security` / sast | any finding (`--error`) |
| Custom Semgrep rule tests | `ci-security` / sast | a `ruleid:` line is missed or an `ok:` line matches |
| `terraform fmt -check`, `validate`, `plan` | `terraform-security` / terraform | format drift, invalid config, plan error |
| Checkov built-in + `CKV2_LAB_*` | `terraform-security` / checkov | any failed check |
| Checkov policy unit tests | `terraform-security` / checkov | a policy does not fail on the insecure fixture or does not pass on `terraform/` |
| Trivy config | `terraform-security` / trivy-config | any HIGH/CRITICAL misconfiguration |
| DAST isolation | `dast-security` | target not bound to `127.0.0.1`, scan network can reach the internet, or ZAP contacted any host other than the target |

## Release policy (applied to the target image)

| Finding | Decision |
|---|---|
| Confirmed exposed secret | Fail immediately; revoke / rotate |
| CRITICAL with a fix available | **Block** pending remediation or formally approved exception |
| HIGH with a fix available | **Block** or documented risk acceptance (owner + expiry) |
| CRITICAL/HIGH with no fix (e.g. `marsdb`) | Block; plan component replacement or compensating control |
| MEDIUM / LOW | Record; remediate within SLA |
| Scanner error / missing report | **Fail closed.** The summary prints "not run" rather than omitting the section |
| False positive | Narrow suppression with reason, owner and expiry. See `security/zap/rules.tsv` for the documented examples |

Current result: **BLOCKED** (7 critical / 24 high, 57 fixable). See the
[findings register](findings-register.md#release-decision).

## Supply-chain controls on the pipeline itself

* Default `permissions: contents: read`. Only the SARIF upload job gets
  `security-events: write`.
* Every action is pinned to a full commit SHA (`# vX.Y.Z` comment for humans).
* Every tool image is pinned by `sha256` digest.
* `actions/checkout` uses `persist-credentials: false`.
* Upstream source is fetched by tag and the **commit SHA is verified**
  before scanning.
* No `pull_request_target`. The lab Semgrep rule `gha-pull-request-target` enforces this.
* Dependabot watches actions, the Terraform provider and Compose images.

## Exceptions

An exception needs: the finding ID, a reason, compensating controls, an
owner and an expiry date, recorded in the findings register. The lab
target's findings are accepted only for the purpose of training, under
these compensating controls: loopback-only binding, no-egress scan
network, ephemeral runners, and `terraform destroy` after every DAST run.
