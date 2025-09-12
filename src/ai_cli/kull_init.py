# src/ai_cli/kull_init.py
from __future__ import annotations
import os
from pathlib import Path
from .config import CONFIG_DIR, CONFIG_PATH, DEFAULTS  # ENV_KEYS not needed here

# ---------- helpers ----------

def detect_distro() -> str:
    p = Path("/etc/os-release")
    if p.exists():
        data = p.read_text(encoding="utf-8", errors="ignore")
        for line in data.splitlines():
            if line.startswith("ID="):
                return line[3:].strip().strip('"').lower()
            if line.startswith("ID_LIKE="):
                return line[8:].strip().strip('"').lower()
    elif Path("/etc/lsb-release").exists():
        return "debian/ubuntu"
    if Path("/etc/debian_version").exists():
        return "debian/ubuntu"
    if Path("/etc/redhat-release").exists():
        return "redhat/centos/fedora"
    if Path("/etc/arch-release").exists():
        return "arch"
    if Path("/etc/alpine-release").exists():
        return "alpine"
    return "unknown"