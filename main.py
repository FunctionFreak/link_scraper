import asyncio
from scraper.scraper import run_search

# CONFIGURATION - Set your search parameters here
query = "what is happening on uk"  # Enter your search query here
num_links = 5                      # Number of links to collect per engine
debug = False                      # Set to True to keep browsers open, False to close them
result = "json"                # Set to "terminal" for console output or "json" for JSON file

if __name__ == "__main__":
    try:
        asyncio.run(run_search(query, num_links, debug, result))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass