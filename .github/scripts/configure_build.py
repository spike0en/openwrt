#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenWrt Build Configuration Generator and Package Auditor.

Validates user-requested package lists, generates a seed .config for the chosen
target architecture and device profile, executes 'make defconfig' for dependency
resolution, and verifies that no requested package was dropped due to unsatisfied
dependencies or invalid package feeds.
"""

import argparse
import os
import re
import subprocess
import sys
from typing import List, Set


def parse_and_validate_packages(raw_packages: str) -> List[str]:
    """
    Parse a space-, comma-, or newline-delimited string of package names and validate identifiers.

    Strips inline comments and empty lines, removes duplicates while preserving order,
    and enforces OpenWrt package identifier rules to prevent shell injection.

    Args:
        raw_packages: Raw package input string from workflow or CLI.

    Returns:
        List of sanitized, unique package names.

    Raises:
        ValueError: If any token contains characters outside [a-zA-Z0-9_-+@.].
    """
    if not raw_packages:
        return []

    # Treat commas as whitespace delimiters for user convenience
    raw_packages = raw_packages.replace(",", " ")

    packages: List[str] = []
    lines = raw_packages.splitlines()

    for line in lines:
        # Strip comments and surrounding whitespace
        line = line.split("#")[0].strip()
        if not line:
            continue

        for token in line.split():
            token = token.strip()
            if not token:
                continue

            # Strict identifier validation prevents command injection / shell metacharacters
            if not re.match(r"^[a-zA-Z0-9_\-+@.]+$", token):
                raise ValueError(
                    f"Invalid package name '{token}'. Package names may only contain "
                    f"alphanumeric characters, hyphens, underscores, pluses, dots, and '@'."
                )

            if token not in packages:
                packages.append(token)

    return packages


def generate_seed_config(
    target: str,
    subtarget: str,
    profile: str,
    packages: List[str],
    output_path: str = ".config"
) -> str:
    """
    Write initial seed .config with target, subtarget, device profile, and packages.

    Args:
        target: OpenWrt target architecture (e.g. 'ath79').
        subtarget: OpenWrt subtarget (e.g. 'generic').
        profile: Device profile ID (e.g. 'tplink_archer-a9-v6').
        packages: List of validated custom packages to enable as built-in.
        output_path: Destination path for the seed config file.

    Returns:
        The generated .config content string.
    """
    lines = [
        "# Auto-generated OpenWrt configuration seed",
        f"CONFIG_TARGET_{target}=y",
        f"CONFIG_TARGET_{target}_{subtarget}=y",
        f"CONFIG_TARGET_{target}_{subtarget}_DEVICE_{profile}=y",
    ]

    # Force built-in (=y) so packages are baked directly into the generated rootfs
    for pkg in packages:
        lines.append(f"CONFIG_PACKAGE_{pkg}=y")

    config_content = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(config_content)

    return config_content


def verify_packages_in_config(config_path: str, requested_packages: List[str]) -> List[str]:
    """
    Audit .config after 'make defconfig' to ensure requested packages were not silently dropped.

    OpenWrt's Kconfig parser silently drops undefined symbols during defconfig expansion.
    This check catches typos or missing feed packages before expensive compilation starts.

    Args:
        config_path: Path to the generated .config file.
        requested_packages: List of package names requested by the user.

    Returns:
        List of missing package names.
    """
    if not os.path.exists(config_path):
        return requested_packages

    with open(config_path, "r", encoding="utf-8", errors="ignore") as f:
        config_lines: Set[str] = set(line.strip() for line in f if line.strip())

    missing: List[str] = []
    for pkg in requested_packages:
        symbol_y = f"CONFIG_PACKAGE_{pkg}=y"
        symbol_m = f"CONFIG_PACKAGE_{pkg}=m"
        # Accept built-in (=y) or module (=m)
        if symbol_y not in config_lines and symbol_m not in config_lines:
            missing.append(pkg)

    return missing


def main():
    parser = argparse.ArgumentParser(description="Configure OpenWrt build and validate package inclusion.")
    parser.add_argument("--target", required=True, help="Target architecture (e.g. ath79)")
    parser.add_argument("--subtarget", required=True, help="Subtarget (e.g. generic)")
    parser.add_argument("--profile", required=True, help="Device profile ID (e.g. tplink_archer-a9-v6)")
    parser.add_argument("--packages", default="", help="Multiline or space-separated package list")
    parser.add_argument("--config-file", default=".config", help="Path to .config file to write/validate")
    parser.add_argument("--run-defconfig", action="store_true", help="Execute 'make defconfig' and verify packages")
    parser.add_argument("--repo-dir", default=".", help="Root of OpenWrt repository")

    args = parser.parse_args()

    try:
        packages = parse_and_validate_packages(args.packages)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print("========================================")
    print(" Configuring OpenWrt Target:")
    print(f"   Target:    {args.target}")
    print(f"   Subtarget: {args.subtarget}")
    print(f"   Profile:   {args.profile}")
    print(f"   Requested Custom Packages ({len(packages)}):")
    for pkg in packages:
        print(f"     + {pkg}")
    print("========================================")

    config_file_path = os.path.join(args.repo_dir, args.config_file)
    generate_seed_config(args.target, args.subtarget, args.profile, packages, config_file_path)
    print(f"Seed configuration written to {config_file_path}")

    if args.run_defconfig:
        print("\nRunning 'make defconfig' to expand dependencies and finalize configuration...")
        result = subprocess.run(["make", "defconfig"], cwd=args.repo_dir, text=True)
        if result.returncode != 0:
            print("ERROR: 'make defconfig' failed.", file=sys.stderr)
            sys.exit(result.returncode)

        print("'make defconfig' completed successfully.")

        missing_packages = verify_packages_in_config(config_file_path, packages)
        if missing_packages:
            print(
                "\nERROR: The following requested packages could not be selected in the OpenWrt configuration:",
                file=sys.stderr
            )
            for mp in missing_packages:
                print(f"  - {mp}", file=sys.stderr)
            print(
                "\nPlease verify that the package names are spelled correctly and available in the installed feeds.",
                file=sys.stderr
            )
            sys.exit(1)

        print("\nAll requested custom packages were successfully verified in .config!")


if __name__ == "__main__":
    main()
