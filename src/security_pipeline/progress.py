from __future__ import annotations

import time


class ProgressPrinter:
    def __init__(self, label: str, total: int, every: int | None = None) -> None:
        self.label = label
        self.total = max(1, total)
        self.every = every or max(1, self.total // 20)
        self.started_at = time.time()

    def update(self, current: int) -> None:
        if current == 1 or current == self.total or current % self.every == 0:
            elapsed = time.time() - self.started_at
            rate = current / elapsed if elapsed > 0 else 0.0
            pct = 100.0 * current / self.total
            remaining = (self.total - current) / rate if rate > 0 else 0.0
            print(
                f"[progress] {self.label}: {current}/{self.total} "
                f"({pct:.1f}%) elapsed={elapsed:.1f}s eta={remaining:.1f}s",
                flush=True,
            )
