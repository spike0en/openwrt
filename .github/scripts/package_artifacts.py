#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenWrt Artifact Packager and Release Notes Generator.

Collects compiled firmware images, manifests, and buildinfo files from
bin/targets/<target>/<subtarget>/, calculates SHA256 checksums, and formats
build-metadata.json and Markdown release_notes.md for GitHub Releases.
"""

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Tuple


def calculate_sha256(filepath: str) -> str:
    """
    Calculate the SHA256 checksum of a file using 64KB chunked reads.

    Args:
        filepath: Path to the target file.

    Returns:
        Hexadecimal 64-character SHA256 string.
    """
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def human_size(bytes_val: int) -> str:
    """
    Format byte count into a readable binary unit string (B, KB, MB, GB).

    Args:
        bytes_val: Size in bytes.

    Returns:
        Formatted string (e.g. '15.36 MB').
    """
    val = float(bytes_val)
    for unit in ["B", "KB", "MB", "GB"]:
        if val < 1024.0:
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{val:.2f} TB"


def get_git_info(repo_dir: str = ".") -> Tuple[str, str, str]:
    """
    Retrieve current git commit SHA, short SHA, and branch name.

    Args:
        repo_dir: Path to the OpenWrt git repository.

    Returns:
        Tuple of (full_commit_sha, short_commit_sha, branch_name).
    """
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_dir, text=True).strip()
    except Exception:
        commit_sha = os.environ.get("GITHUB_SHA", "unknown")

    try:
        short_sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir, text=True).strip()
    except Exception:
        short_sha = commit_sha[:8] if len(commit_sha) >= 8 else commit_sha

    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir, text=True).strip()
    except Exception:
        branch = os.environ.get("GITHUB_REF_NAME", "unknown")

    return commit_sha, short_sha, branch


def get_openwrt_version(repo_dir: str = ".", target_bin_dir: str = "") -> str:
    """
    Extract OpenWrt version/revision from buildinfo or getver.sh.

    Args:
        repo_dir: Path to the OpenWrt git repository.
        target_bin_dir: Path to target output directory.

    Returns:
        Formatted OpenWrt version string (e.g. 'SNAPSHOT (r35715-9fec0086ac)').
    """
    check_paths = [
        os.path.join(target_bin_dir, "version.buildinfo"),
        os.path.join(repo_dir, "version.buildinfo"),
        os.path.join(repo_dir, "artifact", "version.buildinfo"),
    ]
    for p in check_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    ver = f.read().strip()
                    if ver:
                        return f"SNAPSHOT ({ver})" if not ver.startswith("SNAPSHOT") and not ver.startswith("OpenWrt") else ver
            except Exception:
                pass

    getver_sh = os.path.join(repo_dir, "scripts", "getver.sh").replace("\\", "/")
    if os.path.exists(getver_sh):
        try:
            res = subprocess.check_output(["bash", "scripts/getver.sh"], cwd=repo_dir, text=True).strip()
            if res:
                return f"SNAPSHOT ({res})"
        except Exception:
            pass

    return "SNAPSHOT"


def verify_qcn5502_patch(repo_dir: str = ".") -> Tuple[bool, str]:
    """
    Verify whether the QCN5502 2.4 GHz wireless patch is present and active in the DTS.

    Args:
        repo_dir: Path to the OpenWrt git repository.

    Returns:
        Tuple of (is_active, status_message).
    """
    dts_path = os.path.join(repo_dir, "target/linux/ath79/dts/qcn5502_tplink_archer-a9-v6.dts")
    if not os.path.exists(dts_path):
        return False, "DTS file not found"

    with open(dts_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if 'compatible = "qca,qcn5502-wifi"' in content and 'status = "okay"' in content:
        return True, "Active (ath9k QCN5502 2.4 GHz wireless enabled in device tree)"
    return False, "Disabled or missing in device tree"


def main():
    parser = argparse.ArgumentParser(description="Package OpenWrt firmware artifacts and generate release notes.")
    parser.add_argument("--target", required=True, help="Target architecture (e.g. ath79)")
    parser.add_argument("--subtarget", required=True, help="Subtarget (e.g. generic)")
    parser.add_argument("--profile", required=True, help="Device profile ID (e.g. tplink_archer-a9-v6)")
    parser.add_argument("--device-name", required=True, help="Human readable device name")
    parser.add_argument("--router-slug", required=True, help="Clean router slug (e.g. archer-a9-v6)")
    parser.add_argument("--packages", default="", help="Custom packages requested")
    parser.add_argument("--repo-dir", default=".", help="Root of OpenWrt repository")
    parser.add_argument("--bin-dir", default="bin/targets", help="Base directory for built targets")
    parser.add_argument("--out-dir", default="artifact", help="Output artifact directory")
    parser.add_argument("--notes-file", default="release_notes.md", help="Destination file for release notes markdown")

    args = parser.parse_args()

    commit_sha, short_sha, branch = get_git_info(args.repo_dir)
    target_bin_dir = os.path.join(args.repo_dir, args.bin_dir, args.target, args.subtarget)

    os.makedirs(args.out_dir, exist_ok=True)

    custom_packages = [
        p.strip() for p in re.split(r"[\s,\n]+", args.packages)
        if p.strip() and not p.strip().startswith("#")
    ]

    qcn_active, qcn_status = verify_qcn5502_patch(args.repo_dir)
    openwrt_ver = get_openwrt_version(args.repo_dir, target_bin_dir)

    print(f"Scanning for firmware files in: {target_bin_dir}")

    artifact_files: List[str] = []
    if os.path.exists(target_bin_dir):
        search_patterns = [
            f"*{args.profile}*",
            f"*{args.router_slug}*",
            "sha256sums",
            "config.buildinfo",
            "feeds.buildinfo",
            "version.buildinfo",
        ]
        found_set = set()
        for pat in search_patterns:
            for filepath in glob.glob(os.path.join(target_bin_dir, pat)):
                if os.path.isfile(filepath) and filepath not in found_set:
                    found_set.add(filepath)
                    dest_path = os.path.join(args.out_dir, os.path.basename(filepath))
                    shutil.copy2(filepath, dest_path)
                    artifact_files.append(dest_path)

    artifacts_meta: List[Dict[str, any]] = []
    for fpath in sorted(artifact_files):
        fname = os.path.basename(fpath)
        fsize = os.path.getsize(fpath)
        fsha = calculate_sha256(fpath)
        artifacts_meta.append({
            "filename": fname,
            "size_bytes": fsize,
            "size_human": human_size(fsize),
            "sha256": fsha,
        })

    build_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    tag_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    release_tag = f"{args.router_slug}-{tag_date}"
    release_title = f"OpenWrt {args.device_name} ({short_sha})"

    metadata = {
        "build_timestamp_utc": build_date,
        "release_tag": release_tag,
        "release_title": release_title,
        "openwrt_version": openwrt_ver,
        "commit_sha": commit_sha,
        "commit_short": short_sha,
        "branch": branch,
        "device_name": args.device_name,
        "target": args.target,
        "subtarget": args.subtarget,
        "profile": args.profile,
        "router_slug": args.router_slug,
        "qcn5502_patch_active": qcn_active,
        "qcn5502_patch_status": qcn_status,
        "custom_packages": custom_packages,
        "artifacts_count": len(artifacts_meta),
        "artifacts": artifacts_meta,
    }

    meta_json_path = os.path.join(args.out_dir, "build-metadata.json")
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    notes = [
        f"# OpenWrt Firmware for {args.device_name}\n",
        "## Build Specifications\n",
        "| Parameter | Value |",
        "| :--- | :--- |",
        f"| **OpenWrt Version** | `{openwrt_ver}` |",
        f"| **Device Model** | **{args.device_name}** |",
        f"| **Target / Subtarget** | `{args.target}/{args.subtarget}` |",
        f"| **Build Date** | `{build_date}` |\n",
        "## 2.4 GHz QCN5502 Wireless Support\n",
        "> [!IMPORTANT]\n"
        "> Built with the [2.4 GHz wireless support patch](https://github.com/spike0en/openwrt/commit/5521d5daaf58a34ba229b3e4a8208cdd218440c9) for Qualcomm **QCN5502** (`ath9k`), "
        "originally developed by [@looi](https://github.com/looi) in [openwrt#9389](https://github.com/openwrt/openwrt/pull/9389) and subsequently rebased for modern OpenWrt kernel trees by [@deralmas](https://github.com/deralmas) in [openwrt#24342](https://github.com/openwrt/openwrt/pull/24342) ([commit ff3f2fe](https://github.com/openwrt/openwrt/pull/24342/changes/ff3f2fe5fc75efd1976e3d05349b45205d76ece9)).\n",
        "## Included Custom Packages\n",
        "The following custom packages and all their required dependencies were built directly into the firmware image:\n",
    ]

    if custom_packages:
        notes.extend([
            "```text",
            ", ".join(custom_packages),
            "```\n",
        ])
    else:
        notes.extend([
            "```text",
            "Default profile package selection (no additional custom packages specified)",
            "```\n",
        ])

    notes.extend([
        "## Installation Instructions\n",
        "- **First Time Flash (from Stock Vendor Firmware)**: Use the `*factory*` image through the vendor's web upgrade page or TFTP recovery.",
        "- **Upgrade (from existing OpenWrt)**: Use the `*sysupgrade*` image through LuCI (**System** → **Backup / Flash Firmware**) or CLI `sysupgrade -v <image.bin>`.",
    ])

    release_notes_path = args.notes_file
    notes_dir = os.path.dirname(release_notes_path)
    if notes_dir:
        os.makedirs(notes_dir, exist_ok=True)

    with open(release_notes_path, "w", encoding="utf-8") as f:
        f.write("\n".join(notes) + "\n")

    if "GITHUB_ENV" in os.environ:
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
            f.write(f"RELEASE_TAG={release_tag}\n")
            f.write(f"RELEASE_TITLE={release_title}\n")
            f.write(f"BUILD_DATE={tag_date}\n")

    print(f"Artifacts successfully packaged into '{args.out_dir}':")
    print(f"  - Metadata: {meta_json_path}")
    print(f"  - Release notes: {release_notes_path}")
    print(f"  - Total files collected: {len(artifacts_meta)}")


if __name__ == "__main__":
    main()
