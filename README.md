# 🔍 Organic Link Scraper

A powerful **organic search result link scraper** that fetches top organic links from both **Google** and **Bing** search engines simultaneously. Perfect for collecting clean, advertisement-free search results for further content analysis.

## ✨ Features

- **🚀 Parallel Scraping**: Scrapes Google and Bing simultaneously for maximum speed
- **🧹 Clean Results**: Filters out AI summaries, sponsored content, and advertisements
- **🔄 Duplicate Removal**: Automatically removes duplicate links (Google results take priority)
- **📊 Dual Output Modes**: Terminal display or JSON file export
- **🎯 Organic Focus**: Only collects genuine organic search results
- **⚡ Progress Tracking**: Real-time progress bars during scraping

## 🚀 Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration
Edit the parameters in `main.py`:

```python
# CONFIGURATION - Set your search parameters here
query = "what is happening on uk"  # Enter your search query here
num_links = 5                      # Number of links to collect per engine
debug = False                      # Set to True to keep browsers open, False to close them
result = "json"                    # Set to "terminal" for console output or "json" for JSON file
```

### 3. Run the Scraper
```bash
python main.py
```

## 📋 Output Modes

### Terminal Mode (`result = "terminal"`)
Displays results directly in the console with:
- Formatted link titles, URLs, and domains
- Separate sections for Google and Bing results
- Duplicate removal notifications
- Clean, readable output

### JSON Mode (`result = "json"`)
Creates a timestamped JSON file in the root directory:
```json
{
  "search_results": {
    "google": {
      "count": 5,
      "links": [
        {
          "title": "Example Title",
          "url": "https://example.com",
          "domain": "example.com"
        }
      ]
    },
    "bing": {
      "count": 3,
      "links": [...]
    }
  },
  "total_links": 8,
  "timestamp": "2024-12-20T14:30:52"
}
```

## 🔥 Recommended Workflow

For **maximum value**, combine this scraper with content extraction tools:

### Option 1: With Firecrawl
1. Use this scraper to get organic links
2. Feed the URLs to [Firecrawl](https://firecrawl.dev/) for content extraction
3. Get clean, structured content from each link

### Option 2: With Scraph Graph
1. Export results as JSON
2. Use [Scraph Graph](https://scrapegraph-ai.com/) to extract specific content
3. Build comprehensive datasets from organic search results

### Example Pipeline:
```
Link Scraper → JSON Export → Firecrawl/Scraph Graph → Content Analysis
```

## ⚙️ Configuration Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Your search query |
| `num_links` | integer | Number of links per search engine |
| `debug` | boolean | Keep browsers open for inspection |
| `result` | string | Output mode: "terminal" or "json" |

## 🎯 Use Cases

- **Content Research**: Gather organic sources for research topics
- **Competitive Analysis**: Find top-ranking content in your niche
- **Data Collection**: Build datasets from search results
- **SEO Analysis**: Analyze organic search landscapes
- **News Monitoring**: Track organic news results

## 🛡️ What Gets Filtered Out

- ❌ AI-generated summaries
- ❌ Sponsored content and ads
- ❌ YouTube videos and social media reels
- ❌ Duplicate results across engines
- ❌ Internal search engine links

## ✅ What You Get

- ✅ Pure organic search results
- ✅ Clean URLs with titles and domains
- ✅ Deduplicated results
- ✅ Fast parallel collection
- ✅ Ready-to-use data format

## 📁 Project Structure

```
link_scraper/
├── main.py              # Configuration and entry point
├── scraper/
│   ├── __init__.py
│   ├── scraper.py       # Core scraping logic
│   ├── google.py        # Google-specific scraper
│   └── bing.py          # Bing-specific scraper
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## 🔧 Dependencies

- `playwright` - Browser automation
- `asyncio` - Async operations
- Built-in Python libraries for JSON handling

## 💡 Pro Tips

1. **Combine with Content Tools**: This scraper provides URLs - use Firecrawl or Scraph Graph for content
2. **Adjust Link Count**: Start with 5-10 links per engine for testing
3. **Use JSON Mode**: For programmatic processing of results
4. **Debug Mode**: Enable to inspect browser behavior during development

## 📈 Performance

- **Speed**: Parallel processing = ~50% faster than sequential
- **Accuracy**: Filters ensure high-quality organic results
- **Reliability**: Handles cookie dialogs and anti-bot measures
- **Scalability**: Configurable link counts per engine

---

**Ready to collect clean, organic search data? Configure your parameters and start scraping!** 🚀 