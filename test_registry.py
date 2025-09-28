#!/usr/bin/env python3
"""Quick test of the repository registry system."""

import asyncio
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from appimage_updater.repositories.registry import get_repository_registry
from appimage_updater.repositories.domain_service import DomainKnowledgeService
from appimage_updater.config.manager import GlobalConfigManager


async def test_registry():
    """Test the repository registry system."""
    print("🧪 Testing Repository Registry System")
    print("=" * 50)
    
    # Test 1: Registry Discovery
    print("\n1. Testing Registry Discovery:")
    registry = get_repository_registry()
    handlers = registry.get_all_handlers()
    
    print(f"   Found {len(handlers)} handlers:")
    for handler in handlers:
        print(f"   - {handler.metadata.name} (priority: {handler.metadata.priority})")
        print(f"     Domains: {handler.metadata.supported_domains}")
        print(f"     Description: {handler.metadata.description}")
    
    # Test 2: URL Handler Detection
    print("\n2. Testing URL Handler Detection:")
    test_urls = [
        "https://github.com/user/repo",
        "https://gitlab.com/user/repo", 
        "https://example.com/app.AppImage",
        "https://unknown.com/releases/latest"
    ]
    
    for url in test_urls:
        compatible_handlers = registry.get_handlers_for_url(url)
        print(f"   {url}:")
        if compatible_handlers:
            for handler in compatible_handlers:
                print(f"     -> {handler.metadata.name}")
        else:
            print("     -> No handlers found")
    
    # Test 3: Domain Knowledge Service
    print("\n3. Testing Domain Knowledge Service:")
    try:
        domain_service = DomainKnowledgeService()
        known_domains = domain_service.get_all_known_domains()
        print(f"   Known domains: {known_domains}")
        
        # Test domain knowledge lookup
        github_handler = domain_service.get_handler_by_domain_knowledge("https://github.com/user/repo")
        if github_handler:
            print(f"   GitHub domain knowledge: {github_handler.metadata.name}")
        else:
            print("   No GitHub domain knowledge found")
            
    except Exception as e:
        print(f"   Domain service error: {e}")
    
    # Test 4: Handler Creation
    print("\n4. Testing Handler Creation:")
    github_handler = registry.get_handler("github")
    if github_handler:
        try:
            client = github_handler.create_client(timeout=30)
            print(f"   GitHub client created: {type(client).__name__}")
        except Exception as e:
            print(f"   GitHub client creation failed: {e}")
    
    print("\n✅ Registry system test completed!")


if __name__ == "__main__":
    asyncio.run(test_registry())
