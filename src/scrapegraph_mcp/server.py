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
from typing import Any, Dict, Optional, List, Union

import httpx
from fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field


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

    def smartscraper(self, user_prompt: str, website_url: str, number_of_scrolls: int = None, markdown_only: bool = None) -> Dict[str, Any]:
        """
        Extract structured data from a webpage using AI.

        Args:
            user_prompt: Instructions for what data to extract
            website_url: URL of the webpage to scrape
            number_of_scrolls: Number of infinite scrolls to perform (optional)
            markdown_only: Whether to return only markdown content without AI processing (optional)

        Returns:
            Dictionary containing the extracted data or markdown content
        """
        url = f"{self.BASE_URL}/smartscraper"
        data = {
            "user_prompt": user_prompt,
            "website_url": website_url
        }
        
        # Add number_of_scrolls to the request if provided
        if number_of_scrolls is not None:
            data["number_of_scrolls"] = number_of_scrolls
            
        # Add markdown_only to the request if provided
        if markdown_only is not None:
            data["markdown_only"] = markdown_only

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
    scrapegraph_api_key: str = Field(..., description="Your Scrapegraph API key")


# Create MCP server instance
mcp = FastMCP("ScapeGraph API MCP Server")


# Add tool for markdownify
@mcp.tool()
def markdownify(website_url: str, ctx: Context) -> Dict[str, Any]:
    """
    Convert a webpage into clean, formatted markdown.

    Args:
        website_url: URL of the webpage to convert

    Returns:
        Dictionary containing the markdown result
    """
    try:
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
        return client.markdownify(website_url)
    except Exception as e:
        return {"error": str(e)}


# Add tool for smartscraper
@mcp.tool()
def smartscraper(
    user_prompt: str, 
    website_url: str,
    ctx: Context,
    number_of_scrolls: int = None,
    markdown_only: bool = None
) -> Dict[str, Any]:
    """
    Extract structured data from a webpage using AI.

    Args:
        user_prompt: Instructions for what data to extract
        website_url: URL of the webpage to scrape
        number_of_scrolls: Number of infinite scrolls to perform (optional)
        markdown_only: Whether to return only markdown content without AI processing (optional)

    Returns:
        Dictionary containing the extracted data or markdown content
    """
    try:
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
        return client.smartscraper(user_prompt, website_url, number_of_scrolls, markdown_only)
    except Exception as e:
        return {"error": str(e)}


# Add tool for searchscraper
@mcp.tool()
def searchscraper(
    user_prompt: str,
    ctx: Context,
    num_results: int = None,
    number_of_scrolls: int = None
) -> Dict[str, Any]:
    """
    Perform AI-powered web searches with structured results.

    Args:
        user_prompt: Search query or instructions
        num_results: Number of websites to search (optional, default: 3 websites = 30 credits)
        number_of_scrolls: Number of infinite scrolls to perform on each website (optional)

    Returns:
        Dictionary containing search results and reference URLs
    """
    try:
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
        return client.searchscraper(user_prompt, num_results, number_of_scrolls)
    except Exception as e:
        return {"error": str(e)}


# Add tool for SmartCrawler initiation
@mcp.tool()
def smartcrawler_initiate(
    url: str,
    ctx: Context,
    prompt: str = None,
    extraction_mode: str = "ai",
    depth: int = None,
    max_pages: int = None,
    same_domain_only: bool = None
) -> Dict[str, Any]:
    """
    Initiate a SmartCrawler request for intelligent multi-page web crawling.
    
    SmartCrawler supports two modes:
    - AI Extraction Mode (10 credits per page): Extracts structured data based on your prompt
    - Markdown Conversion Mode (2 credits per page): Converts pages to clean markdown

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
    try:
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
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
@mcp.tool()
def smartcrawler_fetch_results(request_id: str, ctx: Context) -> Dict[str, Any]:
    """
    Fetch the results of a SmartCrawler operation.

    Args:
        request_id: The request ID returned by smartcrawler_initiate

    Returns:
        Dictionary containing the crawled data (structured extraction or markdown)
        and metadata about processed pages
    """
    try:
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
        return client.smartcrawler_fetch_results(request_id)
    except Exception as e:
        return {"error": str(e)}


# Add tool for basic scrape
@mcp.tool()
def scrape(website_url: str, ctx: Context, render_heavy_js: Optional[bool] = None) -> Dict[str, Any]:
    """
    Fetch page content for a URL.

    Args:
        website_url: URL to scrape
        render_heavy_js: Whether to render heavy JS (optional)
    """
    try:
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
        return client.scrape(website_url=website_url, render_heavy_js=render_heavy_js)
    except httpx.HTTPError as http_err:
        return {"error": str(http_err)}
    except ValueError as val_err:
        return {"error": str(val_err)}


# Add tool for sitemap extraction
@mcp.tool()
def sitemap(website_url: str, ctx: Context) -> Dict[str, Any]:
    """
    Extract sitemap for a website.

    Args:
        website_url: Base website URL
    """
    try:
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
        return client.sitemap(website_url=website_url)
    except httpx.HTTPError as http_err:
        return {"error": str(http_err)}
    except ValueError as val_err:
        return {"error": str(val_err)}


# Add tool for Agentic Scraper (no live session/browser interaction)
@mcp.tool()
def agentic_scrapper(
    url: str,
    ctx: Context,
    user_prompt: Optional[str] = None,
    output_schema: Optional[Union[str, Dict[str, Any]]] = None,
    steps: Optional[Union[str, List[str]]] = None,
    ai_extraction: Optional[bool] = None,
    persistent_session: Optional[bool] = None,
    timeout_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Run the Agentic Scraper workflow. Accepts flexible input forms for steps and schema.
    """
    # Normalize inputs
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
        client = ScapeGraphClient(ctx.session_config.scrapegraph_api_key)
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
    print("Starting ScapeGraph MCP server!")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()