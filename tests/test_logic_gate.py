"""A logic gate muscadet declares is built by this engine.

Written from both doors: a model adding a gate, and a document that holds one.
"""

import json

import cod3s
import muscadet
import pytest
from muscadet import declare

from cod3s_pycatshoo import ENGINE_NAME
from cod3s_pycatshoo.components import COMPONENT_BUILDERS
from cod3s_pycatshoo.system import drop_system


def _sources(system, names):
    for name in names:
        system.add_component(name=name, cls="ObjFlow", partial_init=True)
        source = system.comp[name]
        source.add_flow_out(name="feed", var_prod_default=True)
        source.set_flows()


def _cond(names):
    return [[{"obj": name, "attr": "feed_fed_out", "value": True}] for name in names]


@pytest.fixture(scope="module")
def a_voter():
    """A 2-of-3 gate added by a model, and the document the model declares."""
    names = ["S1", "S2", "S3"]
    system = muscadet.System("voter")
    try:
        _sources(system, names)
        gate = system.add_component(
            name="Voter",
            cls="ObjLogicGate",
            kind="k",
            k=2,
            cond=_cond(names),
            out_elements=["feed"],
            label="2 of 3",
        )
        # Nothing live leaves the fixture: PyCATSHOO allows one system per
        # process, and the tests below build their own.
        seen = {
            "class": type(gate),
            "registered": system.comp["Voter"] is gate,
            "read_back": declare.component_spec(gate),
            "document": json.loads(json.dumps(declare.system_spec(system))),
            "cond": _cond(names),
        }
    finally:
        drop_system(system)
    return seen


def test_the_engine_declares_what_it_builds():
    muscadet.engine.reset_engines()
    try:
        assert muscadet.get_engine(ENGINE_NAME).component_builders == COMPONENT_BUILDERS
        assert muscadet.component_builder(ENGINE_NAME, "logic_gate") is not None
    finally:
        muscadet.engine.reset_engines()


def test_listing_what_it_builds_loads_nothing_native():
    import subprocess
    import sys

    probe = (
        "import sys\n"
        "import cod3s_pycatshoo.components as c\n"
        "assert sorted(c.COMPONENT_BUILDERS) == ['controller', 'logic_gate']\n"
        "print(sorted(n for n in ('Pycatshoo', 'cod3s', 'muscadet') "
        "if n in sys.modules))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    )
    assert done.stdout.strip() == "[]"


def test_a_gate_a_model_adds_is_this_engines(a_voter):
    from cod3s_pycatshoo.logic_gate import ObjLogicGate

    assert a_voter["class"] is ObjLogicGate
    assert a_voter["registered"]


def test_it_reads_back_as_the_document_muscadet_declares(a_voter):
    read = a_voter["read_back"]
    assert read == a_voter["document"]["components"]["Voter"]
    assert read["kind"] == "logic_gate" and read["cls"] == "ObjLogicGate"
    assert read["source_cls"] == "ObjLogicGate"
    assert read["logic_kind"] == "k" and read["k"] == 2
    assert read["cond"] == a_voter["cond"]
    assert read["out_elements"] == ["feed"] and read["label"] == "2 of 3"


def test_a_document_holding_a_gate_is_built_and_evaluated(a_voter):
    from cod3s_pycatshoo.logic_gate import ObjLogicGate

    rebuilt = declare.build_system(a_voter["document"])
    try:
        gate = rebuilt.comp["Voter"]
        assert type(gate) is ObjLogicGate
        rebuilt.isimu_start()
        assert gate.result.value() is True
        rebuilt.isimu_stop()
        assert (
            declare.system_spec(rebuilt)["components"]["Voter"]
            == (a_voter["document"]["components"]["Voter"])
        )
    finally:
        drop_system(rebuilt)


@pytest.mark.parametrize(
    "kind,k,fed,expected",
    [
        ("or", None, [False, False], False),
        ("or", None, [True, False], True),
        ("and", None, [True, False], False),
        ("and", None, [True, True], True),
        ("k", 2, [True, False, True], True),
        ("k", 2, [True, False, False], False),
        ("or", None, [], False),
        ("and", None, [], True),
    ],
)
def test_the_aggregation(kind, k, fed, expected):
    names = [f"S{i}" for i in range(len(fed))]
    system = muscadet.System("aggregation")
    try:
        for name, value in zip(names, fed, strict=True):
            system.add_component(name=name, cls="ObjFlow", partial_init=True)
            source = system.comp[name]
            source.add_flow_out(name="feed", var_prod_default=value)
            source.set_flows()
        gate = system.add_component(
            name="Gate", cls="ObjLogicGate", kind=kind, k=k, cond=_cond(names)
        )
        system.isimu_start()
        assert gate.result.value() is expected
        system.isimu_stop()
    finally:
        drop_system(system)


def test_a_gate_reading_a_source_that_does_not_exist_is_refused_by_name():
    system = muscadet.System("missing_source")
    try:
        with pytest.raises(declare.ComponentSpecError, match="Nowhere"):
            system.add_component(
                name="Gate", cls="ObjLogicGate", cond=_cond(["Nowhere"])
            )
    finally:
        drop_system(system)


def test_delete():
    cod3s.terminate_session()
