import asyncio
from playwright.async_api import async_playwright

async def inject_google_h3_highlighter(page):
    """Inject JavaScript for highlighting Google H3 search results with persistent numbering"""
    
    js_code = """
    () => {
        console.log('Injecting Google H3 highlighter with persistent numbering...');
        
        // Avoid re-injection
        if (window.googleH3HighlighterInjected) {
            console.log('Google H3 highlighter already injected');
            return 'Already injected';
        }
        window.googleH3HighlighterInjected = true;
        
        // Global persistent numbering system
        let globalLinkCounter = 0;  // This never resets
        let processedLinks = new Map();  // Track which links we've seen before
        let activeHighlights = new Map();  // Currently visible highlights
        let isHighlightingActive = false;
        
        // Function to generate unique identifier for an H3 element
        function getElementId(h3) {
            // Use text content + position in DOM as unique identifier
            const text = h3.textContent.trim();
            const rect = h3.getBoundingClientRect();
            const parentText = h3.parentElement ? h3.parentElement.textContent.trim().substring(0, 50) : '';
            
            // Create a unique ID based on content and context
            return `${text.substring(0, 100)}_${parentText}_${h3.tagName}`;
        }
        
        // Function to check if element is visible
        function isElementVisible(element) {
            if (!element) return false;
            
            const rect = element.getBoundingClientRect();
            
            // Check if element has size
            if (rect.width === 0 || rect.height === 0) return false;
            
            // Check if in viewport
            const inViewport = (
                rect.top < (window.innerHeight || document.documentElement.clientHeight) &&
                rect.bottom > 0 &&
                rect.left < (window.innerWidth || document.documentElement.clientWidth) &&
                rect.right > 0
            );
            
            if (!inViewport) return false;
            
            // Check CSS visibility
            const style = window.getComputedStyle(element);
            if (style.display === 'none' || 
                style.visibility === 'hidden' || 
                style.opacity === '0') {
                return false;
            }
            
            return true;
        }
        
        // Function to check if H3 has link
        function h3HasLink(h3) {
            return h3.querySelector('a') !== null || h3.closest('a') !== null;
        }
        
        // Function to create highlight for H3
        function createHighlight(h3, linkNumber) {
            const rect = h3.getBoundingClientRect();
            
            const highlight = document.createElement('div');
            highlight.className = 'google-h3-highlight';
            highlight.setAttribute('data-link-number', linkNumber);
            
            // Style the highlight box
            Object.assign(highlight.style, {
                position: 'fixed',
                top: rect.top + 'px',
                left: rect.left + 'px',
                width: rect.width + 'px',
                height: rect.height + 'px',
                border: '3px solid #ff0000',
                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                pointerEvents: 'none',
                zIndex: '9999',
                boxSizing: 'border-box'
            });
            
            // Add label with persistent number
            const label = document.createElement('div');
            Object.assign(label.style, {
                position: 'absolute',
                top: '-25px',
                left: '0',
                backgroundColor: '#ff0000',
                color: 'white',
                padding: '2px 8px',
                fontSize: '12px',
                fontFamily: 'Arial, sans-serif',
                borderRadius: '3px',
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
                fontWeight: 'bold'
            });
            label.textContent = `H3 Link ${linkNumber}`;
            
            highlight.appendChild(label);
            document.body.appendChild(highlight);
            
            return highlight;
        }
        
        // Function to update highlight position
        function updateHighlight(h3, highlight) {
            if (!highlight || !document.body.contains(highlight)) return;
            
            const rect = h3.getBoundingClientRect();
            Object.assign(highlight.style, {
                top: rect.top + 'px',
                left: rect.left + 'px',
                width: rect.width + 'px',
                height: rect.height + 'px'
            });
        }
        
        // Function to process all H3 elements with persistent numbering
        function processH3Elements() {
            if (!isHighlightingActive) return;
            
            const h3Elements = document.querySelectorAll('h3');
            const currentlyVisible = new Set();
            
            h3Elements.forEach(h3 => {
                if (!h3HasLink(h3)) return;
                
                const elementId = getElementId(h3);
                const isVisible = isElementVisible(h3);
                
                if (isVisible) {
                    currentlyVisible.add(elementId);
                    
                    // Check if this is a new link we haven't seen before
                    if (!processedLinks.has(elementId)) {
                        // New link - assign next number
                        globalLinkCounter++;
                        processedLinks.set(elementId, {
                            number: globalLinkCounter,
                            element: h3,
                            firstSeen: Date.now()
                        });
                        
                        console.log(`New H3 link discovered: #${globalLinkCounter} - "${h3.textContent.trim().substring(0, 50)}..."`);
                    }
                    
                    const linkData = processedLinks.get(elementId);
                    
                    // Create or update highlight
                    if (!activeHighlights.has(elementId)) {
                        const highlight = createHighlight(h3, linkData.number);
                        activeHighlights.set(elementId, {
                            highlight: highlight,
                            element: h3,
                            number: linkData.number
                        });
                    } else {
                        // Update existing highlight position
                        const activeData = activeHighlights.get(elementId);
                        updateHighlight(h3, activeData.highlight);
                    }
                }
            });
            
            // Remove highlights for elements no longer visible
            for (const [elementId, activeData] of activeHighlights.entries()) {
                if (!currentlyVisible.has(elementId)) {
                    if (activeData.highlight && document.body.contains(activeData.highlight)) {
                        activeData.highlight.remove();
                    }
                    activeHighlights.delete(elementId);
                }
            }
            
            const visibleCount = activeHighlights.size;
            const totalDiscovered = processedLinks.size;
            
            console.log(`Visible: ${visibleCount} highlights | Total discovered: ${totalDiscovered} links`);
        }
        
        // Activate highlighting function
        window.activateGoogleH3Highlighting = () => {
            isHighlightingActive = true;
            
            // Process immediately
            processH3Elements();
            
            // Set up observers for dynamic content
            const observer = new MutationObserver(() => {
                if (isHighlightingActive) {
                    setTimeout(processH3Elements, 100);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // Update on scroll with throttling
            let scrollTimeout;
            window.addEventListener('scroll', () => {
                if (isHighlightingActive) {
                    clearTimeout(scrollTimeout);
                    scrollTimeout = setTimeout(processH3Elements, 50);
                }
            }, { passive: true });
            
            // Update on resize
            window.addEventListener('resize', () => {
                if (isHighlightingActive) {
                    setTimeout(processH3Elements, 100);
                }
            }, { passive: true });
            
            console.log('Google H3 highlighting activated with persistent numbering');
            return activeHighlights.size;
        };
        
        // Get info about highlighted links
        window.getHighlightedLinksInfo = () => {
            const links = [];
            
            for (const [elementId, data] of activeHighlights.entries()) {
                const h3 = data.element;
                if (!h3 || !document.body.contains(h3)) continue;
                
                // Find the actual link
                let linkElement = h3.querySelector('a');
                if (!linkElement) {
                    linkElement = h3.closest('a');
                }
                
                if (linkElement) {
                    links.push({
                        number: data.number,
                        title: h3.textContent.trim(),
                        url: linkElement.href,
                        domain: new URL(linkElement.href).hostname
                    });
                }
            }
            
            return links.sort((a, b) => a.number - b.number);
        };
        
        // Clear highlights function
        window.clearGoogleH3Highlights = () => {
            isHighlightingActive = false;
            
            // Remove all visible highlights
            document.querySelectorAll('.google-h3-highlight').forEach(el => el.remove());
            activeHighlights.clear();
            
            console.log('Google H3 highlights cleared');
        };
        
        return 'Google H3 highlighter with persistent numbering injected successfully';
    }
    """
    
    result = await page.evaluate(js_code)
    return result

