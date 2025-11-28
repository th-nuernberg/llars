"""
Crawler Modules Package

Re-exports all crawler components for easy importing.
"""

from .crawler_core import WebCrawler
from .crawler_service import CrawlerService, crawler_service

__all__ = ['WebCrawler', 'CrawlerService', 'crawler_service']
