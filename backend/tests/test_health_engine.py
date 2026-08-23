from app.models import HealthState
from app.services.health_engine import CheckEvidence, evaluate_state


def checks(*items): return [CheckEvidence(*item) for item in items]


def test_unknown_requires_evidence_then_becomes_healthy():
    assert evaluate_state(HealthState.UNKNOWN, checks((False, 100)))[0] == HealthState.UNKNOWN
    assert evaluate_state(HealthState.UNKNOWN, checks((False, 100), (False, 100), (False, 100)))[0] == HealthState.DOWN
    assert evaluate_state(HealthState.UNKNOWN, checks((True, 900)))[0] == HealthState.HEALTHY


def test_healthy_transitions_and_no_redundant_transition():
    assert evaluate_state(HealthState.HEALTHY, checks((True, 100)))[0] == HealthState.HEALTHY
    assert evaluate_state(HealthState.HEALTHY, checks((True, 500), (True, 700)))[0] == HealthState.DEGRADED
    assert evaluate_state(HealthState.HEALTHY, checks((False, 1), (True, 10), (False, 1)))[0] == HealthState.DEGRADED


def test_latency_boundary_and_recent_window_are_precise():
    assert evaluate_state(HealthState.HEALTHY, checks((True, 499), (True, 500)))[0] == HealthState.HEALTHY
    assert evaluate_state(HealthState.HEALTHY, checks((False, 1), (True, 10), (True, 10)))[0] == HealthState.HEALTHY
    # The supplied list is chronological: old failures outside the latest window do not count.
    assert evaluate_state(HealthState.HEALTHY, checks((False, 1), (False, 1), (True, 10), (True, 10)))[0] == HealthState.HEALTHY


def test_degraded_down_and_healthy():
    assert evaluate_state(HealthState.DEGRADED, checks((False, 1), (False, 1), (False, 1)))[0] == HealthState.DOWN
    assert evaluate_state(HealthState.DEGRADED, checks((True, 100), (True, 200), (True, 499)))[0] == HealthState.HEALTHY


def test_down_and_recovery_rules():
    assert evaluate_state(HealthState.DOWN, checks((True, 900)))[0] == HealthState.RECOVERING
    assert evaluate_state(HealthState.RECOVERING, checks((True, 100), (True, 100), (True, 100)))[0] == HealthState.HEALTHY
    assert evaluate_state(HealthState.RECOVERING, checks((True, 100), (False, 1)))[0] == HealthState.DOWN


def test_flagship_sequence_is_deterministic():
    stream = checks(*((True, 145),) * 3, *((True, 700),) * 2, *((False, 1200),) * 3, (True, 180), *((True, 160),) * 3)
    state = HealthState.UNKNOWN
    transitions = [state]
    history = []
    for item in stream:
        history.append(item)
        next_state, _ = evaluate_state(state, history)
        if next_state != state:
            transitions.append(next_state)
            state = next_state
    assert transitions == [HealthState.UNKNOWN, HealthState.HEALTHY, HealthState.DEGRADED, HealthState.DOWN, HealthState.RECOVERING, HealthState.HEALTHY]
