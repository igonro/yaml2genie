# Continuous integration

The GitHub Actions workflow in `.github/workflows/ci.yml` runs on pushes and
pull requests. It keeps quality checks and unit tests in parallel, uses the
committed `uv.lock`, and verifies the committed CLI artifact before accepting a
change.
