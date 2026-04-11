"""Watch .env files for changes and emit events."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class WatchEvent:
    path: str
    kind: str          # 'modified' | 'created' | 'deleted'
    old_checksum: Optional[str]
    new_checksum: Optional[str]
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return f"WatchEvent(kind={self.kind!r}, path={self.path!r})"


def _file_checksum(path: Path) -> Optional[str]:
    """Return SHA-256 hex digest of file contents, or None if missing."""
    try:
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest()
    except FileNotFoundError:
        return None


class EnvWatcher:
    """Poll one or more .env files and invoke callbacks on change."""

    def __init__(self, paths: List[str], interval: float = 1.0) -> None:
        self.paths = [Path(p) for p in paths]
        self.interval = interval
        self._checksums: Dict[str, Optional[str]] = {
            str(p): _file_checksum(p) for p in self.paths
        }
        self._callbacks: List[Callable[[WatchEvent], None]] = []
        self._running = False

    def on_change(self, callback: Callable[[WatchEvent], None]) -> None:
        """Register a callback invoked with a WatchEvent on each change."""
        self._callbacks.append(callback)

    def poll(self) -> List[WatchEvent]:
        """Check all watched paths once and return any events detected."""
        events: List[WatchEvent] = []
        for path in self.paths:
            key = str(path)
            old = self._checksums[key]
            new = _file_checksum(path)
            if old == new:
                continue
            if old is None:
                kind = "created"
            elif new is None:
                kind = "deleted"
            else:
                kind = "modified"
            evt = WatchEvent(path=key, kind=kind, old_checksum=old, new_checksum=new)
            self._checksums[key] = new
            events.append(evt)
            for cb in self._callbacks:
                cb(evt)
        return events

    def watch(self, max_polls: Optional[int] = None) -> None:
        """Blocking watch loop.  Stops after *max_polls* iterations if given."""
        self._running = True
        count = 0
        while self._running:
            self.poll()
            count += 1
            if max_polls is not None and count >= max_polls:
                break
            time.sleep(self.interval)

    def stop(self) -> None:
        self._running = False
