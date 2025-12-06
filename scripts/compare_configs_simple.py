#!/usr/bin/env python3
"""Compare appimage-updater configuration files between two directories - concise version."""

import json
from pathlib import Path
from typing import Any


def load_config_file(file_path: Path) -> dict[str, Any]:
    """Load a JSON config file."""
    try:
        with open(file_path) as f:
            config = json.load(f)
            return config if isinstance(config, dict) else {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def get_config_files(directory: Path) -> dict[str, Path]:
    """Get all JSON config files in a directory, keyed by filename."""
    config_files = {}
    if directory.exists():
        for file_path in directory.glob("*.json"):
            config_files[file_path.name] = file_path
    return config_files


def extract_app_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract the first app configuration from the config file."""
    if "applications" in config and config["applications"]:
        app_list = config["applications"]
        if isinstance(app_list, list) and len(app_list) > 0:
            first_app = app_list[0]
            return first_app if isinstance(first_app, dict) else {}
    return {}


def compare_simple_values(config1: dict[str, Any], config2: dict[str, Any]) -> dict[str, tuple[Any, Any]]:
    """Compare two config dictionaries and return differences in simple values."""
    differences = {}

    # Keys to compare (excluding complex nested objects for brevity)
    simple_keys = [
        "name", "source_type", "url", "download_dir", "pattern",
        "version_pattern", "basename", "enabled", "prerelease",
        "rotation_enabled", "symlink_path", "retain_count"
    ]

    for key in simple_keys:
        value1 = config1.get(key)
        value2 = config2.get(key)

        if key not in config1:
            differences[key] = ("MISSING", value2 if value2 is not None else "null")
        elif key not in config2:
            differences[key] = (value1 if value1 is not None else "null", "MISSING")
        elif value1 != value2:
            differences[key] = (value1 if value1 is not None else "null", value2 if value2 is not None else "null")

    return differences


def format_value(value: Any) -> str:
    """Format a value for display."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str) and len(value) > 80:
        return value[:77] + "..."
    return str(value)


def main() -> None:
    """Main comparison function."""
    dir1 = Path.home() / ".config/appimage-updater/apps"
    dir2 = Path.home() / ".config/appimage-updater.old/apps"

    print("🔍 AppImage Updater Configuration Comparison")
    print("=" * 50)
    print(f"Directory 1: {dir1}")
    print(f"Directory 2: {dir2}")
    print()
    
    # Get config files from both directories
    configs1 = get_config_files(dir1)
    configs2 = get_config_files(dir2)
    
    if not configs1 and not configs2:
        print("❌ No config files found in either directory")
        return
    
    # Find files that exist in both directories
    common_files = set(configs1.keys()) & set(configs2.keys())
    
    # Find files that only exist in one directory
    only_in_dir1 = set(configs1.keys()) - set(configs2.keys())
    only_in_dir2 = set(configs2.keys()) - set(configs1.keys())
    
    # Compare common files
    if common_files:
        print("📊 CONFIGURATION DIFFERENCES")
        print("=" * 40)
        
        any_differences = False
        for filename in sorted(common_files):
            app_name = filename.replace('.json', '')
            full_config1 = load_config_file(configs1[filename])
            full_config2 = load_config_file(configs2[filename])
            
            config1 = extract_app_config(full_config1)
            config2 = extract_app_config(full_config2)
            
            differences = compare_simple_values(config1, config2)
            
            print(f"\n🔸 {app_name}")
            print("-" * 30)
            if differences:
                any_differences = True
                
                for key, (val1, val2) in sorted(differences.items()):
                    print(f"  {key}:")
                    print(f"   dir1 ← {format_value(val1)}")
                    print(f"   dir2 → {format_value(val2)}")
            else:
                print(f"✅ No differences found in {app_name}")
        
        if not any_differences:
            print("✅ No differences found in common configuration files")
    
    # Show files only in one directory
    if only_in_dir1 or only_in_dir2:
        print(f"\n📂 FILES WITHOUT COUNTERPARTS")
        print("=" * 40)
        
        if only_in_dir1:
            print(f"\nOnly in {dir1.name}/:")
            for filename in sorted(only_in_dir1):
                app_name = filename.replace('.json', '')
                print(f"  • {app_name}")
        
        if only_in_dir2:
            print(f"\nOnly in {dir2.name}/:")
            for filename in sorted(only_in_dir2):
                app_name = filename.replace('.json', '')
                print(f"  • {app_name}")
    
    # Summary
    print("\n📈 SUMMARY")
    print("=" * 20)
    print(f"Files in {dir1.name}/: {len(configs1)}")
    print(f"Files in {dir2.name}/: {len(configs2)}")
    print(f"Common files: {len(common_files)}")
    print(f"Only in dir1: {len(only_in_dir1)}")
    print(f"Only in dir2: {len(only_in_dir2)}")


if __name__ == "__main__":
    main()
