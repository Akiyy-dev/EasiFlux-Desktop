# Windows Packaging Checklist

## Output

- Local one-folder build: `dist/EasiFlux/EasiFlux.exe`
- Local single-file build: `dist/EasiFlux.exe`
- Release archive: `EasiFlux-Windows.zip` (created by GitHub Actions on tag push)

## Local Build Commands

```bash
python scripts/clean.py
python scripts/build.py --clean
python scripts/build.py --mode onefile --clean
```

Windows convenience script:

```powershell
./scripts/build_windows.ps1 -Mode onedir -Clean
./scripts/build_windows.ps1 -Mode onefile -Clean
```

## Acceptance Criteria

- `EasiFlux.exe` starts on machines without Python installed.
- Runtime dependencies are bundled (no `pip install` needed on target machine).
- `resources/styles/dark.qss` and `resources/styles/light.qss` are present and load at startup.
- `PySide6` GUI starts without missing Qt plugin errors.
- `EasiFlux-SDK[websocket]` imports correctly inside packaged app.

## CI / Release Validation

- `.github/workflows/release.yml` runs on tags matching `v*`.
- Builds on `windows-latest` with PyInstaller (`easiflux_desktop.spec`).
- Packages `dist/EasiFlux` into `EasiFlux-Windows.zip`.
- Creates a GitHub Release and uploads the zip as a release asset.

Push/PR workflows (`test.yml`, `lint.yml`) do not depend on local `scripts/` helpers.
