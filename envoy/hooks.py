"""Pre/post hook system for envoy CLI lifecycle events."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class HookEvent(str, Enum):
    PRE_PUSH = "pre-push"
    POST_PUSH = "post-push"
    PRE_PULL = "pre-pull"
    POST_PULL = "post-pull"
    PRE_ROTATE = "pre-rotate"
    POST_ROTATE = "post-rotate"


@dataclass
class HookResult:
    event: HookEvent
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.success else f"exit={self.returncode}"
        return f"<HookResult event={self.event.value} {status}>"


@dataclass
class HookRunner:
    hooks: dict = field(default_factory=dict)  # HookEvent -> List[str]

    @classmethod
    def from_config(cls, config_hooks: dict) -> "HookRunner":
        """Build a HookRunner from a plain dict (e.g. loaded from envoy config)."""
        runner = cls()
        for raw_event, commands in config_hooks.items():
            try:
                event = HookEvent(raw_event)
            except ValueError:
                continue
            if isinstance(commands, str):
                commands = [commands]
            runner.hooks[event] = list(commands)
        return runner

    def run(self, event: HookEvent, timeout: int = 30) -> List[HookResult]:
        """Execute all hooks registered for *event* and return their results."""
        results: List[HookResult] = []
        for cmd in self.hooks.get(event, []):
            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                results.append(
                    HookResult(
                        event=event,
                        command=cmd,
                        returncode=proc.returncode,
                        stdout=proc.stdout.strip(),
                        stderr=proc.stderr.strip(),
                    )
                )
            except subprocess.TimeoutExpired:
                results.append(
                    HookResult(
                        event=event,
                        command=cmd,
                        returncode=124,
                        stdout="",
                        stderr=f"Hook timed out after {timeout}s",
                    )
                )
        return results

    def has_hooks(self, event: HookEvent) -> bool:
        return bool(self.hooks.get(event))