async def accept_cookies(page):
    """Accept Google cookies if the dialog appears"""
    try:
        # Common cookie accept button selectors
        cookie_selectors = [
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            'button:has-text("Accept")',
            '#L2AGLb',  # Common Google cookie button ID
            'button#L2AGLb',
            '[aria-label="Accept all"]',
            'button[jsname="b3VHJd"]'
        ]
        
        # Try each selector
        for selector in cookie_selectors:
            try:
                button = page.locator(selector).first
                if await button.count() > 0:
                    await button.click()
                    print("✅ Cookies accepted")
                    await page.wait_for_timeout(1000)
                    return True
            except:
                continue
                
        print("ℹ️  No cookie dialog found")
        return False
        
    except Exception as e:
        print(f"⚠️  Cookie handling: {str(e)}")
        return False

async def search_google(page, query):
    """Perform a Google search"""
    try:
        # Wait for search box to be ready
        await page.wait_for_selector('textarea[name="q"], input[name="q"]', timeout=5000)
        
        # Find and fill the search box
        search_box = page.locator('textarea[name="q"], input[name="q"]').first
        await search_box.click()
        await search_box.fill(query)
        
        # Press Enter to search
        await search_box.press("Enter")
        
        # Wait for results to load
        await page.wait_for_selector('h3', timeout=10000)
        await page.wait_for_timeout(2000)  # Extra time for all results
        
        print(f"✅ Search completed")
        return True
        
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return False

