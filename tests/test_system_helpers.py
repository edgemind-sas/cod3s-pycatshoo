"""The small pure helpers of the system module, which need no engine."""

import types

from cod3s_pycatshoo.system import order_indicators, set_integration_step


def _system_with(names):
    return types.SimpleNamespace(
        indicators={name: f"indicator {name}" for name in names}
    )


def test_the_indicators_follow_the_order_given():
    system = _system_with(["z_generated", "b", "a"])
    order_indicators(system, ["a", "absent", "b"])
    assert list(system.indicators) == ["a", "b", "z_generated"]


def test_no_order_leaves_the_indicators_where_they_are():
    system = _system_with(["b", "a"])
    order_indicators(system, None)
    order_indicators(system, [])
    assert list(system.indicators) == ["b", "a"]


def test_a_system_without_indicators_is_left_alone():
    order_indicators(types.SimpleNamespace(), ["a"])


def test_no_step_and_no_solver_are_both_fine():
    calls = []
    solver = types.SimpleNamespace(setDt=calls.append)
    discrete = types.SimpleNamespace(currentPDMPManager=lambda: None)
    continuous = types.SimpleNamespace(currentPDMPManager=lambda: solver)

    set_integration_step(continuous, None)
    set_integration_step(discrete, 0.05)
    assert calls == []

    set_integration_step(continuous, "0.05")
    assert calls == [0.05]
