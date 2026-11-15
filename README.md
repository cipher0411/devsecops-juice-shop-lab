# DevSecOps Security Engineering Lab --- OWASP Juice Shop

**Author:** John Uwahamen Usiabulu\
**Focus:** DevSecOps · Cloud Security · Infrastructure as Code ·
Application Security · CI/CD · Security Testing\
**Lab type:** Defensive, isolated security engineering portfolio project

[![OWASP Juice
Shop](https://img.shields.io/badge/Target-OWASP%20Juice%20Shop-orange)](https://github.com/juice-shop/juice-shop)
[![GitHub
Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://docs.github.com/actions)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)](https://developer.hashicorp.com/terraform)
[![Security](https://img.shields.io/badge/Security-Shift%20Left-2E8B57)](#security-controls)
[![License](https://img.shields.io/badge/Lab%20documentation-MIT-blue)](LICENSE)

> A reproducible DevSecOps lab that demonstrates how security controls
> can be embedded into a software delivery lifecycle. The intentionally
> vulnerable application is supplied by the OWASP Juice Shop project;
> this repository documents the lab design, automation, infrastructure
> checks, security testing and evidence process.

------------------------------------------------------------------------

## 1. Executive overview

This project demonstrates an end-to-end security workflow around **OWASP
Juice Shop**, a deliberately insecure web application created for
security training, awareness demonstrations, CTFs and security-tool
evaluation. It covers the practical security engineering activities
expected in a modern delivery team:

-   Source-code and dependency security analysis (SAST / SCA).
-   Secret detection before code is merged.
-   Terraform / Infrastructure-as-Code validation and policy scanning.
-   Container image and filesystem vulnerability scanning.
-   Dynamic application security testing (DAST) against a lab instance.
-   CI quality gates, pull-request feedback and downloadable scan
    evidence.
-   Controlled deployment principles, least privilege and remediation
    tracking.

**Important:** This is a portfolio lab, not a claim that a production
environment has been deployed or independently certified. Run the
workflows, retain the generated evidence, and replace the status
placeholders below with your real results before presenting the
repository as completed work.

## 2. Lab architecture

![DevSecOps lab architecture](assets/lab-architecture.png)

The pipeline is designed to run security checks before a deployment is
approved. The target is isolated and intentionally vulnerable. Do not
expose it to the public internet or use it to test systems you do not
own or have written permission to assess.

### Pipeline stages

  ------------------------------------------------------------------------
  Stage             Control            Example tool      Expected evidence
  ----------------- ------------------ ----------------- -----------------
  1\. Commit / pull Change review and  GitHub            PR checks and
  request           branch protection                    review record

  2\. Secret        Detect credentials Gitleaks          Secret scan
  detection         accidentally                         report
                    committed                            

  3\. SAST          Identify risky     Semgrep           SARIF / JSON
                    source patterns                      findings

  4\. SCA /         Identify           Trivy             SARIF / table
  filesystem        vulnerable                           report
                    packages and files                   

  5\. IaC security  Validate Terraform Terraform,        Terraform plan +
                    and detect         Checkov           Checkov report
                    misconfiguration                     

  6\. Container     Inspect image      Trivy image       Image
  security          packages and                         vulnerability
                    configuration                        report

  7\. DAST          Test the running   OWASP ZAP         ZAP HTML / JSON
                    lab application    Baseline          report

  8\. Release       Review findings    GitHub Actions    Workflow run and
  decision          and approve only   environments      approval record
                    under policy                         
  ------------------------------------------------------------------------

## 3. Technology stack

-   **Target application:** [OWASP Juice
    Shop](https://github.com/juice-shop/juice-shop)
-   **CI/CD:** [GitHub Actions](https://docs.github.com/actions)
-   **Infrastructure as Code:**
    [Terraform](https://developer.hashicorp.com/terraform)
-   **SAST:** [Semgrep](https://semgrep.dev/)
-   **Secrets scanning:**
    [Gitleaks](https://github.com/gitleaks/gitleaks)
-   **Filesystem / container scanning:** [Trivy](https://trivy.dev/)
-   **IaC scanning:** [Checkov](https://www.checkov.io/)
-   **DAST:** [OWASP ZAP](https://www.zaproxy.org/)
-   **Container runtime:** Docker / Docker Compose

Tool versions should be pinned in the actual workflow files and reviewed
regularly. Avoid relying on floating `latest` tags for production
release pipelines.

## 4. Repository structure

A recommended structure for this portfolio repository:

``` text
devsecops-juice-shop-lab/
├── .github/
│   └── workflows/
│       ├── ci-security.yml
│       └── dast.yml
├── assets/
│   ├── lab-architecture.png
│   └── evidence/
├── docker/
│   └── docker-compose.yml
├── terraform/
│   ├── versions.tf
│   ├── main.tf
│   └── outputs.tf
├── reports/
│   └── .gitkeep
├── docs/
│   ├── threat-model.md
│   ├── test-plan.md
│   └── remediation-log.md
├── .gitleaks.toml
├── .gitignore
├── LICENSE
└── README.md
```

The README is the project overview. Add the workflow, Terraform, Compose
and documentation files as you implement each stage; do not imply a file
or control exists until it has been committed and tested.

## 5. Lab setup and procedure

### 5.1 Prerequisites

-   Git and a GitHub account.
-   Docker Desktop or Docker Engine with Compose.
-   Terraform CLI (only needed for the Terraform stage).
-   A terminal (PowerShell, macOS Terminal or Linux shell).
-   Optional local tools: Trivy, Checkov, Semgrep and Gitleaks.

Check your tools:

``` bash
git --version
docker --version
docker compose version
terraform version
```

### 5.2 Create your portfolio repository

Create a new empty GitHub repository, for example
`devsecops-juice-shop-lab`. Do not fork the vulnerable target and
present it as your own application. Keep your own lab documentation and
automation in your portfolio repository, and reference the upstream
project.

``` bash
mkdir devsecops-juice-shop-lab
cd devsecops-juice-shop-lab
git init
git branch -M main
mkdir -p .github/workflows assets/evidence docker terraform reports docs
```

Copy this README and the architecture image into the matching paths,
then commit:

``` bash
git add README.md assets/lab-architecture.png
git commit -m "docs: add DevSecOps lab architecture and runbook"
git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/devsecops-juice-shop-lab.git
git push -u origin main
```

Replace the placeholder URL with your actual repository URL.

### 5.3 Run the vulnerable target locally

The upstream project documents a Docker-based local setup. Bind the
service to loopback so it is not exposed on your network:

``` bash
docker pull bkimminich/juice-shop
docker run --rm --name juice-shop \
  -p 127.0.0.1:3000:3000 \
  bkimminich/juice-shop
```

Open `http://127.0.0.1:3000` in your browser. Stop the container with
`Ctrl+C`.

**Isolation rule:** Use only the local instance you started. Do not scan
the public demonstration instance, third-party websites, or any system
without explicit written authorisation.

### 5.4 Establish a baseline

Before running scans, record:

-   Date and time (UTC).
-   Git commit SHA.
-   Target URL (`http://127.0.0.1:3000`).
-   Tool names and versions.
-   Scan profile and scope.
-   Findings by severity.
-   Any exclusions and the reason for each exclusion.

Save reports under `reports/` or as GitHub Actions artifacts. Sanitise
evidence: never commit real credentials, session cookies, personal data
or exploitable secrets.

## 6. Security testing procedure

### 6.1 Secret scanning --- Gitleaks

Purpose: identify accidentally committed API keys, passwords, tokens and
other credential-like strings.

Example local execution:

``` bash
gitleaks detect --source . --redact --report-format json \
  --report-path reports/gitleaks.json
```

Procedure: 1. Run against the repository before pushing. 2. Review each
match and determine whether it is a real secret or a false positive. 3.
If a real secret was exposed, revoke / rotate it immediately. Removing
it from the latest commit is not sufficient if it exists in Git history.
4. Add narrow, documented allow-list rules only for verified false
positives. 5. Retain the redacted report.

### 6.2 Static analysis --- Semgrep

Purpose: identify insecure coding patterns in source code.

``` bash
semgrep scan --config auto --json \
  --output reports/semgrep.json .
```

Procedure: 1. Run the scan against code you own or are authorised to
assess. 2. Triage findings by rule, file, line and confidence. 3.
Confirm whether the issue is exploitable in context. 4. Record a
remediation recommendation and retest after changes.

### 6.3 Dependency and filesystem scan --- Trivy

Purpose: identify known vulnerabilities in dependencies and filesystem
components.

``` bash
trivy fs --scanners vuln,misconfig,secret \
  --format json --output reports/trivy-fs.json .
```

Review vulnerability identifiers, installed and fixed versions,
severity, reachability where available, and vendor advisories.
Prioritise exploitable critical/high findings and create tracked
remediation work.

### 6.4 Terraform validation and IaC scan

The Terraform directory should describe only infrastructure you intend
to create. For a free local lab, start with Docker-based infrastructure
or use Terraform validation without provisioning cloud resources.

``` bash
cd terraform
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
cd ..
checkov -d terraform --framework terraform \
  --output json --output-file-path reports/checkov.json
```

Before applying any cloud configuration: - Inspect the plan and resource
changes. - Use a dedicated sandbox account and budget alerts. - Use
least-privilege identities and short-lived credentials. - Keep state
files and plan files out of Git. - Encrypt and restrict remote state
access if using a remote backend. - Do not hard-code access keys,
passwords, tokens or private keys. - Require human approval for
production environments.

### 6.5 Container image scan --- Trivy

Purpose: identify known vulnerabilities in the container image before it
is promoted.

``` bash
trivy image --severity HIGH,CRITICAL \
  --format json --output reports/trivy-image.json \
  bkimminich/juice-shop
```

Record the image digest used for the scan. A mutable image tag can point
to a different image later. For repeatable results, pin the image by
digest after verifying the digest from the registry.

### 6.6 Dynamic testing --- OWASP ZAP Baseline

Purpose: run a baseline passive scan against the local lab service.

Start Juice Shop in one terminal, then run ZAP from another:

``` bash
docker run --rm --network host \
  -v "$PWD/reports:/zap/wrk:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://127.0.0.1:3000 \
  -J zap-report.json -r zap-report.html
```

On Docker Desktop for Windows/macOS, `--network host` may not behave
like Linux. Use the host gateway supported by your Docker version (often
`host.docker.internal`) or place both containers on a dedicated Compose
network and target the Juice Shop service name.

The ZAP Baseline scan is primarily passive. It is not a full penetration
test and does not prove the absence of vulnerabilities. Review alerts
manually, validate scope, and document false positives.

## 7. CI/CD workflow design

The GitHub Actions pipeline should run on pull requests and pushes to
the main branch. A recommended job order:

1.  Checkout source.
2.  Run Gitleaks secret detection.
3.  Run Semgrep SAST.
4.  Run Trivy filesystem scan.
5.  Validate Terraform formatting and configuration.
6.  Run Checkov IaC checks.
7.  Build or pull the lab image and run Trivy image scan.
8.  Start the isolated target and run ZAP baseline.
9.  Upload reports as workflow artifacts.
10. Apply policy gates and require approval before any deployment.

### Recommended GitHub repository settings

-   Protect `main`; require pull requests and status checks.
-   Require review from at least one other person where practical.
-   Restrict who can bypass branch protection.
-   Set workflow permissions to read-only by default.
-   Grant `contents: write`, package publishing or cloud permissions
    only to the job that needs them.
-   Pin third-party actions to full commit SHAs and review updates.
-   Store secrets in GitHub Environments / repository secrets; prefer
    OIDC federation for cloud authentication.
-   Require approval for deployment environments.
-   Enable Dependabot updates and secret scanning where available.

### Security gate policy

A practical starter policy (adapt to risk and team context):

  -----------------------------------------------------------------------
  Finding                             Pull request behaviour
  ----------------------------------- -----------------------------------
  Confirmed exposed secret            Fail immediately; revoke / rotate
                                      the secret

  Critical vulnerability with a fix   Block release pending remediation
                                      or formally approved exception

  High vulnerability                  Block release or require documented
                                      risk acceptance

  Medium / low                        Record, prioritise and remediate
                                      within agreed SLA

  Scanner error / unavailable service Fail closed for release; do not
                                      silently skip

  False positive                      Document evidence and narrow
                                      suppression with owner and expiry
  -----------------------------------------------------------------------

A scanner exit code is not a risk assessment. Review exploitability,
exposure, compensating controls and business impact before accepting
risk.

## 8. Terraform and deployment approach

This portfolio can be completed without paying for cloud hosting:

**Free local path** - Docker Engine / Docker Desktop for the target. -
Terraform formatting, validation and Checkov scanning. - GitHub Actions
hosted runners within the usage allowance of your account. - Scan
reports stored as workflow artifacts.

**Optional cloud extension** - Deploy a separate, intentionally isolated
test environment in a cloud sandbox. - Use private networking,
restrictive inbound rules, TLS at the edge, logging and budget alerts. -
Use OIDC rather than long-lived cloud keys. - Keep the vulnerable
application private and temporary. - Destroy the environment after the
exercise.

Do not deploy an intentionally vulnerable training application to a
public production endpoint. If a cloud deployment is used for a
controlled demonstration, enforce access restrictions and obtain
approval first.

## 9. Evidence and reporting

Create an evidence pack for each successful run:

``` text
assets/evidence/
├── 01-github-actions-pipeline.png
├── 02-gitleaks-results.png
├── 03-semgrep-results.png
├── 04-trivy-filesystem-results.png
├── 05-checkov-terraform-results.png
├── 06-trivy-image-results.png
├── 07-zap-baseline-report.png
└── 08-remediation-and-retest.png
```

Capture genuine screenshots from your own workflow runs. Do not use
fabricated scan results, badges or screenshots. Redact secrets,
usernames, internal hostnames and personal information.

### Findings register template

  ----------------------------------------------------------------------------------
  ID         Tool       Finding    Severity   Evidence   Recommendation   Status
  ---------- ---------- ---------- ---------- ---------- ---------------- ----------
  LAB-001    Replace    Replace    Actual     Report     Specific         Open /
             with       with       severity   path /     remediation      Fixed /
             actual     verified              line                        Accepted
             tool       finding                                           

  ----------------------------------------------------------------------------------

### Remediation lifecycle

1.  Validate the alert and reproduce safely.
2.  Identify root cause and affected component.
3.  Assess likelihood, impact, exposure and exploitability.
4.  Assign an owner and remediation deadline.
5.  Implement the fix or approved compensating control.
6.  Re-run the relevant scanner and targeted test.
7.  Attach before/after evidence and close the finding.
8.  Record residual risk and approval where applicable.

## 10. Threat model and scope

**Assets:** source code, CI workflow, dependency graph, container image,
Terraform configuration, scan artefacts and test environment.

**Trust boundaries:** contributor workstation → GitHub repository →
GitHub-hosted runner → container runtime → isolated target.

**Threats considered:** accidental secret disclosure, vulnerable
dependencies, unsafe source patterns, insecure IaC, vulnerable container
packages, over-privileged CI tokens, unreviewed workflow changes and
unintended exposure of the vulnerable target.

**Out of scope:** testing third-party systems, attacking public Juice
Shop demos, credential theft, persistence, denial-of-service,
destructive actions and any activity outside the isolated lab.

## 11. Portfolio completion checklist

-   [ ] Repository created and README / architecture diagram committed.
-   [ ] Local Juice Shop instance runs on loopback only.
-   [ ] GitHub Actions workflows committed and successfully executed.
-   [ ] Gitleaks, Semgrep and Trivy reports retained.
-   [ ] Terraform validation and Checkov scan completed.
-   [ ] ZAP baseline report generated against the local target.
-   [ ] Findings triaged and at least one safe remediation/retest
    documented.
-   [ ] Screenshots captured from actual workflow runs.
-   [ ] Branch protection and least-privilege workflow permissions
    configured.
-   [ ] All claims in the README reflect the actual repository state.

## 12. How to present this project

Suggested CV / GitHub portfolio description (update only after
completing the work):

> Designed and documented an end-to-end DevSecOps security lab using
> OWASP Juice Shop, integrating GitHub Actions with secret detection,
> SAST, dependency and container vulnerability scanning, Terraform
> validation, IaC policy checks and OWASP ZAP baseline testing. Produced
> security evidence, triaged findings and documented remediation and
> release-gating procedures.

Suggested interview talking points: - Why security checks are placed at
different stages of the delivery lifecycle. - The difference between
SAST, SCA, secrets scanning, IaC scanning and DAST. - How you decide
whether a finding should block a release. - Why vulnerable applications
must be isolated. - How you protect CI credentials and Terraform
state. - How you validate a fix and demonstrate closure with evidence.

## 13. References

-   [OWASP Juice Shop --- official
    repository](https://github.com/juice-shop/juice-shop)
-   [OWASP Juice Shop --- official project
    site](https://owasp-juice.shop/)
-   [OWASP Juice Shop companion guide: running the
    application](https://pwning.owasp-juice.shop/companion-guide/latest/part1/running.html)
-   [OWASP Juice Shop companion guide: CI/CD and release
    pipelines](https://pwning.owasp-juice.shop/companion-guide/latest/part3/contribution.html)
-   [GitHub Actions documentation](https://docs.github.com/actions)
-   [Terraform
    documentation](https://developer.hashicorp.com/terraform/docs)
-   [Semgrep documentation](https://semgrep.dev/docs/)
-   [Gitleaks](https://github.com/gitleaks/gitleaks)
-   [Trivy documentation](https://trivy.dev/latest/)
-   [Checkov
    documentation](https://www.checkov.io/1.Welcome/What%20%20is%20Checkov.html)
-   [OWASP ZAP documentation](https://www.zaproxy.org/docs/)

------------------------------------------------------------------------

**Author:** John Uwahamen Usiabulu\
**Portfolio note:** This repository is an independent learning and
demonstration lab. OWASP Juice Shop remains the property of its
respective project maintainers. Use the upstream project in accordance
with its licence and attribution requirements.
