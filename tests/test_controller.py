"""A controller muscadet declares is built by this engine.

The same regulated tank is built twice, by this engine's controller and by the
one muscadet still carries, and the two are compared: the names they create,
the document they are read back as, and the loop they drive.
"""

import importlib.metadata
import json

import cod3s
import muscadet
import pytest
from muscadet import declare
from muscadet.kb.continuous import (  # noqa: F401
    CapacityContinuous,
    ConsumerContinuous,
    SourceContinuous,
)

from cod3s_pycatshoo import ENGINE_NAME
from cod3s_pycatshoo.system import drop_system

from .models import without_provenance

RATE = 2.0
DEMAND = 1.0
INIT = 5.0
ACTIVATE = 3.0
RELEASE = 8.0
STOPS = tuple(float(date) for date in range(1, 21))


def _regulated_tank(name="regulated_tank"):
    """A source filling a tank when its level drops, stopping when it is high."""
    system = muscadet.System(name=name)
    system.add_component(
        name="SRC", cls="SourceContinuous", flow="q", rate=RATE, control="fill"
    )
    system.add_component(
        name="CAP",
        cls="CapacityContinuous",
        flow="q",
        capacity=100.0,
        capacity_name="tank",
        content_init={"q": INIT},
        fill_rate=float("inf"),
    )
    system.add_component(name="SINK", cls="ConsumerContinuous", flow="q", demand=DEMAND)
    system.add_component(
        name="CTRL",
        cls="ObjCtrl",
        label="Level regulation",
        controls_in=[{"name": "tank"}],
        controls_out=[
            {
                "name": "fill",
                "kind": "bool",
                "emit": {
                    "op": "band",
                    "input": "tank",
                    "direction": "below",
                    "activate": ACTIVATE,
                    "release": RELEASE,
                },
            },
            {
                "name": "echo",
                "kind": "value",
                "emit": {"op": "republish", "input": "tank", "gain": 2.0},
            },
        ],
    )
    system.connect_flow(source="SRC", target="CAP", flow_name="q")
    system.connect_flow(source="CAP", target="SINK", flow_name="q")
    system.connect("CAP", "tank_level_out", "CTRL", "tank_level_in")
    system.connect("CTRL", "fill_out", "SRC", "fill_in")
    for date in STOPS:
        system.comp["SINK"].add_atm2states(
            name=f"clock_{int(date)}",
            st1="s0",
            st2="s1",
            occ_law_12={"cls": "delay", "time": date},
            cond_occ_21=False,
        )
    return system


def _observe(system):
    """What one build of the regulated tank creates, declares and does."""
    controller = system.comp["CTRL"]
    seen = {
        "module": type(controller).__module__,
        "interfaces": {
            name: type(interface).__module__
            for name, interface in controller.controls_out.items()
        },
        "boxes": dict(controller.interface_boxes),
        "automata": {
            name: [aut.name for aut in automata]
            for name, automata in controller.emit_automata.items()
        },
        "params": sorted(controller.emit_params),
        "read_back": declare.component_spec(controller),
        "document": json.loads(json.dumps(declare.system_spec(system))),
    }
    trace = []
    system.isimu_start()
    for _ in range(200):
        if system.currentTime() >= STOPS[-1]:
            break
        system.isimu_step_forward()
        trace.append(
            (
                round(system.currentTime(), 6),
                round(system.comp["CAP"].capacities["tank"].get_quantity("q"), 6),
                controller.controls_out["fill"].get_signal(),
                system.comp["SRC"].flows_out["q"].var_fed.value(),
            )
        )
    system.isimu_stop()
    seen["trace"] = trace
    return seen


@pytest.fixture(scope="module")
def by_this_engine():
    muscadet.engine.reset_engines()
    system = _regulated_tank()
    try:
        return _observe(system)
    finally:
        drop_system(system)


@pytest.fixture(scope="module")
def by_muscadet():
    """The same model with no engine advertised: muscadet's own controller."""
    patch = pytest.MonkeyPatch()
    patch.setattr(importlib.metadata, "entry_points", lambda group=None, **kw: [])
    muscadet.engine.reset_engines()
    system = _regulated_tank()
    try:
        return _observe(system)
    finally:
        drop_system(system)
        patch.undo()
        muscadet.engine.reset_engines()


def test_the_engine_declares_that_it_builds_controllers():
    muscadet.engine.reset_engines()
    try:
        assert muscadet.component_builder(ENGINE_NAME, "controller") is not None
    finally:
        muscadet.engine.reset_engines()


def test_a_controller_a_model_adds_is_this_engines(by_this_engine, by_muscadet):
    assert by_this_engine["module"] == "cod3s_pycatshoo.controller"
    assert by_this_engine["interfaces"] == {
        "fill": "cod3s_pycatshoo.controller",
        "echo": "muscadet.capacity",
    }
    assert by_muscadet["module"] == "muscadet.obj_ctrl"


def test_it_creates_the_names_muscadets_controller_created(by_this_engine, by_muscadet):
    assert by_this_engine["automata"]["fill"], "the band compiles to automata"
    for what in ("boxes", "automata", "params"):
        assert by_this_engine[what] == by_muscadet[what]


def test_it_reads_back_as_the_document_muscadet_declares(by_this_engine, by_muscadet):
    read = by_this_engine["read_back"]
    assert read == by_this_engine["document"]["components"]["CTRL"]
    assert read["kind"] == "controller" and read["cls"] == "ObjCtrl"
    assert read["source_cls"] == "ObjCtrl" and read["label"] == "Level regulation"
    assert by_this_engine["document"] == by_muscadet["document"]


def test_it_drives_the_loop_muscadets_controller_drove(by_this_engine, by_muscadet):
    trace = by_this_engine["trace"]
    assert trace == by_muscadet["trace"]
    signals = [signal for _, _, signal, _ in trace]
    # The band starts the source below ACTIVATE and stops it above RELEASE.
    assert signals[0] is False and True in signals
    assert signals[signals.index(True) :].count(False) > 0
    levels = [level for _, level, _, _ in trace]
    assert min(levels) == pytest.approx(ACTIVATE, abs=0.01)
    assert max(levels[signals.index(True) :]) == pytest.approx(RELEASE, abs=0.01)


def test_a_document_holding_a_controller_is_rebuilt_by_this_engine(by_this_engine):
    muscadet.engine.reset_engines()
    rebuilt = declare.build_system(by_this_engine["document"])
    try:
        assert type(rebuilt.comp["CTRL"]).__module__ == "cod3s_pycatshoo.controller"
        # A rebuilt flow component is read back as the class it was expanded
        # onto, so the provenance is the one thing a rebuild does not keep.
        again = json.loads(json.dumps(declare.system_spec(rebuilt)))
        assert without_provenance(again) == without_provenance(
            by_this_engine["document"]
        )
        assert again["components"]["CTRL"] == by_this_engine["read_back"]
    finally:
        drop_system(rebuilt)


def test_a_key_no_controller_reads_is_refused_by_name():
    system = muscadet.System("refused")
    try:
        with pytest.raises(ValueError, match="thresold"):
            system.add_component(name="CTRL", cls="ObjCtrl", thresold=1.0)
        assert "CTRL" not in system.comp
    finally:
        drop_system(system)


def test_delete():
    cod3s.terminate_session()
