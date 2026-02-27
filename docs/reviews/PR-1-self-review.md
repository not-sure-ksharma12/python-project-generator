# Self-Review: PR #1 — CI/CD Pipeline

## What changed and why?

Added a GitHub Actions CI workflow (`.github/workflows/ci.yml`) that automatically runs the test suite on every push to `main`, every pull request, and on manual dispatch. This is the foundation for regression protection — without CI, all test improvements are only useful when developers remember to run them locally.

## Why is this the right test layer (unit/integration/UI)?

This is **infrastructure**, not a test layer itself. It ensures that all tests (unit, integration, and future additions) are executed automatically, catching regressions before they reach `main`. The workflow uses a matrix strategy across Python 3.8–3.12 to verify cross-version compatibility.

## What could still break / what's not covered?

- **wxPython GUI tests** are not run in CI because wxPython requires a display server. GUI tests that mock wx properly will still pass, but any test requiring an actual display will need `xvfb` or similar.
- **OS matrix** is limited to Ubuntu. macOS and Windows runners could be added but would increase CI cost and time.
- **Coverage threshold** is not enforced — the workflow reports coverage but does not fail on a drop. This could be added as a follow-up.

## What risks or follow-ups remain?

- Consider adding a coverage threshold gate (e.g., fail if coverage drops below 30%).
- Consider adding macOS/Windows to the matrix once the test suite is more mature.
- A status badge could be added to `README.md` once the workflow is verified green.
