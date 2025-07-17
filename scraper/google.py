from .scraper import BaseScraper
from playwright.async_api import Page
from typing import List, Dict

class GoogleScraper(BaseScraper):
    """Google search scraper implementation"""
    
    def get_search_url(self) -> str:
        """Return Google search URL"""
        return "https://www.google.com"
    
    def get_search_selectors(self) -> Dict[str, List[str]]:
        """Return Google-specific selectors"""
        return {
            'search_box': [
                'textarea[name="q"]',
                'input[name="q"]',
                'input[type="text"][name="q"]',
                'textarea.gLFyf',
                'input.gLFyf'
            ]
        }
    
    def get_cookie_selectors(self) -> List[str]:
        """Return Google cookie accept button selectors"""
        return [
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            'button:has-text("Accept")',
            '#L2AGLb',
            'button#L2AGLb',
            '[aria-label="Accept all"]',
            'button[jsname="b3VHJd"]'
        ]
    
    def get_link_selector(self) -> str:
        """Google uses H3 for search result titles"""
        return 'h3'
    
    def get_excluded_domains(self) -> List[str]:
        """Exclude Google's own domains and video platforms"""
        google_domains = ['google.com', 'googleapis.com', 'googleusercontent.com']
        # Get video domains from parent class and combine
        video_domains = super().get_excluded_domains()
        return google_domains + video_domains
    
    async def inject_highlighter(self, page: Page) -> str:
        """Inject Google H3 highlighter JavaScript"""
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
            let globalLinkCounter = 0;
            let processedLinks = new Map();
            let activeHighlights = new Map();
            let isHighlightingActive = false;
            
            // Function to generate unique identifier for an H3 element
            function getElementId(h3) {
                const text = h3.textContent.trim();
                const rect = h3.getBoundingClientRect();
                const parentText = h3.parentElement ? h3.parentElement.textContent.trim().substring(0, 50) : '';
                return `${text.substring(0, 100)}_${parentText}_${h3.tagName}`;
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
                        
                        if (!processedLinks.has(elementId)) {
                            globalLinkCounter++;
                            processedLinks.set(elementId, {
                                number: globalLinkCounter,
                                element: h3,
                                firstSeen: Date.now()
                            });
                            
                            console.log(`New H3 link discovered: #${globalLinkCounter} - "${h3.textContent.trim().substring(0, 50)}..."`);
                        }
                        
                        const linkData = processedLinks.get(elementId);
                        
                        if (!activeHighlights.has(elementId)) {
                            const highlight = createHighlight(h3, linkData.number);
                            activeHighlights.set(elementId, {
                                highlight: highlight,
                                element: h3,
                                number: linkData.number
                            });
                        } else {
                            const activeData = activeHighlights.get(elementId);
                            updateHighlight(h3, activeData.highlight);
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
                
                console.log(`Visible: ${visibleCount} highlights | Total discovered: ${totalDiscovered} links`);
            }
            
            // Activate highlighting function
            window.activateGoogleH3Highlighting = () => {
                isHighlightingActive = true;
                
                processH3Elements();
                
                const observer = new MutationObserver(() => {
                    if (isHighlightingActive) {
                        setTimeout(processH3Elements, 100);
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
                        scrollTimeout = setTimeout(processH3Elements, 50);
                    }
                }, { passive: true });
                
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
                
                document.querySelectorAll('.google-h3-highlight').forEach(el => el.remove());
                activeHighlights.clear();
                
                console.log('Google H3 highlights cleared');
            };
            
            return 'Google H3 highlighter with persistent numbering injected successfully';
        }
        """
        
        result = await page.evaluate(js_code)
        return result