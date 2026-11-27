"""The combinational logic gate, on PyCATSHOO.

muscadet declares a gate (``muscadet.logic_gate.ObjLogicGate``, kind
``logic_gate``) and hands its declaration here. This module is what evaluates
one during a run: a component without automaton, whose boolean ``result`` is
recomputed by a sensitive method each time a source variable changes.

Imports the native library at load, so nothing imports this module before a
gate has to be built (:mod:`cod3s_pycatshoo.components`).
"""

import cod3s
import Pycatshoo as Pyc
from cod3s.pycatshoo.common import prepare_attr_tree
from cod3s.specs.conditions import sanitize_cond_format
from muscadet.common import copy_declaration, resolve_gate_logic
from muscadet.declare import ComponentSpecError
from muscadet.initial_state import RANK_OUTPUT, register_initial_evaluation

#: The declaration kind this module builds.
KIND = "logic_gate"


class ObjLogicGate(cod3s.PycComponent):
    """A live gate: one boolean variable, recomputed on its sources.

    ``result`` is exported through one message box per downstream element, so
    a flow input consumes the gate like any other source.
    """

    #: The declaration kind this component was built from. muscadet reads a
    #: live component back into a document on this, never on its class.
    declared_kind = KIND

    def __init__(self, name, cond=None, out_elements=None, kind="or", k=None, **kwargs):
        super().__init__(name, **kwargs)

        self.declared_cond = copy_declaration(sanitize_cond_format(cond or []))
        self.declared_out_elements = list(out_elements or [])
        self.logic_kind = kind
        self.logic_k = k
        self.result = self.addVariable("result", Pyc.TVarType.t_bool, False)

        inner_logic, outer_logic = resolve_gate_logic(kind, k)
        cond_bis = prepare_attr_tree(self.declared_cond, system=self.system())

        def recompute():
            value = outer_logic(
                [
                    inner_logic(
                        [
                            (
                                getattr(leaf["attr"], leaf["attr_val_name"])()
                                == leaf.get("value", True)
                            )
                            for leaf in clause
                        ]
                    )
                    for clause in cond_bis
                ]
            )
            self.result.setValue(bool(value))

        self._recompute = recompute

        # No automaton: the recompute is registered on every source variable,
        # so a change of any input re-evaluates the gate.
        for clause in cond_bis:
            for leaf in clause:
                leaf["attr"].addSensitiveMethod(f"logic_gate_{name}", recompute)

        for elem in self.declared_out_elements:
            self.addMessageBox(f"{elem}_out")
            self.addMessageBoxExport(f"{elem}_out", self.result, elem)

        recompute()  # seed the initial value

        # A member of the initial fixpoint: the components it feeds are
        # replayed at start, and would otherwise read the value seeded here,
        # before any source had started.
        register_initial_evaluation(self, recompute, [self.result], RANK_OUTPUT)


def build(system, spec):
    """Build the gate ``spec`` declares on ``system``, once its sources exist."""
    name = spec["name"]
    groups = sanitize_cond_format(copy_declaration(spec.get("cond", [])))
    for group in groups:
        for leaf in group:
            try:
                prepare_attr_tree([[leaf]], system=system)
            except (KeyError, ValueError) as error:
                raise ComponentSpecError(
                    f"Logic gate {name}: cannot resolve source "
                    f"{leaf['obj']}.{leaf['attr']}: {error}"
                ) from error
    return ObjLogicGate(
        name,
        cond=copy_declaration(spec.get("cond", [])),
        out_elements=list(spec.get("out_elements", [])),
        kind=spec.get("logic_kind", "or"),
        k=spec.get("k"),
        label=spec.get("label"),
        description=spec.get("description"),
        metadata=copy_declaration(spec.get("metadata", {})),
    )
