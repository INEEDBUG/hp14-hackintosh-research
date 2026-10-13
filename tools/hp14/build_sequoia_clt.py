#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 INEEDBUG
"""Build only the pinned Sequoia x86_64 target with existing CLT/SDK. Never install."""
from pathlib import Path
import argparse, concurrent.futures, datetime, hashlib, json, plistlib, subprocess, sys
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("worktree",type=Path)
parser.add_argument("output",type=Path)
parser.add_argument("--sdk",type=Path,help="Existing MacKernelSDK checkout; defaults to worktree/MacKernelSDK")
parser.add_argument("--diagnostics",choices=[0,1],type=int,default=0)
args=parser.parse_args()
w=args.worktree.resolve()
out=args.output.resolve()
sdk=(args.sdk or w/"MacKernelSDK").resolve()
pin="f26a3afc8a0eecd6995ebdba48498f36bac107ad"
if subprocess.check_output(["git","rev-parse","HEAD"],cwd=w,text=True).strip()!=pin:
    raise SystemExit("Source HEAD does not match the reviewed upstream pin")
if not (sdk/"Headers").is_dir():
    raise SystemExit("Existing MacKernelSDK headers are required; this script does not install them")
clang=subprocess.check_output(["/usr/bin/xcrun","--find","clang++"],text=True).strip()
macsdk=subprocess.check_output(["/usr/bin/xcrun","--sdk","macosx","--show-sdk-path"],text=True).strip()
resource=subprocess.check_output([clang,"-print-resource-dir"],text=True).strip()
flags=["-arch","x86_64","-isysroot",macsdk,"-std=gnu++14","-nostdinc",
       "-isystem",str(sdk/"Headers"),"-isystem",macsdk+"/usr/include/c++/v1",
       "-isystem",resource+"/include","-include",str(w/"itlwm/PrivateSPI.pch"),
       "-DKERNEL=1","-DKERNEL_PRIVATE=1","-DPRIVATE=1","-DIEEE80211_STA_ONLY",
       "-DAIRPORT_WCL","-DAIRPORT","-D__PRIVATE_SPI__","-DIO80211FAMILY_V2",
       "-D__IO80211_TARGET=__MAC_15_2",'-DITLWM_VERSION="2.4.0"','-DGIT_COMMIT="_hp14offline"',
       "-fapple-kext","-mkernel","-fno-exceptions","-fno-rtti","-fno-builtin","-fno-common",
       "-mno-red-zone","-fstack-protector-strong","-mmacosx-version-min=15.2","-O1",
       "-Wno-deprecated-register","-DHP14_WIFI_DIAGNOSTICS="+str(args.diagnostics),
       "-ffile-prefix-map="+str(w)+"=source","-ffile-prefix-map="+str(sdk)+"=MacKernelSDK"]
for inc in ["itl80211/openbsd","itl80211","include","include/Airport","AirportItlwm",
            "itlwm","itlwm/hal_iwm","itlwm/hal_iwx","itlwm/hal_iwn","itl80211/linux"]:
    flags.extend(["-I",str(w/inc)])
out.mkdir(parents=True,exist_ok=True)
objects=out/"objects"; logs=out/"logs"
objects.mkdir(exist_ok=True);logs.mkdir(exist_ok=True)
project=json.loads(subprocess.check_output(["/usr/bin/plutil","-convert","json","-o","-",str(w/"itlwm.xcodeproj/project.pbxproj")]))
obj=project["objects"];proj=obj[project["rootObject"]]
target=next(v for v in obj.values() if v.get("isa")=="PBXNativeTarget" and v.get("name")=="AirportItlwm-Sequoia")
paths={}
def visit(ident,parent):
    node=obj[ident]; path=node.get("path","")
    tree=node.get("sourceTree","<group>")
    here=(w/path) if tree=="SOURCE_ROOT" else parent/path
    if node["isa"] in ["PBXGroup","PBXVariantGroup"]:
        for child in node.get("children",[]):visit(child,here)
    else:paths[ident]=here
visit(proj["mainGroup"],w)
sources=[];empty_refs=[]
for phaseid in target["buildPhases"]:
    phase=obj[phaseid]
    if phase["isa"]!="PBXSourcesBuildPhase":continue
    for buildid in phase["files"]:
        ref=obj[buildid].get("fileRef")
        if not ref:empty_refs.append(buildid);continue
        if ref not in paths:
            node=obj[ref]
            if node.get("sourceTree")!="SOURCE_ROOT":
                raise ValueError("Unresolved non-root source ref: "+ref)
            paths[ref]=w/node["path"]
        sources.append(paths[ref])
start=datetime.datetime.now(datetime.timezone.utc)
firmware=w/"include/FwBinary.cpp"
if not firmware.exists():
    generated=subprocess.run(["/usr/bin/python3",str(w/"scripts/zlib_compress_fw.py"),str(firmware),str(w/"itlwm/firmware")],capture_output=True)
    (logs/"firmware-generator.log").write_bytes(generated.stdout+generated.stderr)
    if generated.returncode:raise SystemExit("Firmware source generation failed; nothing executed on hardware")
