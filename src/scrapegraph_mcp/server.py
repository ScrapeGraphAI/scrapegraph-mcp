#!/usr/bin/env python3
"""
MCP server for ScapeGraph API integration.

This server exposes methods to use ScapeGraph's AI-powered web scraping services:
- markdownify: Convert any webpage into clean, formatted markdown
- smartscraper: Extract structured data from any webpage using AI
- searchscraper: Perform AI-powered web searches with structured results
- smartcrawler_initiate: Initiate intelligent multi-page web crawling with AI extraction or markdown conversion
- smartcrawler_fetch_results: Retrieve results from asynchronous crawling operations
- scrape: Fetch raw page content with optional JavaScript rendering
- sitemap: Extract and discover complete website structure
- agentic_scrapper: Execute complex multi-step web scraping workflows

## Parameter Validation and Error Handling

All tools include comprehensive parameter validation with detailed error messages:

### Common Validation Rules:
- URLs must include protocol (http:// or https://)
- Numeric parameters must be within specified ranges
- Mutually exclusive parameters cannot be used together
- Required parameters must be provided
- JSON schemas must be valid JSON format

### Error Response Format:
All tools return errors in a consistent format:
```json
{
  "error": "Detailed error message explaining the issue",
  "error_type": "ValidationError|HTTPError|TimeoutError|etc.",
  "parameter": "parameter_name_if_applicable",
  "valid_range": "acceptable_values_if_applicable"
}
```

### Example Validation Errors:
- Invalid URL: "website_url must include protocol (http:// or https://)"
- Range violation: "number_of_scrolls must be between 0 and 50"
- Mutual exclusion: "Cannot specify both website_url and website_html"
- Missing required: "prompt is required when extraction_mode is 'ai'"
- Invalid JSON: "output_schema must be valid JSON format"

### Best Practices for Error Handling:
1. Always check the 'error' field in responses
2. Use parameter validation before making requests
3. Implement retry logic for timeout errors
4. Handle rate limiting gracefully
5. Validate URLs before passing to tools

For comprehensive parameter documentation, use the resource:
`scrapegraph://parameters/reference`
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
    Get the API key from HTTP header or MCP session config.

    Supports two modes:
    - HTTP mode (Render): API key from 'X-API-Key' header via mcp-remote
    - Stdio mode (Smithery): API key from session_config.scrapegraph_api_key

    Args:
        ctx: FastMCP context

    Returns:
        API key string

    Raises:
        ValueError: If no API key is found
    """
    from fastmcp.server.dependencies import get_http_headers

    # Try HTTP header first (for remote/Render deployments)
    try:
        headers = get_http_headers()
        api_key = headers.get('x-api-key')
        if api_key:
            logger.info("API key retrieved from X-API-Key header")
            return api_key
    except LookupError:
        # Not in HTTP context, try session config (Smithery/stdio mode)
        pass

    # Try session config (for Smithery/stdio deployments)
    if hasattr(ctx, 'session_config') and ctx.session_config is not None:
        api_key = getattr(ctx.session_config, 'scrapegraph_api_key', None)
        if api_key:
            logger.info("API key retrieved from session config")
            return api_key

    logger.error("No API key found in header or session config")
    raise ValueError(
        "ScapeGraph API key is required. Please provide it via:\n"
        "- HTTP header 'X-API-Key' (for remote server via mcp-remote)\n"
        "- MCP config 'scrapegraphApiKey' (for Smithery/local stdio)"
    )


# Create MCP server instance
mcp = FastMCP("ScapeGraph API MCP Server")


# Health check endpoint for remote deployments (Render, etc.)
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for container orchestration and load balancers."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "service": "scrapegraph-mcp"})


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


