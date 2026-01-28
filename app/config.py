"""
Application configuration settings.

This module contains configurable parameters for the analytics system,
including performance optimizations and default values.
"""
import os
from typing import Optional, List, Dict


# Analytics Performance Settings
ANALYTICS_DEFAULT_LOOKBACK_DAYS = int(os.getenv("ANALYTICS_DEFAULT_LOOKBACK_DAYS", "180"))
"""
Default number of days to look back for analytics calculations.

Limiting the lookback window improves performance as data grows.
- 180 days (6 months) provides good historical context while maintaining performance
- Can be overridden via environment variable ANALYTICS_DEFAULT_LOOKBACK_DAYS
- Individual queries can still request custom date ranges
"""

# Redis Cache Settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
"""Redis connection URL for caching."""

REDIS_CACHE_TTL_DASHBOARD = int(os.getenv("REDIS_CACHE_TTL_DASHBOARD", "900"))
"""Dashboard cache TTL in seconds (default: 15 minutes)."""

REDIS_CACHE_TTL_TRENDS = int(os.getenv("REDIS_CACHE_TTL_TRENDS", "3600"))
"""Trends cache TTL in seconds (default: 1 hour)."""

REDIS_CACHE_TTL_BATCH = int(os.getenv("REDIS_CACHE_TTL_BATCH", "86400"))
"""Batch analytics cache TTL in seconds (default: 24 hours)."""

# Database Settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
"""Database connection pool size."""

DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
"""Maximum overflow connections beyond pool size."""

# LLM API Settings (for Tales data collection)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
"""OpenAI API key for LLM-powered features."""

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
"""Anthropic API key for LLM-powered features."""

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
"""Google Gemini API key for LLM-powered features."""

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
"""Perplexity API key for AI-powered research features."""

DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
"""Default LLM provider: 'openai', 'anthropic', or 'gemini'."""

# Upload directory for generated files
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
"""Directory for uploaded and generated files."""


# Create a settings object for configuration access
class _Settings:
    """Settings object for LLM configuration"""
    def __init__(self):
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
        self.GEMINI_API_KEY = GEMINI_API_KEY
        self.PERPLEXITY_API_KEY = PERPLEXITY_API_KEY
        self.DEFAULT_LLM_PROVIDER = DEFAULT_LLM_PROVIDER
        self.UPLOAD_DIR = UPLOAD_DIR


settings = _Settings()


# Tenant Product Access Configuration
class TenantConfig:
    """Configuration for tenant-specific product access"""

    # All tenants have access to Tales
    TENANT_PRODUCTS: Dict[str, List[str]] = {
        "default": ["tales"]
    }

    @staticmethod
    def get_tenant_products(tenant_name: str) -> List[str]:
        """
        Get list of products enabled for a tenant

        Args:
            tenant_name: The name of the tenant

        Returns:
            List of product IDs that the tenant can access
        """
        return ["tales"]

    @staticmethod
    def is_product_enabled_for_tenant(tenant_name: str, product: str) -> bool:
        """
        Check if a product is enabled for a specific tenant

        Args:
            tenant_name: The name of the tenant
            product: The product ID to check

        Returns:
            True if the tenant has access to the product, False otherwise
        """
        return product == "tales"
