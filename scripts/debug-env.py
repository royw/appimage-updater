#!/usr/bin/env python3
"""
Environment debugging tool to compare local vs GitHub Actions environment
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import json

def run_command(cmd):
    """Run command and return output safely"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else f"ERROR: {result.stderr.strip()}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_environment_info():
    """Collect comprehensive environment information"""
    info = {
        "system": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "python_version": sys.version,
            "python_executable": sys.executable,
        },
        "environment_variables": {
            "CI": os.getenv("CI", "Not set"),
            "GITHUB_ACTIONS": os.getenv("GITHUB_ACTIONS", "Not set"),
            "RUNNER_OS": os.getenv("RUNNER_OS", "Not set"),
            "RUNNER_ARCH": os.getenv("RUNNER_ARCH", "Not set"),
            "PYTHONPATH": os.getenv("PYTHONPATH", "Not set"),
            "PATH": os.getenv("PATH", "Not set")[:200] + "..." if len(os.getenv("PATH", "")) > 200 else os.getenv("PATH", "Not set"),
        },
        "python_packages": {
            "uv_version": run_command("uv --version"),
            "pip_version": run_command("pip --version"),
            "pytest_version": run_command("python -c 'import pytest; print(pytest.__version__)'"),
            "typer_version": run_command("python -c 'import typer; print(typer.__version__)'"),
            "httpx_version": run_command("python -c 'import httpx; print(httpx.__version__)'"),
        },
        "project_info": {
            "current_directory": str(Path.cwd()),
            "project_files": {
                "pyproject.toml": Path("pyproject.toml").exists(),
                "uv.lock": Path("uv.lock").exists(),
                "src/appimage_updater": Path("src/appimage_updater").exists(),
                "tests/": Path("tests").exists(),
            }
        },
        "test_environment": {
            "pytest_plugins": run_command("python -c 'import pytest; print([p for p in pytest.config.get_plugin_manager().list_plugin_distinfo()])'"),
            "asyncio_version": run_command("python -c 'import asyncio; print(asyncio.__doc__[:50] if asyncio.__doc__ else \"No doc\")'"),
            "mock_available": run_command("python -c 'from unittest.mock import Mock, AsyncMock; print(\"Available\")'"),
        }
    }
    
    return info

def compare_with_github_actions():
    """Show differences from expected GitHub Actions environment"""
    print("🔍 Environment Analysis")
    print("=" * 50)
    
    # Expected GitHub Actions values
    expected_ci_vars = {
        "CI": "true",
        "GITHUB_ACTIONS": "true", 
        "RUNNER_OS": "Linux",
        "RUNNER_ARCH": "X64"
    }
    
    print("\n📋 CI Environment Variables:")
    for var, expected in expected_ci_vars.items():
        actual = os.getenv(var, "Not set")
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {var}: {actual} (expected: {expected})")
    
    print(f"\n🐍 Python Environment:")
    print(f"  Version: {sys.version.split()[0]}")
    print(f"  Executable: {sys.executable}")
    print(f"  Platform: {platform.platform()}")
    
    print(f"\n📦 Package Versions:")
    packages = ["uv", "pytest", "typer", "httpx", "ruff", "mypy"]
    for pkg in packages:
        version = run_command(f"python -c 'import {pkg}; print({pkg}.__version__)'")
        if "ERROR" not in version:
            print(f"  ✅ {pkg}: {version}")
        else:
            version_alt = run_command(f"{pkg} --version")
            if "ERROR" not in version_alt:
                print(f"  ✅ {pkg}: {version_alt}")
            else:
                print(f"  ❌ {pkg}: Not available")

def save_debug_info():
    """Save complete environment info to file"""
    info = get_environment_info()
    
    debug_file = Path("debug-environment.json")
    with open(debug_file, "w") as f:
        json.dump(info, f, indent=2, default=str)
    
    print(f"\n💾 Complete environment info saved to: {debug_file}")
    return debug_file

def main():
    print("🔧 AppImage Updater - Environment Debug Tool")
    print("=" * 50)
    
    compare_with_github_actions()
    debug_file = save_debug_info()
    
    print(f"\n🚀 Quick CI Test:")
    print("Run this to test your environment:")
    print("  ./scripts/ci-local.sh")
    print("\nOr test specific components:")
    print("  uv run pytest tests/e2e/ -v")
    print("  uv run mypy src/")
    print("  uv run ruff check src/")

if __name__ == "__main__":
    main()
