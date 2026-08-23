"""Pure, deterministic Phase 1 health-state rules."""
from collections.abc import Sequence
from dataclasses import dataclass

from app.models import HealthState

LATENCY_DEGRADED_MS = 500


@dataclass(frozen=True)
class CheckEvidence:
    success: bool
    latency_ms: int | None


def _last(checks: Sequence[CheckEvidence], count: int) -> Sequence[CheckEvidence]:
    return checks[-count:]


def _consecutive_failures(checks: Sequence[CheckEvidence], count: int) -> bool:
    sample = _last(checks, count)
    return len(sample) == count and all(not check.success for check in sample)


def _healthy_successes(checks: Sequence[CheckEvidence], count: int) -> bool:
    sample = _last(checks, count)
    return len(sample) == count and all(check.success and check.latency_ms is not None and check.latency_ms < LATENCY_DEGRADED_MS for check in sample)


def evaluate_state(current: HealthState, checks: Sequence[CheckEvidence]) -> tuple[HealthState, str | None]:
    """Return the next state and a human-readable reason. Checks are chronological."""
    if not checks:
        return current, None
    latest = checks[-1]

    if current == HealthState.UNKNOWN:
        if latest.success:
            return HealthState.HEALTHY, "first successful check"
        if _consecutive_failures(checks, 3):
            return HealthState.DOWN, "three consecutive failures while unknown"

    elif current == HealthState.HEALTHY:
        last_two = _last(checks, 2)
        if len(last_two) == 2 and all(c.success and c.latency_ms is not None and c.latency_ms >= LATENCY_DEGRADED_MS for c in last_two):
            return HealthState.DEGRADED, "two consecutive high-latency checks"
        recent_three = _last(checks, 3)
        if len(recent_three) == 3 and sum(not c.success for c in recent_three) >= 2:
            return HealthState.DEGRADED, "two failures in the most recent three checks"

    elif current == HealthState.DEGRADED:
        if _consecutive_failures(checks, 3):
            return HealthState.DOWN, "three consecutive failed checks"
        if _healthy_successes(checks, 3):
            return HealthState.HEALTHY, "three consecutive low-latency successful checks"

    elif current == HealthState.DOWN:
        if latest.success:
            return HealthState.RECOVERING, "first successful check after down"

    elif current == HealthState.RECOVERING:
        if not latest.success:
            return HealthState.DOWN, "failure during recovery"
        if _healthy_successes(checks, 3):
            return HealthState.HEALTHY, "three consecutive low-latency successful checks during recovery"

    return current, None

