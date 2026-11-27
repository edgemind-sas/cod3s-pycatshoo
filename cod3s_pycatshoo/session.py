"""An interactive PyCATSHOO session, from a system declaration.

The session's system is built from the document, configured with what travels
beside it (value changes, integration step, sequence targets), and wrapped in a
started stepping engine. At this stage that engine is cod3s'
``ISimuEngine``.
"""

from dataclasses import dataclass
from typing import Any

from .engine import native_engine_version
from .system import build_system, drop_system, set_integration_step


@dataclass
class InteractiveSession:
    """A started interactive session.

    The caller steps ``engine`` and reads ``system``. It owns the teardown
    (:func:`cod3s_pycatshoo.system.drop_system`).
    """

    #: The live PyCATSHOO system the session steps.
    system: Any
    #: The started stepping engine.
    engine: Any
    #: The version the native PyCATSHOO library reports.
    engine_version: str


def start_session(
    spec: dict,
    *,
    system: Any = None,
    attribute_overrides: Any = None,
    pdmp_dt: float | None = None,
    targets: Any = None,
) -> InteractiveSession:
    """Build the system ``spec`` declares and start an interactive session on it.

    Parameters
    ----------
    spec : dict
        A muscadet system declaration.
    system : muscadet.System, optional
        An empty system to fill.
    attribute_overrides : dict or cod3s.specs.study_yaml.AttributeOverrides, optional
        The session's value changes, applied on the built system. Their effect
        on what the components are declared with is expected to be in the
        document already.
    pdmp_dt : float, optional
        Base integration step of the continuous solver.
    targets : sequence of str, optional
        The events the session declares as sequence targets, by name.
    """
    built = build_system(spec, system=system)
    try:
        if attribute_overrides:
            from cod3s.scripts.study_runner import apply_attribute_overrides
            from cod3s.specs.study_yaml import AttributeOverrides

            apply_attribute_overrides(
                built, AttributeOverrides.model_validate(attribute_overrides)
            )
        set_integration_step(built, pdmp_dt)
        if targets:
            built.declare_run_targets(targets)

        from cod3s.pycatshoo.isimu.engine import ISimuEngine

        engine = ISimuEngine(built)
        engine.start()
    except BaseException:
        drop_system(built)
        raise
    return InteractiveSession(
        system=built, engine=engine, engine_version=native_engine_version()
    )
