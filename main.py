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
    print(f"🔧 Debug mode: {'ON' if config['debug'] else 'OFF'}")
    print("-" * 70)
    
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
                print(f"[{source}Scraper] ❌ Error: {str(result)}")
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
        
        print(f"\n✅ Both scrapers completed! Collected data in {(datetime.now() - start_time).total_seconds():.2f} seconds")
        
        return processed_results
        
    except Exception as e:
        print(f"❌ Critical error in parallel execution: {str(e)}")
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

async def main():
    """Main execution function"""
    print_banner()
    
    # Get user inputs
    config = get_user_inputs()
    
    try:
        # Show debug mode message if enabled
        if config['debug']:
            print("\n🔍 Debug mode active - browsers will stay open after completion")
            print("⚠️  Close browser windows manually when done\n")
        
        # Run scrapers and get results
        results = await run_scrapers(config)
        
        # Display results immediately after both scrapers complete
        format_results(results)
        
        # Handle debug mode
        if config['debug']:
            print("\n🔍 Debug mode: Browsers are kept open for inspection")
            print("⚠️  Press Ctrl+C to exit when done")
            print("💡 You can continue browsing the search results...")
            print("🔒 Browsers will stay open until you terminate this program")
            
            try:
                # Keep the program running indefinitely in debug mode
                print("\n⏳ Program is running... Keeping browsers alive...")
                while True:
                    await asyncio.sleep(10)  # Check every 10 seconds
            except KeyboardInterrupt:
                print("\n\n✅ Exiting debug mode...")
                print("💡 Browser windows will close when the program exits")
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