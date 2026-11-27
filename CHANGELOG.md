# Changelog

## 0.2.0

The adapter builds its first component. A logic gate is declared by muscadet
and built here.

- The engine registers a component builder for the `logic_gate` declaration
  kind (`cod3s_pycatshoo.components.COMPONENT_BUILDERS`). muscadet hands the
  checked declaration of a gate to it, whether the gate comes from a document
  or from `system.add_component(cls="ObjLogicGate", ...)`.
- `cod3s_pycatshoo.logic_gate` carries the live gate: one boolean variable,
  recomputed each time a source variable changes, exported under one element
  per downstream input. Same behaviour, same names and same read-back
  document as the gate muscadet carried.
- A campaign run without a `system` drops the system it built once it is over.
  It used to leave it alive and out of reach, so that the next build of the
  process failed. A caller that reads indicators after a campaign hands its
  own `system`, as before.

Requires muscadet 6.6.0 (or 6.0.6 on the 6.0 maintenance line).

## 0.1.1

- The package no longer declares `[tool.uv.sources]`. uv applies the sources a
  git dependency declares, so 0.1.0 imposed its own muscadet reference on any
  project installing it, and could not be resolved by a project pinning
  another muscadet release. The development environment is now built from
  `requirements-dev.txt`. No code change.

## 0.1.0

First release. PyCATSHOO becomes an engine registered at muscadet's extension
point, like any other, instead of a special case written into muscadet.

- The distribution advertises `pycatshoo` under the `muscadet.engines` entry
  point group. muscadet discovers it without importing it by name.
- `simulate` runs a system declaration as a Monte Carlo campaign, or as a whole
  study when handed a `study` and a `results_dir`.
- `isimu_start` opens an interactive session on a declaration.
- Registration is refused where the PyCATSHOO native library cannot be loaded,
  with the reason, so that the engines registered with muscadet are the engines
  the interpreter can run.

At this stage the adapter delegates: muscadet's `declare.build_system` builds
the system and cod3s 1.x runs it. Requires muscadet 6.4.0 (or 6.0.4 on the 6.0
maintenance line) and cod3s 1.26.