missing=[str(p) for p in sources if not p.exists()]
if missing:raise SystemExit("Missing source paths: "+repr(missing))
def compile_one(source):
    name=str(source.relative_to(w)).replace("/","__")
    dest=objects/(name+".o")
    command=[clang,*flags,"-c",str(source),"-o",str(dest)]
    proc=subprocess.run(command,cwd=w,capture_output=True,timeout=240)
    (logs/(name+".log")).write_bytes(proc.stdout+proc.stderr)
    errors=[line for line in proc.stderr.decode(errors="replace").splitlines() if "error:" in line]
    return {"source":str(source.relative_to(w)),"exit":proc.returncode,"object":str(dest),"errors":errors[:8],
            "warning_count":proc.stderr.count(b"warning:")}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    compiled=list(pool.map(compile_one,sources))
result={"start_utc":start.isoformat(),"source_pin":"f26a3afc8a0eecd6995ebdba48498f36bac107ad",
        "target":"AirportItlwm-Sequoia","arch":"x86_64","sources":compiled,
        "empty_upstream_source_refs_skipped":empty_refs,"installed":False,
        "firmware_scope":"Compile-time embedding only; no firmware execution, flash or radio control"}
(out/"compile-result.json").write_text(json.dumps(result,indent=2)+"\n")
failed=[x for x in compiled if x["exit"]]
if failed:
    print(json.dumps({"compiled":len(compiled),"failed":failed,"result":str(out/"compile-result.json")}))
    raise SystemExit(20)
module=out/"module-info.c"
module.write_text('#include <mach/mach_types.h>\n#include <mach/kmod.h>\nextern kern_return_t _start(kmod_info_t *, void *);\nextern kern_return_t _stop(kmod_info_t *, void *);\nKMOD_EXPLICIT_DECL(com.zxystd.AirportItlwm, "2.4.0", _start, _stop)\n__private_extern__ kmod_start_func_t *_realmain = 0;\n__private_extern__ kmod_stop_func_t *_antimain = 0;\n__private_extern__ int _kext_apple_cc = __APPLE_CC__;\n')
module_obj=objects/"module-info.o"
proc=subprocess.run([clang,"-x","c","-arch","x86_64","-nostdinc","-isystem",str(sdk/"Headers"),
                     "-DKERNEL=1","-DPRIVATE=1","-fapple-kext","-mkernel","-fno-builtin","-fno-common",
                     "-c",str(module),"-o",str(module_obj)],capture_output=True)
(logs/"module-info.log").write_bytes(proc.stdout+proc.stderr)
if proc.returncode:
    print(json.dumps({"module_exit":proc.returncode,"diagnostics":proc.stderr.decode()[:2500]}))
    raise SystemExit(21)
bundle=out/"AirportItlwm.kext";binary=bundle/"Contents/MacOS/AirportItlwm"
binary.parent.mkdir(parents=True,exist_ok=True)
resource=subprocess.check_output([clang,"-print-resource-dir"],text=True).strip()
ld=subprocess.check_output(["/usr/bin/xcrun","--find","ld"],text=True).strip()
macsdk=subprocess.check_output(["/usr/bin/xcrun","--sdk","macosx","--show-sdk-path"],text=True).strip()
command=[ld,"-arch","x86_64","-kext","-static","-syslibroot",macsdk,
         "-L",str(sdk/"Library/x86_64"),"-L",str(sdk/"Library/universal"),
         "-o",str(binary),*[x["object"] for x in compiled],str(module_obj),
         resource+"/lib/darwin/libclang_rt.cc_kext.a","-lkmod","-lkmodc++"]
proc=subprocess.run(command,capture_output=True,timeout=60)
(logs/"link.log").write_bytes(proc.stdout+proc.stderr)
if proc.returncode:
    print(json.dumps({"link_exit":proc.returncode,"diagnostics":proc.stderr.decode()[:4500]}))
    raise SystemExit(22)
info=plistlib.loads((w/"AirportItlwm/WCL/Sequoia-Info.plist").read_bytes())
info["CFBundleVersion"]="2.4.0";info["CFBundleShortVersionString"]="2.4.0"
info["CFBundleIdentifier"]="com.zxystd.AirportItlwm";info["CFBundleExecutable"]="AirportItlwm"
info["CFBundleDevelopmentRegion"]="en";info["CFBundleName"]="AirportItlwm"
info["CFBundlePackageType"]="KEXT"
info["HP14OfflineExperimental"]=True
if "$(" in json.dumps(info):
    raise SystemExit("Unresolved Xcode substitution remains in bundle metadata")
(bundle/"Contents/Info.plist").write_bytes(plistlib.dumps(info))
(bundle/"Contents/PkgInfo").write_bytes(b"KEXT????")
result.update({"end_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"all_sources_compiled":True,
               "link_exit":0,"bundle":str(bundle),"binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
               "loadability":"UNVERIFIED","physical_wifi_fixes":"UNVERIFIED"})
(out/"BUILD-RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="sources"}))
