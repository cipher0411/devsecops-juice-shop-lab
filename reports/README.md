# Evidence

Reports committed here came from **real local runs** on 2026-11-15
(see `docs/test-plan.md` for versions and digests). Every CI run also
uploads fresh copies as workflow artifacts (30-day retention).

| Path | Produced by | Notes |
|---|---|---|
| `gitleaks/gitleaks-repo.json` | Gitleaks, this repo's full history | `[]` = no leaks |
| `gitleaks/gitleaks-juice-shop-source.json` | Gitleaks, Juice Shop v20.4.0 source | `--redact`: secret values are not in the report |
| `semgrep/semgrep-repo.{json,sarif}` | Semgrep gating scan of this repo | 0 findings |
| `semgrep/semgrep-juice-shop.{json,sarif}` | Semgrep on Juice Shop source | 923 files, 90 findings |
| `trivy/trivy-image.json` | Trivy, digest-pinned Juice Shop image | 113 vulnerabilities |
| `trivy/trivy-fs-juice-shop.json` | Trivy fs (vuln, misconfig, secret) on source | upstream's own AWS Terraform misconfigurations |
| `trivy/trivy-config-repo-before-fix.json` → `trivy-config-repo.json` | Trivy config on this repo | LAB-OPS-03 before / after |
| `checkov/baseline` → `checkov/retest` → `checkov/final` | Checkov + `CKV2_LAB_*` | 6 failed → 0 failed |
| `zap-pre-isolation/` | ZAP before LAB-OPS-01 | `site[]` shows 28 hosts contacted |
| `zap/` | ZAP after the fix (hermetic image, internal network) | only `http://juice-shop:3000` |
| `validation/manual-validation.md` | Manual safe reproduction | tokens redacted, never stored |

Sanitisation: Gitleaks over `reports/` finds 0 secrets. Git author metadata
was stripped from the Trivy config reports. Private IPs in the ZAP reports
belong to the ephemeral Docker network.
