#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 INEEDBUG
"""Compile actual production methods with host kernel-boundary fixtures.

This verifies cursor/control-flow behavior, not kernel ABI, firmware or RF.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess


def functions(source):
    pattern = re.compile(r"(?:IOReturn|void)\s+AirportItlwmSkywalkInterface::\s*"
                         r"(setSCAN_REQ(?:Gated)?|getSCAN_RESULT(?:Gated)?|setSCANCACHE_CLEAR|"
                         r"clearSCANCACHEGated|resetScanCursor|scanCursorCommand|recordWiFiDiagnostic)\s*\(")
    found = []
    for match in pattern.finditer(source):
        start = source.index("{", match.end())
        depth = 1
        end = start + 1
        while depth:
            depth += (source[end] == "{") - (source[end] == "}")
            end += 1
        found.append(source[match.start():end])
    conv = source.index("static int convertNodeToScanResult(")
    start = source.index("{", conv)
    depth, end = 1, start + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[conv:end] + "\n\n" + "\n\n".join(found)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("worktree", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_path = args.worktree / "AirportItlwm/AirportItlwmSkywalkInterface.cpp"
    source = source_path.read_text()
    (args.output / "production.inc").write_text(functions(source))
    (args.output / "sys").mkdir(exist_ok=True)
    shutil.copyfile(args.worktree / "itl80211/openbsd/sys/tree.h", args.output / "sys/tree.h")
    shutil.copyfile(args.worktree / "itl80211/openbsd/sys/_null.h", args.output / "sys/_null.h")
    fixture = Path(__file__).with_name("scan_fixture.cpp")
    binary = args.output / "scan-fixture"
    build = subprocess.run(["/usr/bin/clang++", "-std=c++14", "-DAIRPORT_WCL", "-D__IO80211_TARGET=150200",
                            "-D__MAC_15_2=150200", "-DHP14_WIFI_DIAGNOSTICS=1", "-O1", "-g", "-fsanitize=address,undefined",
                            "-fno-omit-frame-pointer", "-I", str(args.output), str(fixture), "-o", str(binary)],
                           capture_output=True, text=True)
    (args.output / "compile.log").write_text(build.stdout + build.stderr)
    if build.returncode:
        print(json.dumps({"compile_exit":build.returncode,"log":str(args.output / "compile.log")}))
        return 2
    names = ["restart_after_last_result", "restart_after_partial_read", "cache_freed_between_reads",
             "cache_clear_starts_new_enumeration", "rates_are_copied", "init_rejection_preserved",
             "complete_list_and_eof", "passive_scan_does_not_start_active_bgscan",
             "scan_request_emits_numeric_diagnostic", "diagnostic_is_line_delimited",
             "rate_count_is_bounded", "unavailable_gate_is_rejected", "stopping_is_rejected",
             "active_scan_preserves_cache"]
    results = []
    for name in names:
        run = subprocess.run([str(binary), name], capture_output=True, text=True, timeout=10)
        (args.output / (name + ".log")).write_text(run.stdout + run.stderr)
        results.append({"test":name,"exit":run.returncode,"first_line":(run.stdout+run.stderr).splitlines()[:2]})
    report = {"source_sha256":hashlib.sha256(source.encode()).hexdigest(),"compiled_actual_methods":True,
              "compile_exit":0,"tests":results,"pass":sum(r["exit"]==0 for r in results),
              "fail":sum(r["exit"]!=0 for r in results),"limits":"Host fixtures are not kernel/firmware/RF validation."}
    (args.output / "result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
    return 1 if report["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