async def collect_highlighted_links(page, max_links=4):
    """Scroll and collect highlighted links"""
    collected_links = []
    collected_urls = set()
    scroll_attempts = 0
    max_scroll_attempts = 20
    
    print(f"\n📌 Collecting links...")
    
    while len(collected_links) < max_links and scroll_attempts < max_scroll_attempts:
        # Get current highlighted links
        current_links = await page.evaluate("window.getHighlightedLinksInfo()")
        
        # Add new links to collection
        for link in current_links:
            if link['url'] not in collected_urls and len(collected_links) < max_links:
                # Skip Google's own links
                if 'google.com' in link['domain']:
                    continue
                    
                collected_links.append(link)
                collected_urls.add(link['url'])
                
                # Show progress
                progress = '■' * len(collected_links) + '□' * (max_links - len(collected_links))
                print(f"   [{progress}] {len(collected_links)}/{max_links} links collected")
        
        # If we have enough links, stop
        if len(collected_links) >= max_links:
            break
            
        # Scroll down
        await page.evaluate("window.scrollBy(0, 400)")
        await page.wait_for_timeout(1500)
        
        scroll_attempts += 1
        
        # Check if at bottom
        at_bottom = await page.evaluate("""
            () => {
                return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;
            }
        """)
        
        if at_bottom:
            print("   ℹ️  Reached end of results")
            break
    
    return collected_links

async def main():
    print("\n" + "="*50)
    print("🔍 GOOGLE SEARCH LINK COLLECTOR")
    print("="*50 + "\n")
    
    # Get search query - keep asking until we get one
    query = ""
    while not query.strip():
        query = input("Enter search query: ").strip()
        if not query:
            print("⚠️  Please enter a search query!\n")
    
    print(f"\n🔄 Searching for: '{query}'...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
                '--disable-dev-shm-usage'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to Google
            print("📍 Opening Google...")
            await page.goto("https://www.google.com", wait_until='networkidle')
            await page.wait_for_timeout(1000)
            
            # Accept cookies
            await accept_cookies(page)
            
            # Perform search
            if not await search_google(page, query):
                print("❌ Search failed. Exiting...")
                await browser.close()
                return
            
            # Inject and activate highlighter
            await inject_google_h3_highlighter(page)
            await page.wait_for_timeout(500)
            
            # Activate highlighting
            await page.evaluate("window.activateGoogleH3Highlighting()")
            print("✅ Link highlighter activated")
            await page.wait_for_timeout(1000)
            
            # Collect links
            links = await collect_highlighted_links(page, max_links=4)
            
            # Display results
            print("\n" + "="*50)
            print("📊 SEARCH RESULTS:")
            print("="*50)
            
            if links:
                for i, link in enumerate(links, 1):
                    print(f"\n{i}. {link['title'][:70]}{'...' if len(link['title']) > 70 else ''}")
                    print(f"   🔗 {link['url']}")
                    print(f"   📍 {link['domain']}")
            else:
                print("\n❌ No links found. Try a different query.")
            
            print("\n" + "="*50)
            print("✅ Done! Browser will close in 5 seconds...")
            print("="*50)
            
            # Keep browser open briefly to see results
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"\n❌ Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")