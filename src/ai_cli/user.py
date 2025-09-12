# src/ai_cli/user.py
import os, getpass

def current_username() -> str:
    # Prefer the real invoking user if running via sudo
    return os.getenv("KULL_USERNAME") or os.getenv("SUDO_USER") or os.getenv("USER") or getpass.getuser() or "user"
