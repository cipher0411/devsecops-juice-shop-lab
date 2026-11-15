# Remediation log

Each entry follows the same lifecycle: **detect → validate → root cause →
fix → retest → evidence**. All of them are in the git history and can be
followed commit by commit (`git log --oneline`).

---

## LAB-IAC-01…06 - container guardrails (Terraform)

**Detect.** I wrote seven custom Checkov policies (`security/checkov/policies/CKV2_LAB_*`),
because Checkov's built-in checks barely cover the `kreuzwerker/docker`
provider. The scan of the first Terraform version, which relied on
provider defaults, failed **6 of 7**:

```text
CKV2_LAB_001 ports.ip == 127.0.0.1 ............ FAILED
CKV2_LAB_002 capabilities.drop contains ALL ... FAILED
CKV2_LAB_003 no-new-privileges ................ FAILED
CKV2_LAB_004 memory limit ..................... FAILED
CKV2_LAB_005 image pinned by digest ........... FAILED
CKV2_LAB_006 not privileged ................... passed
CKV2_LAB_007 explicit non-root user ........... FAILED
```

**Validate.** The provider documents that `ports.ip` *defaults to 0.0.0.0*.
Leaving it unset would publish an intentionally vulnerable application on
every network interface of the host.

**Prove the policies.** A policy that only ever passes proves nothing.
`security/checkov/tests/insecure/main.tf` sets explicit bad values (`ip =
"0.0.0.0"`, `user = "0"`, `privileged = true`, …).
`scripts/test-checkov-policies.sh` asserts that **all 7 policies fail there
and pass on `terraform/`**. It runs in CI on every IaC change.

**Fix** (commit `fix(iac): harden Juice Shop container…`): loopback binding,
`drop = ["ALL"]`, `no-new-privileges:true`, 1 GiB memory limit, UID 65532,
and the image pinned as `:v20.4.0@sha256:9bbaecc4…`.

**Retest.** Checkov passed 7 / failed 0 (`reports/checkov/retest`). Runtime check
after `terraform apply`:

```text
$ docker inspect juice-shop-lab-app
user=65532 caps=[ALL] sec=[no-new-privileges:true] mem=1073741824 priv=false
ports: 127.0.0.1:3001->3000/tcp
$ curl http://<host-LAN-IP>:3001/   ->  connection refused (expected)
$ curl http://127.0.0.1:3001/       ->  HTTP 200
```

---

## LAB-OPS-01 - DAST scanner left the lab {#lab-ops-01}

**Detect.** I reviewed `site[]` in the ZAP JSON report, not just the alert
list. ZAP had recorded **28 sites**: the lab target plus 27 third-party
origins (github.com, x.com, twitter.com, facebook CDN, accounts.google.com,
sentry.io, owasp.org …).

**Validate / root cause.** `zap-baseline.py -j` runs the client spider, which
drives a real Firefox. Juice Shop embeds and links third-party resources,
and the browser loaded them. No alerts were raised against those hosts and
all checks were passive. It still broke the lab's own rule: *"the scanner
only talks to the lab target"*. A config-only scope list depends on every
ZAP component honouring it.

**Fix.** Enforce scope at the network layer instead of in tool config:

* Terraform adds `docker_network.scan` with `internal = true` (no route
  off the host). Juice Shop joins both networks, ZAP joins **only** `scan`.
* `dast-security.yml` checks the network is internal, proves an egress
  attempt to `https://github.com` fails, and after the scan **fails the job
  if ZAP's report lists any site other than `http://juice-shop:3000`**.

**Retest.** `sites contacted: ['http://juice-shop:3000']`, down from 28 to 1.

---

## LAB-OPS-02 - silent loss of DAST coverage {#lab-ops-02}

**Detect.** After LAB-OPS-01, the alert types per run dropped from 17 to 10.
A longer spider window (`-m 5`) gave 11, so crawl time was not the cause.

**Root cause.** ZAP's debug log showed `-addonupdate -addoninstall
pscanrulesBeta`: the baseline script downloads beta passive rules at
start-up. With no egress, that download failed **without failing the scan**.
COEP/COOP, Dangerous JS Functions, Deprecated Feature Policy and the
cacheability rules all disappeared quietly. This is the classic "scanner
error must not silently pass" problem.

**Fix.** A hermetic scanner image, `security/zap/Dockerfile`. It starts from the
digest-pinned ZAP image and installs the add-ons at build time, when it
still has network access. The build fails if `pscanrulesBeta` is missing.

**Retest.** 17 alert types, matching the pre-isolation run. The one-for-one
swap of individual alerts is client-spider variance. The run still
contacted only `http://juice-shop:3000`.

---

## LAB-OPS-03 - scanner image hardening (Trivy DS-0002 / DS-0026)

**Detect.** The new Dockerfile was caught by this repo's own gating
`trivy config` scan, so the pipeline did its job on the pipeline itself:

```text
security/zap/Dockerfile DS-0002 HIGH Image user should not be 'root'
security/zap/Dockerfile DS-0026 LOW  No HEALTHCHECK defined
```

**Validate.** The effective user was already `uid=1000(zap)`, but only by
inheritance from the base image. A base-image change could silently
switch the runtime user to root.

**Fix.** Explicit `USER zap`. `HEALTHCHECK NONE` records the decision
that a one-shot CLI scanner has no service to probe.

**Retest.** `trivy config --severity HIGH,CRITICAL --exit-code 1` → exit 0,
0 misconfigurations (`reports/trivy/trivy-config-repo.json`, before:
`trivy-config-repo-before-fix.json`).

---

## LAB-OPS-04 - SAST scoped to the wrong files {#lab-ops-04}

**Detect.** While triaging, I noticed some Semgrep result paths that cannot
exist in Juice Shop: `security/semgrep/fixtures/...` (this repo's own test
fixtures), plus results under `data/static/codefixes/`, which was
supposed to be excluded.

**Root cause.** Semgrep was started with `-w target/juice-shop` and no
explicit target, so it resolved the *outer* git repository as the project
root and scanned everything. Exclusion patterns written relative to the
Juice Shop folder therefore never matched.

**Fix.** Run from the repo root with an explicit target path
(`semgrep scan … target/juice-shop`) and `**/`-anchored exclusions. The
CI workflow was updated the same way.

**Retest.** The result went from 1,269 files / 178 findings to **923 files / 90
findings**, with 0 out-of-scope paths, 0 `codefixes/` files, 0 `*.spec.ts`
and 0 `test/`. Without this check the evidence pack would have
overstated the target's findings by about 2×.

---

## Lessons recorded

1. Provider defaults are a security decision. Write a policy for the ones that matter.
2. Test your policies against known-bad input, or they are just decoration.
3. Read the *metadata* of a scan report (sites contacted, files scanned), not just the findings.
4. Network isolation is more reliable than tool-level scope configuration.
5. Hardening one thing (egress) can silently break another (rule download).
   Measure coverage before and after.
