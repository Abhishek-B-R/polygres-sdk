# Polygres SDK migration notes

Polygres publishes topic-based migration notes here only when a release adds a
deprecation, changes existing behavior, or makes a breaking pre-1.0 change.
Routine additive releases do not receive an empty topic file.

Each topic note records the affected SDK versions and methods, old and new
behavior, exact caller action, warning and removal versions, and safe before
and after examples. The notes are included in both wheel and source
distributions and can be read with `importlib.resources` from
`polygres/migrations`.

Version 0.2.0 adds package and Runtime API contract metadata without changing
the behavior of existing public SDK methods, so it requires no topic migration
note.
