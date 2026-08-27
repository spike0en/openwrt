#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenWrt Router Model Resolver for Supported QCN5502 Devices."""

import argparse
import os
import re
import sys
from typing import Dict

# Curated static configuration for supported QCN5502 devices
DEVICES: Dict[str, Dict[str, str]] = {
    "tplink_archer-a9-v6": {
        "name": "TP-Link Archer A9 v6",
        "target": "ath79",
        "subtarget": "generic",
        "profile": "tplink_archer-a9-v6",
        "slug": "archer-a9-v6",
        "packages": "kmod-usb2 kmod-usb-ledtrig-usbport kmod-ath10k-ct ath10k-firmware-qca9984-ct",
    },
    "asus_rt-ac59u-v2": {
        "name": "ASUS RT-AC59U v2",
        "target": "ath79",
        "subtarget": "generic",
        "profile": "asus_rt-ac59u-v2",
        "slug": "rt-ac59u-v2",
        "packages": "kmod-usb2 kmod-usb-ledtrig-usbport kmod-ath10k-ct ath10k-firmware-qca9888-ct",
    },
    "asus_rt-ac59u": {
        "name": "ASUS RT-AC59U",
        "target": "ath79",
        "subtarget": "generic",
        "profile": "asus_rt-ac59u",
        "slug": "rt-ac59u",
        "packages": "kmod-usb2 kmod-usb-ledtrig-usbport kmod-ath10k-ct ath10k-firmware-qca9888-ct",
    },
    "asus_zenwifi-cd6n": {
        "name": "ASUS ZenWiFi CD6N",
        "target": "ath79",
        "subtarget": "generic",
        "profile": "asus_zenwifi-cd6n",
        "slug": "zenwifi-cd6n",
        "packages": "kmod-ath10k-ct ath10k-firmware-qca9888-ct",
    },
    "asus_zenwifi-cd6r": {
        "name": "ASUS ZenWiFi CD6R",
        "target": "ath79",
        "subtarget": "generic",
        "profile": "asus_zenwifi-cd6r",
        "slug": "zenwifi-cd6r",
        "packages": "kmod-ath10k-ct ath10k-firmware-qca9888-ct",
    },
    "netgear_ex7300-v2": {
        "name": "NETGEAR EX7300 v2",
        "target": "ath79",
        "subtarget": "generic",
        "profile": "netgear_ex7300-v2",
        "slug": "ex7300-v2",
        "packages": "kmod-ath10k-ct ath10k-firmware-qca9984-ct",
    },
}

# Aliases for flexible matching
ALIASES: Dict[str, str] = {
    "archer a9": "tplink_archer-a9-v6",
    "archer a9 v6": "tplink_archer-a9-v6",
    "tp link archer a9": "tplink_archer-a9-v6",
    "tp link archer a9 v6": "tplink_archer-a9-v6",
    "tplink archer a9 v6": "tplink_archer-a9-v6",
    "tplink_archer a9 v6": "tplink_archer-a9-v6",
    "tplink_archer-a9-v6": "tplink_archer-a9-v6",
    "asus rt ac59u v2": "asus_rt-ac59u-v2",
    "rt ac59u v2": "asus_rt-ac59u-v2",
    "rt-ac59u-v2": "asus_rt-ac59u-v2",
    "asus rt ac59u": "asus_rt-ac59u",
    "rt ac59u": "asus_rt-ac59u",
    "rt-ac59u": "asus_rt-ac59u",
    "asus zenwifi cd6n": "asus_zenwifi-cd6n",
    "zenwifi cd6n": "asus_zenwifi-cd6n",
    "zenwifi-cd6n": "asus_zenwifi-cd6n",
    "asus zenwifi cd6r": "asus_zenwifi-cd6r",
    "zenwifi cd6r": "asus_zenwifi-cd6r",
    "zenwifi-cd6r": "asus_zenwifi-cd6r",
    "netgear ex7300 v2": "netgear_ex7300-v2",
    "ex7300 v2": "netgear_ex7300-v2",
    "ex7300-v2": "netgear_ex7300-v2",
}


def normalize(text: str) -> str:
    """
    Normalize arbitrary model strings into lowercase, space-separated alphanumeric tokens.

    Replaces punctuation, delimiters (hyphens, underscores, slashes), and excessive whitespace
    to enable resilient matching across variant query formats (e.g. 'Archer A9 v6' vs 'archer-a9-v6').

    Args:
        text: Raw device model or alias input string.

    Returns:
        Cleaned, normalized string of space-separated lowercase tokens.
    """
    if not text:
        return ""
    return " ".join(re.sub(r"[\s_\-/,().]+", " ", text.lower()).split())


def main():
    """
    Parse command-line query, resolve against curated QCN5502 models, and export environment variables.

    Exits with code 0 on successful resolution, exporting build parameters (TARGET, SUBTARGET,
    PROFILE, DEVICE_NAME, ROUTER_SLUG, DEVICE_PACKAGES) to stdout, $GITHUB_ENV, and $GITHUB_OUTPUT.
    Exits with code 1 on unknown or unsupported device queries.
    """
    parser = argparse.ArgumentParser(description="Resolve router model to supported QCN5502 OpenWrt target profile.")
    parser.add_argument("--query", "-q", required=True, help="Router model name")
    parser.add_argument("--repo-dir", default=".", help="Root of OpenWrt repository")
    parser.add_argument("--export-github-env", action="store_true", help="Export environment variables to $GITHUB_ENV")
    parser.add_argument("--export-github-output", action="store_true", help="Export output parameters to $GITHUB_OUTPUT")

    args = parser.parse_args()

    # Step 1: Normalize input query and match against direct aliases or device table
    q_norm = normalize(args.query)
    prof = ALIASES.get(q_norm)
    if not prof:
        for k, v in DEVICES.items():
            if q_norm in (normalize(v["name"]), normalize(k), normalize(f"{v['target']}/{v['subtarget']}/{k}")):
                prof = k
                break

    # Step 2: Validate against supported QCN5502 profile whitelist
    if not prof or prof not in DEVICES:
        print(f"ERROR: Unsupported router model '{args.query}'.", file=sys.stderr)
        print("This workflow only supports the following 6 router models:", file=sys.stderr)
        for dev in DEVICES.values():
            print(f"  - {dev['name']} ({dev['profile']})", file=sys.stderr)
        sys.exit(1)

    res = DEVICES[prof]

    print("========================================")
    print(f" Resolved Router Model: {res['name']}")
    print(f" Target Architecture:   {res['target']}")
    print(f" Subtarget:             {res['subtarget']}")
    print(f" Device Profile:        {res['profile']}")
    print(f" Device Packages:       {res['packages']}")
    print(f" Router Slug:           {res['slug']}")
    print("========================================")

    env_vars = {
        "TARGET": res["target"],
        "SUBTARGET": res["subtarget"],
        "PROFILE": res["profile"],
        "DEVICE_NAME": res["name"],
        "ROUTER_SLUG": res["slug"],
        "DEVICE_PACKAGES": res["packages"],
    }

    if args.export_github_env and "GITHUB_ENV" in os.environ:
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

    if args.export_github_output and "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")


if __name__ == "__main__":
    main()
