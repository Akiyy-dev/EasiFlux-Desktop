# AGENTS.md

## Cursor Cloud specific instructions

EasiFlux-Desktop is a single Python PySide6 (Qt 6) desktop GUI app — a cryptocurrency
contract trading client for EasiCoin. There is **no local backend, database, or
container**; the only external dependency for *live* trading is the remote EasiCoin
API (via the `EasiFlux-SDK` PyPI package), which is **optional** and not needed to
launch the app or run the test suite.

### Environment
- Dependencies are installed into a virtualenv at `.venv` (the startup update script
  creates it and runs `pip install -e ".[dev]"`). Activate it before any command:
  `source .venv/bin/activate`.
- Qt system libraries (libegl1, libgl1, libxcb-*, etc.) and `python3.12-venv` are
  pre-installed in the VM snapshot. They are NOT in the update script; if a fresh VM
  is missing them, re-install per `.github/workflows/ci.yml` (Qt libs) and
  `apt-get install -y python3.12-venv`.

### Lint / test / build / run (standard commands)
- Lint: `ruff check src tests`
- Tests: `QT_QPA_PLATFORM=offscreen pytest tests/ -v` — headless; `QT_QPA_PLATFORM=offscreen`
  is required since there is no implicit display in tests.
- Run the GUI app (headless display is available at `DISPLAY=:1`):
  `DISPLAY=:1 QT_QPA_PLATFORM=xcb python -m easiflux_desktop` (or the `easiflux-desktop` entry point).
  For a non-GUI smoke check use `QT_QPA_PLATFORM=offscreen` instead.
- Build (optional): `pyinstaller easiflux_desktop.spec`.

### Non-obvious caveats
- On startup the app logs `Keyring read failed: No recommended backend was available`.
  This is **benign** — there is no OS keychain backend in the VM, credential storage is
  handled gracefully and the app/tests run fine without it.
- All data views (Market chart, Account/Orders tables, Analytics) render empty without
  live API credentials; this is expected, not a bug.
- The optional `local-sdk` extra (`pip install -e ".[local-sdk]"`) points the SDK at a
  sibling `../EasiFlux-SDK` checkout — only use it if that repo is present.
