# Findings register

Scan baseline: **2026-11-15**, OWASP Juice Shop **v20.4.0**
(commit `266448ab`, image `sha256:9bbaecc4…`), tools and versions as in
[test-plan.md](test-plan.md). Raw evidence is in [`reports/`](../reports).

Findings are split by **who owns the fix**:

* **Part A - this repository** (IaC, pipeline, scanner setup). These are
  gated. Each one was remediated and retested.
* **Part B - the lab target** (OWASP Juice Shop). The app is vulnerable on
  purpose. These findings are triaged and validated as evidence. The fix
  belongs upstream, so the status is *Accepted (training target)* and the
  release decision for the image is **BLOCKED**.

Severity is my triaged severity in context, not just the scanner's label.
"Validated" means it was reproduced safely against the local lab instance
(`127.0.0.1`), see [`reports/validation/manual-validation.md`](../reports/validation/manual-validation.md).

---

## Part A - this repository (remediated)

| ID | Tool | Finding | Severity | Evidence | Remediation | Status |
|---|---|---|---|---|---|---|
| LAB-IAC-01 | Checkov `CKV2_LAB_001` | Juice Shop port published without `ip`. The Docker provider default is **0.0.0.0**, so the vulnerable app was reachable from the LAN | High | `reports/checkov/baseline` | `ports.ip = "127.0.0.1"`; verified a LAN-IP request is refused | **Fixed** |
| LAB-IAC-02 | Checkov `CKV2_LAB_002` | Container kept the default Linux capability set | Medium | `reports/checkov/baseline` | `capabilities { drop = ["ALL"] }` | **Fixed** |
| LAB-IAC-03 | Checkov `CKV2_LAB_003` | `no-new-privileges` not set | Medium | `reports/checkov/baseline` | `security_opts = ["no-new-privileges:true"]` | **Fixed** |
| LAB-IAC-04 | Checkov `CKV2_LAB_004` | No memory limit | Low | `reports/checkov/baseline` | `memory = 1024` | **Fixed** |
| LAB-IAC-05 | Checkov `CKV2_LAB_005` | Image referenced by mutable tag | Medium | `reports/checkov/baseline` | Pinned `:v20.4.0@sha256:9bbaecc4…` | **Fixed** |
| LAB-IAC-06 | Checkov `CKV2_LAB_007` | Runtime user inherited from the image, not declared | Low | `reports/checkov/baseline` | `user = "65532"` | **Fixed** |
| LAB-OPS-01 | Manual review of ZAP JSON | DAST scope leak: the ZAP client spider drove a real browser that contacted **27 third-party sites** (github.com, x.com, facebook, Google…) while scanning the lab | High (scope / rules of engagement) | `reports/zap-pre-isolation/zap-baseline.json` (`site[]` = 28) | ZAP moved to an `internal = true` Docker network with no egress; CI asserts egress is blocked and fails if ZAP talks to any host but the target | **Fixed** - retest contacted 1 site |
| LAB-OPS-02 | Side effect of LAB-OPS-01 | With no egress, `zap-baseline.py` could not download `pscanrulesBeta`, so 7 passive rules silently stopped running (17 → 10 alert types) | Medium (silent loss of coverage) | Comparison in [remediation-log.md](remediation-log.md#lab-ops-02) | Hermetic scanner image `security/zap/Dockerfile` bakes in the add-ons | **Fixed** - 17 alert types restored |
| LAB-OPS-03 | Trivy `DS-0002` / `DS-0026` | New ZAP Dockerfile had no explicit `USER` (HIGH) and no `HEALTHCHECK` (LOW) | High / Low | `reports/trivy/trivy-config-repo-before-fix.json` | `USER zap`, `HEALTHCHECK NONE` (one-shot CLI) | **Fixed** - 0 misconfigurations |
| LAB-OPS-04 | Manual review of Semgrep JSON | Pipeline bug: Semgrep resolved the outer repo as project root, so test fixtures leaked into the target results and the `codefixes/` exclusion silently did nothing (1,269 files / 178 findings) | Medium (wrong evidence) | [remediation-log.md](remediation-log.md#lab-ops-04) | Scan an explicit path with `**/`-anchored excludes | **Fixed** - 923 files / 90 findings, none out of scope |

Gating scans of this repository at the final commit: Gitleaks **0** leaks
(full history), Semgrep **0** findings (`p/github-actions`, `p/terraform`,
`p/secrets`, `p/dockerfile`, lab rules), Trivy config **0**
misconfigurations, Checkov **7/7** passed.

---

## Part B - OWASP Juice Shop (training target, upstream fix)

### Static analysis and secrets

| ID | Tool | Finding | Severity | Evidence | Recommendation | Status |
|---|---|---|---|---|---|---|
| LAB-SAST-01 | Semgrep `express-sequelize-injection` | SQL built by string interpolation of `req.body.email` in the login query | **Critical** - **validated**: `' OR 1=1--` logs in as `admin@juice-sh.op` (role admin), control request returns 401 | `routes/login.ts:34` | Parameterised query / Sequelize `replacements`; never interpolate request data into SQL | Accepted (training target) |
| LAB-SAST-02 | Gitleaks `private-key` + Semgrep `hardcoded-jwt-secret` | RSA private key used to sign every JWT is hard-coded in source. The same key also appears as a TLS key in `terraform/networking.tf:171` (key reuse) | **Critical** - anyone with the source can mint admin tokens | `lib/insecurity.ts:21`, `:54` | Load the key from a secret manager, rotate it, use separate keys per purpose | Accepted (training target) |
| LAB-SAST-03 | Semgrep `node_nosqli_injection` (19), `node_nosqli_js_injection` (2) | Request data flows into MarsDB/Mongo-style queries, e.g. `routes/address.ts:18` | High (not individually validated) | `reports/semgrep/semgrep-juice-shop.json` | Type-check and cast query inputs; reject operator objects (`$where`, `$ne`) | Accepted - needs per-instance triage |
| LAB-SAST-04 | Semgrep `express-open-redirect` | Redirect allowlist uses `url.includes(allowed)`, so any URL that *contains* an allowed URL passes | Medium - **validated**: `?to=https://example.org/?pivot=https://github.com/juice-shop/juice-shop` → `302` to example.org; control → `406` | `routes/redirect.ts:18`, `lib/insecurity.ts:136` | Parse the URL and compare origin + path for exact equality | Accepted (training target) |
| LAB-SAST-05 | Semgrep `express_xss`, `code-string-concat` | User-controlled profile data rendered/evaluated in `routes/userProfile.ts` | High (not individually validated) | `routes/userProfile.ts:34`, `:65` | Context-aware output encoding; remove dynamic evaluation | Accepted (training target) |
| LAB-SAST-06 | Lab rule `gha-pull-request-target` | Upstream `pr-compliance.yml` runs on `pull_request_target` with `pull-requests: write` | Low - triaged: the job does **not** check out PR code, it only reads PR metadata via `github-script`. True-positive pattern, low exploitability | `.github/workflows/pr-compliance.yml:3` | Keep it, but never add a checkout of `head.sha` to this workflow | Accepted (upstream) |
| LAB-SAST-07 | Semgrep `run-shell-injection` (7) | `${{ github.ref_name }}` interpolated into `run:` in `update-challenges-ebook.yml` | Low - triaged: only triggered by pushes to `master`/`develop` (maintainer-controlled ref names) | `.github/workflows/update-challenges-ebook.yml:23` | Pass through `env:` and quote it | Accepted (upstream) |
| LAB-SAST-08 | Lab rule `compose-port-published-on-all-interfaces` | Upstream `infrastructure/docker-compose.yml` publishes ports on 0.0.0.0 | Medium | `infrastructure/docker-compose.yml:8-9` | Bind to `127.0.0.1:` for local use | Accepted (upstream) |
| LAB-SEC-01 | Gitleaks (75 hits) | 58 of 75 are in `test/` fixtures, 10 in `frontend` (6 in `*.spec.ts` sample JWTs; 4 in `faucet.component.ts` / `passkey-providers.ts` needing review) and 3 in `data/static/users.yml` (challenge data). True positives that matter: LAB-SAST-02 | Triage summary | `reports/gitleaks/gitleaks-juice-shop-source.json` | Allowlist test fixtures narrowly *with a reason*; rotate and remove real keys | Triaged |

### Dependencies and container image (Trivy, digest-pinned image)

Totals: **7 critical, 24 high, 65 medium, 15 low, 2 unknown**. 57 have a
fixed version available.

| ID | Package (installed) | Advisory | Severity | Fixed in | Status |
|---|---|---|---|---|---|
| LAB-SCA-01 | `jsonwebtoken` 0.1.0 / 0.4.0 | CVE-2015-9235 - verification bypass with altered token | Critical | ≥ 4.2.2 (use 9.x) | Accepted (training target) |
| LAB-SCA-02 | `crypto-js` 3.3.0 | CVE-2023-46233 - PBKDF2 far weaker than specified | Critical | 4.2.0 | Accepted (training target) |
| LAB-SCA-03 | `lodash` 2.4.2 | CVE-2019-10744 - prototype pollution (`defaultsDeep`) | Critical | 4.17.21 | Accepted (training target) |
| LAB-SCA-04 | `marsdb` 0.6.11 | GHSA-5mrr-rgp6-x4gr - command injection | Critical | **no fix** → replace the component | Accepted (training target) |
| LAB-SCA-05 | `tar` 6.2.1 | CVE-2026-59873 + 9 high (path traversal, file overwrite, DoS) | Critical | 7.5.21 | Accepted (training target) |
| LAB-SCA-06 | `express-jwt` 0.1.3, `jws` 0.2.6 | CVE-2020-15084 auth bypass; CVE-2016-1000223 / CVE-2025-65945 signature issues | High | 6.0.0 / 3.2.3+ | Accepted (training target) |
| LAB-SCA-07 | `zlib1g` (Debian 13.7 base) | CVE-2026-85091 heap overflow, CVE-2026-76844 | High | `1:1.3.dfsg+really1.3.1-1+deb13u1` | Accepted - rebuild on patched base |

### Dynamic analysis (ZAP baseline, passive)

| ID | ZAP alert (plugin) | Risk | Validation and triage | Status |
|---|---|---|---|---|
| LAB-ZAP-01 | CSP header not set (10038) | Medium | **Validated**: no `Content-Security-Policy` on `/` | Accepted (training target) |
| LAB-ZAP-02 | Cross-Domain Misconfiguration (10098) | Medium | **Validated**: `Access-Control-Allow-Origin: *` on `/` and static assets | Accepted (training target) |
| LAB-ZAP-03 | Missing anti-clickjacking header (10020) | Medium → **Low** | `/` *does* send `X-Frame-Options: SAMEORIGIN`. The alert only fires on `socket.io` polling responses, which are not frameable documents. Partial false positive | Accepted |
| LAB-ZAP-04 | Off-site redirect (10028) | High | Same root cause as LAB-SAST-04 (correlated SAST + DAST) | Accepted (training target) |
| LAB-ZAP-05 | Application error disclosure (90022) | Low | `/rest/user/reset-password` returns `500` with error details | Accepted (training target) |
| LAB-ZAP-06 | Session ID in URL rewrite (3) | Medium → **FP** | The `sid` is the socket.io transport id, not an auth session | False positive (documented) |
| - | Timestamp disclosure (10096) | Info | Numeric values in JS bundles; set to `INFO` in `security/zap/rules.tsv` | False positive |

> **ZAP coverage note:** The client spider is not deterministic. Runs in
> this lab crawled 257-1,286 URLs; the full rule set raised 15-17 alert types. Treat the
> alert *types* as the stable signal, not exact instance counts.

## Release decision

| Artifact | Policy result | Decision |
|---|---|---|
| This repository (IaC, workflows, scanner config) | 0 gating findings | **PASS** |
| `bkimminich/juice-shop:v20.4.0@sha256:9bbaecc4…` | 7 critical / 24 high, 57 fixable; validated SQLi and hard-coded signing key | **BLOCKED**: would not be promoted. It is a training target and runs only on loopback |
