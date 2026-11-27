"""The engine muscadet reaches under the name ``pycatshoo``.

Registered through the ``muscadet.engines`` entry point of this distribution,
so a run that names ``"pycatshoo"`` reaches it without anyone importing this
package. What it receives is a system declaration, and what it does with it is
the PyCATSHOO side of the seam: build one system from the document, run it.
It also builds the components muscadet declares and no longer carries
(:mod:`cod3s_pycatshoo.components`).

Three kinds of run, two registered runners:

- :func:`simulate` with run parameters: a Monte Carlo campaign on the system
  the document describes, returning what the campaign returns;
- :func:`simulate` with a ``study``: a whole study (simulation settings, result
  tables, sequence analysis) written under ``results_dir``, returning a
  :class:`cod3s_pycatshoo.study.StudyRun`;
- :func:`isimu_start`: an interactive session, returning a
  :class:`cod3s_pycatshoo.session.InteractiveSession`.

**One live system per process.** PyCATSHOO refuses a second one, so a caller
runs each document in a process of its own, or drops the system it was handed
back (:func:`cod3s_pycatshoo.system.drop_system`) before asking for another.

This module imports nothing native at load: discovering the engine must not
cost a server that only lists what is installed more than a metadata read.
"""

from typing import Any

#: The name a run selects this engine by, and the name of its entry point.
ENGINE_NAME = "pycatshoo"

#: The Python module the PyCATSHOO distribution ships.
NATIVE_MODULE = "Pycatshoo"


class NativeEngineMissingError(ImportError):
    """The PyCATSHOO native library cannot be loaded by this interpreter.

    PyCATSHOO has no Python distribution: it is found through ``PYTHONPATH``
    and loaded through ``LD_LIBRARY_PATH``. Either one missing leaves this
    adapter installed and unable to run, which is said by name rather than
    left to the first ``import`` inside a campaign.
    """


def native_engine() -> Any:
    """The PyCATSHOO module, or :class:`NativeEngineMissingError` saying why not."""
    import importlib

    try:
        return importlib.import_module(NATIVE_MODULE)
    except (Exception, SystemExit) as error:
        # Broad on purpose: an absent module raises ImportError, a native
        # library loaded against the wrong interpreter raises whatever the
        # extension chose to raise.
        raise NativeEngineMissingError(
            f"the PyCATSHOO native library ({NATIVE_MODULE}) cannot be loaded: "
            f"{type(error).__name__}: {error}. It is found through PYTHONPATH "
            "and loaded through LD_LIBRARY_PATH; sourcing the pycatshoorc file "
            "of the PyCATSHOO installation sets both"
        ) from error


def native_engine_version() -> str:
    """The version the loaded PyCATSHOO library reports."""
    return str(native_engine().glLogManager().version())


def register() -> None:
    """Register this engine at muscadet's extension point.

    The hook of the ``muscadet.engines`` entry point. It REFUSES to register
    where the native library cannot be loaded, so that "the engines registered
    with muscadet" reads as "the engines this interpreter can run": muscadet
    keeps the refusal and reports it when the engine is asked for.
    """
    native_engine()

    from muscadet.engine import register_engine

    from .components import COMPONENT_BUILDERS

    register_engine(
        ENGINE_NAME,
        simulate=simulate,
        isimu_start=isimu_start,
        description="PyCATSHOO, through the cod3s-pycatshoo adapter",
        replace=True,
        component_builders=COMPONENT_BUILDERS,
    )


def simulate(
    spec: dict,
    *args: Any,
    system: Any = None,
    study: Any = None,
    results_dir: Any = None,
    logger: Any = None,
    indicator_order: list | None = None,
    **kwargs: Any,
) -> Any:
    """Run the system ``spec`` declares on PyCATSHOO.

    Parameters
    ----------
    spec : dict
        A muscadet system declaration.
    system : muscadet.System, optional
        An empty system to fill, for a caller that owns its creation and reads
        the campaign's indicators on it afterwards. Without one, the system is
        built here and dropped once the campaign is over.
    study : dict or cod3s.specs.StudyYaml, optional
        When given, the run is a whole study: see
        :func:`cod3s_pycatshoo.study.run_study`, which also reads
        ``results_dir``, ``logger`` and ``indicator_order``.
    *args, **kwargs
        Without a ``study``, the parameters of the campaign, handed to the
        system's ``simulate`` untouched (``targets`` included).

    Returns
    -------
    Any
        A :class:`cod3s_pycatshoo.study.StudyRun` for a study, otherwise what
        the campaign returns.
    """
    if study is not None:
        from .study import run_study

        if args or kwargs:
            raise TypeError(
                "a study run takes its parameters from the study: unexpected "
                f"{[*map(repr, args), *sorted(kwargs)]}"
            )
        if results_dir is None:
            raise TypeError("a study run needs a results_dir to write under")
        return run_study(
            spec,
            study,
            results_dir=results_dir,
            logger=logger,
            indicator_order=indicator_order,
            system=system,
        )

    from .system import build_system, drop_system

    built = build_system(spec, system=system)
    if system is not None:
        return built.simulate(*args, **kwargs)
    # A system the caller never saw cannot be dropped by the caller, and
    # PyCATSHOO allows one per process: it is dropped here, run or not.
    try:
        return built.simulate(*args, **kwargs)
    finally:
        drop_system(built)


def isimu_start(spec: dict, *args: Any, **kwargs: Any) -> Any:
    """Open an interactive session on the system ``spec`` declares.

    See :func:`cod3s_pycatshoo.session.start_session` for the parameters.
    """
    from .session import start_session

    return start_session(spec, *args, **kwargs)
