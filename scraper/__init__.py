"""
Scraper package for parallel Google and Bing search result collection
"""

from .scraper import BaseScraper, run_search
from .google import GoogleScraper
from .bing import BingScraper

__all__ = ['BaseScraper', 'GoogleScraper', 'BingScraper', 'run_search']