#!/usr/bin/env python3
"""Example demonstrating the new centralized version services architecture.

This example shows how to use the new version services to replace scattered
version processing logic throughout the application.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from appimage_updater.config.models import ApplicationConfig
from appimage_updater.core.version_service import version_service


async def demonstrate_version_services():
    """Demonstrate the new centralized version services."""
    
    print("🎯 Centralized Version Services Architecture Demo")
    print("=" * 60)
    
    # Create example application config
    app_config = ApplicationConfig(
        name="InkScape",
        source_type="dynamic_download",
        url="https://inkscape.org/release/all/gnulinux/appimage/",
        download_dir=Path.home() / "Applications" / "InkScape",
        pattern="(?i)^Inkscape.*\\.AppImage$",
        prerelease=False
    )
    
    print(f"\n📱 Application: {app_config.name}")
    print(f"🔗 URL: {app_config.url}")
    print(f"📁 Download Dir: {app_config.download_dir}")
    
    # === LOCAL VERSION DETECTION ===
    print(f"\n🏠 LOCAL VERSION DETECTION")
    print("-" * 30)
    
    current_version = version_service.get_current_version(app_config)
    print(f"Current Version: {current_version}")
    
    if current_version:
        print("✅ Found version from .info file")
    else:
        print("❌ No current version detected")
    
    # === REPOSITORY VERSION DETECTION ===
    print(f"\n🌐 REPOSITORY VERSION DETECTION")
    print("-" * 35)
    
    latest_version = await version_service.get_latest_version(app_config)
    print(f"Latest Version: {latest_version}")
    
    if latest_version:
        print("✅ Successfully retrieved from repository")
    else:
        print("❌ Failed to get latest version")
    
    # === VERSION COMPARISON ===
    print(f"\n⚖️  VERSION COMPARISON")
    print("-" * 22)
    
    if current_version and latest_version:
        update_available = version_service.compare_versions(current_version, latest_version)
        print(f"Update Available: {update_available}")
        
        if update_available:
            print("🔄 Update recommended")
        else:
            print("✅ Application is up to date")
    else:
        print("❓ Cannot compare versions (missing data)")
    
    # === PATTERN GENERATION ===
    print(f"\n🎯 PATTERN GENERATION")
    print("-" * 21)
    
    # From repository
    repo_pattern = await version_service.generate_pattern_from_repository(app_config)
    print(f"Repository Pattern: {repo_pattern}")
    
    # From filename
    test_filename = "Inkscape-9dee831-x86_64.AppImage"
    file_pattern = version_service.generate_pattern_from_filename(test_filename)
    print(f"Filename Pattern: {file_pattern}")
    
    # === VERSION PARSING ===
    print(f"\n🔍 VERSION PARSING")
    print("-" * 18)
    
    # Test with git hash (should return None)
    git_hash_file = "Inkscape-9dee831-x86_64.AppImage"
    extracted_version = version_service.extract_version_from_filename(git_hash_file)
    print(f"From '{git_hash_file}': {extracted_version}")
    
    # Test with version
    version_file = "MyApp-v1.2.3-linux-x86_64.AppImage"
    extracted_version2 = version_service.extract_version_from_filename(version_file)
    print(f"From '{version_file}': {extracted_version2}")
    
    # === ARCHITECTURE BENEFITS ===
    print(f"\n🏗️  ARCHITECTURE BENEFITS")
    print("-" * 26)
    print("✅ Single Responsibility: Each service has one clear purpose")
    print("✅ Centralized Logic: No more scattered version processing")
    print("✅ Consistent Results: Same logic used everywhere")
    print("✅ Easy Testing: Services can be tested independently")
    print("✅ Repository Agnostic: Works with any repository type")
    print("✅ Maintainable: Changes in one place affect entire system")
    
    print(f"\n🎉 Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demonstrate_version_services())
