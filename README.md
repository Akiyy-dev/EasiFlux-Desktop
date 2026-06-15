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

```bash
ruff check src tests
pytest tests/ -v
```

## License

MIT
