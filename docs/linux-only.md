# Linux-Only Platform Support

*[Home](index.md) > Linux-Only Support*

## Platform Limitation

**AppImage Updater is designed exclusively for Linux systems.** This is a fundamental architectural decision based on the nature of the AppImage package format.

## Why Linux-Only

### AppImage is Linux-Specific

[AppImage](https://appimage.org/) is a universal software package format designed specifically for Linux distributions. It provides:

- **Portable Applications**: Self-contained executables that run on most Linux distributions
- **No Installation Required**: Applications run directly without system installation
- **Distribution Agnostic**: Works across different Linux distributions (Ubuntu, Fedora, Arch, etc.)

### Technical Reasons

1. **Package Format**: AppImage files are Linux ELF executables with embedded filesystems
1. **Runtime Dependencies**: Requires Linux kernel features and libraries
1. **File Permissions**: Uses Linux executable permissions and filesystem features
1. **System Integration**: Designed for Linux desktop environments and application launchers

## Supported Linux Distributions

AppImage Updater works on all major Linux distributions:

### Debian-Based

- **Ubuntu** (all versions)
- **Debian** (stable, testing, unstable)
- **Linux Mint**
- **Elementary OS**
- **Pop!\_OS**

### Red Hat-Based

- **Fedora**
- **CentOS** / **RHEL**
- **Rocky Linux**
- **AlmaLinux**

### SUSE-Based

- **openSUSE** (Leap, Tumbleweed)
- **SUSE Linux Enterprise**

### Arch-Based

- **Arch Linux**
- **Manjaro**
- **EndeavourOS**

### Other Distributions

- **Gentoo**
- **Void Linux**
- **Alpine Linux**
- **NixOS**
- And many others

## Architecture Support

AppImage Updater supports multiple CPU architectures on Linux:

- **x86_64** (AMD64) - Primary architecture
- **ARM64** (AArch64) - Modern ARM processors
- **ARMv7** - 32-bit ARM processors
- **i686** - 32-bit x86 processors (legacy)

## What About Other Platforms

### macOS

- **Not Supported**: macOS has its own package formats (.dmg, .pkg, .app bundles)
- **Alternative**: Use [Homebrew](https://brew.sh/) or [MacPorts](https://www.macports.org/) for macOS package management

### Windows

- **Not Supported**: Windows has its own package formats (.exe, .msi, .appx)
- **Alternative**: Use [Chocolatey](https://chocolatey.org/) or [Scoop](https://scoop.sh/) for Windows package management

### Why Not Cross-Platform

While the underlying Python code could theoretically run on other platforms, it would be misleading and confusing to support non-Linux platforms for a Linux-specific package format. This design decision ensures:

1. **Clear Purpose**: Tool focuses on its intended use case
1. **Better User Experience**: No confusion about platform compatibility
1. **Simpler Codebase**: No need for platform-specific workarounds
1. **Accurate Documentation**: All examples and guides are Linux-focused

## Installation Requirements

To use AppImage Updater, you need:

- **Linux Operating System** (any distribution)
- **Python 3.11+** (available on all modern Linux distributions)
- **Internet Connection** (for downloading updates)

## Error Handling

If you attempt to run AppImage Updater on a non-Linux system, you'll receive a clear error message:

```text
RuntimeError: AppImage Updater only supports Linux. Detected platform: darwin
```

This prevents confusion and clearly communicates the platform requirement.

## Getting Started on Linux

Ready to start using AppImage Updater on your Linux system?

1. **[Installation Guide](installation.md)** - Install AppImage Updater
1. **[Getting Started](getting-started.md)** - Add your first applications
1. **[Usage Guide](usage.md)** - Complete command reference
1. **[Examples](examples.md)** - Real-world usage patterns

## Community and Support

AppImage Updater is developed and tested exclusively on Linux systems. Our community consists of Linux users managing AppImage applications across various distributions.

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive Linux-focused guides
- **Examples**: Real-world Linux usage patterns
