# Self-Review: PR #2 — CLI Interface Tests

## What changed and why?

Added `tests/test_cli.py` with 14 tests covering the `__main__.py` CLI entry point. This file previously had **0% test coverage** — the highest-priority gap in the codebase. Tests cover argument parsing (`--version`, `--help`, `--cli`, `--gui`), flag routing to the correct modules, argument forwarding, and error handling when wxPython is unavailable.

## Why is this the right test layer (unit/integration/UI)?

These are **unit tests** with mocked dependencies. The `__main__.py` module is a thin dispatcher — it parses arguments and delegates to either the GUI or CLI module. Unit tests with mocks are the right approach because:
- We don't want tests to depend on wxPython being installed
- We don't want tests to actually generate projects (that's integration-level)
- We need fast, deterministic verification of routing logic

## What could still break / what's not covered?

- The actual `from . import project_generator` import failure path is hard to test because Python's import machinery caches modules aggressively. The defensive fallback (`import project_generator as cli_mod`) is effectively untestable without subprocess isolation.
- The GUI launch path (`app.MainLoop()`) is not tested beyond verifying that a missing `wx` returns exit code 1.
- Coverage is 63% rather than the 80% target — the remaining 37% is the GUI launch path which requires wxPython.

## What risks or follow-ups remain?

- GUI integration tests (Issue #1) would cover the remaining `__main__.py` paths.
- Consider using `subprocess.run` to test `python -m python_project_generator --version` end-to-end.
