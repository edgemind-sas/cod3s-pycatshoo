"""The PyCATSHOO system a declaration describes, built and dropped.

At this stage the construction is delegated: muscadet's ``declare.build_system``
reads the document and instantiates muscadet's own component classes, which are
still PyCATSHOO components. The delegation is what this package replaces family
by family, each one compared document against document before it switches.
"""

from collections.abc import Iterable
from typing import Any


def drop_system(system: Any) -> None:
    """Delete ``system`` and close the PyCATSHOO session, so another can be built.

    PyCATSHOO allows a single live system per process. Never raises: a teardown
    must not replace the failure it follows.
    """
    import contextlib

    with contextlib.suppress(Exception):
        import cod3s

        system.deleteSys()
        cod3s.terminate_session()


def build_system(spec: dict, system: Any = None) -> Any:
    """Build the system ``spec`` declares.

    A build that FAILS drops what it had built before raising: a half-built
    system left alive makes every later system of the process fail with an
    exception that names nothing.

    Parameters
    ----------
    spec : dict
        A muscadet system declaration.
    system : muscadet.System, optional
        An empty system to fill. Created from the document's ``name`` when not
        given.
    """
    from muscadet import declare
    from muscadet.system import System

    if system is None:
        system = System(name=spec.get("name") or "system")
    try:
        return declare.build_system(spec, system=system)
    except BaseException:
        drop_system(system)
        raise


def order_indicators(system: Any, names: Iterable[str] | None) -> None:
    """Put ``system``'s indicators in the order of ``names``.

    Presentation only. The result tables are rendered in the order of the
    system's indicators, and a system built from a declaration holds them in
    the order of the document, sorted by name. A caller that wants its own
    order (a study's) names it here. An indicator ``names`` does not mention
    keeps its place after the named ones; nothing is re-registered with the
    engine.
    """
    indicators = getattr(system, "indicators", None)
    if not names or not isinstance(indicators, dict):
        return
    ordered = {name: indicators[name] for name in names if name in indicators}
    ordered.update(
        (name, indic) for name, indic in indicators.items() if name not in ordered
    )
    indicators.clear()
    indicators.update(ordered)


def watch_event_crossings(system: Any) -> int:
    """Have the continuous solver stop where an event crosses; the events watched.

    An event is a two-state automaton guarded by a comparison, most often on a
    quantity of the model. On a continuous model that quantity is integrated,
    and the solver stops only on the transitions it was told to watch. Left
    unwatched, an event is noticed at the next discrete step, with the value
    the quantity has by then: it occurs late, and an excursion that ends before
    the next discrete step is never seen.

    Every transition of every event is registered, without reading its
    condition. A system with no continuous flow has no solver and is left
    untouched.
    """
    import cod3s

    if getattr(system, "pdmp_manager", None) is None:
        return 0
    events = [
        comp
        for comp in (system.comp or {}).values()
        if isinstance(comp, cod3s.ObjEvent)
    ]
    for event in events:
        for automaton in event.automata_d.values():
            system.pdmp_add_watched_automaton(automaton)
    return len(events)


def set_integration_step(system: Any, pdmp_dt: Any) -> None:
    """Set the base integration step of the continuous solver, if there is one.

    Two absences, neither an error: no step leaves the engine's own default,
    and no solver means a purely discrete model, where a step would govern an
    integration that never happens.
    """
    if pdmp_dt is None:
        return
    manager = system.currentPDMPManager()
    if manager is not None:
        manager.setDt(float(pdmp_dt))
