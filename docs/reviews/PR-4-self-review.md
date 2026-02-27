# Self-Review: PR #4 — Parameterized Generation Tests for All Template Types

## What changed and why?

Added `tests/test_all_templates.py` with 61 tests covering all 18 registered template types. Previously only 2 templates (minimal-python and flask-web-app) had generation tests. This PR uses `pytest.mark.parametrize` to test every template, plus dedicated structure tests for 7 fully-implemented templates (Flask, FastAPI, data-science, CLI tool, binary-extension, namespace-package, plugin-framework).

## Why is this the right test layer (unit/integration/UI)?

These are **integration tests** — they call `generate_project()` with real filesystem output and verify the resulting directory structure. This is the right level because:
- Template generation involves file I/O, directory creation, and string interpolation
- Mocking the filesystem would miss real bugs (path issues, encoding, missing directories)
- Using `pytest.mark.parametrize` keeps the tests DRY and automatically covers new templates as they're added
- Tests complete in ~0.14s total, so performance is not a concern

## What could still break / what's not covered?

- **File content correctness** is not deeply verified for most templates. We check that files exist but don't assert the full content of every generated file.
- **Stub templates** (django, ml, library, game, desktop-gui, microservice, api-client, automation, jupyter-research) all fall back to `_generate_minimal_template`, so they pass but don't test unique behavior. When these stubs are implemented, the structure tests will need updating.
- **Template-specific dependencies** in generated `requirements.txt` files are not checked (e.g., Flask template should list Flask as a dependency).

## What risks or follow-ups remain?

- When stub templates get full implementations, add structure assertions for each.
- Consider adding content-level checks for requirements.txt per template.
- The `python-skeleton` template uses a download path that falls back to minimal — this is tested but the download/cache path is not exercised (would need Issue #4).
