# Conventions

## Scope

- This repository holds the PyCATSHOO side of muscadet's engine seam, and only
  that. It uses the public Python interface of the distributed PyCATSHOO
  library. Nothing here is taken from, or describes, PyCATSHOO's own sources,
  and the PyCATSHOO binary is never committed.
- muscadet and cod3s are declared by version range in `pyproject.toml`, never
  by an embedded URL, and `pyproject.toml` carries no `[tool.uv.sources]`: uv
  applies the sources a git dependency declares, so they would reach every
  project that installs the adapter. `requirements-dev.txt` builds this
  repository's own environment.

## Code

- English for code, comments, docstrings, commit messages and pull requests.
- Line length 88, `ruff check` and `ruff format --check` clean.
- Importing `cod3s_pycatshoo` loads nothing native. A module that needs
  PyCATSHOO, cod3s' execution layer or muscadet's live classes imports them
  where it uses them.
- A name of the declaration is resolved through an explicit table of this
  package, never by a search among live subclasses.

## Tests

- pytest, run through the project environment with PyCATSHOO sourced:
  `. "$PYCATSHOO_DIR/pycatshoorc" && .venv/bin/python -m pytest`.
- PyCATSHOO allows one live system per process. A test module that builds a
  system tears it down (`cod3s_pycatshoo.system.drop_system`), and a test that
  needs a clean process spawns one with `sys.executable`.
- Reference results are never regenerated to make a test pass.

## Delivery

- Work happens on a branch (`feat/<topic>`, `fix/<topic>`), merged into `main`
  by a pull request with a merge commit, once the full suite is green locally.
- A change that ships bumps `cod3s_pycatshoo/version.py` and adds its entry at
  the top of `CHANGELOG.md` in the same pull request.
- After the merge: an annotated tag `X.Y.Z` with the message
  `cod3s-pycatshoo X.Y.Z` on the merge commit, pushed to `origin`.
- A release of the adapter does not require a release of muscadet or of cod3s:
  compatibility is a version range, widened here when it has been verified.
