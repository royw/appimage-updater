# Installation

AppImage Updater can be installed using several methods depending on your needs.

## Requirements

- Python 3.11 or higher
- Internet connection for downloading updates

## End User Installation

### Using pipx (Recommended)

The recommended way to install AppImage Updater is using pipx, which creates an isolated environment:

```bash
pipx install appimage-updater
```

### Using pip

Alternatively, you can install using pip:

```bash
# User installation (recommended)
pip install --user appimage-updater

# System-wide installation (requires sudo)
sudo pip install appimage-updater
```

### From Source (Non-Development)

To install the latest version directly from the repository:

```bash
pipx install git+https://github.com/royw/appimage-updater.git
# or with pip
pip install --user git+https://github.com/royw/appimage-updater.git
```

## Development Installation

### Prerequisites for Development

- Git - Version control system
- Python 3.11 or higher
- [uv package manager](https://docs.astral.sh/uv/getting-started/installation/)
- [Task](https://taskfile.dev/installation/) - Task runner for development commands

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater

# Install dependencies and setup environment
task install

# Activate virtual environment
source .venv/bin/activate

# Verify setup
task check
```

### Alternative Development Setup

If you prefer manual setup without Task:

```bash
# Clone and enter directory
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater

# Install dependencies
uv sync

# Install the package in development mode
uv pip install -e .
```

## Verification

After installation, verify that the application is working correctly:

```bash
appimage-updater --version
```

You should see output similar to:

```text
appimage-updater, version 0.2.0
```

## Next Steps

Once installed, you can:

1. [Get started quickly](getting-started.md#quick-start)
1. [Add your first application](getting-started.md#adding-applications)
1. [Start checking for updates](getting-started.md#checking-updates)

For developers:

1. See [Development Guide](development.md) for workflow and contribution guidelines
1. Review [Architecture](architecture.md) for codebase understanding
1. Check [Testing](testing.md) for running tests

## Alternative Installation Methods

### Virtual Environment

For isolated installation without pipx:

```bash
# Create virtual environment
python -m venv appimage-updater-env

# Activate environment
source appimage-updater-env/bin/activate  # On Windows: appimage-updater-env\Scripts\activate

# Install AppImage Updater
pip install appimage-updater
```

### Docker (Experimental)

For containerized usage:

```bash
# Build container
docker build -t appimage-updater .

# Run with volume mount for config
docker run -v ~/.config/appimage-updater:/config appimage-updater check
```

## Troubleshooting

### Python Version Issues

Ensure you're using Python 3.11 or higher:

```bash
python --version
```

### Permission Errors

If you get permission errors:

- **Recommended**: Use `pipx install appimage-updater`
- Use `--user` flag: `pip install --user appimage-updater`
- Create a virtual environment
- **Avoid**: Don't use `sudo` with pipx

### pipx Not Found

If pipx is not installed:

```bash
# Install pipx first
python -m pip install --user pipx
python -m pipx ensurepath

# Then install AppImage Updater
pipx install appimage-updater
```

### Development Setup Issues

For development installation problems:

```bash
# Ensure uv is installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure Task is installed (see https://taskfile.dev/installation/)
# Then retry setup
task install
```
