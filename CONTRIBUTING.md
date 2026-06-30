# Contributing to EasiFlux Desktop

Thank you for contributing to EasiFlux Desktop. This document describes the development workflow for contributors and maintainers.

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

For local SDK development (optional):

```bash
pip install -e ../EasiFlux-SDK
```

## Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
ruff check src tests
ruff format --check src tests
```

Apply formatting locally:

```bash
ruff format src tests
```

## Testing

Run the test suite headlessly:

```bash
QT_QPA_PLATFORM=offscreen pytest tests/ -v
```

On Windows PowerShell:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
pytest tests/ -v
```

## Local Build

Clean build artifacts:

```bash
python scripts/clean.py
```

Build with PyInstaller:

```bash
python scripts/build.py --clean
python scripts/build.py --mode onefile --clean
```

Windows convenience script:

```powershell
./scripts/build_windows.ps1 -Mode onedir -Clean
```

## Pull Request Process

1. Fork the repository and create a feature branch.
2. Make your changes without modifying unrelated code.
3. Run lint and tests locally before opening a PR.
4. Open a pull request against `main`.
5. Ensure CI workflows pass:
   - **Lint** (`.github/workflows/lint.yml`)
   - **Test** (`.github/workflows/test.yml`)

## Release Process (Maintainers)

1. Update `version` in `pyproject.toml`.
2. Merge changes into `main`.
3. Create a GitHub Release with a tag starting with `V` (for example `V0.1.0`), and select the target branch explicitly:
   - `main` for stable releases
   - `dev` or another branch for beta releases

4. GitHub Actions (`.github/workflows/release.yml`) will:
   - Build the Windows executable with PyInstaller
   - Rename the release to `{version}.{YYYYMMDD}-{channel}` (for example `0.1.0.20260628-beta`)
   - Use channel `release` only when the Release target branch is `main`; all other branch names use `beta`
   - Upload `EasiFlux-Windows-{full-release-name}.zip` to the release

Users can download the zip from the Release page, extract it, and run `EasiFlux.exe` without installing Python.

## Project Structure

```
src/easiflux_desktop/   Application source code
tests/                  Pytest suite
resources/              Static assets (QSS styles)
scripts/                Local development helpers (not used by CI)
.github/workflows/      GitHub Actions CI/CD
```

## Questions

Open an issue for bugs, feature requests, or questions about contributing.
