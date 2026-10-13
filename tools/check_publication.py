#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 INEEDBUG
"""Bounded text/privacy checks; a successful scan does not replace human review."""
from pathlib import Path
import ipaddress
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "private-key": re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|ENCRYPTED) PRIVATE KEY-----"),
    "access-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,})\b"),
    "personal-home-path": re.compile(r"(?:[A-Za-z]:[\\/]Users[\\/][^\s<>]+|/" + r"Users/[^\s<>/]+|/" + r"home/[^\s<>/]+)"),
    "credential-assignment": re.compile(r"(?im)^\s*(?:password|passwd|api_key|access_token|refresh_token)\s*[:=]\s*['\"][^'\"]+['\"]"),
    "mac-address": re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"),
}


def main():
    proc = subprocess.run(["git", "ls-files", "-z", "--cached"], cwd=ROOT, capture_output=True)
    if proc.returncode or not proc.stdout:
        print("Stage the intended publication files before checking.")
        return 2
    paths = [ROOT / p for p in proc.stdout.decode().split("\0") if p]
    findings = []
    for path in paths:
        name = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            findings.append({"file": name, "category": "symlink"})
            continue
        staged = subprocess.check_output(["git", "show", ":" + name], cwd=ROOT)
        if staged != path.read_bytes():
            findings.append({"file": name, "category": "unstaged-drift"})
        try:
            body = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            findings.append({"file": name, "category": "non-text-or-unreadable"})
            continue
        for category, pattern in RULES.items():
            for match in pattern.finditer(body):
                findings.append({"file": name, "line": body[:match.start()].count("\n") + 1,
                                 "category": category})
        for match in re.finditer(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", body):
            try:
                addr = ipaddress.ip_address(match.group())
            except ValueError:
                continue
            if not any(addr in net for net in map(ipaddress.ip_network,
                    ["192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"])):
                findings.append({"file": name, "category": "non-example-ipv4"})
        if path.suffix == ".json":
            json.loads(body)
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", body):
                if "://" not in target and not (path.parent / target.split("#")[0]).exists():
                    findings.append({"file": name, "category": "broken-local-link"})
    print(json.dumps({"files_checked": len(paths), "findings": findings,
                      "scope": "Tracked text, selected patterns, JSON and local Markdown links; manual review required."}))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
