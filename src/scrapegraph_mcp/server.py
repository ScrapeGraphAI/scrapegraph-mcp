#!/usr/bin/env python3
"""
MCP server for ScapeGraph API integration (API v2).

Aligned with scrapegraph-py v2 ([ScrapeGraphAI/scrapegraph-py#82](https://github.com/ScrapeGraphAI/scrapegraph-py/pull/82)):
- markdownify: Page content via POST /scrape (markdown by default)
- smartscraper: Structured extraction via POST /extract (URL input only)
- searchscraper: Web search via POST /search
- smartcrawler_initiate / smartcrawler_fetch_results: Async crawl via /crawl (markdown or html only)
- crawl_stop / crawl_resume: Control running crawl jobs
- scrape: Format-specific fetch (markdown, html, screenshot, branding)
- credits / sgai_history: Account usage and request history
- monitor_*: Scheduled extraction jobs (replaces legacy scheduled jobs)

Removed on v2 (no API equivalent): sitemap, agentic_scrapper, markdownify_status, smartscraper_status.
Optional base URL override: SCRAPEGRAPH_API_BASE_URL (default https://api.scrapegraphai.com/api/v2).

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
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

import httpx
from fastmcp import Context, FastMCP
from pydantic import AliasChoices, BaseModel, Field
from smithery.decorators import smithery
from starlette.requests import Request
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MCP_SERVER_VERSION = "2.0.0"
DEFAULT_API_BASE_URL = "https://api.scrapegraphai.com/api/v2"


def _api_base_url() -> str:
    return os.environ.get("SCRAPEGRAPH_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


class ScapeGraphClient:
    """HTTP client for ScrapeGraphAI API v2 (see scrapegraph-py PR #82)."""

    def __init__(self, api_key: str, base_url: Optional[str] = None) -> None:
        self.api_key = api_key
        self.base_url = (base_url or _api_base_url()).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "SGAI-APIKEY": api_key,
            "Content-Type": "application/json",
            "accept": "application/json",
            "X-SDK-Version": f"scrapegraph-mcp@{MCP_SERVER_VERSION}",
        }
        self.client = httpx.Client(timeout=httpx.Timeout(120.0))

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise Exception(f"Error {response.status_code}: {response.text}")
        if not response.content:
            return {"ok": True}
        try:
            out = response.json()
            if isinstance(out, dict):
                return out
            return {"result": out}
        except json.JSONDecodeError:
            return {"raw": response.text}

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        r = self.client.request(method, url, headers=self.headers, json=json_body, params=params)
        return self._parse_response(r)

    def _fetch_config(
        self,
        *,
        mode: Optional[str] = None,
        timeout: Optional[int] = None,
        wait: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        country: Optional[str] = None,
        scrolls: Optional[int] = None,
        mock: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        cfg: Dict[str, Any] = {}
        if mode is not None:
            cfg["mode"] = mode
        if timeout is not None:
            cfg["timeout"] = timeout
        if wait is not None:
            cfg["wait"] = wait
        if headers is not None:
            cfg["headers"] = headers
        if cookies is not None:
            cfg["cookies"] = cookies
        if country is not None:
            cfg["country"] = country
        if scrolls is not None:
            cfg["scrolls"] = scrolls
        if mock is not None:
            cfg["mock"] = mock
        return cfg or None

    def scrape_v2(
        self,
        website_url: str,
        output_format: str = "markdown",
        *,
        fetch_config_dict: Optional[Dict[str, Any]] = None,
        screenshot_full_page: bool = False,
    ) -> Dict[str, Any]:
        fmt = output_format.lower()
        body: Dict[str, Any] = {"url": website_url}
        if fmt == "markdown":
            body["markdown"] = {"mode": "normal"}
        elif fmt == "html":
            body["html"] = {"mode": "normal"}
        elif fmt == "screenshot":
            body["screenshot"] = {"full_page": screenshot_full_page}
        elif fmt == "branding":
            body["branding"] = {}
        else:
            raise ValueError(
                f"Invalid output_format {output_format!r}; use markdown, html, screenshot, or branding"
            )
        if fetch_config_dict:
            body["fetch_config"] = fetch_config_dict
        return self._request("POST", "/scrape", json_body=body)

    def markdownify(
        self,
        website_url: str,
        mode: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        country: Optional[str] = None,
        timeout: Optional[int] = None,
        wait: Optional[int] = None,
        scrolls: Optional[int] = None,
        mock: Optional[bool] = None,
    ) -> Dict[str, Any]:
        fc = self._fetch_config(
            mode=mode, timeout=timeout, wait=wait, headers=headers,
            cookies=cookies, country=country, scrolls=scrolls, mock=mock,
        )
        return self.scrape_v2(website_url, "markdown", fetch_config_dict=fc)

    def extract(
        self,
        user_prompt: str,
        website_url: str,
        output_schema: Optional[Dict[str, Any]] = None,
        fetch_config_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"url": website_url, "prompt": user_prompt}
        if output_schema is not None:
            body["output_schema"] = output_schema
        if fetch_config_dict:
            body["fetch_config"] = fetch_config_dict
        return self._request("POST", "/extract", json_body=body)

    def smartscraper(
        self,
        user_prompt: str,
        website_url: str,
        output_schema: Optional[Dict[str, Any]] = None,
        fetch_config_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.extract(user_prompt, website_url, output_schema, fetch_config_dict)

    def search_api(
        self,
        query: str,
        num_results: Optional[int] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        n = 5 if num_results is None else num_results
        n = max(3, min(20, n))
        body: Dict[str, Any] = {"query": query, "num_results": n}
        if output_schema is not None:
            body["output_schema"] = output_schema
        return self._request("POST", "/search", json_body=body)

    def searchscraper(
        self,
        user_prompt: str,
        num_results: Optional[int] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.search_api(user_prompt, num_results=num_results, output_schema=output_schema)

    def scrape(
        self,
        website_url: str,
        output_format: str = "markdown",
        screenshot_full_page: bool = False,
        fetch_config_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.scrape_v2(
            website_url,
            output_format,
            fetch_config_dict=fetch_config_dict,
            screenshot_full_page=screenshot_full_page,
        )

    def crawl_start(
        self,
        url: str,
        *,
        depth: int = 2,
        max_pages: int = 10,
        crawl_format: str = "markdown",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        fetch_config_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cf = crawl_format.lower()
        if cf not in ("markdown", "html"):
            raise ValueError("crawl_format must be 'markdown' or 'html'")
        body: Dict[str, Any] = {
            "url": url,
            "depth": depth,
            "max_pages": max_pages,
            "format": cf,
        }
        if include_patterns is not None:
            body["include_patterns"] = include_patterns
        if exclude_patterns is not None:
            body["exclude_patterns"] = exclude_patterns
        if fetch_config_dict:
            body["fetch_config"] = fetch_config_dict
        return self._request("POST", "/crawl", json_body=body)

    def smartcrawler_fetch_results(self, request_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/crawl/{request_id}")

    def crawl_stop(self, crawl_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/crawl/{crawl_id}/stop")

    def crawl_resume(self, crawl_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/crawl/{crawl_id}/resume")

    def credits(self) -> Dict[str, Any]:
        return self._request("GET", "/credits")

    def history(
        self,
        endpoint: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        params = {
            k: v
            for k, v in {
                "endpoint": endpoint,
                "status": status_filter,
                "limit": limit,
                "offset": offset,
            }.items()
            if v is not None
        }
        return self._request("GET", "/history", params=params or None)

    def monitor_create(
        self,
        name: str,
        url: str,
        prompt: str,
        interval: str,
        output_schema: Optional[Dict[str, Any]] = None,
        fetch_config_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "name": name,
            "url": url,
            "prompt": prompt,
            "interval": interval,
        }
        if output_schema is not None:
            body["output_schema"] = output_schema
        if fetch_config_dict:
            body["fetch_config"] = fetch_config_dict
        return self._request("POST", "/monitor", json_body=body)

    def monitor_list(self) -> Dict[str, Any]:
        return self._request("GET", "/monitor")

    def monitor_get(self, monitor_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/monitor/{monitor_id}")

    def monitor_pause(self, monitor_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/monitor/{monitor_id}/pause")

    def monitor_resume(self, monitor_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/monitor/{monitor_id}/resume")

    def monitor_delete(self, monitor_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/monitor/{monitor_id}")

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
        api_key = headers.get("x-api-key")
        if api_key:
            logger.info("API key retrieved from X-API-Key header")
            return str(api_key)
    except LookupError:
        # Not in HTTP context, try session config (Smithery/stdio mode)
        pass

    # Try session config (for Smithery/stdio deployments)
    if hasattr(ctx, "session_config") and ctx.session_config is not None:
        api_key = getattr(ctx.session_config, "scrapegraph_api_key", None)
        if api_key:
            logger.info("API key retrieved from session config")
            return str(api_key)

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
async def health_check(_request: Request) -> JSONResponse:
    """Health check endpoint for container orchestration and load balancers."""
    return JSONResponse({"status": "healthy", "service": "scrapegraph-mcp"})


# Add prompts to help users interact with the server
@mcp.prompt()
def web_scraping_guide() -> str:
    """
    A comprehensive guide to using ScapeGraph's web scraping tools effectively.

    This prompt provides examples and best practices for each tool in the ScapeGraph MCP server.
    """
    return """# ScapeGraph Web Scraping Guide (API v2)

See [scrapegraph-py#82](https://github.com/ScrapeGraphAI/scrapegraph-py/pull/82) for the upstream SDK migration.

## Core tools
- **markdownify** — `POST /scrape` (markdown output)
- **scrape** — `POST /scrape` (markdown, html, screenshot, branding)
- **smartscraper** — `POST /extract` (URL + prompt; no inline HTML/markdown source on v2)
- **searchscraper** — `POST /search` (query + num_results 3–20)
- **smartcrawler_initiate** / **smartcrawler_fetch_results** — `POST/GET /crawl` (markdown or html crawl only; no per-page AI crawl on v2)
- **crawl_stop** / **crawl_resume** — control a running job
- **credits** — `GET /credits`
- **sgai_history** — `GET /history`
- **monitor_*** — scheduled jobs (`POST/GET/DELETE /monitor`, pause/resume)

## Best practices
1. Use **markdownify** or **scrape** before **smartscraper** when you only need readable text.
2. Multi-page **AI** extraction: run **smartscraper** per URL, or use **monitor_create** on a schedule.
3. Poll **smartcrawler_fetch_results** until the crawl finishes.
4. Override API host with env **SCRAPEGRAPH_API_BASE_URL** if needed (default production v2 base URL).
"""


@mcp.prompt()
def quick_start_examples() -> str:
    """
    Quick start examples for common ScapeGraph use cases.

    Ready-to-use examples for immediate productivity.
    """
    return """# ScapeGraph Quick Start (API v2)

### Extract structured data (single URL)
```
Tool: smartscraper
website_url: https://example.com/product/1
user_prompt: "Extract name, price, and availability"
```

### Markdown snapshot
```
Tool: markdownify
website_url: https://docs.example.com
```

### Search
```
Tool: searchscraper
user_prompt: "Latest Python 3.12 release highlights"
num_results: 5
```

### Multi-page crawl (markdown/html only)
```
Tool: smartcrawler_initiate
url: https://blog.example.com
extraction_mode: "markdown"
max_pages: 15
depth: 2
```
Then poll `smartcrawler_fetch_results` with the returned `id`.

### Credits and history
```
Tool: credits
Tool: sgai_history
limit: 10
```

Auth: `SGAI_API_KEY` or MCP `scrapegraphApiKey`. Optional: `SCRAPEGRAPH_API_BASE_URL`.
"""


# Add resources to expose server capabilities and data
@mcp.resource("scrapegraph://api/status")
def api_status() -> str:
    """
    Current status and capabilities of the ScapeGraph API server.

    Provides real-time information about available tools, credit usage, and server health.
    """
    return """# ScapeGraph API Status (MCP v2)

- **MCP package version**: 2.0.0 (matches [scrapegraph-py#82](https://github.com/ScrapeGraphAI/scrapegraph-py/pull/82) API surface)
- **Default API base**: `https://api.scrapegraphai.com/api/v2` (override with `SCRAPEGRAPH_API_BASE_URL`)
- **Auth headers**: `Authorization: Bearer`, `SGAI-APIKEY`, `X-SDK-Version: scrapegraph-mcp@2.0.0`

## Tools
markdownify, scrape, smartscraper, searchscraper, smartcrawler_initiate, smartcrawler_fetch_results, crawl_stop, crawl_resume, credits, sgai_history, monitor_create, monitor_list, monitor_get, monitor_pause, monitor_resume, monitor_delete

## Removed vs legacy MCP
sitemap, agentic_scrapper, markdownify_status, smartscraper_status — not available on API v2.

Credit costs are determined by the ScrapeGraphAI API; use **credits** to check balance.
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

> **API v2 note:** This document still contains legacy v1-era tool names and parameters in places.
> Trust the live tool schemas in the MCP client and the module docstring in `server.py` for v2.
> New tools: `credits`, `sgai_history`, `crawl_stop`, `crawl_resume`, `monitor_*`. Removed: `sitemap`,
> `agentic_scrapper`, `markdownify_status`, `smartscraper_status`.

## 📋 Complete Parameter Documentation

This guide provides comprehensive documentation for every parameter across all ScapeGraph MCP tools. Use this as your definitive reference for understanding parameter behavior, constraints, and best practices.

---

## 🔧 Common Parameters

### URL Parameters
**Used in**: markdownify, smartscraper, searchscraper, smartcrawler_initiate, scrape, monitor_*, and related v2 tools

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

## 🚀 Fetch/Proxy Parameters

### `mode`
**Used in**: markdownify, scrape, smartscraper, smartcrawler_initiate, monitor_create

- **Type**: `Optional[str]`
- **Default**: `auto`
- **Options**:
  - `"auto"`: Automatically selects the best provider chain
  - `"fast"`: Direct HTTP fetch via impit (fastest, no JS)
  - `"js"`: Headless browser rendering for JS-heavy pages
  - `"direct+stealth"`: Residential proxy with stealth headers (no JS)
  - `"js+stealth"`: JS rendering combined with stealth/residential proxy
- **Performance Impact**:
  - `fast`: 2-5 seconds
  - `js`: 15-30 seconds
  - `direct+stealth`/`js+stealth`: variable, depends on proxy
- **Cost**: Same regardless of setting

### `timeout`
**Used in**: markdownify, scrape, smartscraper, smartcrawler_initiate, monitor_create
- **Type**: `Optional[int]`
- **Range**: 1000-60000 milliseconds
- **Purpose**: Request timeout

### `wait`
**Used in**: markdownify, scrape, smartscraper, smartcrawler_initiate, monitor_create
- **Type**: `Optional[int]`
- **Range**: 0-30000 milliseconds
- **Purpose**: Wait after page load before scraping

### `cookies`
**Used in**: markdownify, scrape, smartscraper, smartcrawler_initiate, monitor_create
- **Type**: `Optional[Dict[str, str]]`
- **Purpose**: Cookies to send with the request

### `country`
**Used in**: markdownify, scrape, smartscraper, smartcrawler_initiate, monitor_create
- **Type**: `Optional[str]`
- **Purpose**: Two-letter country code for geo-located requests (e.g. 'us')

---

## 🔄 Crawling Parameters

### `extraction_mode`
**Used in**: smartcrawler_initiate

- **Type**: `str`
- **Default**: `"markdown"`
- **Options**:
  - `"markdown"`: Markdown conversion (2 credits/page)
  - `"html"`: HTML output
- **Use Cases**:
  - Markdown: Content archival, documentation backup
  - HTML: Full HTML preservation

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
Parameters: mode="js" (or mode="js+stealth" if bot detection is present)
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

> **API v2:** Some rows reference removed tools (`sitemap`, `agentic_scrapper`). See `scrapegraph://api/status`.

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
def markdownify(
    website_url: str,
    ctx: Context,
    mode: Optional[Literal["auto", "fast", "js", "direct+stealth", "js+stealth"]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    country: Optional[str] = None,
    timeout: Optional[int] = None,
    wait: Optional[int] = None,
    scrolls: Optional[int] = None,
    mock: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Convert a webpage into clean, formatted markdown (API v2 POST /scrape).

    Args:
        website_url: URL to convert (must include http:// or https://).
        mode: Fetch/proxy mode controlling how the page is retrieved.
            - auto: Automatically selects the best provider chain (default).
            - fast: Direct HTTP fetch via impit (fastest, no JS).
            - js: Headless browser rendering for JavaScript-heavy pages.
            - direct+stealth: Residential proxy with stealth headers (no JS).
            - js+stealth: JS rendering combined with stealth/residential proxy.
        headers: Custom HTTP headers to send with the request.
        cookies: Cookies to send with the request.
        country: Two-letter country code for geo-located requests (e.g. 'us').
        timeout: Request timeout in milliseconds (1000-60000).
        wait: Milliseconds to wait after page load before scraping (0-30000).
        scrolls: Number of scrolls to perform (0-100).
        mock: Use mock mode for testing (no credits consumed).
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.markdownify(
            website_url=website_url, mode=mode, headers=headers, cookies=cookies,
            country=country, timeout=timeout, wait=wait, scrolls=scrolls, mock=mock,
        )
    except Exception as e:
        return {"error": str(e)}


# Add tool for smartscraper
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def smartscraper(
    user_prompt: str,
    website_url: str,
    ctx: Context,
    output_schema: Optional[
        Annotated[
            Union[str, Dict[str, Any]],
            Field(
                default=None,
                description="JSON schema dict or JSON string defining the expected output structure",
                json_schema_extra={"oneOf": [{"type": "string"}, {"type": "object"}]},
            ),
        ]
    ] = None,
    mode: Optional[Literal["auto", "fast", "js", "direct+stealth", "js+stealth"]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    country: Optional[str] = None,
    timeout: Optional[int] = None,
    wait: Optional[int] = None,
    scrolls: Optional[int] = None,
    mock: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Extract structured data from a webpage using AI (API v2 POST /extract).

    Args:
        user_prompt: Natural language instructions describing what data to extract.
        website_url: URL to extract data from (must include http:// or https://).
        output_schema: JSON schema (dict or JSON string) defining the expected output structure.
            If "required" field is missing, it will be automatically added as [].
        mode: Fetch/proxy mode — auto, fast, js, direct+stealth, js+stealth.
        headers: Custom HTTP headers.
        cookies: Cookies to send with the request.
        country: Two-letter country code for geo-located requests (e.g. 'us').
        timeout: Request timeout in milliseconds (1000-60000).
        wait: Milliseconds to wait after page load (0-30000).
        scrolls: Number of scrolls to perform (0-100).
        mock: Use mock mode for testing.
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

        if normalized_schema is not None:
            if "required" not in normalized_schema:
                normalized_schema["required"] = []

        fc = client._fetch_config(
            mode=mode, timeout=timeout, wait=wait, headers=headers,
            cookies=cookies, country=country, scrolls=scrolls, mock=mock,
        )

        return client.smartscraper(
            user_prompt=user_prompt,
            website_url=website_url,
            output_schema=normalized_schema,
            fetch_config_dict=fc,
        )
    except Exception as e:
        return {"error": str(e)}


# Add tool for searchscraper
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False})
def searchscraper(
    user_prompt: str,
    ctx: Context,
    num_results: Optional[int] = None,
    output_schema: Optional[
        Annotated[
            Union[str, Dict[str, Any]],
            Field(
                default=None,
                description="JSON schema dict or JSON string for structured search output",
                json_schema_extra={"oneOf": [{"type": "string"}, {"type": "object"}]},
            ),
        ]
    ] = None,
) -> Dict[str, Any]:
    """
    AI-powered web search with structured data extraction (API v2 POST /search).

    Args:
        user_prompt: Search query or natural language instructions.
        num_results: Number of search results (3-20, default 5).
        output_schema: JSON schema (dict or JSON string) for structured output.
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)

        normalized_schema: Optional[Dict[str, Any]] = None
        if isinstance(output_schema, dict):
            normalized_schema = output_schema
        elif isinstance(output_schema, str):
            try:
                parsed = json.loads(output_schema)
                if isinstance(parsed, dict):
                    normalized_schema = parsed
                else:
                    return {"error": "output_schema must be a JSON object"}
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON for output_schema: {e}"}

        return client.searchscraper(user_prompt, num_results=num_results, output_schema=normalized_schema)
    except Exception as e:
        return {"error": str(e)}


# Add tool for SmartCrawler initiation
@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def smartcrawler_initiate(
    url: str,
    ctx: Context,
    extraction_mode: str = "markdown",
    depth: Optional[int] = None,
    max_pages: Optional[int] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    mode: Optional[Literal["auto", "fast", "js", "direct+stealth", "js+stealth"]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    country: Optional[str] = None,
    timeout: Optional[int] = None,
    wait: Optional[int] = None,
    scrolls: Optional[int] = None,
    mock: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Start an asynchronous multi-page crawl (API v2 POST /crawl).

    Supports markdown or html output only. Poll smartcrawler_fetch_results with the returned id.

    Args:
        url: Starting URL (http/https).
        extraction_mode: 'markdown' (default) or 'html'.
        depth: Crawl depth (1-10, default 2).
        max_pages: Max pages (1-100, default 10).
        include_patterns: URL patterns to include.
        exclude_patterns: URL patterns to exclude.
        mode: Fetch/proxy mode — auto, fast, js, direct+stealth, js+stealth.
        headers: Custom HTTP headers.
        cookies: Cookies to send with the request.
        country: Two-letter country code for geo-located requests.
        timeout: Request timeout in milliseconds (1000-60000).
        wait: Milliseconds to wait after page load (0-30000).
        scrolls: Number of scrolls to perform (0-100).
        mock: Use mock mode for testing.
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)

        if extraction_mode not in ("markdown", "html"):
            raise ValueError("extraction_mode must be 'markdown' or 'html'")

        d = 2 if depth is None else depth
        mp = 10 if max_pages is None else max_pages
        if d < 1 or d > 10:
            raise ValueError("depth must be between 1 and 10")
        if mp < 1 or mp > 100:
            raise ValueError("max_pages must be between 1 and 100")

        fc = client._fetch_config(
            mode=mode, timeout=timeout, wait=wait, headers=headers,
            cookies=cookies, country=country, scrolls=scrolls, mock=mock,
        )
        return client.crawl_start(
            url,
            depth=d,
            max_pages=mp,
            crawl_format=extraction_mode,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            fetch_config_dict=fc,
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


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def crawl_stop(crawl_id: str, ctx: Context) -> Dict[str, Any]:
    """Stop a running crawl job (API v2 POST /crawl/:id/stop)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.crawl_stop(crawl_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def crawl_resume(crawl_id: str, ctx: Context) -> Dict[str, Any]:
    """Resume a stopped crawl job (API v2 POST /crawl/:id/resume)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.crawl_resume(crawl_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def credits(ctx: Context) -> Dict[str, Any]:
    """Return remaining API credits (API v2 GET /credits)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.credits()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False})
def sgai_history(
    ctx: Context,
    endpoint: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """
    List recent API requests (API v2 GET /history).

    Args:
        endpoint: Filter by service name (e.g. scrape, extract, search).
        status: Filter by status string.
        limit: Max rows (1–100).
        offset: Skip offset for pagination.
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.history(endpoint=endpoint, status_filter=status, limit=limit, offset=offset)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def monitor_create(
    name: str,
    url: str,
    prompt: str,
    interval: str,
    ctx: Context,
    output_schema: Optional[
        Annotated[
            Union[str, Dict[str, Any]],
            Field(
                default=None,
                description="JSON schema dict or JSON string for structured monitor output",
                json_schema_extra={"oneOf": [{"type": "string"}, {"type": "object"}]},
            ),
        ]
    ] = None,
    mode: Optional[Literal["auto", "fast", "js", "direct+stealth", "js+stealth"]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    country: Optional[str] = None,
    timeout: Optional[int] = None,
    wait: Optional[int] = None,
    scrolls: Optional[int] = None,
    mock: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Create a scheduled monitor job (API v2 POST /monitor).

    Args:
        name: Monitor name.
        url: URL to monitor.
        prompt: Prompt for AI extraction.
        interval: 5-field cron expression for scheduling.
        output_schema: JSON schema for structured output.
        mode: Fetch/proxy mode — auto, fast, js, direct+stealth, js+stealth.
        headers: Custom HTTP headers.
        cookies: Cookies to send with the request.
        country: Two-letter country code for geo-located requests.
        timeout: Request timeout in milliseconds (1000-60000).
        wait: Milliseconds to wait after page load (0-30000).
        scrolls: Number of scrolls to perform (0-100).
        mock: Use mock mode for testing.
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        normalized_schema: Optional[Dict[str, Any]] = None
        if isinstance(output_schema, dict):
            normalized_schema = output_schema
        elif isinstance(output_schema, str):
            try:
                parsed = json.loads(output_schema)
                if isinstance(parsed, dict):
                    normalized_schema = parsed
                else:
                    return {"error": "output_schema must be a JSON object"}
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON for output_schema: {e}"}

        fc = client._fetch_config(
            mode=mode, timeout=timeout, wait=wait, headers=headers,
            cookies=cookies, country=country, scrolls=scrolls, mock=mock,
        )
        return client.monitor_create(
            name=name, url=url, prompt=prompt, interval=interval,
            output_schema=normalized_schema, fetch_config_dict=fc,
        )
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def monitor_list(ctx: Context) -> Dict[str, Any]:
    """List monitors (API v2 GET /monitor)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.monitor_list()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def monitor_get(monitor_id: str, ctx: Context) -> Dict[str, Any]:
    """Get one monitor by id (API v2 GET /monitor/:id)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.monitor_get(monitor_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def monitor_pause(monitor_id: str, ctx: Context) -> Dict[str, Any]:
    """Pause a monitor (API v2 POST /monitor/:id/pause)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.monitor_pause(monitor_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False})
def monitor_resume(monitor_id: str, ctx: Context) -> Dict[str, Any]:
    """Resume a paused monitor (API v2 POST /monitor/:id/resume)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.monitor_resume(monitor_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False})
def monitor_delete(monitor_id: str, ctx: Context) -> Dict[str, Any]:
    """Delete a monitor (API v2 DELETE /monitor/:id)."""
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        return client.monitor_delete(monitor_id)
    except Exception as e:
        return {"error": str(e)}


# Add tool for basic scrape
@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True})
def scrape(
    website_url: str,
    ctx: Context,
    output_format: Literal["markdown", "html", "screenshot", "branding"] = "markdown",
    screenshot_full_page: bool = False,
    mode: Optional[Literal["auto", "fast", "js", "direct+stealth", "js+stealth"]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    country: Optional[str] = None,
    timeout: Optional[int] = None,
    wait: Optional[int] = None,
    scrolls: Optional[int] = None,
    mock: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Fetch page content (API v2 POST /scrape).

    Args:
        website_url: URL to scrape (must include http:// or https://).
        output_format: Output format — markdown, html, screenshot, or branding.
        screenshot_full_page: Capture full page screenshot (only for screenshot format).
        mode: Fetch/proxy mode — auto, fast, js, direct+stealth, js+stealth.
        headers: Custom HTTP headers.
        cookies: Cookies to send with the request.
        country: Two-letter country code for geo-located requests (e.g. 'us').
        timeout: Request timeout in milliseconds (1000-60000).
        wait: Milliseconds to wait after page load (0-30000).
        scrolls: Number of scrolls to perform (0-100).
        mock: Use mock mode for testing.
    """
    try:
        api_key = get_api_key(ctx)
        client = ScapeGraphClient(api_key)
        fc = client._fetch_config(
            mode=mode, timeout=timeout, wait=wait, headers=headers,
            cookies=cookies, country=country, scrolls=scrolls, mock=mock,
        )
        return client.scrape(
            website_url=website_url,
            output_format=output_format,
            screenshot_full_page=screenshot_full_page,
            fetch_config_dict=fc,
        )
    except Exception as e:
        return {"error": str(e)}


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
