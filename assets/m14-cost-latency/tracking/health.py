"""
Health checks for scheduled jobs. Run before the heavy work; fail fast
and alert if a dependency is down so you do not spend 10 minutes on a
job that was always going to fail.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class HealthStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class HealthCheck:
    name: str
    check: Callable[[], bool]
    detail_fn: Callable[[], str] | None = None
    critical: bool = True

    def run(self) -> tuple[HealthStatus, str]:
        try:
            ok = self.check()
        except Exception as exc:
            return HealthStatus.DOWN, f"{type(exc).__name__}: {exc}"

        if ok:
            return HealthStatus.OK, "ok"
        detail = self.detail_fn() if self.detail_fn else "check returned False"
        return (HealthStatus.DOWN if self.critical else HealthStatus.DEGRADED), detail


def run_all(checks: list[HealthCheck]) -> dict:
    """
    Run every check. Returns a structured report. Overall status is the
    worst individual status.
    """
    by_name: dict[str, dict] = {}
    overall = HealthStatus.OK

    for check in checks:
        status, detail = check.run()
        by_name[check.name] = {"status": status.value, "detail": detail}
        if status == HealthStatus.DOWN and check.critical:
            overall = HealthStatus.DOWN
        elif status != HealthStatus.OK and overall == HealthStatus.OK:
            overall = HealthStatus.DEGRADED

    return {"overall": overall.value, "checks": by_name}
