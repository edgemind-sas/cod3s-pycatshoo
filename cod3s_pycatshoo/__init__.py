"""PyCATSHOO engine adapter for muscadet system declarations.

muscadet describes a system as a document, the system declaration, and knows no
engine. This package is the engine side for PyCATSHOO: it registers itself at
muscadet's extension point (``muscadet.engines`` entry point group) and builds
and runs a PyCATSHOO system from the document it is handed.

Importing this package loads nothing native. The PyCATSHOO library is loaded
when the engine is registered or run, and its absence is reported by name
(:class:`cod3s_pycatshoo.engine.NativeEngineMissingError`).
"""

from .engine import ENGINE_NAME, NativeEngineMissingError, register
from .version import __version__

__all__ = ["ENGINE_NAME", "NativeEngineMissingError", "__version__", "register"]
