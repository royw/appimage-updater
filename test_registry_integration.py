#!/usr/bin/env python3
"""Integration test of the registry system with AppImage Updater CLI."""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from appimage_updater.repositories.registry import get_repository_registry
from appimage_updater.repositories.domain_service import DomainKnowledgeService
from appimage_updater.repositories.factory import get_repository_client_async


async def test_registry_integration():
    """Test the registry system integration with real URLs."""
    print("🧪 Testing Registry System Integration")
    print("=" * 50)
    
    # Test URLs for different repository types
    test_cases = [
        ("GitHub", "https://github.com/AppImage/AppImageKit"),
        ("GitLab", "https://gitlab.com/inkscape/inkscape"),
        ("Direct AppImage", "https://example.com/app.AppImage"),
        ("Dynamic Download", "https://unknown.example.com/releases"),
    ]
    
    registry = get_repository_registry()
    domain_service = DomainKnowledgeService()
    
    print("\n1. Testing Repository Detection:")
    for name, url in test_cases:
        print(f"\n   {name}: {url}")
        
        # Test handler detection
        handlers = registry.get_handlers_for_url(url)
        print(f"   Registry handlers: {[h.metadata.name for h in handlers]}")
        
        # Test domain knowledge
        known_handler = domain_service.get_handler_by_domain_knowledge(url)
        if known_handler:
            print(f"   Domain knowledge: {known_handler.metadata.name}")
        else:
            print("   Domain knowledge: None (will probe)")
        
        # Test client creation
        try:
            client = await get_repository_client_async(url, timeout=5)
            print(f"   ✅ Client created: {type(client).__name__}")
            print(f"   Repository type: {client.repository_type}")
        except Exception as e:
            print(f"   ❌ Client creation failed: {e}")
    
    print("\n2. Testing Domain Knowledge Learning:")
    
    # Test learning from a successful GitHub detection
    github_url = "https://github.com/example/test"
    try:
        # This should learn that github.com -> github
        client = await get_repository_client_async(github_url, timeout=5)
        print(f"   ✅ GitHub client created for learning test")
        
        # Check if domain knowledge was updated
        known_domains = domain_service.get_all_known_domains()
        print(f"   Known domains after learning: {known_domains}")
        
    except Exception as e:
        print(f"   ❌ Learning test failed: {e}")
    
    print("\n3. Testing Registry Metadata:")
    all_handlers = registry.get_all_handlers()
    print(f"   Total handlers: {len(all_handlers)}")
    
    for handler in all_handlers:
        metadata = handler.metadata
        print(f"   - {metadata.name} (priority: {metadata.priority})")
        print(f"     Domains: {metadata.supported_domains}")
        print(f"     Description: {metadata.description}")
    
    print("\n✅ Registry integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_registry_integration())
