"""The components this engine builds, by declaration kind.

An explicit table: muscadet asks for the builder of a kind
(:func:`muscadet.engine.component_builder`) and never searches live classes by
name. Each entry imports its module when called, so listing what the engine
builds loads nothing native.
"""

from typing import Any


def build_logic_gate(system: Any, spec: dict) -> Any:
    """Build a combinational gate from its declaration."""
    from .logic_gate import build

    return build(system, spec)


#: ``declaration kind -> (system, spec) -> component``.
COMPONENT_BUILDERS = {"logic_gate": build_logic_gate}
