"""An event on a continuous quantity occurs when the quantity crosses, not later.

A study event such as ``ROOM.quantity >= 4.0`` is declared as a
``cod3s.ObjEvent``: a two-state automaton whose ``occ`` transition is guarded by
the comparison. On a model with continuous flows the quantity is integrated by
PyCATSHOO's continuous solver, and the solver only stops on the transitions it
was told to watch. An event nobody registered is noticed at the NEXT discrete
step, whatever that step is, and with the value the quantity has by then.

Two things follow, both measured on a study of a hydrogen plant:

* the event occurs late, at the date of an unrelated transition;
* an excursion that ends before the next discrete step is never seen at all.

The second one is the defect. The sequence target of a study is the ``occ``
state of its event, so a sequence calculation classed 17 histories of 1 000 as
reaching the feared event while the ``had_value`` indicator of the same
quantity, which PyCATSHOO follows along the integration, counted 20 (501
against 570 on the study with an attacker). Same seed, same histories: the
three missing ones crossed the threshold and came back under it between two
discrete steps.

This module plays the smallest system that shows it: one quantity following a
sine, over the threshold from t = 0.52 to t = 2.62, a horizon at t = 3 and no
discrete transition in between. The measure is the engine's own answer, read
off its indicators, on the two readings of the same event.
"""

import types

import muscadet
import Pycatshoo as pyc

from cod3s_pycatshoo import study as study_side
from cod3s_pycatshoo.system import watch_event_crossings

THRESHOLD = 0.5
#: Past the excursion: sin(3) = 0.14, so the event's condition is false again
#: at the only instant the engine is asked to stop at.
HORIZON = 3.0


class _Oscillator(muscadet.ObjFlow):
    """``level`` follows sin(t): above the threshold for a while, then back under it."""

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.v_level = self.addVariable("level", pyc.TVarType.t_double, 0.0)
        self.v_speed = self.addVariable("speed", pyc.TVarType.t_double, 1.0)

    def add_flows(self, **kwargs):
        super().add_flows(**kwargs)
        # A continuous flow is what makes the system continuous for muscadet,
        # i.e. what creates the PDMP manager.
        self.add_flow_continuous_out(name="q", var_fed_default=1.0)

    def compute_level(self):
        self.v_level.setDvdtODE(self.v_speed.value())
        self.v_speed.setDvdtODE(-self.v_level.value())


class _OscillatorSystem(muscadet.System):
    def prerun_step(self):
        comp = self.comp["OSC"]
        self.pdmp_add_ode_variable(comp.v_level)
        self.pdmp_add_ode_variable(comp.v_speed)
        self.pdmp_add_equation_method("compute_level", comp, 0)
        return super().prerun_step()


def _oscillator_with_an_event():
    """The system a declaration would describe: one quantity, one event on it."""
    system = _OscillatorSystem(name="EventCrossing")
    system.add_component(name="OSC", cls="_Oscillator")
    system.add_component(
        name="reached",
        cls="ObjEvent",
        cond=[[{"obj": "OSC", "attr": "level", "ope": ">=", "value": THRESHOLD}]],
    )
    return system


def _had_value_of_the_excursion(system):
    """One history; ``had_value`` of the quantity and of its event, at the horizon."""
    try:
        quantity = system.add_indicator(
            name="quantity_had_value",
            component="^OSC$",
            attr_name="^level$",
            attr_type="VAR",
            measure="had_value",
            operator=">=",
            value_test=THRESHOLD,
            stats=["mean"],
        )
        event = system.add_indicator(
            name="event_had_value",
            component="^reached$",
            attr_name="^occ$",
            attr_type="ST",
            measure="had_value",
            operator="==",
            value_test=True,
            stats=["mean"],
        )
        system.simulate({"nb_runs": 1, "schedule": [HORIZON], "seed": 1})
        return {
            "quantity": float(quantity[0].stat_values("mean")[-1]),
            "event": float(event[0].stat_values("mean")[-1]),
        }
    finally:
        system.deleteSys()


def test_the_system_of_a_run_sees_an_excursion_that_ends_before_the_next_discrete_step(
    monkeypatch,
):
    """The event and the indicator of the same quantity count the same histories.

    Through the builder a study run hands the campaign, the road of every
    study: a registration nobody calls would leave a campaign exactly where
    the defect was found. Only the reading of the document is replaced, by the
    system that document would describe.
    """
    monkeypatch.setattr(
        study_side,
        "build_system",
        lambda spec, system=None: _oscillator_with_an_event(),
    )
    system = study_side.DeclarationBuilder({}).build()

    measured = _had_value_of_the_excursion(system)

    assert measured["quantity"] == 1.0
    assert measured["event"] == measured["quantity"]


def test_an_unwatched_event_misses_the_excursion():
    """The engine's behaviour the registration answers, measured rather than supposed.

    If this one reddens, PyCATSHOO started following every transition along the
    integration by itself: ``watch_event_crossings`` is then redundant and can
    go, with this test.
    """
    measured = _had_value_of_the_excursion(_oscillator_with_an_event())

    assert measured["quantity"] == 1.0
    assert measured["event"] == 0.0


def test_a_discrete_system_is_left_untouched():
    """No continuous flow, no solver: nothing is registered and none is created."""

    discrete = types.SimpleNamespace(pdmp_manager=None, comp={"reached": object()})

    assert watch_event_crossings(discrete) == 0
