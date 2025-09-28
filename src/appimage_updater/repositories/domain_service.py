"""Domain knowledge service for intelligent repository detection."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from loguru import logger

from ..config.manager import GlobalConfigManager
from ..config.models import DomainKnowledge
from .registry import get_repository_registry, RepositoryHandler


class DomainKnowledgeService:
    """Service for managing domain knowledge and repository detection."""
    
    def __init__(self, config_manager: GlobalConfigManager | None = None):
        self.config_manager = config_manager or GlobalConfigManager()
        self.registry = get_repository_registry()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""
    
    def get_handler_by_domain_knowledge(self, url: str) -> RepositoryHandler | None:
        """Get repository handler using domain knowledge (fast path)."""
        domain = self._extract_domain(url)
        if not domain:
            return None
        
        try:
            config = self.config_manager.load_config()
            knowledge = config.global_config.domain_knowledge
            
            # Check each repository type's known domains
            domain_mappings = {
                "github": knowledge.github_domains,
                "gitlab": knowledge.gitlab_domains, 
                "direct_download": knowledge.direct_domains,
                "dynamic_download": knowledge.dynamic_domains,
            }
            
            for handler_name, domains in domain_mappings.items():
                if domain in domains:
                    handler = self.registry.get_handler(handler_name)
                    if handler:
                        logger.debug(f"Fast-path: {domain} -> {handler_name}")
                        return handler
            
        except Exception as e:
            logger.debug(f"Error loading domain knowledge: {e}")
        
        return None
    
    def get_handlers_for_url(self, url: str) -> list[RepositoryHandler]:
        """Get all handlers that can handle the URL, with domain knowledge optimization."""
        # First try fast-path using domain knowledge
        known_handler = self.get_handler_by_domain_knowledge(url)
        if known_handler:
            return [known_handler]
        
        # Fall back to registry-based detection
        return self.registry.get_handlers_for_url(url)
    
    async def learn_domain(self, url: str, handler_name: str) -> None:
        """Persist successful domain detection."""
        domain = self._extract_domain(url)
        if not domain:
            return
        
        try:
            config = self.config_manager.load_config()
            knowledge = config.global_config.domain_knowledge
            
            # Add to appropriate domain list
            updated = False
            if handler_name == "github" and domain not in knowledge.github_domains:
                knowledge.github_domains.append(domain)
                updated = True
            elif handler_name == "gitlab" and domain not in knowledge.gitlab_domains:
                knowledge.gitlab_domains.append(domain)
                updated = True
            elif handler_name == "direct_download" and domain not in knowledge.direct_domains:
                knowledge.direct_domains.append(domain)
                updated = True
            elif handler_name == "dynamic_download" and domain not in knowledge.dynamic_domains:
                knowledge.dynamic_domains.append(domain)
                updated = True
            
            if updated:
                knowledge.last_updated = datetime.now().isoformat()
                self.config_manager.save_config(config)
                logger.info(f"Learned domain: {domain} -> {handler_name}")
            
        except Exception as e:
            logger.error(f"Failed to learn domain {domain}: {e}")
    
    async def forget_domain(self, url: str, failed_handler_name: str) -> None:
        """Remove domain from knowledge due to API failure."""
        domain = self._extract_domain(url)
        if not domain:
            return
        
        try:
            config = self.config_manager.load_config()
            knowledge = config.global_config.domain_knowledge
            
            # Remove from failed handler's domain list
            updated = False
            if failed_handler_name == "github" and domain in knowledge.github_domains:
                knowledge.github_domains.remove(domain)
                updated = True
            elif failed_handler_name == "gitlab" and domain in knowledge.gitlab_domains:
                knowledge.gitlab_domains.remove(domain)
                updated = True
            elif failed_handler_name == "direct_download" and domain in knowledge.direct_domains:
                knowledge.direct_domains.remove(domain)
                updated = True
            elif failed_handler_name == "dynamic_download" and domain in knowledge.dynamic_domains:
                knowledge.dynamic_domains.remove(domain)
                updated = True
            
            if updated:
                knowledge.last_updated = datetime.now().isoformat()
                self.config_manager.save_config(config)
                logger.warning(f"Forgot domain: {domain} (failed as {failed_handler_name})")
            
        except Exception as e:
            logger.error(f"Failed to forget domain {domain}: {e}")
    
    def get_all_known_domains(self) -> dict[str, list[str]]:
        """Get all known domains grouped by repository type."""
        try:
            config = self.config_manager.load_config()
            knowledge = config.global_config.domain_knowledge
            
            return {
                "github": list(knowledge.github_domains),
                "gitlab": list(knowledge.gitlab_domains),
                "direct_download": list(knowledge.direct_domains),
                "dynamic_download": list(knowledge.dynamic_domains),
            }
        except Exception as e:
            logger.error(f"Failed to get known domains: {e}")
            return {"github": [], "gitlab": [], "direct_download": [], "dynamic_download": []}
    
    def get_registry_supported_domains(self) -> dict[str, list[str]]:
        """Get supported domains from registry handlers."""
        return self.registry.get_supported_domains()
    
    def initialize_default_domains(self) -> None:
        """Initialize domain knowledge with default known domains from handlers."""
        try:
            config = self.config_manager.load_config()
            knowledge = config.global_config.domain_knowledge
            
            # Get default domains from handlers
            registry_domains = self.get_registry_supported_domains()
            
            updated = False
            for handler_name, domains in registry_domains.items():
                if handler_name == "github":
                    for domain in domains:
                        if domain not in knowledge.github_domains:
                            knowledge.github_domains.append(domain)
                            updated = True
                elif handler_name == "gitlab":
                    for domain in domains:
                        if domain not in knowledge.gitlab_domains:
                            knowledge.gitlab_domains.append(domain)
                            updated = True
            
            if updated:
                knowledge.last_updated = datetime.now().isoformat()
                self.config_manager.save_config(config)
                logger.info("Initialized domain knowledge with handler defaults")
                
        except Exception as e:
            logger.error(f"Failed to initialize default domains: {e}")