@mcp.resource("scrapegraph://parameters/reference")
def parameter_reference_guide() -> str:
    """
    Comprehensive parameter reference guide for all ScapeGraph MCP tools.
    
    Complete documentation of every parameter with examples, constraints, and best practices.
    """
    return """# ScapeGraph MCP Parameter Reference Guide

## 📋 Complete Parameter Documentation

This guide provides comprehensive documentation for every parameter across all ScapeGraph MCP tools. Use this as your definitive reference for understanding parameter behavior, constraints, and best practices.

---

## 🔧 Common Parameters

### URL Parameters
**Used in**: markdownify, smartscraper, searchscraper, smartcrawler_initiate, scrape, sitemap, agentic_scrapper

#### `website_url` / `url`
- **Type**: `str` (required)
- **Format**: Must include protocol (http:// or https://)
- **Examples**: 
  - ✅ `https://example.com/page`
  - ✅ `https://docs.python.org/3/tutorial/`
  - ❌ `example.com` (missing protocol)
  - ❌ `ftp://example.com` (unsupported protocol)
- **Best Practices**:
  - Always include the full URL with protocol
  - Ensure the URL is publicly accessible
  - Test URLs manually before automation

---

## 🤖 AI and Extraction Parameters

### `user_prompt`
**Used in**: smartscraper, searchscraper, agentic_scrapper

- **Type**: `str` (required)
- **Purpose**: Natural language instructions for AI extraction
- **Examples**:
  - `"Extract product name, price, description, and availability"`
  - `"Find contact information: email, phone, address"`
  - `"Get article title, author, publication date, summary"`
- **Best Practices**:
  - Be specific about desired fields
  - Mention data types (numbers, dates, URLs)
  - Include context about data location
  - Use clear, descriptive language

### `output_schema`
**Used in**: smartscraper, agentic_scrapper

- **Type**: `Optional[Union[str, Dict[str, Any]]]`
- **Purpose**: Define expected output structure
- **Formats**:
  - Dictionary: `{'type': 'object', 'properties': {'title': {'type': 'string'}}, 'required': []}`
  - JSON string: `'{"type": "object", "properties": {"name": {"type": "string"}}, "required": []}'`
- **IMPORTANT**: Must include a `"required"` field (can be empty array `[]` if no fields are required)
- **Examples**:
  ```json
  {
    "type": "object",
    "properties": {
      "products": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"},
            "available": {"type": "boolean"}
          },
          "required": []
        }
      }
    },
    "required": []
  }
  ```
- **Best Practices**:
  - Always include the `"required"` field (use `[]` if no fields are required)
  - Use for complex, structured extractions
  - Define clear data types
  - Consider nested structures for complex data
  - Note: If `"required"` field is missing, it will be automatically added as `[]`

---

## 🌐 Content Source Parameters

### `website_html`
**Used in**: smartscraper

- **Type**: `Optional[str]`
- **Purpose**: Process local HTML content
- **Constraints**: Maximum 2MB
- **Use Cases**:
  - Pre-fetched HTML content
  - Generated HTML from other sources
  - Offline HTML processing
- **Mutually Exclusive**: Cannot use with `website_url` or `website_markdown`

### `website_markdown`
**Used in**: smartscraper

- **Type**: `Optional[str]`
- **Purpose**: Process local markdown content
- **Constraints**: Maximum 2MB
- **Use Cases**:
  - Documentation processing
  - README file analysis
  - Converted web content
- **Mutually Exclusive**: Cannot use with `website_url` or `website_html`

---

## 📄 Pagination and Scrolling Parameters

### `number_of_scrolls`
**Used in**: smartscraper, searchscraper

- **Type**: `Optional[int]`
- **Range**: 0-50 scrolls
- **Default**: 0 (no scrolling)
- **Purpose**: Handle dynamically loaded content
- **Examples**:
  - `0`: Static content, no scrolling needed
  - `3`: Social media feeds, product listings
  - `10`: Long articles, extensive catalogs
- **Performance Impact**: +5-10 seconds per scroll
- **Best Practices**:
  - Start with 0 and increase if content seems incomplete
  - Use sparingly to control processing time
  - Consider site loading behavior

### `total_pages`
**Used in**: smartscraper

- **Type**: `Optional[int]`
- **Range**: 1-100 pages
- **Default**: 1 (single page)
- **Purpose**: Process paginated content
- **Cost Impact**: 10 credits × pages
- **Examples**:
  - `1`: Single page extraction
  - `5`: First 5 pages of results
  - `20`: Comprehensive pagination
- **Best Practices**:
  - Set reasonable limits to control costs
  - Consider total credit usage
  - Test with small numbers first

---

## 🚀 Performance Parameters

### `render_heavy_js`
**Used in**: smartscraper, scrape

- **Type**: `Optional[bool]`
- **Default**: `false`
- **Purpose**: Enable JavaScript rendering for SPAs
- **When to Use `true`**:
  - React/Angular/Vue applications
  - Dynamic content loading
  - AJAX-heavy interfaces
  - Content appearing after page load
- **When to Use `false`**:
  - Static websites
  - Server-side rendered content
  - Traditional HTML pages
  - When speed is priority
- **Performance Impact**:
  - `false`: 2-5 seconds
  - `true`: 15-30 seconds
- **Cost**: Same regardless of setting

### `stealth`
**Used in**: smartscraper

- **Type**: `Optional[bool]`
- **Default**: `false`
- **Purpose**: Bypass basic bot detection
- **When to Use**:
  - Sites with anti-scraping measures
  - E-commerce sites with protection
  - Sites requiring "human-like" behavior
- **Limitations**:
  - Not 100% guaranteed
  - May increase processing time
  - Some advanced detection may still work

---

## 🔄 Crawling Parameters

### `prompt`
**Used in**: smartcrawler_initiate

- **Type**: `Optional[str]`
- **Required**: When `extraction_mode="ai"`
- **Purpose**: AI extraction instructions for all crawled pages
- **Examples**:
  - `"Extract API endpoint name, method, parameters"`
  - `"Get article title, author, publication date"`
- **Best Practices**:
  - Use general terms that apply across page types
  - Consider varying page structures
  - Be specific about desired fields

### `extraction_mode`
**Used in**: smartcrawler_initiate

- **Type**: `str`
- **Default**: `"ai"`
- **Options**:
  - `"ai"`: AI-powered extraction (10 credits/page)
  - `"markdown"`: Markdown conversion (2 credits/page)
- **Cost Comparison**:
  - AI mode: 50 pages = 500 credits
  - Markdown mode: 50 pages = 100 credits
- **Use Cases**:
  - AI: Data collection, research, analysis
  - Markdown: Content archival, documentation backup

### `depth`
**Used in**: smartcrawler_initiate

- **Type**: `Optional[int]`
- **Default**: Unlimited
- **Purpose**: Control link traversal depth
- **Levels**:
  - `0`: Only starting URL
  - `1`: Starting URL + direct links
  - `2`: Two levels of link following
  - `3+`: Deeper traversal
- **Considerations**:
  - Higher depth = exponential growth
  - Use with `max_pages` for control
  - Consider site structure

### `max_pages`
**Used in**: smartcrawler_initiate

- **Type**: `Optional[int]`
- **Default**: Unlimited
- **Purpose**: Limit total pages crawled
- **Recommended Ranges**:
  - `10-20`: Testing, small sites
  - `50-100`: Medium sites
  - `200-500`: Large sites
  - `1000+`: Enterprise crawling
- **Cost Calculation**:
  - AI mode: `max_pages × 10` credits
  - Markdown mode: `max_pages × 2` credits

### `same_domain_only`
**Used in**: smartcrawler_initiate

- **Type**: `Optional[bool]`
- **Default**: `true`
- **Purpose**: Control cross-domain crawling
- **Options**:
  - `true`: Stay within same domain (recommended)
  - `false`: Allow external domains (use with caution)
- **Best Practices**:
  - Use `true` for focused crawling
  - Set `max_pages` when using `false`
  - Consider crawling scope carefully

---

## 🔄 Search Parameters

### `num_results`
**Used in**: searchscraper

- **Type**: `Optional[int]`
- **Default**: 3 websites
- **Range**: 1-20 (recommended ≤10)
- **Cost**: `num_results × 10` credits
- **Examples**:
  - `1`: Quick lookup (10 credits)
  - `3`: Standard research (30 credits)
  - `5`: Comprehensive (50 credits)
  - `10`: Extensive analysis (100 credits)

---

## 🤖 Agentic Automation Parameters

### `steps`
**Used in**: agentic_scrapper

- **Type**: `Optional[Union[str, List[str]]]`
- **Purpose**: Sequential workflow instructions
- **Formats**:
  - List: `['Click search', 'Enter term', 'Extract results']`
  - JSON string: `'["Step 1", "Step 2", "Step 3"]'`
- **Best Practices**:
  - Break complex actions into simple steps
  - Be specific about UI elements
  - Include wait/loading steps
  - Order logically

### `ai_extraction`
**Used in**: agentic_scrapper

- **Type**: `Optional[bool]`
- **Default**: `true`
- **Purpose**: Control extraction intelligence
- **Options**:
  - `true`: Advanced AI extraction (recommended)
  - `false`: Simpler, faster extraction
- **Trade-offs**:
  - `true`: Better accuracy, slower processing
  - `false`: Faster execution, less accurate

### `persistent_session`
**Used in**: agentic_scrapper

- **Type**: `Optional[bool]`
- **Default**: `false`
- **Purpose**: Maintain session state between steps
- **When to Use `true`**:
  - Login flows
  - Shopping cart processes
  - Form wizards with dependencies
- **When to Use `false`**:
  - Simple data extraction
  - Independent actions
  - Public content scraping

### `timeout_seconds`
**Used in**: agentic_scrapper

- **Type**: `Optional[float]`
- **Default**: 120.0 (2 minutes)
- **Recommended Ranges**:
  - `60-120`: Simple workflows (2-5 steps)
  - `180-300`: Medium complexity (5-10 steps)
  - `300-600`: Complex workflows (10+ steps)
  - `600+`: Very complex workflows
- **Considerations**:
  - Include page load times
  - Factor in network latency
  - Allow for AI processing time

---

## 💰 Credit Cost Summary

| Tool | Base Cost | Additional Costs |
|------|-----------|------------------|
| `markdownify` | 2 credits | None |
| `smartscraper` | 10 credits | +10 per additional page |
| `searchscraper` | 30 credits (3 sites) | +10 per additional site |
| `smartcrawler` | 2-10 credits/page | Depends on extraction mode |
| `scrape` | 1 credit | None |
| `sitemap` | 1 credit | None |
| `agentic_scrapper` | Variable | Based on complexity |

---

## ⚠️ Common Parameter Mistakes

### URL Formatting
- ❌ `example.com` → ✅ `https://example.com`
- ❌ `ftp://site.com` → ✅ `https://site.com`

### Mutually Exclusive Parameters
- ❌ Setting both `website_url` and `website_html`
- ✅ Choose one input source only

### Range Violations
- ❌ `number_of_scrolls: 100` → ✅ `number_of_scrolls: 10`
- ❌ `total_pages: 1000` → ✅ `total_pages: 100`

### JSON Schema Errors
- ❌ Invalid JSON string format
- ✅ Valid JSON or dictionary format

### Timeout Issues
- ❌ `timeout_seconds: 30` for complex workflows
- ✅ `timeout_seconds: 300` for complex workflows

---

## 🎯 Parameter Selection Guide

### For Simple Content Extraction
```
Tool: markdownify or smartscraper
Parameters: website_url, user_prompt (if smartscraper)
```

### For Dynamic Content
```
Tool: smartscraper or scrape
Parameters: render_heavy_js=true, stealth=true (if needed)
```

### For Multi-Page Content
```
Tool: smartcrawler_initiate
Parameters: max_pages, depth, extraction_mode
```

### For Research Tasks
```
Tool: searchscraper
Parameters: num_results, user_prompt
```

### For Complex Automation
```
Tool: agentic_scrapper
Parameters: steps, persistent_session, timeout_seconds
```

---

## 📚 Additional Resources

- **Tool Comparison**: Use `scrapegraph://tools/comparison` resource
- **Use Cases**: Check `scrapegraph://examples/use-cases` resource
- **API Status**: Monitor `scrapegraph://api/status` resource
- **Quick Examples**: See prompt `quick_start_examples`

---

*Last Updated: November 2024*
*For the most current parameter information, refer to individual tool documentation.*
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
        website_url (str): The complete URL of the webpage to convert to markdown format.
            - Must include protocol (http:// or https://)
            - Supports most web content types (HTML, articles, documentation)
            - Works with both static and dynamic content
            - Examples:
              * https://example.com/page
              * https://docs.python.org/3/tutorial/
              * https://github.com/user/repo/README.md
            - Invalid examples:
              * example.com (missing protocol)
              * ftp://example.com (unsupported protocol)
              * localhost:3000 (missing protocol)

    Returns:
        Dictionary containing:
        - markdown: The converted markdown content as a string
        - metadata: Additional information about the conversion (title, description, etc.)
        - status: Success/error status of the operation
        - credits_used: Number of credits consumed (always 2 for this operation)

    Raises:
        ValueError: If website_url is malformed or missing protocol
        HTTPError: If the webpage cannot be accessed or returns an error
        TimeoutError: If the webpage takes too long to load (>120 seconds)
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
    structured data from web content. Supports three input modes: URL scraping. Ideal for extracting product information, contact details,
    article metadata, or any structured content. Costs 10 credits per page. Read-only operation.

    Args:
        user_prompt (str): Natural language instructions describing what data to extract.
            - Be specific about the fields you want for better results
            - Use clear, descriptive language about the target data
            - Examples:
              * "Extract product name, price, description, and availability status"
              * "Find all contact methods: email addresses, phone numbers, and social media links"
              * "Get article title, author, publication date, and summary"
              * "Extract all job listings with title, company, location, and salary"
            - Tips for better results:
              * Specify exact field names you want
              * Mention data types (numbers, dates, URLs, etc.)
              * Include context about where data might be located

        website_url (Optional[str]): The complete URL of the webpage to scrape.
            - Mutually exclusive with website_html and website_markdown
            - Must include protocol (http:// or https://)
            - Supports dynamic and static content
            - Examples:
              * https://example.com/products/item
              * https://news.site.com/article/123
              * https://company.com/contact
            - Default: None (must provide one of the three input sources)

        website_html (Optional[str]): Raw HTML content to process locally.
            - Mutually exclusive with website_url and website_markdown
            - Maximum size: 2MB
            - Useful for processing pre-fetched or generated HTML
            - Use when you already have HTML content from another source
            - Example: "<html><body><h1>Title</h1><p>Content</p></body></html>"
            - Default: None

        website_markdown (Optional[str]): Markdown content to process locally.
            - Mutually exclusive with website_url and website_html
            - Maximum size: 2MB
            - Useful for extracting from markdown documents or converted content
            - Works well with documentation, README files, or converted web content
            - Example: "# Title\n\n## Section\n\nContent here..."
            - Default: None

        output_schema (Optional[Union[str, Dict]]): JSON schema defining expected output structure.
            - Can be provided as a dictionary or JSON string
            - Helps ensure consistent, structured output format
            - Optional but recommended for complex extractions
            - IMPORTANT: Must include a "required" field (can be empty array [] if no fields are required)
            - Examples:
              * As dict: {'type': 'object', 'properties': {'title': {'type': 'string'}, 'price': {'type': 'number'}}, 'required': []}
              * As JSON string: '{"type": "object", "properties": {"name": {"type": "string"}}, "required": []}'
              * For arrays: {'type': 'array', 'items': {'type': 'object', 'properties': {...}, 'required': []}, 'required': []}
              * With required fields: {'type': 'object', 'properties': {'name': {'type': 'string'}, 'email': {'type': 'string'}}, 'required': ['name', 'email']}
            - Note: If "required" field is missing, it will be automatically added as an empty array []
            - Default: None (AI will infer structure from prompt)

        number_of_scrolls (Optional[int]): Number of infinite scrolls to perform before scraping.
            - Range: 0-50 scrolls
            - Default: 0 (no scrolling)
            - Useful for dynamically loaded content (lazy loading, infinite scroll)
            - Each scroll waits for content to load before continuing
            - Examples:
              * 0: Static content, no scrolling needed
              * 3: Social media feeds, product listings
              * 10: Long articles, extensive product catalogs
            - Note: Increases processing time proportionally

        total_pages (Optional[int]): Number of pages to process for pagination.
            - Range: 1-100 pages
            - Default: 1 (single page only)
            - Automatically follows pagination links when available
            - Useful for multi-page listings, search results, catalogs
            - Examples:
              * 1: Single page extraction
              * 5: First 5 pages of search results
              * 20: Comprehensive catalog scraping
            - Note: Each page counts toward credit usage (10 credits × pages)

        render_heavy_js (Optional[bool]): Enable heavy JavaScript rendering for dynamic sites.
            - Default: false
            - Set to true for Single Page Applications (SPAs), React apps, Vue.js sites
            - Increases processing time but captures client-side rendered content
            - Use when content is loaded dynamically via JavaScript
            - Examples of when to use:
              * React/Angular/Vue applications
              * Sites with dynamic content loading
              * AJAX-heavy interfaces
              * Content that appears after page load
            - Note: Significantly increases processing time (30-60 seconds vs 5-15 seconds)

        stealth (Optional[bool]): Enable stealth mode to avoid bot detection.
            - Default: false
            - Helps bypass basic anti-scraping measures
            - Uses techniques to appear more like a human browser
            - Useful for sites with bot detection systems
            - Examples of when to use:
              * Sites that block automated requests
              * E-commerce sites with protection
              * Sites that require "human-like" behavior
            - Note: May increase processing time and is not 100% guaranteed

    Returns:
        Dictionary containing:
        - extracted_data: The structured data matching your prompt and optional schema
        - metadata: Information about the extraction process
        - credits_used: Number of credits consumed (10 per page processed)
        - processing_time: Time taken for the extraction
        - pages_processed: Number of pages that were analyzed
        - status: Success/error status of the operation

    Raises:
        ValueError: If no input source provided or multiple sources provided
        HTTPError: If website_url cannot be accessed
        TimeoutError: If processing exceeds timeout limits
        ValidationError: If output_schema is malformed JSON
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

        # Ensure output_schema has a 'required' field if it exists
        if normalized_schema is not None:
            if "required" not in normalized_schema:
                normalized_schema["required"] = []

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
        user_prompt (str): Search query or natural language instructions for information to find.
            - Can be a simple search query or detailed extraction instructions
            - The AI will search the web and extract relevant data from found pages
            - Be specific about what information you want extracted
            - Examples:
              * "Find latest AI research papers published in 2024 with author names and abstracts"
              * "Search for Python web scraping tutorials with ratings and difficulty levels"
              * "Get current cryptocurrency prices and market caps for top 10 coins"
              * "Find contact information for tech startups in San Francisco"
              * "Search for job openings for data scientists with salary information"
            - Tips for better results:
              * Include specific fields you want extracted
              * Mention timeframes or filters (e.g., "latest", "2024", "top 10")
              * Specify data types needed (prices, dates, ratings, etc.)

        num_results (Optional[int]): Number of websites to search and extract data from.
            - Default: 3 websites (costs 30 credits total)
            - Range: 1-20 websites (recommended to stay under 10 for cost efficiency)
            - Each website costs 10 credits, so total cost = num_results × 10
            - Examples:
              * 1: Quick single-source lookup (10 credits)
              * 3: Standard research (30 credits) - good balance of coverage and cost
              * 5: Comprehensive research (50 credits)
              * 10: Extensive analysis (100 credits)
            - Note: More results provide broader coverage but increase costs and processing time

        number_of_scrolls (Optional[int]): Number of infinite scrolls per searched webpage.
            - Default: 0 (no scrolling on search result pages)
            - Range: 0-10 scrolls per page
            - Useful when search results point to pages with dynamic content loading
            - Each scroll waits for content to load before continuing
            - Examples:
              * 0: Static content pages, news articles, documentation
              * 2: Social media pages, product listings with lazy loading
              * 5: Extensive feeds, long-form content with infinite scroll
            - Note: Increases processing time significantly (adds 5-10 seconds per scroll per page)

    Returns:
        Dictionary containing:
        - search_results: Array of extracted data from each website found
        - sources: List of URLs that were searched and processed
        - total_websites_processed: Number of websites successfully analyzed
        - credits_used: Total credits consumed (num_results × 10)
        - processing_time: Total time taken for search and extraction
        - search_query_used: The actual search query sent to search engines
        - metadata: Additional information about the search process

    Raises:
        ValueError: If user_prompt is empty or num_results is out of range
        HTTPError: If search engines are unavailable or return errors
        TimeoutError: If search or extraction process exceeds timeout limits
        RateLimitError: If too many requests are made in a short time period

    Note:
        - Results may vary between calls due to changing web content (non-idempotent)
        - Search engines may return different results over time
        - Some websites may be inaccessible or block automated access
        - Processing time increases with num_results and number_of_scrolls
        - Consider using smartscraper on specific URLs if you know the target sites
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
        url (str): The starting URL to begin crawling from.
            - Must include protocol (http:// or https://)
            - The crawler will discover and process linked pages from this starting point
            - Should be a page with links to other pages you want to crawl
            - Examples:
              * https://docs.example.com (documentation site root)
              * https://blog.company.com (blog homepage)
              * https://example.com/products (product category page)
              * https://news.site.com/category/tech (news section)
            - Best practices:
              * Use homepage or main category pages as starting points
              * Ensure the starting page has links to content you want to crawl
              * Consider site structure when choosing the starting URL

        prompt (Optional[str]): AI prompt for data extraction.
            - REQUIRED when extraction_mode is 'ai'
            - Ignored when extraction_mode is 'markdown'
            - Describes what data to extract from each crawled page
            - Applied consistently across all discovered pages
            - Examples:
              * "Extract API endpoint name, method, parameters, and description"
              * "Get article title, author, publication date, and summary"
              * "Find product name, price, description, and availability"
              * "Extract job title, company, location, salary, and requirements"
            - Tips for better results:
              * Be specific about fields you want from each page
              * Consider that different pages may have different content structures
              * Use general terms that apply across multiple page types

        extraction_mode (str): Extraction mode for processing crawled pages.
            - Default: "ai"
            - Options:
              * "ai": AI-powered structured data extraction (10 credits per page)
                - Uses the prompt to extract specific data from each page
                - Returns structured JSON data
                - More expensive but provides targeted information
                - Best for: Data collection, research, structured analysis
              * "markdown": Simple markdown conversion (2 credits per page)
                - Converts each page to clean markdown format
                - No AI processing, just content conversion
                - More cost-effective for content archival
                - Best for: Documentation backup, content migration, reading
            - Cost comparison:
              * AI mode: 50 pages = 500 credits
              * Markdown mode: 50 pages = 100 credits

        depth (Optional[int]): Maximum depth of link traversal from the starting URL.
            - Default: unlimited (will follow links until max_pages or no more links)
            - Depth levels:
              * 0: Only the starting URL (no link following)
              * 1: Starting URL + pages directly linked from it
              * 2: Starting URL + direct links + links from those pages
              * 3+: Continues following links to specified depth
            - Examples:
              * 1: Crawl blog homepage + all blog posts
              * 2: Crawl docs homepage + category pages + individual doc pages
              * 3: Deep crawling for comprehensive site coverage
            - Considerations:
              * Higher depth can lead to exponential page growth
              * Use with max_pages to control scope and cost
              * Consider site structure when setting depth

        max_pages (Optional[int]): Maximum number of pages to crawl in total.
            - Default: unlimited (will crawl until no more links or depth limit)
            - Recommended ranges:
              * 10-20: Testing and small sites
              * 50-100: Medium sites and focused crawling
              * 200-500: Large sites and comprehensive analysis
              * 1000+: Enterprise-level crawling (high cost)
            - Cost implications:
              * AI mode: max_pages × 10 credits
              * Markdown mode: max_pages × 2 credits
            - Examples:
              * 10: Quick site sampling (20-100 credits)
              * 50: Standard documentation crawl (100-500 credits)
              * 200: Comprehensive site analysis (400-2000 credits)
            - Note: Crawler stops when this limit is reached, regardless of remaining links

        same_domain_only (Optional[bool]): Whether to crawl only within the same domain.
            - Default: true (recommended for most use cases)
            - Options:
              * true: Only crawl pages within the same domain as starting URL
                - Prevents following external links
                - Keeps crawling focused on the target site
                - Reduces risk of crawling unrelated content
                - Example: Starting at docs.example.com only crawls docs.example.com pages
              * false: Allow crawling external domains
                - Follows links to other domains
                - Can lead to very broad crawling scope
                - May crawl unrelated or unwanted content
                - Use with caution and appropriate max_pages limit
            - Recommendations:
              * Use true for focused site crawling
              * Use false only when you specifically need cross-domain data
              * Always set max_pages when using false to prevent runaway crawling

    Returns:
        Dictionary containing:
        - request_id: Unique identifier for this crawl operation (use with smartcrawler_fetch_results)
        - status: Initial status of the crawl request ("initiated" or "processing")
        - estimated_cost: Estimated credit cost based on parameters (actual cost may vary)
        - crawl_parameters: Summary of the crawling configuration
        - estimated_time: Rough estimate of processing time
        - next_steps: Instructions for retrieving results

    Raises:
        ValueError: If URL is malformed, prompt is missing for AI mode, or parameters are invalid
        HTTPError: If the starting URL cannot be accessed
        RateLimitError: If too many crawl requests are initiated too quickly

    Note:
        - This operation is asynchronous and may take several minutes to complete
        - Use smartcrawler_fetch_results with the returned request_id to get results
        - Keep polling smartcrawler_fetch_results until status is "completed"
        - Actual pages crawled may be less than max_pages if fewer links are found
        - Processing time increases with max_pages, depth, and extraction_mode complexity
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
        website_url (str): The complete URL of the webpage to scrape.
            - Must include protocol (http:// or https://)
            - Returns raw HTML content of the page
            - Works with both static and dynamic websites
            - Examples:
              * https://example.com/page
              * https://api.example.com/docs
              * https://news.site.com/article/123
              * https://app.example.com/dashboard (may need render_heavy_js=true)
            - Supported protocols: HTTP, HTTPS
            - Invalid examples:
              * example.com (missing protocol)
              * ftp://example.com (unsupported protocol)

        render_heavy_js (Optional[bool]): Enable full JavaScript rendering for dynamic content.
            - Default: false (faster, lower cost, works for most static sites)
            - Set to true for sites that require JavaScript execution to display content
            - When to use true:
              * Single Page Applications (React, Angular, Vue.js)
              * Sites with dynamic content loading via AJAX
              * Content that appears only after JavaScript execution
              * Interactive web applications
              * Sites where initial HTML is mostly empty
            - When to use false (default):
              * Static websites and blogs
              * Server-side rendered content
              * Traditional HTML pages
              * News articles and documentation
              * When you need faster processing
            - Performance impact:
              * false: 2-5 seconds processing time
              * true: 15-30 seconds processing time (waits for JS execution)
            - Cost: Same (1 credit) regardless of render_heavy_js setting

    Returns:
        Dictionary containing:
        - html_content: The raw HTML content of the page as a string
        - page_title: Extracted page title if available
        - status_code: HTTP response status code (200 for success)
        - final_url: Final URL after any redirects
        - content_length: Size of the HTML content in bytes
        - processing_time: Time taken to fetch and process the page
        - javascript_rendered: Whether JavaScript rendering was used
        - credits_used: Number of credits consumed (always 1)

    Raises:
        ValueError: If website_url is malformed or missing protocol
        HTTPError: If the webpage returns an error status (404, 500, etc.)
        TimeoutError: If the page takes too long to load
        ConnectionError: If the website cannot be reached

    Use Cases:
        - Getting raw HTML for custom parsing
        - Checking page structure before using other tools
        - Fetching content for offline processing
        - Debugging website content issues
        - Pre-processing before AI extraction

    Note:
        - This tool returns raw HTML without any AI processing
        - Use smartscraper for structured data extraction
        - Use markdownify for clean, readable content
        - Consider render_heavy_js=true if initial results seem incomplete
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
        website_url (str): The base URL of the website to extract sitemap from.
            - Must include protocol (http:// or https://)
            - Should be the root domain or main section you want to map
            - The tool will discover all accessible pages from this starting point
            - Examples:
              * https://example.com (discover entire website structure)
              * https://docs.example.com (map documentation site)
              * https://blog.company.com (discover all blog pages)
              * https://shop.example.com (map e-commerce structure)
            - Best practices:
              * Use root domain (https://example.com) for complete site mapping
              * Use subdomain (https://docs.example.com) for focused mapping
              * Ensure the URL is accessible and doesn't require authentication
            - Discovery methods:
              * Checks for robots.txt and sitemap.xml files
              * Crawls navigation links and menus
              * Discovers pages through internal link analysis
              * Identifies common URL patterns and structures

    Returns:
        Dictionary containing:
        - discovered_urls: List of all URLs found on the website
        - site_structure: Hierarchical organization of pages and sections
        - url_categories: URLs grouped by type (pages, images, documents, etc.)
        - total_pages: Total number of pages discovered
        - subdomains: List of subdomains found (if any)
        - sitemap_sources: Sources used for discovery (sitemap.xml, robots.txt, crawling)
        - page_types: Breakdown of different content types found
        - depth_analysis: URL organization by depth from root
        - external_links: Links pointing to external domains (if found)
        - processing_time: Time taken to complete the discovery
        - credits_used: Number of credits consumed (always 1)

    Raises:
        ValueError: If website_url is malformed or missing protocol
        HTTPError: If the website cannot be accessed or returns errors
        TimeoutError: If the discovery process takes too long
        ConnectionError: If the website cannot be reached

    Use Cases:
        - Planning comprehensive crawling operations
        - Understanding website architecture and organization
        - Discovering all available content before targeted scraping
        - SEO analysis and site structure optimization
        - Content inventory and audit preparation
        - Identifying pages for bulk processing operations

    Best Practices:
        - Run sitemap before using smartcrawler_initiate for better planning
        - Use results to set appropriate max_pages and depth parameters
        - Check discovered URLs to understand site organization
        - Identify high-value pages for targeted extraction
        - Use for cost estimation before large crawling operations

    Note:
        - Very cost-effective at only 1 credit per request
        - Results may vary based on site structure and accessibility
        - Some pages may require authentication and won't be discovered
        - Large sites may have thousands of URLs - consider filtering results
        - Use discovered URLs as input for other scraping tools
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
        url (str): The target website URL where the agentic scraping workflow should start.
            - Must include protocol (http:// or https://)
            - Should be the starting page for your automation workflow
            - The agent will begin its actions from this URL
            - Examples:
              * https://example.com/search (start at search page)
              * https://shop.example.com/login (begin with login flow)
              * https://app.example.com/dashboard (start at main interface)
              * https://forms.example.com/contact (begin at form page)
            - Considerations:
              * Choose a starting point that makes sense for your workflow
              * Ensure the page is publicly accessible or handle authentication
              * Consider the logical flow of actions from this starting point

        user_prompt (Optional[str]): High-level instructions for what the agent should accomplish.
            - Describes the overall goal and desired outcome of the automation
            - Should be clear and specific about what you want to achieve
            - Works in conjunction with the steps parameter for detailed guidance
            - Examples:
              * "Navigate to the search page, search for laptops, and extract the top 5 results with prices"
              * "Fill out the contact form with sample data and submit it"
              * "Login to the dashboard and extract all recent notifications"
              * "Browse the product catalog and collect information about all items"
              * "Navigate through the multi-step checkout process and capture each step"
            - Tips for better results:
              * Be specific about the end goal
              * Mention what data you want extracted
              * Include context about the expected workflow
              * Specify any particular elements or sections to focus on

        output_schema (Optional[Union[str, Dict]]): Desired output structure for extracted data.
            - Can be provided as a dictionary or JSON string
            - Defines the format and structure of the final extracted data
            - Helps ensure consistent, predictable output format
            - IMPORTANT: Must include a "required" field (can be empty array [] if no fields are required)
            - Examples:
              * Simple object: {'type': 'object', 'properties': {'title': {'type': 'string'}, 'price': {'type': 'number'}}, 'required': []}
              * Array of objects: {'type': 'array', 'items': {'type': 'object', 'properties': {'name': {'type': 'string'}, 'value': {'type': 'string'}}, 'required': []}, 'required': []}
              * Complex nested: {'type': 'object', 'properties': {'products': {'type': 'array', 'items': {...}}, 'total_count': {'type': 'number'}}, 'required': []}
              * As JSON string: '{"type": "object", "properties": {"results": {"type": "array"}}, "required": []}'
              * With required fields: {'type': 'object', 'properties': {'id': {'type': 'string'}, 'name': {'type': 'string'}}, 'required': ['id']}
            - Note: If "required" field is missing, it will be automatically added as an empty array []
            - Default: None (agent will infer structure from prompt and steps)

        steps (Optional[Union[str, List[str]]]): Step-by-step instructions for the agent.
            - Can be provided as a list of strings or JSON array string
            - Provides detailed, sequential instructions for the automation workflow
            - Each step should be a clear, actionable instruction
            - Examples as list:
              * ['Click the search button', 'Enter "laptops" in the search box', 'Press Enter', 'Wait for results to load', 'Extract product information']
              * ['Fill in email field with test@example.com', 'Fill in password field', 'Click login button', 'Navigate to profile page']
            - Examples as JSON string:
              * '["Open navigation menu", "Click on Products", "Select category filters", "Extract all product data"]'
            - Best practices:
              * Break complex actions into simple steps
              * Be specific about UI elements (button text, field names, etc.)
              * Include waiting/loading steps when necessary
              * Specify extraction points clearly
              * Order steps logically for the workflow

        ai_extraction (Optional[bool]): Enable AI-powered extraction mode for intelligent data parsing.
            - Default: true (recommended for most use cases)
            - Options:
              * true: Uses advanced AI to intelligently extract and structure data
                - Better at handling complex page layouts
                - Can adapt to different content structures
                - Provides more accurate data extraction
                - Recommended for most scenarios
              * false: Uses simpler extraction methods
                - Faster processing but less intelligent
                - May miss complex or nested data
                - Use when speed is more important than accuracy
            - Performance impact:
              * true: Higher processing time but better results
              * false: Faster execution but potentially less accurate extraction

        persistent_session (Optional[bool]): Maintain session state between steps.
            - Default: false (each step starts fresh)
            - Options:
              * true: Keeps cookies, login state, and session data between steps
                - Essential for authenticated workflows
                - Maintains shopping cart contents, user preferences, etc.
                - Required for multi-step processes that depend on previous actions
                - Use for: Login flows, shopping processes, form wizards
              * false: Each step starts with a clean session
                - Faster and simpler for independent actions
                - No state carried between steps
                - Use for: Simple data extraction, public content scraping
            - Examples when to use true:
              * Login → Navigate to protected area → Extract data
              * Add items to cart → Proceed to checkout → Extract order details
              * Multi-step form completion with session dependencies

        timeout_seconds (Optional[float]): Maximum time to wait for the entire workflow.
            - Default: 120 seconds (2 minutes)
            - Recommended ranges:
              * 60-120: Simple workflows (2-5 steps)
              * 180-300: Medium complexity (5-10 steps)
              * 300-600: Complex workflows (10+ steps or slow sites)
              * 600+: Very complex or slow-loading workflows
            - Considerations:
              * Include time for page loads, form submissions, and processing
              * Factor in network latency and site response times
              * Allow extra time for AI processing and extraction
              * Balance between thoroughness and efficiency
            - Examples:
              * 60.0: Quick single-page data extraction
              * 180.0: Multi-step form filling and submission
              * 300.0: Complex navigation and comprehensive data extraction
              * 600.0: Extensive workflows with multiple page interactions

    Returns:
        Dictionary containing:
        - extracted_data: The structured data matching your prompt and optional schema
        - workflow_log: Detailed log of all actions performed by the agent
        - pages_visited: List of URLs visited during the workflow
        - actions_performed: Summary of interactions (clicks, form fills, navigations)
        - execution_time: Total time taken for the workflow
        - steps_completed: Number of steps successfully executed
        - final_page_url: The URL where the workflow ended
        - session_data: Session information if persistent_session was enabled
        - credits_used: Number of credits consumed (varies by complexity)
        - status: Success/failure status with any error details

    Raises:
        ValueError: If URL is malformed or required parameters are missing
        TimeoutError: If the workflow exceeds the specified timeout
        NavigationError: If the agent cannot navigate to required pages
        InteractionError: If the agent cannot interact with specified elements
        ExtractionError: If data extraction fails or returns invalid results

    Use Cases:
        - Automated form filling and submission
        - Multi-step checkout processes
        - Login-protected content extraction
        - Interactive search and filtering workflows
        - Complex navigation scenarios requiring user simulation
        - Data collection from dynamic, JavaScript-heavy applications

    Best Practices:
        - Start with simple workflows and gradually increase complexity
        - Use specific element identifiers in steps (button text, field labels)
        - Include appropriate wait times for page loads and dynamic content
        - Test with persistent_session=true for authentication-dependent workflows
        - Set realistic timeouts based on workflow complexity
        - Provide clear, sequential steps that build on each other
        - Use output_schema to ensure consistent data structure

    Note:
        - This tool can perform actions on websites (non-read-only)
        - Results may vary between runs due to dynamic content (non-idempotent)
        - Credit cost varies based on workflow complexity and execution time
        - Some websites may have anti-automation measures that could affect success
        - Consider using simpler tools (smartscraper, markdownify) for basic extraction needs
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

    # Ensure output_schema has a 'required' field if it exists
    if normalized_schema is not None:
        if "required" not in normalized_schema:
            normalized_schema["required"] = []

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
    """Run the ScapeGraph MCP server.

    Supports two transport modes:
    - stdio (default): For local use with Claude Desktop, Cursor, etc.
    - http: For remote deployment on Render, Koyeb, etc.

    Set MCP_TRANSPORT=http environment variable for remote deployment.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    try:
        if transport == "http":
            # Remote deployment mode (Render, Koyeb, etc.)
            host = os.getenv("HOST", "0.0.0.0")
            port = int(os.getenv("PORT", "8000"))
            logger.info(f"Starting ScapeGraph MCP server in HTTP mode on {host}:{port}")
            print(f"Starting ScapeGraph MCP server in HTTP mode on {host}:{port}")
            mcp.run(transport="http", host=host, port=port)
        else:
            # Local stdio mode (Claude Desktop, Cursor, etc.)
            server_path = os.path.abspath(__file__)
            logger.info(f"Starting ScapeGraph MCP server from local codebase: {server_path}")
            print("Starting ScapeGraph MCP server (local codebase)")
            mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        print(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    main()