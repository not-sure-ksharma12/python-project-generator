# Self-Review: PR #3 — Feature-Flag File Generation & Placeholder Tests

## What changed and why?

Added `tests/test_feature_flags.py` with 22 tests covering feature-flag behavior and metadata placeholder injection. The minimal template's feature flags (cli, tests, pypi_packaging, readme, changelog, gitignore, contributors, code_of_conduct, security) previously had no dedicated tests verifying that:
- Enabling a flag creates the expected file
- Disabling a flag omits the file
- Feature combinations work together without conflicts
- Metadata (author, email, version, description) is correctly embedded in generated files

## Why is this the right test layer (unit/integration/UI)?

These are **integration tests** — they call `generate_project()` end-to-end and inspect the filesystem output. This is the right level because:
- Feature flags affect file *generation*, not just logic — we need to verify actual files
- Mocking the filesystem would miss real bugs (e.g., directory creation order, encoding issues)
- Tests use temp directories and are fast (~0.08s total), so no need for mocking

## What could still break / what's not covered?

- Only the `minimal-python` template is tested for feature flags. Other templates (Flask, FastAPI, etc.) have their own feature sets.
- Advanced features like `mac_app_bundle`, `icon_generator`, and `github_actions` are not tested here (they're more complex and were not in scope for this issue).
- File *content* is checked for metadata presence but not for full correctness — e.g., we verify the author is in setup.py but don't assert the full file structure.

## What risks or follow-ups remain?

- Issue #5 (parameterized template tests) will cover the other templates.
- Consider adding feature-flag tests for non-minimal templates in a future issue.
- The `_apply_optional_scripts` method (mac_app_bundle, icon_generator) has significant untested code.
