# EasiFlux-Desktop

Professional cryptocurrency contract trading desktop client built on [EasiFlux-SDK](https://github.com/Akiyy-dev/EasiFlux-SDK).

## Requirements

- Python 3.10+
- EasiCoin API credentials (for live trading)

## Installation

```bash
# Install from source
pip install -e ".[dev]"

# Local SDK development (optional)
pip install -e ../EasiFlux-SDK
```

## Run

```bash
python -m easiflux_desktop
# or
easiflux-desktop
```

## Architecture

```
UI → Application → Service → Adapter → EasiFlux-SDK → Exchange API
```

See the architecture plan for full design documentation.

## Development

Set up a virtual environment and install development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide.

## Testing

```bash
QT_QPA_PLATFORM=offscreen pytest tests/ -v
```

CI runs tests on every push and pull request via [`.github/workflows/test.yml`](.github/workflows/test.yml).

## Linting

```bash
ruff check src tests
ruff format --check src tests
```

Apply formatting locally:

```bash
ruff format src tests
```

CI runs lint checks via [`.github/workflows/lint.yml`](.github/workflows/lint.yml).

## Building

Clean build artifacts:

```bash
python scripts/clean.py
```

Build a Windows executable locally with PyInstaller:

```bash
python scripts/build.py --clean
python scripts/build.py --mode onefile --clean
```

Windows convenience script:

```powershell
./scripts/build_windows.ps1 -Mode onedir -Clean
```

Build outputs:

- `dist/EasiFlux/EasiFlux.exe` (one-folder, default)
- `dist/EasiFlux.exe` (single-file)

Packaging specs:

- `easiflux_desktop.spec` (one-folder)
- `easiflux_desktop_onefile.spec` (single-file)

See [docs/windows-packaging.md](docs/windows-packaging.md) for the packaging checklist.

## Release

Releases are automated when a GitHub Release is published with a tag starting with `V`.

1. Update `version` in `pyproject.toml`.
2. Merge changes to `main` (or build from another branch for beta releases).
3. Create a GitHub Release with tag such as `V0.1.0`.

4. [`.github/workflows/release.yml`](.github/workflows/release.yml) builds on Windows and updates the release name to `{version}.{YYYYMMDD}-{channel}`:
   - example (beta): `0.1.0.20260628-beta`
   - example (main): `0.1.0.20260628-release`
   - create the Release from the `main` branch → `release`
   - create the Release from any other branch (for example `dev`) → `beta`
   - channel is determined from the Release target branch (`target_commitish`), not from whether the commit also exists on `main`
5. Uploads `EasiFlux-Windows-{full-release-name}.zip` to the release.

Users can download the zip from the Release page, extract it, and run `EasiFlux.exe` without installing Python.

## License

MIT
