import asyncio
import sys
import json
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
            headless=(not self.debug),  # Visible only in debug mode
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
                        # Silent cookie acceptance - no print
                        await self.page.wait_for_timeout(1000)
                        return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
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
                        break
                except:
                    continue
            
            if not search_box:
                return False
                
            await search_box.click()
            await self.page.wait_for_timeout(500)
            await search_box.fill(self.query)
            await self.page.wait_for_timeout(500)
            await search_box.press("Enter")
            
            # Wait for results with better selectors for each engine
            await self.page.wait_for_timeout(3000)  # Give more time for results to load
            
            # Check if we have search results based on engine type
            if "Bing" in self.__class__.__name__:
                # For Bing, wait for the search results container
                try:
                    await self.page.wait_for_selector('#b_results, .b_algo, ol#b_results li', timeout=10000)
                except:
                    pass
            else:
                # For Google, wait for search results
                try:
                    await self.page.wait_for_selector('#search, .g, #rso', timeout=10000)
                except:
                    pass
            
            await self.page.wait_for_timeout(2000)
            
            return True
            
        except Exception as e:
            return False
    
    async def collect_links(self) -> List[Dict[str, Any]]:
        """Scroll and collect highlighted links"""
        collected_links = []
        collected_urls = set()
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while len(collected_links) < self.num_links and scroll_attempts < max_scroll_attempts:
            # Get current highlighted links
            try:
                current_links = await self.page.evaluate("window.getHighlightedLinksInfo()")
            except Exception as e:
                current_links = []
            
            # Add new links to collection
            for link in current_links:
                if link['url'] not in collected_urls and len(collected_links) < self.num_links:
                    # Skip internal links
                    if any(domain in link['domain'] for domain in self.get_excluded_domains()):
                        continue
                        
                    collected_links.append(link)
                    collected_urls.add(link['url'])
                    
                    # Show progress only
                    progress = '■' * len(collected_links) + '□' * (self.num_links - len(collected_links))
                    print(f"\r   [{self.__class__.__name__}] [{progress}] {len(collected_links)}/{self.num_links} links collected", end='', flush=True)
            
            if len(collected_links) >= self.num_links:
                break
                
            # Scroll down
            try:
                await self.page.evaluate("window.scrollBy(0, 400)")
                await self.page.wait_for_timeout(1500)
            except Exception as e:
                break
            
            scroll_attempts += 1
            
            # Check if at bottom
            try:
                at_bottom = await self.page.evaluate("""
                    () => {
                        return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;
                    }
                """)
            except:
                at_bottom = False
            
            if at_bottom:
                break
        
        # Add newline after progress bar
        print()  # Move to next line after progress bar

        return collected_links
    
    def get_excluded_domains(self) -> List[str]:
        """Return list of domains to exclude from results"""
        # Common video platforms to exclude
        return [
            'youtube.com', 'youtu.be', 'm.youtube.com',
            'vimeo.com', 'dailymotion.com', 'twitch.tv',
            'tiktok.com', 'instagram.com/reel', 'facebook.com/watch'
        ]
    
    async def run(self) -> Dict[str, Any]:
        """Main execution method"""
        self.start_time = datetime.now()
        
        # Don't use 'async with' to keep browser alive in debug mode
        playwright = await async_playwright().start()
        
        try:
            # Setup browser
            await self.setup_browser(playwright)
            
            # Navigate to search engine
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
            engine_name = self.__class__.__name__.replace('Scraper', '')  # 'Google' or 'Bing'
            await self.page.evaluate(f"window.activate{engine_name}{self.get_link_selector().upper()}Highlighting()")
            await self.page.wait_for_timeout(1000)
            
            # Collect links
            links = await self.collect_links()
            
            # Prepare results
            result = {
                'source': self.__class__.__name__.replace('Scraper', ''),
                'links': links,
                'status': 'success',
                'error': None,
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
            
            # In debug mode, keep browser open
            if not self.debug:
                await self.page.wait_for_timeout(2000)
            
            return result
            
        except Exception as e:
            return {
                'source': self.__class__.__name__.replace('Scraper', ''),
                'links': [],
                'status': 'failed',
                'error': str(e),
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
            
        finally:
            # Simple: if debug mode, don't close browser. Otherwise, close it.
            if not self.debug:
                if self.browser:
                    await self.browser.close()
                await playwright.stop()
            # Don't stop playwright in debug mode


async def show_loading():
    """Show loading animation until scraping starts"""
    import time
    
    loading_chars = ['.', '..', '...', '....', '.....']
    
    # Show loading animation for a few cycles
    for _ in range(15):  # Run for about 3 seconds
        for char in loading_chars:
            print(f"\rLoading{char}", end='', flush=True)
            await asyncio.sleep(0.2)
    
    print()  # New line after loading


def format_results(results: List[Dict[str, Any]], output_mode: str = "terminal") -> None:
    """Format and display the collected results with proper grouping"""
    if output_mode == "terminal":
        print("\n" + "="*70)
        print("📊 SEARCH RESULTS")
        print("="*70)
    
        # Find Google and Bing results
        google_links = []
        bing_links = []
        google_status = "NOT FOUND"
        bing_status = "NOT FOUND"
        
        for result in results:
            if result['source'] == 'Google':
                google_links = result['links'] if result['status'] == 'success' else []
                google_status = result['status']
            elif result['source'] == 'Bing':
                bing_links = result['links'] if result['status'] == 'success' else []
                bing_status = result['status']
        
        # Remove duplicates: filter out Bing links that have same URL as Google links
        google_urls = {link['url'] for link in google_links}
        original_bing_count = len(bing_links)
        bing_links = [link for link in bing_links if link['url'] not in google_urls]
        removed_duplicates = original_bing_count - len(bing_links)
        
        if removed_duplicates > 0:
            print(f"🔄 Removed {removed_duplicates} duplicate(s) from Bing results (already found in Google)")
        
        # GOOGLE RESULTS FIRST
        print(f"\n🔍 [GOOGLE] - {google_status.upper()} ({len(google_links)} links)")
        print("-" * 70)
        
        if google_links:
            for i, link in enumerate(google_links, 1):
                print(f"\n{i}. {link['title']}")
                print(f"   🔗 {link['url']}")
                print(f"   📍 {link['domain']}")
        else:
            print("\n❌ No Google links collected")
            if google_status == 'failed':
                error_msg = next((r.get('error', 'Unknown error') for r in results if r['source'] == 'Google'), 'Unknown error')
                print(f"   Error: {error_msg}")
        
        # BING RESULTS SECOND
        print(f"\n🔍 [BING] - {bing_status.upper()} ({len(bing_links)} links)")
        print("-" * 70)
        
        if bing_links:
            for i, link in enumerate(bing_links, 1):
                print(f"\n{i}. {link['title']}")
                print(f"   🔗 {link['url']}")
                print(f"   📍 {link['domain']}")
        else:
            print("\n❌ No Bing links collected")
            if bing_status == 'failed':
                error_msg = next((r.get('error', 'Unknown error') for r in results if r['source'] == 'Bing'), 'Unknown error')
                print(f"   Error: {error_msg}")
        
        print("\n" + "="*70)
    
    elif output_mode == "json":
        # Find Google and Bing results
        google_links = []
        bing_links = []
        
        for result in results:
            if result['source'] == 'Google':
                google_links = result['links'] if result['status'] == 'success' else []
            elif result['source'] == 'Bing':
                bing_links = result['links'] if result['status'] == 'success' else []
        
        # Remove duplicates: filter out Bing links that have same URL as Google links
        google_urls = {link['url'] for link in google_links}
        bing_links = [link for link in bing_links if link['url'] not in google_urls]
        
        # Prepare JSON data
        json_data = {
            "search_results": {
                "google": {
                    "count": len(google_links),
                    "links": google_links
                },
                "bing": {
                    "count": len(bing_links),
                    "links": bing_links
                }
            },
            "total_links": len(google_links) + len(bing_links),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to JSON file
        filename = f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Results saved to {filename}")
        print(f"📊 Total links: {json_data['total_links']} (Google: {len(google_links)}, Bing: {len(bing_links)})")


async def run_scrapers(query: str, num_links: int, debug: bool) -> List[Dict[str, Any]]:
    """Run both scrapers in parallel"""
    from .google import GoogleScraper
    from .bing import BingScraper
    
    # Create scraper instances
    google_scraper = GoogleScraper(
        query=query,
        num_links=num_links,
        debug=debug
    )
    
    bing_scraper = BingScraper(
        query=query,
        num_links=num_links,
        debug=debug
    )
    
    # Run scrapers in parallel
    start_time = datetime.now()
    
    try:
        # Run both scrapers simultaneously and wait for both to complete
        results = await asyncio.gather(
            google_scraper.run(),
            bing_scraper.run(),
            return_exceptions=True
        )
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                source = ['Google', 'Bing'][i]
                processed_results.append({
                    'source': source,
                    'links': [],
                    'status': 'failed',
                    'error': str(result),
                    'duration': (datetime.now() - start_time).total_seconds()
                })
            else:
                processed_results.append(result)
        
        # Ensure we have both results
        if len(processed_results) < 2:
            # Add missing results
            sources = [r.get('source', '') for r in processed_results]
            for source in ['Google', 'Bing']:
                if source not in sources:
                    processed_results.append({
                        'source': source,
                        'links': [],
                        'status': 'failed',
                        'error': 'Scraper failed to start',
                        'duration': (datetime.now() - start_time).total_seconds()
                    })
        
        return processed_results
        
    except Exception as e:
        # Return error results for both
        return [
            {
                'source': 'Google',
                'links': [],
                'status': 'failed',
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            },
            {
                'source': 'Bing',
                'links': [],
                'status': 'failed',
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
        ]


async def run_search(query: str, num_links: int, debug: bool, result: str = "terminal"):
    """Main execution function"""
    await show_loading()
    
    try:
        # Run scrapers and get results
        results = await run_scrapers(query, num_links, debug)
        
        # Display results immediately after both scrapers complete
        format_results(results, result)
        
        # Handle debug mode
        if debug:
            try:
                # Keep the program running indefinitely in debug mode
                while True:
                    await asyncio.sleep(10)  # Check every 10 seconds
            except KeyboardInterrupt:
                pass
        
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sys.exit(1)