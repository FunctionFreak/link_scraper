import asyncio
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page, BrowserContext
from typing import List, Dict, Optional, Any
from datetime import datetime

class BaseScraper(ABC):
    """Base scraper class with common functionality for search engines"""
    
    def __init__(self, query: str, num_links: int = 4, debug: bool = False):
        self.query = query
        self.num_links = num_links
        self.debug = debug
        self.browser = None
        self.context = None
        self.page = None
        self.results = []
        self.start_time = None
        
    @abstractmethod
    def get_search_url(self) -> str:
        """Return the search engine URL"""
        pass
    
    @abstractmethod
    def get_search_selectors(self) -> Dict[str, List[str]]:
        """Return search engine specific selectors"""
        pass
    
    @abstractmethod
    def get_cookie_selectors(self) -> List[str]:
        """Return cookie accept button selectors"""
        pass
    
    @abstractmethod
    async def inject_highlighter(self, page: Page) -> str:
        """Inject the link highlighter JavaScript"""
        pass
    
    @abstractmethod
    def get_link_selector(self) -> str:
        """Return the selector for links (h2, h3, etc)"""
        pass
    
    async def setup_browser(self, playwright):
        """Initialize browser with common settings"""
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--start-maximized'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            bypass_csp=True,
            ignore_https_errors=True
        )
        
        self.page = await self.context.new_page()
        
    async def accept_cookies(self) -> bool:
        """Accept cookies if dialog appears"""
        try:
            await self.page.wait_for_timeout(1000)
            
            for selector in self.get_cookie_selectors():
                try:
                    button = self.page.locator(selector).first
                    if await button.count() > 0 and await button.is_visible():
                        await button.click()
                        print(f"[{self.__class__.__name__}] ✅ Cookies accepted")
                        await self.page.wait_for_timeout(1000)
                        return True
                except:
                    continue
                    
            print(f"[{self.__class__.__name__}] ℹ️  No cookie dialog found")
            return False
            
        except Exception as e:
            print(f"[{self.__class__.__name__}] ⚠️  Cookie handling: {str(e)}")
            return False
    
    async def perform_search(self) -> bool:
        """Perform the search"""
        try:
            await self.page.wait_for_timeout(2000)
            
            search_selectors = self.get_search_selectors()
            search_box = None
            
            for selector in search_selectors['search_box']:
                try:
                    if await self.page.locator(selector).count() > 0:
                        search_box = self.page.locator(selector).first
                        print(f"[{self.__class__.__name__}] ✅ Found search box: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                print(f"[{self.__class__.__name__}] ❌ Could not find search box")
                return False
                
            await search_box.click()
            await self.page.wait_for_timeout(500)
            await search_box.fill(self.query)
            await self.page.wait_for_timeout(500)
            await search_box.press("Enter")
            
            # Wait for results
            await self.page.wait_for_selector(self.get_link_selector(), timeout=15000)
            await self.page.wait_for_timeout(2000)
            
            print(f"[{self.__class__.__name__}] ✅ Search completed")
            return True
            
        except Exception as e:
            print(f"[{self.__class__.__name__}] ❌ Search error: {str(e)}")
            return False
    
    async def collect_links(self) -> List[Dict[str, Any]]:
        """Scroll and collect highlighted links"""
        collected_links = []
        collected_urls = set()
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        print(f"\n[{self.__class__.__name__}] 📌 Collecting links...")
        
        while len(collected_links) < self.num_links and scroll_attempts < max_scroll_attempts:
            # Get current highlighted links
            current_links = await self.page.evaluate("window.getHighlightedLinksInfo()")
            
            # Add new links to collection
            for link in current_links:
                if link['url'] not in collected_urls and len(collected_links) < self.num_links:
                    # Skip internal links
                    if any(domain in link['domain'] for domain in self.get_excluded_domains()):
                        continue
                        
                    collected_links.append(link)
                    collected_urls.add(link['url'])
                    
                    # Show progress
                    progress = '■' * len(collected_links) + '□' * (self.num_links - len(collected_links))
                    print(f"   [{progress}] {len(collected_links)}/{self.num_links} links collected")
            
            if len(collected_links) >= self.num_links:
                break
                
            # Scroll down
            await self.page.evaluate("window.scrollBy(0, 400)")
            await self.page.wait_for_timeout(1500)
            
            scroll_attempts += 1
            
            # Check if at bottom
            at_bottom = await self.page.evaluate("""
                () => {
                    return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;
                }
            """)
            
            if at_bottom:
                print(f"   [{self.__class__.__name__}] ℹ️  Reached end of results")
                break
        
        if len(collected_links) < self.num_links:
            print(f"   [{self.__class__.__name__}] ⚠️  Only found {len(collected_links)} links")
        
        return collected_links
    
    def get_excluded_domains(self) -> List[str]:
        """Return list of domains to exclude from results"""
        return []
    
    async def run(self) -> Dict[str, Any]:
        """Main execution method"""
        self.start_time = datetime.now()
        
        async with async_playwright() as playwright:
            try:
                # Setup browser
                await self.setup_browser(playwright)
                
                # Navigate to search engine
                print(f"[{self.__class__.__name__}] 📍 Opening {self.get_search_url()}...")
                await self.page.goto(self.get_search_url(), wait_until='domcontentloaded')
                await self.page.wait_for_timeout(3000)
                
                # Accept cookies
                await self.accept_cookies()
                
                # Perform search
                if not await self.perform_search():
                    return {
                        'source': self.__class__.__name__.replace('Scraper', ''),
                        'links': [],
                        'status': 'failed',
                        'error': 'Search failed',
                        'duration': (datetime.now() - self.start_time).total_seconds()
                    }
                
                # Inject and activate highlighter
                await self.inject_highlighter(self.page)
                await self.page.wait_for_timeout(500)
                
                # Activate highlighting
                await self.page.evaluate(f"window.activate{self.get_search_url().split('.')[1].title()}{self.get_link_selector().upper()}Highlighting()")
                print(f"[{self.__class__.__name__}] ✅ Link highlighter activated")
                await self.page.wait_for_timeout(1000)
                
                # Collect links
                links = await self.collect_links()
                
                # Keep browser open if debug mode
                if self.debug:
                    print(f"\n[{self.__class__.__name__}] 🔍 Debug mode: Browser will stay open...")
                    await asyncio.sleep(3600)  # Keep open for 1 hour or until closed
                else:
                    await self.page.wait_for_timeout(2000)
                
                return {
                    'source': self.__class__.__name__.replace('Scraper', ''),
                    'links': links,
                    'status': 'success',
                    'error': None,
                    'duration': (datetime.now() - self.start_time).total_seconds()
                }
                
            except Exception as e:
                print(f"[{self.__class__.__name__}] ❌ Error: {str(e)}")
                return {
                    'source': self.__class__.__name__.replace('Scraper', ''),
                    'links': [],
                    'status': 'failed',
                    'error': str(e),
                    'duration': (datetime.now() - self.start_time).total_seconds()
                }
                
            finally:
                if not self.debug and self.browser:
                    await self.browser.close()