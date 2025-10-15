"""Domain knowledge service for intelligent repository detection."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from loguru import logger

from ..config.manager import GlobalConfigManager
from ..config.models import DomainKnowledge
from .registry import RepositoryHandler, get_repository_registry


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
            knowledge = self._load_domain_knowledge()
            return self._find_handler_for_domain(domain, knowledge)
        except Exception as e:
            logger.debug(f"Error loading domain knowledge: {e}")
            return None

    def _load_domain_knowledge(self) -> DomainKnowledge:
        """Load domain knowledge from configuration."""
        config = self.config_manager.load_config()
        return config.global_config.domain_knowledge

    def _get_domain_mappings(self, knowledge: Any) -> dict[str, list[str]]:
        """Get domain mappings for known repository types."""
        return {
            "github": knowledge.github_domains,
            "gitlab": knowledge.gitlab_domains,
            "direct_download": knowledge.direct_domains,
            "dynamic_download": knowledge.dynamic_domains,
        }

    def _find_handler_for_domain(self, domain: str, knowledge: Any) -> RepositoryHandler | None:
        """Find a handler for the given domain using domain knowledge."""
        domain_mappings = self._get_domain_mappings(knowledge)

        for handler_name, domains in domain_mappings.items():
            if domain in domains:
                handler = self.registry.get_handler(handler_name)
                if handler:
                    logger.debug(f"Fast-path: {domain} -> {handler_name}")
                    return handler
        return None

    def get_handlers_for_url(self, url: str) -> list[RepositoryHandler]:
        """Get all handlers that can handle the URL, with domain knowledge optimization."""
        # First try fast-path using domain knowledge
        known_handler = self.get_handler_by_domain_knowledge(url)
        if known_handler:
            return [known_handler]

        # Fall back to registry-based detection
        return self.registry.get_handlers_for_url(url)

    def _get_domain_list_for_handler(self, knowledge: Any, handler_name: str) -> list[str] | None:
        """Get the appropriate domain list for a handler."""
        domain_mapping = {
            "github": knowledge.github_domains,
            "gitlab": knowledge.gitlab_domains,
            "direct_download": knowledge.direct_domains,
            "dynamic_download": knowledge.dynamic_domains,
        }
        return domain_mapping.get(handler_name)

    def _add_domain_to_knowledge(self, knowledge: Any, handler_name: str, domain: str) -> bool:
        """Add domain to appropriate knowledge list if not already present."""
        domain_list = self._get_domain_list_for_handler(knowledge, handler_name)
        if domain_list is not None and domain not in domain_list:
            domain_list.append(domain)
            return True
        return False

    async def learn_domain(self, url: str, handler_name: str) -> None:
        """Persist successful domain detection."""
        domain = self._extract_domain(url)
        if not domain:
            return

        try:
            config = self.config_manager.load_config()
            knowledge = config.global_config.domain_knowledge

            # Add to appropriate domain list
            updated = self._add_domain_to_knowledge(knowledge, handler_name, domain)

            if updated:
                self.config_manager.save()
                logger.debug(f"Learned domain: {domain} -> {handler_name}")

        except Exception as e:
            logger.error(f"Failed to learn domain {domain}: {e}")

    def _remove_domain_from_knowledge(self, knowledge: Any, handler_name: str, domain: str) -> bool:
        """Remove domain from appropriate knowledge list if present."""
        domain_list = self._get_domain_list_for_handler(knowledge, handler_name)
        if domain_list is not None and domain in domain_list:
            domain_list.remove(domain)
            return True
        return False

    async def forget_domain(self, url: str, failed_handler_name: str) -> None:
        """Remove domain from knowledge due to API failure."""
        domain = self._extract_domain(url)
        if not domain:
            return

        try:
            config = self.config_manager.load_config()
            knowledge = config.global_config.domain_knowledge

            # Remove from failed handler's domain list
            updated = self._remove_domain_from_knowledge(knowledge, failed_handler_name, domain)

            if updated:
                self.config_manager.save()
                logger.warning(f"Forgot domain: {domain} (failed as {failed_handler_name})")

        except Exception as e:
            logger.error(f"Failed to forget domain {domain}: {e}")
