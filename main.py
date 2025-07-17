import asyncio
import sys
from datetime import datetime
from typing import List, Dict, Any
from scraper import GoogleScraper, BingScraper

def print_banner():
    """Print application banner"""
    print("\n" + "="*70)
    print("🔍 PARALLEL SEARCH SCRAPER - Google & Bing")
    print("="*70)
    print("✅ Collects organic search results from both engines simultaneously")
    print("❌ Filters out: AI summaries, sponsored content, ads")
    print("="*70 + "\n")

def get_user_inputs() -> Dict[str, Any]:
    """Get user inputs for search configuration"""
    # Get search query
    query = ""
    while not query.strip():
        query = input("Enter search query: ").strip()
        if not query:
            print("⚠️  Please enter a search query!\n")
    
    # Get number of links
    while True:
        try:
            num_links_input = input("\nNumber of links to collect per engine (default: 4): ").strip()
            if not num_links_input:
                num_links = 4
                break
            num_links = int(num_links_input)
            if num_links < 1:
                print("⚠️  Please enter a number greater than 0")
                continue
            break
        except ValueError:
            print("⚠️  Please enter a valid number")
    
    # Get debug mode
    debug_input = input("\nKeep browsers open after completion? (y/N): ").strip().lower()
    debug = debug_input in ['y', 'yes', 'true', '1']
    
    return {
        'query': query,
        'num_links': num_links,
        'debug': debug
    }

def format_results(results: List[Dict[str, Any]]) -> None:
    """Format and display the collected results with proper grouping"""
    print("\n" + "="*70)
    print("📊 SEARCH RESULTS SUMMARY")
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
    
    # Display summary
    print(f"\n🔍 Google Search: {'✅ ' + google_status.upper() if google_status == 'success' else '❌ ' + google_status.upper()}")
    print(f"   Links found: {len(google_links)}")
    
    print(f"\n🔍 Bing Search: {'✅ ' + bing_status.upper() if bing_status == 'success' else '❌ ' + bing_status.upper()}")
    print(f"   Links found: {len(bing_links)}")
    
    # Display detailed results
    print("\n" + "="*70)
    print("📋 DETAILED RESULTS")
    print("="*70)
    
    # Google Results - Always show this section first
    print(f"\n[GOOGLE] Results:")
    print("-" * 50)
    
    if google_links:
        for i, link in enumerate(google_links, 1):
            print(f"\n{i}. {link['title'][:70]}{'...' if len(link['title']) > 70 else ''}")
            print(f"   🔗 {link['url']}")
            print(f"   📍 {link['domain']}")
    else:
        print("\n❌ No Google links collected")
    
    # Bing Results - Always show this section second
    print(f"\n[BING] Results:")
    print("-" * 50)
    
    if bing_links:
        for i, link in enumerate(bing_links, 1):
            print(f"\n{i}. {link['title'][:70]}{'...' if len(link['title']) > 70 else ''}")
            print(f"   🔗 {link['url']}")
            print(f"   📍 {link['domain']}")
    else:
        print("\n❌ No Bing links collected")
    
    print("\n" + "="*70)

async def run_scrapers(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run both scrapers in parallel"""
    # Create scraper instances
    google_scraper = GoogleScraper(
        query=config['query'],
        num_links=config['num_links'],
        debug=config['debug']
    )
    
    bing_scraper = BingScraper(
        query=config['query'],
        num_links=config['num_links'],
        debug=config['debug']
    )
    
    print(f"\n🚀 Starting parallel search for: '{config['query']}'")
    print(f"📌 Collecting {config['num_links']} links from each engine...")
    print(f"🔧 Debug mode: {'ON' if config['debug'] else 'OFF'}\n")
    
    # Run scrapers in parallel
    start_time = datetime.now()
    
    # If debug mode, run with special handling
    if config['debug']:
        print("🔍 Debug mode active - browsers will stay open")
        print("⚠️  Close browser windows manually when done\n")
        
        # Create tasks
        tasks = [
            asyncio.create_task(google_scraper.run()),
            asyncio.create_task(bing_scraper.run())
        ]
        
        # Wait for both to complete their scraping (not browser closing)
        results = []
        for task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                print(f"❌ Task error: {str(e)}")
        
        return results
    else:
        # Normal mode - use gather
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
        
        return processed_results

async def main():
    """Main execution function"""
    print_banner()
    
    # Get user inputs
    config = get_user_inputs()
    
    try:
        # Run scrapers
        results = await run_scrapers(config)
        
        # Always display results immediately after collection
        format_results(results)
        
        if config['debug']:
            print("\n🔍 Debug mode: Browsers are still open for inspection")
            print("⚠️  Press Ctrl+C to exit when done\n")
            
            try:
                # Keep the program running
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n✅ Exiting debug mode...")
        else:
            print("\n✅ Search completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Search cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Program terminated by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")