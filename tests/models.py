"""The small systems the suite declares, written once.

Each function returns a DOCUMENT: the system is built, declared and torn down
here, so a test starts from what an engine is actually handed. PyCATSHOO allows
one live system per process, which is why nothing live leaves this module.
"""

import json

import cod3s
import muscadet
import muscadet.kb.rbd

FLOW = "is_ok"
FEARED_EVENT = "EVT_LOSS"


def series_declaration(name="Series"):
    """Source -> Block -> Target, one exponential failure mode, one event."""
    system = muscadet.System(name=name)
    try:
        system.add_component(name="Src", cls="Source")
        system.add_component(name="Blk", cls="Block")
        system.add_component(name="Tgt", cls="Target")
        system.connect_flow(source="Src", target="Blk", flow_name=FLOW)
        system.connect_flow(source="Blk", target="Tgt", flow_name=FLOW)
        system.comp["Blk"].add_exp_failure_mode(
            name="failure",
            failure_rate=0.1,
            repair_rate=0.5,
            failure_effects=[(FLOW, False)],
        )
        system.add_component(
            cls="ObjEvent",
            name=FEARED_EVENT,
            cond=[[{"attr": f"{FLOW}_fed_in", "obj": "Tgt", "value": False}]],
        )
        system.add_indicator_var(
            component="^Tgt$", var=f"^{FLOW}_fed_in$", stats=["mean"]
        )
        # Through json: a document that only survives in memory is not one.
        return json.loads(json.dumps(muscadet.system_spec(system)))
    finally:
        system.deleteSys()
        cod3s.terminate_session()


def without_provenance(document):
    """The document, minus the class each component was read back from."""
    stripped = dict(document)
    stripped["components"] = {
        name: {k: v for k, v in spec.items() if k != "source_cls"}
        for name, spec in document["components"].items()
    }
    return stripped
