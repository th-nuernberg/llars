# web_crawler.py
"""
Intelligent Website Crawler for RAG Collections.

This module re-exports components from the modules package for backwards compatibility.
The actual implementation is split into:
- modules/crawler_core.py: WebCrawler class with core crawling logic
- modules/crawler_service.py: CrawlerService for managing crawl jobs

Features:
- Respects robots.txt
- Rate limiting to be friendly
- Extracts clean text from HTML
- Follows internal links (same domain)
- Configurable depth and max pages
- Sitemap.xml support
"""

# Re-export for backwards compatibility
from .modules import WebCrawler, CrawlerService, crawler_service

__all__ = ['WebCrawler', 'CrawlerService', 'crawler_service']
