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

- `.github/workflows/release.yml` runs when a GitHub Release is published with a tag starting with `V` (for example `V0.1.0`).
- Builds on `windows-latest` with PyInstaller (`easiflux_desktop.spec`).
- Appends build metadata to the release name: `{version}.{YYYYMMDD}-{channel}`.
  - example (beta): `0.1.0.20260628-beta`
  - example (main): `0.1.0.20260628-release`
  - `main` branch builds use channel suffix `release`
  - non-`main` branch builds use channel suffix `beta`
- Packages `dist/EasiFlux` into `EasiFlux-Windows-{version}.{date}-{channel}.zip`.
- Uploads the zip to the same GitHub Release and updates the release title.

Push/PR workflows (`test.yml`, `lint.yml`) do not depend on local `scripts/` helpers.
