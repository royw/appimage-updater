# Installation

AppImage Updater can be installed using several methods depending on your needs.

## Requirements

- Python 3.11 or higher
- pip (Python package manager)
- Internet connection for downloading updates

## Installation Methods

### From PyPI (Recommended)

The easiest way to install AppImage Updater is from PyPI using pip:

```bash
pip install appimage-updater
```

For system-wide installation, you might need `sudo`:

```bash
sudo pip install appimage-updater
```

### From Source

If you want the latest development version or want to contribute:

```bash
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater
pip install -e .
```

### Using UV (Fast Python Package Manager)

If you have [uv](https://github.com/astral-sh/uv) installed:

```bash
uv pip install appimage-updater
```

### Using pipx (Isolated Installation)

For an isolated installation that won't interfere with your system Python:

```bash
pipx install appimage-updater
```

## Verification

After installation, verify that the application is working correctly:

```bash
appimage-updater --version
```

You should see output similar to:
```
appimage-updater, version 0.2.0
```

## Next Steps

Once installed, you can:

1. [Initialize your configuration](getting-started.md#initialization)
2. [Add your first application](getting-started.md#adding-applications)
3. [Start checking for updates](getting-started.md#checking-updates)

## Troubleshooting

### Python Version Issues

If you encounter Python version errors, ensure you're using Python 3.11 or higher:

```bash
python --version
```

### Permission Errors

If you get permission errors during installation:

- Use `--user` flag: `pip install --user appimage-updater`
- Use a virtual environment (recommended)
- Use `pipx` for isolated installation

### Virtual Environment Setup

For isolated development:

```bash
python -m venv appimage-updater-env
source appimage-updater-env/bin/activate  # On Windows: appimage-updater-env\Scripts\activate
pip install appimage-updater
```
