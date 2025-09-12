from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
import profile
from typing import List, Optional

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

class UserRole(Enum):
    SYSADMIN = "sysadmin"
    DEVELOPER = "developer"
    STUDENT = "student"
    SECURITY = "security"
    DEVOPS = "devops"

class RiskTolerance(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class OutputFormat(Enum):
    MARKDOWN = "markdown"
    JSON = "json"

@dataclass
class UserProfile:
    username: str
    skill_level: SkillLevel = SkillLevel.INTERMEDIATE
    roles: UserRole = UserRole.SYSADMIN
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM
    format: OutputFormat = OutputFormat.MARKDOWN
    preferred_tools: List[str] = None

    def __post_init__(self):
        if self.preferred_tools is None:
            self.preferred_tools = []

ROLE_CONFIG = {
    UserRole.SYSADMIN: {
        "focus": "service health, logs, system state",
        "priorities": ["repeat errors", "failed units", "resource pressure"],
        "preferred_commands": ["journalctl", "systemctl", "dmesg", "ss", "ps"],
        "avoid_commands": ["reboot", "rm", "kill -9"],
    },
    UserRole.DEVELOPER: {
        "focus": "build/run failures and stack traces",
        "priorities": ["compile/runtime errors", "dependency issues", "perf hotspots"],
        "preferred_commands": ["grep", "tail", "cat", "ls", "strace"],
        "avoid_commands": [],
    },
    UserRole.STUDENT: {
        "focus": "clear explanation and safe checks",
        "priorities": ["plain-language summary", "read-only verification"],
        "preferred_commands": ["journalctl", "ls", "grep", "tail"],
        "avoid_commands": ["sudo", "rm", "system changes"],
    },
    UserRole.SECURITY: {
        "focus": "auth failures, anomalous processes, suspicious sockets",
        "priorities": ["IoCs", "failed logins", "unexpected listeners", "privilege escalation"],
        "preferred_commands": ["journalctl", "last", "ss", "lsof", "ps"],
        "avoid_commands": [],
    },
    UserRole.DEVOPS: {
        "focus": "service reliability and quick triage",
        "priorities": ["service errors", "latency spikes", "restarts/crashes"],
        "preferred_commands": ["journalctl", "systemctl", "kubectl", "ss", "curl"],
        "avoid_commands": [],
    }
}

SKILL_CONFIG = {
    SkillLevel.BEGINNER: {
        "verbosity": "short with brief explanations",
        "include_explanations": True,
        "include_man_pages": True,
        "max_commands_per_step": 2,
    },
    SkillLevel.INTERMEDIATE: {
        "verbosity": "concise",
        "include_explanations": True,
        "include_man_pages": False,
        "max_commands_per_step": 3,
        "safety_level": "medium",
    },
    SkillLevel.EXPERT: {
        "verbosity": "very terse",
        "include_explanations": False,
        "include_man_pages": False,
        "max_commands_per_step": 5,
        "safety_level": "low",
    }
}

# Just some decorators for prompt sections
def build_customized_rules(user: UserProfile) -> str:
    role_cfg = ROLE_CONFIG[user.role]  # Fixed: user.role not user.roles
    skill_cfg = SKILL_CONFIG[user.skill_level]
    
    safety_map = {
        "high": "extremely cautious; read-only checks first; explain risks briefly",
        "medium": "prefer read-only checks; show when sudo is required", 
        "low": "standard safety; assume user understands risk",
    }
    
    # Get safety level and map it to description
    safety_level = skill_cfg.get("safety_level", "medium")
    safety_desc = safety_map[safety_level]
    
    # Build explanation and man page guidance
    explain = "Include brief explanations where helpful." if skill_cfg["include_explanations"] else "Minimal explanation."
    man = "Suggest `man` pages if relevant." if skill_cfg["include_man_pages"] else "Skip `man` pages unless critical."
    
    # Fixed: proper indentation
    tools = ", ".join(user.preferred_tools) if user.preferred_tools else "none declared"

    rules = f"""
User Role: {user.role.value}
Focus Areas: {role_cfg['focus']}
Priorities: {', '.join(role_cfg['priorities'])}
Preferred Commands: {', '.join(role_cfg['preferred_commands'])}
Avoid Commands: {', '.join(role_cfg['avoid_commands']) if role_cfg['avoid_commands'] else 'none specified'}

Skill Level: {user.skill_level.value}
Verbosity: {skill_cfg['verbosity']}
Safety Guidance: {safety_desc}
Explanations: {explain}
Man Pages: {man}
Max Commands Per Step: {skill_cfg['max_commands_per_step']}
Preferred Tools: {tools}
"""

    return rules