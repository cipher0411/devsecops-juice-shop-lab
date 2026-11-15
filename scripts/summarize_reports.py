#!/usr/bin/env python3
"""Summarise scanner reports into Markdown (stdlib only).

Usage:
    python scripts/summarize_reports.py [REPORTS_DIR] >> "$GITHUB_STEP_SUMMARY"

Every section is optional: a missing report is listed as "not run" rather
than silently skipped, so a scanner that failed to produce output is
visible to the reviewer (fail-closed reporting).
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]


def load(path: pathlib.Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def row(*cells) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def counts_row(counter: collections.Counter) -> str:
    return " / ".join(f"{s[0]}:{counter.get(s, 0)}" for s in SEVERITIES)


def gitleaks(reports: pathlib.Path, out: list[str]) -> None:
    out.append("### Secrets - Gitleaks")
    out.append(row("Scope", "Findings", "By rule"))
    out.append(row("---", "---", "---"))
    for name, label in [
        ("gitleaks-repo.json", "This repo (full git history) - **gating**"),
        ("gitleaks-juice-shop-source.json", "Juice Shop source - informational"),
    ]:
        data = load(reports / "gitleaks" / name)
        if data is None:
            out.append(row(label, "not run", "-"))
            continue
        rules = collections.Counter(f["RuleID"] for f in data)
        out.append(row(label, len(data), ", ".join(f"{k} {v}" for k, v in rules.most_common()) or "-"))
    out.append("")


def semgrep(reports: pathlib.Path, out: list[str]) -> None:
    out.append("### SAST - Semgrep")
    out.append(row("Scope", "Files scanned", "Findings", "ERROR / WARNING / INFO", "Top rules"))
    out.append(row("---", "---", "---", "---", "---"))
    for name, label in [
        ("semgrep-repo.json", "This repo - **gating**"),
        ("semgrep-juice-shop.json", "Juice Shop source - informational"),
    ]:
        data = load(reports / "semgrep" / name)
        if data is None:
            out.append(row(label, "-", "not run", "-", "-"))
            continue
        results = data["results"]
        sev = collections.Counter(r["extra"]["severity"] for r in results)
        top = collections.Counter(r["check_id"].split(".")[-1] for r in results).most_common(3)
        out.append(row(
            label,
            len(data.get("paths", {}).get("scanned", [])),
            len(results),
            f"{sev.get('ERROR', 0)} / {sev.get('WARNING', 0)} / {sev.get('INFO', 0)}",
            ", ".join(f"`{k}` {v}" for k, v in top) or "-",
        ))
    out.append("")


def trivy(reports: pathlib.Path, out: list[str]) -> None:
    out.append("### SCA, container and misconfiguration - Trivy")
    out.append(row("Scope", "Vulnerabilities (C/H/M/L/U)", "Fixable", "Misconfig (C/H/M/L/U)", "Secrets"))
    out.append(row("---", "---", "---", "---", "---"))
    for name, label in [
        ("trivy-config-repo.json", "This repo IaC - **gating**"),
        ("trivy-image.json", "Juice Shop image (digest-pinned)"),
        ("trivy-fs-juice-shop.json", "Juice Shop source tree"),
    ]:
        data = load(reports / "trivy" / name)
        if data is None:
            out.append(row(label, "not run", "-", "-", "-"))
            continue
        vulns, misconf = collections.Counter(), collections.Counter()
        fixable = secrets = 0
        for result in data.get("Results", []) or []:
            for v in result.get("Vulnerabilities") or []:
                vulns[v["Severity"]] += 1
                fixable += bool(v.get("FixedVersion"))
            for m in result.get("Misconfigurations") or []:
                if m.get("Status", "FAIL") == "FAIL":
                    misconf[m["Severity"]] += 1
            secrets += len(result.get("Secrets") or [])
        out.append(row(label, counts_row(vulns), fixable, counts_row(misconf), secrets))
    out.append("")


def checkov(reports: pathlib.Path, out: list[str]) -> None:
    out.append("### IaC policy - Checkov (built-in + CKV2_LAB_* custom policies)")
    out.append(row("Run", "Passed", "Failed", "Failed checks"))
    out.append(row("---", "---", "---", "---"))
    runs = sorted(p for p in (reports / "checkov").glob("*/results_json.json"))
    if not runs:
        out.append(row("checkov", "-", "not run", "-"))
    for path in runs:
        data = load(path)
        data = data[0] if isinstance(data, list) else data
        failed = data["results"].get("failed_checks", [])
        out.append(row(
            path.parent.name,
            data["summary"]["passed"],
            data["summary"]["failed"],
            ", ".join(sorted({f["check_id"] for f in failed})) or "-",
        ))
    out.append("")


def zap(reports: pathlib.Path, out: list[str]) -> None:
    out.append("### DAST - OWASP ZAP baseline")
    data = load(reports / "zap" / "zap-baseline.json")
    if data is None:
        out.append("ZAP report: not run")
        out.append("")
        return
    out.append(row("Risk", "Alert", "Plugin", "Instances"))
    out.append(row("---", "---", "---", "---"))
    order = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}
    alerts = [a for site in data.get("site", []) for a in site.get("alerts", [])]
    alerts.sort(key=lambda a: (order.get(a["riskdesc"].split()[0], 9), a["alert"]))
    for a in alerts:
        out.append(row(a["riskdesc"].split(" (")[0], a["alert"], a["pluginid"], a["count"]))
    out.append("")


def main() -> int:
    reports = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "reports")
    out = ["## Security scan summary", ""]
    for section in (gitleaks, semgrep, trivy, checkov, zap):
        section(reports, out)
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
