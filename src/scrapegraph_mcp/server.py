#!/usr/bin/env python3
"""
MCP server for ScapeGraph API integration.
This server exposes methods to use ScapeGraph's AI-powered web scraping services:
- markdownify: Convert any webpage into clean, formatted markdown
- smartscraper: Extract structured data from any webpage using AI
- searchscraper: Perform AI-powered web searches with structured results
- smartcrawler_initiate: Initiate intelligent multi-page web crawling with AI extraction or markdown conversion
- smartcrawler_fetch_results: Retrieve results from asynchronous crawling operations
"""

import json
import logging
import os
from typing import Any, Dict, Optional, List, Union, Annotated

import httpx
from fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field, AliasChoices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScapeGraphClient:
    """Client for interacting with the ScapeGraph API."""

    BASE_URL = "https://api.scrapegraphai.com/v1"

    def __init__(self, api_key: str):
        """
        Initialize the ScapeGraph API client.

        Args:
            api_key: API key for ScapeGraph API
        """
        self.api_key = api_key
        self.headers = {
            "SGAI-APIKEY": api_key,
            "Content-Type": "application/json"
        }
        self.client = httpx.Client(timeout=httpx.Timeout(120.0))


    def markdownify(self, website_url: str) -> Dict[str, Any]:
        """
        Convert a webpage into clean, formatted markdown.

        Args:
            website_url: URL of the webpage to convert

        Returns:
            Dictionary containing the markdown result
        """
        url = f"{self.BASE_URL}/markdownify"
        data = {
            "website_url": website_url
        }

        response = self.client.post(url, headers=self.headers, json=data)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        return response.json()

    def smartscraper(
        self,
        user_prompt: str,
        website_url: str = None,
        website_html: str = None,
        website_markdown: str = None,
        output_schema: Dict[str, Any] = None,
        number_of_scrolls: int = None,
        total_pages: int = None,
        render_heavy_js: bool = None,
        stealth: bool = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from a webpage using AI.

        Args:
            user_prompt: Instructions for what data to extract
            website_url: URL of the webpage to scrape (mutually exclusive with website_html and website_markdown)
            website_html: HTML content to process locally (mutually exclusive with website_url and website_markdown, max 2MB)
            website_markdown: Markdown content to process locally (mutually exclusive with website_url and website_html, max 2MB)
            output_schema: JSON schema defining expected output structure (optional)
            number_of_scrolls: Number of infinite scrolls to perform (0-50, default 0)
            total_pages: Number of pages to process for pagination (1-100, default 1)
            render_heavy_js: Enable heavy JavaScript rendering for dynamic pages (default false)
            stealth: Enable stealth mode to avoid bot detection (default false)

        Returns:
            Dictionary containing the extracted data
        """
        url = f"{self.BASE_URL}/smartscraper"
        data = {"user_prompt": user_prompt}

        # Add input source (mutually exclusive)
        if website_url is not None:
            data["website_url"] = website_url
        elif website_html is not None:
            data["website_html"] = website_html
        elif website_markdown is not None:
            data["website_markdown"] = website_markdown
        else:
            raise ValueError("Must provide one of: website_url, website_html, or website_markdown")

        # Add optional parameters
        if output_schema is not None:
            data["output_schema"] = output_schema
        if number_of_scrolls is not None:
            data["number_of_scrolls"] = number_of_scrolls
        if total_pages is not None:
            data["total_pages"] = total_pages
        if render_heavy_js is not None:
            data["render_heavy_js"] = render_heavy_js
        if stealth is not None:
            data["stealth"] = stealth

        response = self.client.post(url, headers=self.headers, json=data)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        return response.json()

    def searchscraper(self, user_prompt: str, num_results: int = None, number_of_scrolls: int = None) -> Dict[str, Any]:
        """
        Perform AI-powered web searches with structured results.

        Args:
            user_prompt: Search query or instructions
            num_results: Number of websites to search (optional, default: 3 websites = 30 credits)
            number_of_scrolls: Number of infinite scrolls to perform on each website (optional)

        Returns:
            Dictionary containing search results and reference URLs
        """
        url = f"{self.BASE_URL}/searchscraper"
        data = {
            "user_prompt": user_prompt
        }
        
        # Add num_results to the request if provided
        if num_results is not None:
            data["num_results"] = num_results
            
        # Add number_of_scrolls to the request if provided
        if number_of_scrolls is not None:
            data["number_of_scrolls"] = number_of_scrolls

        response = self.client.post(url, headers=self.headers, json=data)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        return response.json()

    def scrape(self, website_url: str, render_heavy_js: Optional[bool] = None) -> Dict[str, Any]:
        """
        Basic scrape endpoint to fetch page content.

        Args:
            website_url: URL to scrape
            render_heavy_js: Whether to render heavy JS (optional)

        Returns:
            Dictionary containing the scraped result
        """
        url = f"{self.BASE_URL}/scrape"
        payload: Dict[str, Any] = {"website_url": website_url}
        if render_heavy_js is not None:
            payload["render_heavy_js"] = render_heavy_js

        response = self.client.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def sitemap(self, website_url: str) -> Dict[str, Any]:
        """
        Extract sitemap for a given website.

        Args:
            website_url: Base website URL

        Returns:
            Dictionary containing sitemap URLs/structure
        """
        url = f"{self.BASE_URL}/sitemap"
        payload: Dict[str, Any] = {"website_url": website_url}

        response = self.client.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def agentic_scrapper(
        self,
        url: str,
        user_prompt: Optional[str] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        steps: Optional[List[str]] = None,
        ai_extraction: Optional[bool] = None,
        persistent_session: Optional[bool] = None,
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run the Agentic Scraper workflow (no live session/browser interaction).

        Args:
            url: Target website URL
            user_prompt: Instructions for what to do/extract (optional)
            output_schema: Desired structured output schema (optional)
            steps: High-level steps/instructions for the agent (optional)
            ai_extraction: Whether to enable AI extraction mode (optional)
            persistent_session: Whether to keep session alive between steps (optional)
            timeout_seconds: Per-request timeout override in seconds (optional)
        """
        endpoint = f"{self.BASE_URL}/agentic-scrapper"
        payload: Dict[str, Any] = {"url": url}
        if user_prompt is not None:
            payload["user_prompt"] = user_prompt
        if output_schema is not None:
            payload["output_schema"] = output_schema
        if steps is not None:
            payload["steps"] = steps
        if ai_extraction is not None:
            payload["ai_extraction"] = ai_extraction
        if persistent_session is not None:
            payload["persistent_session"] = persistent_session

        if timeout_seconds is not None:
            response = self.client.post(endpoint, headers=self.headers, json=payload, timeout=timeout_seconds)
        else:
            response = self.client.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def smartcrawler_initiate(
        self, 
        url: str, 
        prompt: str = None, 
        extraction_mode: str = "ai",
        depth: int = None,
        max_pages: int = None,
        same_domain_only: bool = None
    ) -> Dict[str, Any]:
        """
        Initiate a SmartCrawler request for multi-page web crawling.
        
        SmartCrawler supports two modes:
        - AI Extraction Mode (10 credits per page): Extracts structured data based on your prompt
        - Markdown Conversion Mode (2 credits per page): Converts pages to clean markdown

        Smartcrawler takes some time to process the request and returns the request id.
        Use smartcrawler_fetch_results to get the results of the request.
        You have to keep polling the smartcrawler_fetch_results until the request is complete.
        The request is complete when the status is "completed".

        Args:
            url: Starting URL to crawl
            prompt: AI prompt for data extraction (required for AI mode)
            extraction_mode: "ai" for AI extraction or "markdown" for markdown conversion (default: "ai")
            depth: Maximum link traversal depth (optional)
            max_pages: Maximum number of pages to crawl (optional)
            same_domain_only: Whether to crawl only within the same domain (optional)

        Returns:
            Dictionary containing the request ID for async processing
        """
        endpoint = f"{self.BASE_URL}/crawl"
        data = {
            "url": url
        }
        
        # Handle extraction mode
        if extraction_mode == "markdown":
            data["markdown_only"] = True
        elif extraction_mode == "ai":
            if prompt is None:
                raise ValueError("prompt is required when extraction_mode is 'ai'")
            data["prompt"] = prompt
        else:
            raise ValueError(f"Invalid extraction_mode: {extraction_mode}. Must be 'ai' or 'markdown'")
        if depth is not None:
            data["depth"] = depth
        if max_pages is not None:
            data["max_pages"] = max_pages
        if same_domain_only is not None:
            data["same_domain_only"] = same_domain_only

        response = self.client.post(endpoint, headers=self.headers, json=data)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        return response.json()

    def smartcrawler_fetch_results(self, request_id: str) -> Dict[str, Any]:
        """
        Fetch the results of a SmartCrawler operation.

        Args:
            request_id: The request ID returned by smartcrawler_initiate

        Returns:
            Dictionary containing the crawled data (structured extraction or markdown)
            and metadata about processed pages

        Note:
        It takes some time to process the request and returns the results.
        Meanwhile it returns the status of the request.
        You have to keep polling the smartcrawler_fetch_results until the request is complete.
        The request is complete when the status is "completed". and you get results
        Keep polling the smartcrawler_fetch_results until the request is complete.
        """
        endpoint = f"{self.BASE_URL}/crawl/{request_id}"
        
        response = self.client.get(endpoint, headers=self.headers)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()


# Pydantic configuration schema for Smithery
class ConfigSchema(BaseModel):
    scrapegraph_api_key: Optional[str] = Field(
        default=None,
        description="Your Scrapegraph API key (optional - can also be set via SGAI_API_KEY environment variable)",
        # Accept both camelCase (from smithery.yaml) and snake_case (internal) for validation,
        # and serialize back to camelCase to match Smithery expectations.
        validation_alias=AliasChoices("scrapegraphApiKey", "scrapegraph_api_key"),
        serialization_alias="scrapegraphApiKey",
    )


def get_api_key(ctx: Context) -> str:
    """
    Get the API key from config or environment variable.
    
    Args:
        ctx: FastMCP context
        
    Returns:
        API key string
        
    Raises:
        ValueError: If no API key is found
    """
    try:
        logger.info(f"Getting API key. Context type: {type(ctx)}")
        logger.info(f"Context has session_config: {hasattr(ctx, 'session_config')}")
        
        # Try to get from config first, but handle cases where session_config might be None
        api_key = None
        if hasattr(ctx, 'session_config') and ctx.session_config is not None:
            logger.info(f"Session config type: {type(ctx.session_config)}")
            api_key = getattr(ctx.session_config, 'scrapegraph_api_key', None)
            logger.info(f"API key from config: {'***' if api_key else 'None'}")
        else:
            logger.info("No session_config available or session_config is None")
        
        # If not in config, try environment variable
        if not api_key:
            api_key = os.getenv('SGAI_API_KEY')
            logger.info(f"API key from env: {'***' if api_key else 'None'}")

        # If still no API key found, raise error
        if not api_key:
            logger.error("No API key found in config or environment")
            raise ValueError(
                "ScapeGraph API key is required. Please provide it either:\n"
                "1. In the MCP server configuration as 'scrapegraph_api_key'\n"
                "2. As an environment variable 'SGAI_API_KEY'"
            )
        
        logger.info("API key successfully retrieved")
        return api_key
    
    except Exception as e:
        logger.warning(f"Error getting API key from context: {e}. Falling back to cached method.")
        # Fallback to cached method if context handling fails
        return get_cached_api_key()


# Create MCP server instance
mcp = FastMCP("ScapeGraph API MCP Server")

# Global API key cache to handle session issues
_api_key_cache: Optional[str] = None

def get_cached_api_key() -> str:
    """Get API key from cache or environment, bypassing session config issues."""
    global _api_key_cache
    
    if _api_key_cache is None:
        _api_key_cache = os.getenv('SGAI_API_KEY')
        if _api_key_cache:
            logger.info("API key loaded from environment variable")
        else:
            logger.error("No API key found in environment variable SGAI_API_KEY")
            raise ValueError(
                "ScapeGraph API key is required. Please set the SGAI_API_KEY environment variable."
            )
    
    return _api_key_cache


# Add prompts to help users interact with the server
@mcp.prompt()
def web_scraping_guide() -> str:
    """
    A comprehensive guide to using ScapeGraph's web scraping tools effectively.
    
    This prompt provides examples and best practices for each tool in the ScapeGraph MCP server.
    """
    return """# ScapeGraph Web Scraping Guide

## Available Tools Overview

### 1. **markdownify** - Convert webpages to clean markdown
**Use case**: Get clean, readable content from any webpage
**Example**: 
- Input: `https://docs.python.org/3/tutorial/`
- Output: Clean markdown of the Python tutorial

### 2. **smartscraper** - AI-powered data extraction
**Use case**: Extract specific structured data using natural language prompts
**Examples**:
- "Extract all product names and prices from this e-commerce page"
- "Get contact information including email, phone, and address"
- "Find all article titles, authors, and publication dates"

### 3. **searchscraper** - AI web search with extraction
**Use case**: Search the web and extract structured information
**Examples**:
- "Find the latest AI research papers and their abstracts"
- "Search for Python web scraping tutorials with ratings"
- "Get current cryptocurrency prices and market caps"

### 4. **smartcrawler_initiate** - Multi-page intelligent crawling
**Use case**: Crawl multiple pages with AI extraction or markdown conversion
**Modes**:
- AI Mode (10 credits/page): Extract structured data
- Markdown Mode (2 credits/page): Convert to markdown
**Example**: Crawl a documentation site to extract all API endpoints

### 5. **smartcrawler_fetch_results** - Get crawling results
**Use case**: Retrieve results from initiated crawling operations
**Note**: Keep polling until status is "completed"

### 6. **scrape** - Basic page content fetching
**Use case**: Get raw page content with optional JavaScript rendering
**Example**: Fetch content from dynamic pages that require JS

### 7. **sitemap** - Extract website structure
**Use case**: Get all URLs and structure of a website
**Example**: Map out a website's architecture before crawling

### 8. **agentic_scrapper** - AI-powered automated scraping
**Use case**: Complex multi-step scraping with AI automation
**Example**: Navigate through forms, click buttons, extract data

## Best Practices

1. **Start Simple**: Use `markdownify` or `scrape` for basic content
2. **Be Specific**: Provide detailed prompts for better AI extraction
3. **Use Crawling Wisely**: Set appropriate limits for `max_pages` and `depth`
4. **Monitor Credits**: AI extraction uses more credits than markdown conversion
5. **Handle Async**: Use `smartcrawler_fetch_results` to poll for completion

## Common Workflows

### Extract Product Information
1. Use `smartscraper` with prompt: "Extract product name, price, description, and availability"
2. For multiple pages: Use `smartcrawler_initiate` in AI mode

### Research and Analysis
1. Use `searchscraper` to find relevant pages
2. Use `smartscraper` on specific pages for detailed extraction

### Site Documentation
1. Use `sitemap` to discover all pages
2. Use `smartcrawler_initiate` in markdown mode to convert all pages

### Complex Navigation
1. Use `agentic_scrapper` for sites requiring interaction
2. Provide step-by-step instructions in the `steps` parameter
"""


@mcp.prompt()
def quick_start_examples() -> str:
    """
    Quick start examples for common ScapeGraph use cases.
    
    Ready-to-use examples for immediate productivity.
    """
    return """# ScapeGraph Quick Start Examples

## 🚀 Ready-to-Use Examples

### Extract E-commerce Product Data
```
Tool: smartscraper
URL: https://example-shop.com/products/laptop
Prompt: "Extract product name, price, specifications, customer rating, and availability status"
```

### Convert Documentation to Markdown
```
Tool: markdownify
URL: https://docs.example.com/api-reference
```

### Research Latest News
```
Tool: searchscraper
Prompt: "Find latest news about artificial intelligence breakthroughs in 2024"
num_results: 5
```

### Crawl Entire Blog for Articles
```
Tool: smartcrawler_initiate
URL: https://blog.example.com
Prompt: "Extract article title, author, publication date, and summary"
extraction_mode: "ai"
max_pages: 20
```

### Get Website Structure
```
Tool: sitemap
URL: https://example.com
```

### Extract Contact Information
```
Tool: smartscraper
URL: https://company.example.com/contact
Prompt: "Find all contact methods: email addresses, phone numbers, physical address, and social media links"
```

### Automated Form Navigation
```
Tool: agentic_scrapper
URL: https://example.com/search
user_prompt: "Navigate to the search page, enter 'web scraping tools', and extract the top 5 results"
steps: ["Find search box", "Enter search term", "Submit form", "Extract results"]
```

## 💡 Pro Tips

1. **For Dynamic Content**: Use `render_heavy_js: true` with the `scrape` tool
2. **For Large Sites**: Start with `sitemap` to understand structure
3. **For Async Operations**: Always poll `smartcrawler_fetch_results` until complete
4. **For Complex Sites**: Use `agentic_scrapper` with detailed step instructions
5. **For Cost Efficiency**: Use markdown mode for content conversion, AI mode for data extraction

## 🔧 Configuration

Set your API key via:
- Environment variable: `SGAI_API_KEY=your_key_here`
- MCP configuration: `scrapegraph_api_key: "your_key_here"`

No configuration required - the server works with environment variables!
"""


# Add resources to expose server capabilities and data
@mcp.resource("scrapegraph://api/status")
def api_status() -> str:
    """
    Current status and capabilities of the ScapeGraph API server.
    
    Provides real-time information about available tools, credit usage, and server health.
    """
    return """# ScapeGraph API Status

## Server Information
- **Status**: ✅ Online and Ready
- **Version**: 1.0.0
- **Base URL**: https://api.scrapegraphai.com/v1

## Available Tools
1. **markdownify** - Convert webpages to markdown (2 credits/page)
2. **smartscraper** - AI data extraction (10 credits/page)
3. **searchscraper** - AI web search (30 credits for 3 websites)
4. **smartcrawler** - Multi-page crawling (2-10 credits/page)
5. **scrape** - Basic page fetching (1 credit/page)
6. **sitemap** - Website structure extraction (1 credit)
7. **agentic_scrapper** - AI automation (variable credits)

## Credit Costs
- **Markdown Conversion**: 2 credits per page
- **AI Extraction**: 10 credits per page
- **Web Search**: 10 credits per website (default 3 websites)
- **Basic Scraping**: 1 credit per page
- **Sitemap**: 1 credit per request

## Configuration
- **API Key**: Required (set via SGAI_API_KEY env var or config)
- **Timeout**: 120 seconds default (configurable)
- **Rate Limits**: Applied per API key

## Best Practices
- Use markdown mode for content conversion (cheaper)
- Use AI mode for structured data extraction
- Set appropriate limits for crawling operations
- Monitor credit usage for cost optimization

Last Updated: $(date)
"""


@mcp.resource("scrapegraph://examples/use-cases")
def common_use_cases() -> str:
    """
    Common use cases and example implementations for ScapeGraph tools.
    
    Real-world examples with expected inputs and outputs.
    """
    return """# ScapeGraph Common Use Cases

## 🛍️ E-commerce Data Extraction

### Product Information Scraping
**Tool**: smartscraper
**Input**: Product page URL + "Extract name, price, description, rating, availability"
**Output**: Structured JSON with product details
**Credits**: 10 per page

### Price Monitoring
**Tool**: smartcrawler_initiate (AI mode)
**Input**: Product category page + price extraction prompt
**Output**: Structured price data across multiple products
**Credits**: 10 per page crawled

## 📰 Content & Research

### News Article Extraction
**Tool**: searchscraper
**Input**: "Latest news about [topic]" + num_results
**Output**: Article titles, summaries, sources, dates
**Credits**: 10 per website searched

### Documentation Conversion
**Tool**: smartcrawler_initiate (markdown mode)
**Input**: Documentation site root URL
**Output**: Clean markdown files for all pages
**Credits**: 2 per page converted

## 🏢 Business Intelligence

### Contact Information Gathering
**Tool**: smartscraper
**Input**: Company website + "Find contact details"
**Output**: Emails, phones, addresses, social media
**Credits**: 10 per page

### Competitor Analysis
**Tool**: searchscraper + smartscraper combination
**Input**: Search for competitors + extract key metrics
**Output**: Structured competitive intelligence
**Credits**: Variable based on pages analyzed

## 🔍 Research & Analysis

### Academic Paper Research
**Tool**: searchscraper
**Input**: Research query + academic site focus
**Output**: Paper titles, abstracts, authors, citations
**Credits**: 10 per source website

### Market Research
**Tool**: smartcrawler_initiate
**Input**: Industry website + data extraction prompts
**Output**: Market trends, statistics, insights
**Credits**: 10 per page (AI mode)

## 🤖 Automation Workflows

### Form-based Data Collection
**Tool**: agentic_scrapper
**Input**: Site URL + navigation steps + extraction goals
**Output**: Data collected through automated interaction
**Credits**: Variable based on complexity

### Multi-step Research Process
**Workflow**: sitemap → smartcrawler_initiate → smartscraper
**Input**: Target site + research objectives
**Output**: Comprehensive site analysis and data extraction
**Credits**: Cumulative based on tools used

## 💡 Optimization Tips

1. **Start with sitemap** to understand site structure
2. **Use markdown mode** for content archival (cheaper)
3. **Use AI mode** for structured data extraction
4. **Batch similar requests** to optimize credit usage
5. **Set appropriate crawl limits** to control costs
6. **Use specific prompts** for better AI extraction accuracy

## 📊 Expected Response Times

- **Simple scraping**: 5-15 seconds
- **AI extraction**: 15-45 seconds per page
- **Crawling operations**: 1-5 minutes (async)
- **Search operations**: 30-90 seconds
- **Agentic workflows**: 2-10 minutes

## 🚨 Common Pitfalls

- Not setting crawl limits (unexpected credit usage)
- Vague extraction prompts (poor AI results)
- Not polling async operations (missing results)
- Ignoring rate limits (request failures)
- Not handling JavaScript-heavy sites (incomplete data)
"""


@mcp.resource("scrapegraph://tools/comparison")
def tool_comparison_guide() -> str:
    """
    Detailed comparison of ScapeGraph tools to help choose the right tool for each task.
    
    Decision matrix and feature comparison across all available tools.
    """
    return """# ScapeGraph Tools Comparison Guide

## 🎯 Quick Decision Matrix

| Need | Recommended Tool | Alternative | Credits |
|------|------------------|-------------|---------|
| Convert page to markdown | `markdownify` | `scrape` + manual | 2 |
| Extract specific data | `smartscraper` | `agentic_scrapper` | 10 |
| Search web for info | `searchscraper` | Multiple `smartscraper` | 30 |
| Crawl multiple pages | `smartcrawler_initiate` | Loop `smartscraper` | 2-10/page |
| Get raw page content | `scrape` | `markdownify` | 1 |
| Map site structure | `sitemap` | Manual discovery | 1 |
| Complex automation | `agentic_scrapper` | Custom scripting | Variable |

## 🔍 Detailed Tool Comparison

### Content Extraction Tools

#### markdownify vs scrape
- **markdownify**: Clean, formatted markdown output
- **scrape**: Raw HTML with optional JS rendering
- **Use markdownify when**: You need readable content
- **Use scrape when**: You need full HTML or custom parsing

#### smartscraper vs agentic_scrapper
- **smartscraper**: Single-page AI extraction
- **agentic_scrapper**: Multi-step automated workflows
- **Use smartscraper when**: Simple data extraction from one page
- **Use agentic_scrapper when**: Complex navigation required

### Scale & Automation

#### Single Page Tools
- `markdownify`, `smartscraper`, `scrape`, `sitemap`
- **Pros**: Fast, predictable costs, simple
- **Cons**: Manual iteration for multiple pages

#### Multi-Page Tools
- `smartcrawler_initiate`, `searchscraper`, `agentic_scrapper`
- **Pros**: Automated scale, comprehensive results
- **Cons**: Higher costs, longer processing times

### Cost Optimization

#### Low Cost (1-2 credits)
- `scrape`: Basic page fetching
- `markdownify`: Content conversion
- `sitemap`: Site structure

#### Medium Cost (10 credits)
- `smartscraper`: AI data extraction
- `searchscraper`: Per website searched

#### Variable Cost
- `smartcrawler_initiate`: 2-10 credits per page
- `agentic_scrapper`: Depends on complexity

## 🚀 Performance Characteristics

### Speed (Typical Response Times)
1. **scrape**: 2-5 seconds
2. **sitemap**: 3-8 seconds
3. **markdownify**: 5-15 seconds
4. **smartscraper**: 15-45 seconds
5. **searchscraper**: 30-90 seconds
6. **smartcrawler**: 1-5 minutes (async)
7. **agentic_scrapper**: 2-10 minutes

### Reliability
- **Highest**: `scrape`, `sitemap`, `markdownify`
- **High**: `smartscraper`, `searchscraper`
- **Variable**: `smartcrawler`, `agentic_scrapper` (depends on site complexity)

## 🎨 Output Format Comparison

### Structured Data
- **smartscraper**: JSON with extracted fields
- **searchscraper**: JSON with search results
- **agentic_scrapper**: Custom schema support

### Content Formats
- **markdownify**: Clean markdown text
- **scrape**: Raw HTML
- **sitemap**: URL list/structure

### Async Operations
- **smartcrawler_initiate**: Returns request ID
- **smartcrawler_fetch_results**: Returns final data
- All others: Immediate response

## 🛠️ Integration Patterns

### Simple Workflows
```
URL → markdownify → Markdown content
URL → smartscraper → Structured data
Query → searchscraper → Research results
```

### Complex Workflows
```
URL → sitemap → smartcrawler_initiate → smartcrawler_fetch_results
URL → agentic_scrapper (with steps) → Complex extracted data
Query → searchscraper → smartscraper (on results) → Detailed analysis
```

### Hybrid Approaches
```
URL → scrape (check if JS needed) → smartscraper (extract data)
URL → sitemap (map structure) → smartcrawler (batch process)
```

## 📋 Selection Checklist

**Choose markdownify when:**
- ✅ Need readable content format
- ✅ Converting documentation/articles
- ✅ Cost is a primary concern

**Choose smartscraper when:**
- ✅ Need specific data extracted
- ✅ Working with single pages
- ✅ Want AI-powered extraction

**Choose searchscraper when:**
- ✅ Need to find information across web
- ✅ Research-oriented tasks
- ✅ Don't have specific URLs

**Choose smartcrawler when:**
- ✅ Need to process multiple pages
- ✅ Can wait for async processing
- ✅ Want consistent extraction across site

**Choose agentic_scrapper when:**
- ✅ Site requires complex navigation
- ✅ Need to interact with forms/buttons
- ✅ Custom workflow requirements
"""


# Add tool for markdownify
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def markdownify(website_url: str, ctx: Context) -> Dict[str, Any]:
    """
    Convert a webpage into clean, formatted markdown.

    This tool fetches any webpage and converts its content into clean, readable markdown format.
    Useful for extracting content from documentation, articles, and web pages for further processing.
    Costs 2 credits per page. Read-only operation with no side effects.

    Args:
        website_url: The complete URL of the webpage to convert to markdown format. Must include protocol (http:// or https://). Example: https://example.com/page

    Returns:
        Dictionary containing the markdown result with the page content in markdown format
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.markdownify(website_url)
    except Exception as e:
        return {"error": str(e)}


# Add tool for smartscraper
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def smartscraper(
    user_prompt: str,
    ctx: Context,
    website_url: Optional[str] = None,
    website_html: Optional[str] = None,
    website_markdown: Optional[str] = None,
    output_schema: Optional[Annotated[Union[str, Dict[str, Any]], Field(
        default=None,
        description="JSON schema dict or JSON string defining the expected output structure",
        json_schema_extra={
            "oneOf": [
                {"type": "string"},
                {"type": "object"}
            ]
        }
    )]] = None,
    number_of_scrolls: Optional[int] = None,
    total_pages: Optional[int] = None,
    render_heavy_js: Optional[bool] = None,
    stealth: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Extract structured data from a webpage, HTML, or markdown using AI-powered extraction.

    This tool uses advanced AI to understand your natural language prompt and extract specific
    structured data from web content. Supports three input modes: URL scraping, local HTML processing,
    or local markdown processing. Ideal for extracting product information, contact details,
    article metadata, or any structured content. Costs 10 credits per page. Read-only operation.

    Args:
        user_prompt: Natural language instructions describing what data to extract. Be specific about the fields you want. Example: 'Extract product name, price, description, and availability status'
        website_url: The complete URL of the webpage to scrape (mutually exclusive with website_html and website_markdown). Must include protocol. Example: https://example.com/products/item
        website_html: Raw HTML content to process locally (mutually exclusive with website_url and website_markdown, max 2MB). Useful for processing pre-fetched or generated HTML
        website_markdown: Markdown content to process locally (mutually exclusive with website_url and website_html, max 2MB). Useful for extracting from markdown documents
        output_schema: JSON schema dict or JSON string defining the expected output structure. Example: {'type': 'object', 'properties': {'title': {'type': 'string'}, 'price': {'type': 'number'}}}
        number_of_scrolls: Number of infinite scrolls to perform before scraping (0-50, default 0). Useful for dynamically loaded content. Example: 3 for pages with lazy-loading
        total_pages: Number of pages to process for pagination (1-100, default 1). Useful for multi-page content
        render_heavy_js: Enable heavy JavaScript rendering for Single Page Applications and dynamic sites (default false). Increases processing time but captures client-side rendered content
        stealth: Enable stealth mode to avoid bot detection (default false). Useful for sites with anti-scraping measures

    Returns:
        Dictionary containing the extracted data in structured format matching your prompt requirements
        and optional output_schema
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)

        # Parse output_schema if it's a JSON string
        normalized_schema: Optional[Dict[str, Any]] = None
        if isinstance(output_schema, dict):
            normalized_schema = output_schema
        elif isinstance(output_schema, str):
            try:
                parsed_schema = json.loads(output_schema)
                if isinstance(parsed_schema, dict):
                    normalized_schema = parsed_schema
                else:
                    return {"error": "output_schema must be a JSON object"}
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON for output_schema: {str(e)}"}

        return client.smartscraper(
            user_prompt=user_prompt,
            website_url=website_url,
            website_html=website_html,
            website_markdown=website_markdown,
            output_schema=normalized_schema,
            number_of_scrolls=number_of_scrolls,
            total_pages=total_pages,
            render_heavy_js=render_heavy_js,
            stealth=stealth
        )
    except Exception as e:
        return {"error": str(e)}


# Add tool for searchscraper
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False})
def searchscraper(
    user_prompt: str,
    ctx: Context,
    num_results: Optional[int] = None,
    number_of_scrolls: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform AI-powered web searches with structured data extraction.

    This tool searches the web based on your query and uses AI to extract structured information
    from the search results. Ideal for research, competitive analysis, and gathering information
    from multiple sources. Each website searched costs 10 credits (default 3 websites = 30 credits).
    Read-only operation but results may vary over time (non-idempotent).

    Args:
        user_prompt: Search query or natural language instructions for what information to find across the web. Example: 'Find latest AI research papers published in 2024 with author names and abstracts'
        num_results: Number of websites to search and extract data from. Default is 3 websites. Note: Each website costs 10 credits, so 3 websites = 30 credits
        number_of_scrolls: Number of infinite scrolls to perform on each searched webpage before extraction. Default is 0. Useful for pages with dynamically loaded content

    Returns:
        Dictionary containing structured search results with extracted data from multiple websites,
        including reference URLs for each source
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.searchscraper(user_prompt, num_results, number_of_scrolls)
    except Exception as e:
        return {"error": str(e)}


# Add tool for SmartCrawler initiation
@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def smartcrawler_initiate(
    url: str,
    ctx: Context,
    prompt: Optional[str] = None,
    extraction_mode: str = "ai",
    depth: Optional[int] = None,
    max_pages: Optional[int] = None,
    same_domain_only: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Initiate an asynchronous multi-page web crawling operation with AI extraction or markdown conversion.

    This tool starts an intelligent crawler that discovers and processes multiple pages from a starting URL.
    Choose between AI Extraction Mode (10 credits/page) for structured data or Markdown Mode (2 credits/page)
    for content conversion. The operation is asynchronous - use smartcrawler_fetch_results to retrieve results.
    Creates a new crawl request (non-idempotent, non-read-only).

    SmartCrawler supports two modes:
    - AI Extraction Mode: Extracts structured data based on your prompt from every crawled page
    - Markdown Conversion Mode: Converts each page to clean markdown format

    Args:
        url: The starting URL to begin crawling from. The crawler will discover and process linked pages from this starting point. Must include protocol. Example: https://docs.example.com
        prompt: AI prompt for data extraction (REQUIRED when extraction_mode is 'ai', ignored for 'markdown' mode). Describe what data to extract from each page. Example: 'Extract API endpoint name, method, parameters, and description'
        extraction_mode: Extraction mode: 'ai' for AI-powered structured data extraction (10 credits/page) or 'markdown' for simple markdown conversion (2 credits/page). Default is 'ai'
        depth: Maximum depth of link traversal from the starting URL. Depth 1 means only pages linked from the start URL. Default is unlimited depth. Example: 2
        max_pages: Maximum number of pages to crawl in total. Use this to control costs and scope. Default is unlimited. Recommended: Start with 10-20 for testing. Example: 50
        same_domain_only: If true, only crawls pages within the same domain as the starting URL. Prevents following external links. Default is true. Set false to crawl external links

    Returns:
        Dictionary containing the unique request_id for polling results with smartcrawler_fetch_results.
        Keep polling until status is 'completed'
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.smartcrawler_initiate(
            url=url,
            prompt=prompt,
            extraction_mode=extraction_mode,
            depth=depth,
            max_pages=max_pages,
            same_domain_only=same_domain_only
        )
    except Exception as e:
        return {"error": str(e)}


# Add tool for fetching SmartCrawler results
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def smartcrawler_fetch_results(request_id: str, ctx: Context) -> Dict[str, Any]:
    """
    Retrieve the results of an asynchronous SmartCrawler operation.

    This tool fetches the results from a previously initiated crawling operation using the request_id.
    The crawl request processes asynchronously in the background. Keep polling this endpoint until
    the status field indicates 'completed'. While processing, you'll receive status updates.
    Read-only operation that safely retrieves results without side effects.

    Args:
        request_id: The unique request ID returned by smartcrawler_initiate. Use this to retrieve the crawling results. Keep polling until status is 'completed'. Example: 'req_abc123xyz'

    Returns:
        Dictionary containing:
        - status: Current status of the crawl operation ('processing', 'completed', 'failed')
        - results: Crawled data (structured extraction or markdown) when completed
        - metadata: Information about processed pages, URLs visited, and processing statistics
        Keep polling until status is 'completed' to get final results
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.smartcrawler_fetch_results(request_id)
    except Exception as e:
        return {"error": str(e)}


# Add tool for basic scrape
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def scrape(
    website_url: str,
    ctx: Context,
    render_heavy_js: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Fetch raw page content from any URL with optional JavaScript rendering.

    This tool performs basic web scraping to retrieve the raw HTML content of a webpage.
    Optionally enable JavaScript rendering for Single Page Applications (SPAs) and sites with
    heavy client-side rendering. Lower cost than AI extraction (1 credit/page).
    Read-only operation with no side effects.

    Args:
        website_url: The complete URL of the webpage to scrape. Must include protocol (http:// or https://). Returns raw page content. Example: https://example.com/page
        render_heavy_js: If true, enables full JavaScript rendering for pages with heavy client-side rendering (SPAs, React apps, etc.). Increases processing time but captures dynamic content. Default is false

    Returns:
        Dictionary containing the raw HTML content of the page. Enable render_heavy_js for
        dynamic content that requires JavaScript execution
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.scrape(website_url=website_url, render_heavy_js=render_heavy_js)
    except httpx.HTTPError as http_err:
        return {"error": str(http_err)}
    except ValueError as val_err:
        return {"error": str(val_err)}


# Add tool for sitemap extraction
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def sitemap(website_url: str, ctx: Context) -> Dict[str, Any]:
    """
    Extract and discover the complete sitemap structure of any website.

    This tool automatically discovers all accessible URLs and pages within a website, providing
    a comprehensive map of the site's structure. Useful for understanding site architecture before
    crawling or for discovering all available content. Very cost-effective at 1 credit per request.
    Read-only operation with no side effects.

    Args:
        website_url: The base URL of the website to extract sitemap from. Returns discovered URLs and site structure. Must include protocol. Example: https://example.com

    Returns:
        Dictionary containing the discovered URLs, site structure, and hierarchy. Includes all
        accessible pages, subdomains, and resource paths found on the website
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.sitemap(website_url=website_url)
    except httpx.HTTPError as http_err:
        return {"error": str(http_err)}
    except ValueError as val_err:
        return {"error": str(val_err)}


# Add tool for Agentic Scraper (no live session/browser interaction)
@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def agentic_scrapper(
    url: str,
    ctx: Context,
    user_prompt: Optional[str] = None,
    output_schema: Optional[Annotated[Union[str, Dict[str, Any]], Field(
        default=None,
        description="Desired output structure as a JSON schema dict or JSON string",
        json_schema_extra={
            "oneOf": [
                {"type": "string"},
                {"type": "object"}
            ]
        }
    )]] = None,
    steps: Optional[Annotated[Union[str, List[str]], Field(
        default=None,
        description="Step-by-step instructions for the agent as a list of strings or JSON array string",
        json_schema_extra={
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}}
            ]
        }
    )]] = None,
    ai_extraction: Optional[bool] = None,
    persistent_session: Optional[bool] = None,
    timeout_seconds: Optional[float] = None
) -> Dict[str, Any]:
    """
    Execute complex multi-step web scraping workflows with AI-powered automation.

    This tool runs an intelligent agent that can navigate websites, interact with forms and buttons,
    follow multi-step workflows, and extract structured data. Ideal for complex scraping scenarios
    requiring user interaction simulation, form submissions, or multi-page navigation flows.
    Supports custom output schemas and step-by-step instructions. Variable credit cost based on
    complexity. Can perform actions on the website (non-read-only, non-idempotent).

    The agent accepts flexible input formats for steps (list or JSON string) and output_schema
    (dict or JSON string) to accommodate different client implementations.

    Args:
        url: The target website URL where the agentic scraping workflow should start. Must include protocol. Example: https://example.com/search
        user_prompt: High-level instructions for what the agent should accomplish on the website. Example: 'Navigate to the search page, search for laptops, and extract the top 5 results with prices'
        output_schema: Desired output structure as a JSON schema dict or JSON string. Defines the format of extracted data. Example: {'type': 'object', 'properties': {'title': {'type': 'string'}, 'price': {'type': 'number'}}}
        steps: Step-by-step instructions for the agent as a list of strings or JSON array string. Example: ['Click search button', 'Enter search term', 'Wait for results', 'Extract data']
        ai_extraction: Whether to enable AI-powered extraction mode for intelligent data parsing. Default is true. Set false for simpler extraction
        persistent_session: Whether to maintain session state between steps (keeps cookies, login state, etc.). Useful for authenticated workflows. Default is false
        timeout_seconds: Maximum time in seconds to wait for the entire workflow to complete. Default is 120 seconds. Increase for complex workflows. Example: 300.0

    Returns:
        Dictionary containing the extracted data matching the specified output_schema, along with
        execution metadata, visited URLs, and action logs from the automated workflow
    """
    # Normalize inputs to handle flexible formats from different MCP clients
    normalized_steps: Optional[List[str]] = None
    if isinstance(steps, list):
        normalized_steps = steps
    elif isinstance(steps, str):
        parsed_steps: Optional[Any] = None
        try:
            parsed_steps = json.loads(steps)
        except json.JSONDecodeError:
            parsed_steps = None
        if isinstance(parsed_steps, list):
            normalized_steps = parsed_steps
        else:
            normalized_steps = [steps]

    normalized_schema: Optional[Dict[str, Any]] = None
    if isinstance(output_schema, dict):
        normalized_schema = output_schema
    elif isinstance(output_schema, str):
        try:
            parsed_schema = json.loads(output_schema)
            if isinstance(parsed_schema, dict):
                normalized_schema = parsed_schema
            else:
                return {"error": "output_schema must be a JSON object"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON for output_schema: {str(e)}"}

    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.agentic_scrapper(
            url=url,
            user_prompt=user_prompt,
            output_schema=normalized_schema,
            steps=normalized_steps,
            ai_extraction=ai_extraction,
            persistent_session=persistent_session,
            timeout_seconds=timeout_seconds,
        )
    except httpx.TimeoutException as timeout_err:
        return {"error": f"Request timed out: {str(timeout_err)}"}
    except httpx.HTTPError as http_err:
        return {"error": str(http_err)}
    except ValueError as val_err:
        return {"error": str(val_err)}


# Smithery server creation function
@smithery.server(config_schema=ConfigSchema)
def create_server() -> FastMCP:
    """
    Create and return the FastMCP server instance for Smithery deployment.
    
    Returns:
        Configured FastMCP server instance
    """
    return mcp


def main() -> None:
    """Run the ScapeGraph MCP server."""
    try:
        logger.info("Starting ScapeGraph MCP server!")
        print("Starting ScapeGraph MCP server!")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        print(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    main()