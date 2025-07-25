from .scraper import BaseScraper
from playwright.async_api import Page
from typing import List, Dict

class BingScraper(BaseScraper):
    """Bing search scraper implementation with organic result filtering"""
    
    def get_search_url(self) -> str:
        """Return Bing search URL"""
        return "https://www.bing.com"
    
    def get_search_selectors(self) -> Dict[str, List[str]]:
        """Return Bing-specific selectors"""
        return {
            'search_box': [
                'input[id="sb_form_q"]',
                'input[name="q"]',
                'input.b_searchbox',
                '#sb_form_q',
                'textarea[name="q"]'
            ]
        }
    
    def get_cookie_selectors(self) -> List[str]:
        """Return Bing cookie accept button selectors"""
        return [
            'button:has-text("Accept")',
            'button:has-text("I agree")',
            'button:has-text("Accept all")',
            '#bnp_btn_accept',
            'button#bnp_btn_accept',
            'button[aria-label="Accept"]',
            '.bnp_btn_accept',
            '#onetrust-accept-btn-handler'
        ]
    
    def get_link_selector(self) -> str:
        """Bing uses H2 for search result titles"""
        return 'h2'
    
    def get_excluded_domains(self) -> List[str]:
        """Exclude Bing/Microsoft domains and video platforms"""
        bing_domains = ['bing.com', 'microsoft.com', 'msn.com', 'microsoftonline.com']
        # Get video domains from parent class and combine
        video_domains = super().get_excluded_domains()
        return bing_domains + video_domains
    
    async def inject_highlighter(self, page: Page) -> str:
        """Inject Bing H2 highlighter JavaScript with organic filtering"""
        js_code = """
        () => {
            console.log('Injecting Bing H2 highlighter with persistent numbering...');
            
            // Avoid re-injection
            if (window.bingH2HighlighterInjected) {
                console.log('Bing H2 highlighter already injected');
                return 'Already injected';
            }
            window.bingH2HighlighterInjected = true;
            
            // Global persistent numbering system
            let globalLinkCounter = 0;
            let processedLinks = new Map();
            let activeHighlights = new Map();
            let isHighlightingActive = false;
            
            // Function to generate unique identifier for an H2 element
            function getElementId(h2) {
                const text = h2.textContent.trim();
                const rect = h2.getBoundingClientRect();
                const parentText = h2.parentElement ? h2.parentElement.textContent.trim().substring(0, 50) : '';
                return `${text.substring(0, 100)}_${parentText}_${h2.tagName}`;
            }
            
            // Function to check if element is visible
            function isElementVisible(element) {
                if (!element) return false;
                
                const rect = element.getBoundingClientRect();
                
                if (rect.width === 0 || rect.height === 0) return false;
                
                const inViewport = (
                    rect.top < (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.bottom > 0 &&
                    rect.left < (window.innerWidth || document.documentElement.clientWidth) &&
                    rect.right > 0
                );
                
                if (!inViewport) return false;
                
                const style = window.getComputedStyle(element);
                if (style.display === 'none' || 
                    style.visibility === 'hidden' || 
                    style.opacity === '0') {
                    return false;
                }
                
                return true;
            }
            
            // Function to check if H2 has link
            function h2HasLink(h2) {
                return h2.querySelector('a') !== null || h2.closest('a') !== null;
            }
            
            // Function to check if H2 is organic search result (not AI summary, sponsored, or promotional)
            function isOrganicSearchResult(h2) {
                if (!h2) return false;
                
                // First, check if it's in a clear organic search result container
                const organicContainer = h2.closest('.b_algo, .b_algoheader, li.b_algo, div.b_algo, [data-priority], .b_title, .b_caption');
                if (organicContainer) {
                    console.log('Found H2 in organic container:', h2.textContent.trim().substring(0, 50));
                    return true;
                }
                
                // Check if H2 is within a result item that has organic indicators
                const resultItem = h2.closest('li, .result, [role="listitem"], .b_attribution');
                if (resultItem) {
                    // Look for organic indicators in the result item
                    const hasOrganicIndicators = resultItem.querySelector('.b_caption, .b_attribution, .b_adurl, cite');
                    if (hasOrganicIndicators) {
                        console.log('Found H2 with organic indicators:', h2.textContent.trim().substring(0, 50));
                        return true;
                    }
                }
                
                // Get the text content and surrounding elements
                const text = h2.textContent.trim().toLowerCase();
                
                // Check for AI summary indicators in text
                const aiSummaryKeywords = [
                    'ai summary', 'ai-generated', 'generated by ai', 'copilot', 'chatgpt',
                    'ai overview', 'ai response', 'generated summary', 'ai-powered',
                    'artificial intelligence', 'machine learning', 'auto-generated'
                ];
                
                // Check for sponsored/promotional indicators in text
                const sponsoredKeywords = [
                    'sponsored', 'advertisement', 'promoted', 'ad', 'ads',
                    'promotion', 'promotional', 'partner', 'affiliate'
                ];
                
                // Check text content for AI/sponsored keywords
                for (const keyword of [...aiSummaryKeywords, ...sponsoredKeywords]) {
                    if (text.includes(keyword)) {
                        console.log('Rejected H2 due to keyword:', keyword, h2.textContent.trim().substring(0, 50));
                        return false;
                    }
                }
                
                // Check parent elements for AI/sponsored classes and attributes
                let currentElement = h2;
                for (let i = 0; i < 5; i++) {
                    if (!currentElement) break;
                    
                    const className = currentElement.className ? currentElement.className.toLowerCase() : '';
                    const id = currentElement.id ? currentElement.id.toLowerCase() : '';
                    
                    // Explicitly exclude known non-organic containers
                    if (className.includes('b_ad') || 
                        className.includes('b_sponsored') ||
                        className.includes('b_promotion') ||
                        className.includes('b_ai') ||
                        className.includes('b_copilot') ||
                        className.includes('b_summary') ||
                        className.includes('sidebar') ||
                        className.includes('related') ||
                        className.includes('carousel') ||
                        id.includes('sidebar') ||
                        id.includes('related')) {
                        console.log('Rejected H2 due to non-organic container:', className, h2.textContent.trim().substring(0, 50));
                        return false;
                    }
                    
                    currentElement = currentElement.parentElement;
                }
                
                // Check the link itself
                const link = h2.querySelector('a') || h2.closest('a');
                if (link) {
                    const href = link.href;
                    
                    // Skip internal Bing links or AI-related links
                    if (href && (
                        href.includes('bing.com') ||
                        href.includes('microsoft.com') ||
                        href.includes('copilot') ||
                        href.includes('chatgpt') ||
                        href.includes('#') ||
                        href.startsWith('javascript:')
                    )) {
                        console.log('Rejected H2 due to internal link:', href, h2.textContent.trim().substring(0, 50));
                        return false;
                    }
                    
                    // Check if it's a real external link
                    if (href && (href.startsWith('http://') || href.startsWith('https://'))) {
                        console.log('Accepted H2 with external link:', href, h2.textContent.trim().substring(0, 50));
                        return true;
                    }
                }
                
                // If we reach here, it's likely organic but not in a clear container
                if (h2.querySelector('a') && h2.textContent.trim().length > 10) {
                    console.log('Accepted H2 as likely organic:', h2.textContent.trim().substring(0, 50));
                    return true;
                }
                
                console.log('Rejected H2 - no clear organic indicators:', h2.textContent.trim().substring(0, 50));
                return false;
            }
            
            // Function to create highlight for H2
            function createHighlight(h2, linkNumber) {
                const rect = h2.getBoundingClientRect();
                
                const highlight = document.createElement('div');
                highlight.className = 'bing-h2-highlight';
                highlight.setAttribute('data-link-number', linkNumber);
                
                Object.assign(highlight.style, {
                    position: 'fixed',
                    top: rect.top + 'px',
                    left: rect.left + 'px',
                    width: rect.width + 'px',
                    height: rect.height + 'px',
                    border: '3px solid #0078d4',
                    backgroundColor: 'rgba(0, 120, 212, 0.1)',
                    pointerEvents: 'none',
                    zIndex: '9999',
                    boxSizing: 'border-box'
                });
                
                const label = document.createElement('div');
                Object.assign(label.style, {
                    position: 'absolute',
                    top: '-25px',
                    left: '0',
                    backgroundColor: '#0078d4',
                    color: 'white',
                    padding: '2px 8px',
                    fontSize: '12px',
                    fontFamily: 'Arial, sans-serif',
                    borderRadius: '3px',
                    whiteSpace: 'nowrap',
                    pointerEvents: 'none',
                    fontWeight: 'bold'
                });
                label.textContent = `H2 Link ${linkNumber}`;
                
                highlight.appendChild(label);
                document.body.appendChild(highlight);
                
                return highlight;
            }
            
            // Function to update highlight position
            function updateHighlight(h2, highlight) {
                if (!highlight || !document.body.contains(highlight)) return;
                
                const rect = h2.getBoundingClientRect();
                Object.assign(highlight.style, {
                    top: rect.top + 'px',
                    left: rect.left + 'px',
                    width: rect.width + 'px',
                    height: rect.height + 'px'
                });
            }
            
            // Function to process all H2 elements with persistent numbering
            function processH2Elements() {
                if (!isHighlightingActive) return;
                
                const h2Elements = document.querySelectorAll('h2');
                const currentlyVisible = new Set();
                
                h2Elements.forEach(h2 => {
                    if (!h2HasLink(h2)) return;
                    if (!isOrganicSearchResult(h2)) return; // Skip AI summaries, sponsored content, etc.
                    
                    const elementId = getElementId(h2);
                    const isVisible = isElementVisible(h2);
                    
                    if (isVisible) {
                        currentlyVisible.add(elementId);
                        
                        if (!processedLinks.has(elementId)) {
                            globalLinkCounter++;
                            processedLinks.set(elementId, {
                                number: globalLinkCounter,
                                element: h2,
                                firstSeen: Date.now()
                            });
                            
                            console.log(`New ORGANIC H2 link discovered: #${globalLinkCounter} - "${h2.textContent.trim().substring(0, 50)}..."`);
                        }
                        
                        const linkData = processedLinks.get(elementId);
                        
                        if (!activeHighlights.has(elementId)) {
                            const highlight = createHighlight(h2, linkData.number);
                            activeHighlights.set(elementId, {
                                highlight: highlight,
                                element: h2,
                                number: linkData.number
                            });
                        } else {
                            const activeData = activeHighlights.get(elementId);
                            updateHighlight(h2, activeData.highlight);
                        }
                    }
                });
                
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
                
                console.log(`Visible: ${visibleCount} organic highlights | Total organic discovered: ${totalDiscovered} links`);
            }
            
            // Activate highlighting function
            window.activateBingH2Highlighting = () => {
                isHighlightingActive = true;
                
                processH2Elements();
                
                const observer = new MutationObserver(() => {
                    if (isHighlightingActive) {
                        setTimeout(processH2Elements, 100);
                    }
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
                
                let scrollTimeout;
                window.addEventListener('scroll', () => {
                    if (isHighlightingActive) {
                        clearTimeout(scrollTimeout);
                        scrollTimeout = setTimeout(processH2Elements, 50);
                    }
                }, { passive: true });
                
                window.addEventListener('resize', () => {
                    if (isHighlightingActive) {
                        setTimeout(processH2Elements, 100);
                    }
                }, { passive: true });
                
                console.log('Bing ORGANIC H2 highlighting activated with persistent numbering (excludes AI summaries, sponsored content)');
                return activeHighlights.size;
            };
            
            // Get info about highlighted links
            window.getHighlightedLinksInfo = () => {
                const links = [];
                
                for (const [elementId, data] of activeHighlights.entries()) {
                    const h2 = data.element;
                    if (!h2 || !document.body.contains(h2)) continue;
                    
                    let linkElement = h2.querySelector('a');
                    if (!linkElement) {
                        linkElement = h2.closest('a');
                    }
                    
                    if (linkElement) {
                        links.push({
                            number: data.number,
                            title: h2.textContent.trim(),
                            url: linkElement.href,
                            domain: new URL(linkElement.href).hostname
                        });
                    }
                }
                
                return links.sort((a, b) => a.number - b.number);
            };
            
            // Clear highlights function
            window.clearBingH2Highlights = () => {
                isHighlightingActive = false;
                
                document.querySelectorAll('.bing-h2-highlight').forEach(el => el.remove());
                activeHighlights.clear();
                
                console.log('Bing H2 highlights cleared');
            };
            
            return 'Bing H2 highlighter with persistent numbering injected successfully';
        }
        """
        
        result = await page.evaluate(js_code)
        return result