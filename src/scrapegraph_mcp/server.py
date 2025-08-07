#!/usr/bin/env python3
"""
MCP server for ScapeGraph API integration.
This server exposes methods to use ScapeGraph's AI-powered web scraping services:
- markdownify: Convert any webpage into clean, formatted markdown
- smartscraper: Extract structured data from any webpage using AI
- searchscraper: Perform AI-powered web searches with structured results
- crawl_requester: Initiate intelligent web crawling requests (step 1)
- crawl_fetcher: Fetch results from crawling requests (step 2)
"""

import os
from typing import Any, Dict

import httpx
from mcp.server.fastmcp import FastMCP


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
        self.client = httpx.Client(timeout=60.0)

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

    def crawl_requester(
        self, 
        url: str, 
        prompt: str = None, 
        cache_website: bool = None,
        depth: int = None,
        max_pages: int = None,
        same_domain_only: bool = None,
        markdown_only: bool = None
    ) -> Dict[str, Any]:
        """
        Initiate a web crawling request and get a request ID.

        Args:
            url: Starting URL to crawl
            prompt: AI prompt for data extraction (optional, if not provided returns markdown only)
            cache_website: Whether to cache the website content (optional)
            depth: Maximum crawling depth (optional)
            max_pages: Maximum number of pages to crawl (optional)
            same_domain_only: Whether to crawl only within the same domain (optional)
            markdown_only: Whether to return only markdown content without AI processing (optional)

        Returns:
            Dictionary containing the request ID and status
        """
        endpoint = f"{self.BASE_URL}/crawl/requester"
        data = {
            "url": url
        }
        
        # Add optional parameters if provided
        if prompt is not None:
            data["prompt"] = prompt
        if cache_website is not None:
            data["cache_website"] = cache_website
        if depth is not None:
            data["depth"] = depth
        if max_pages is not None:
            data["max_pages"] = max_pages
        if same_domain_only is not None:
            data["same_domain_only"] = same_domain_only
        if markdown_only is not None:
            data["markdown_only"] = markdown_only

        response = self.client.post(endpoint, headers=self.headers, json=data)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        return response.json()

    def crawl_fetcher(self, request_id: str) -> Dict[str, Any]:
        """
        Fetch the results of a crawling request using the request ID.

        Args:
            request_id: The request ID returned by crawl_requester

        Returns:
            Dictionary containing the crawl results or status
        """
        endpoint = f"{self.BASE_URL}/crawl/fetcher"
        data = {
            "request_id": request_id
        }

        response = self.client.post(endpoint, headers=self.headers, json=data)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()


# Create MCP server
mcp = FastMCP("ScapeGraph API MCP Server")

# Default API key (will be overridden in main or by direct assignment)
default_api_key = os.environ.get("SGAI_API_KEY")
scrapegraph_client = ScapeGraphClient(default_api_key) if default_api_key else None


# Add tool for markdownify
@mcp.tool()
def markdownify(website_url: str) -> Dict[str, Any]:
    """
    Convert a webpage into clean, formatted markdown.

    Args:
        website_url: URL of the webpage to convert

    Returns:
        Dictionary containing the markdown result
    """
    if scrapegraph_client is None:
        return {"error": "ScapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.markdownify(website_url)
    except Exception as e:
        return {"error": str(e)}


# Add tool for smartscraper
@mcp.tool()
def smartscraper(
    user_prompt: str, 
    website_url: str,
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
    if scrapegraph_client is None:
        return {"error": "ScapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.smartscraper(user_prompt, website_url, number_of_scrolls, markdown_only)
    except Exception as e:
        return {"error": str(e)}


# Add tool for searchscraper
@mcp.tool()
def searchscraper(
    user_prompt: str,
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
    if scrapegraph_client is None:
        return {"error": "ScapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.searchscraper(user_prompt, num_results, number_of_scrolls)
    except Exception as e:
        return {"error": str(e)}


# Add tool for crawl requester (smartcrawler step 1)
@mcp.tool()
def crawl_requester(
    url: str,
    prompt: str = None,
    cache_website: bool = None,
    depth: int = None,
    max_pages: int = None,
    same_domain_only: bool = None,
    markdown_only: bool = None
) -> Dict[str, Any]:
    """
    Initiate a web crawling request and get a request ID.

    Args:
        url: Starting URL to crawl
        prompt: AI prompt for data extraction (optional, if not provided returns markdown only)
        cache_website: Whether to cache the website content (optional)
        depth: Maximum crawling depth (optional)
        max_pages: Maximum number of pages to crawl (optional)
        same_domain_only: Whether to crawl only within the same domain (optional)
        markdown_only: Whether to return only markdown content without AI processing (optional)

    Returns:
        Dictionary containing the request ID and status
    """
    if scrapegraph_client is None:
        return {"error": "ScapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.crawl_requester(
            url=url,
            prompt=prompt,
            cache_website=cache_website,
            depth=depth,
            max_pages=max_pages,
            same_domain_only=same_domain_only,
            markdown_only=markdown_only
        )
    except Exception as e:
        return {"error": str(e)}


# Add tool for crawl fetcher (smartcrawler step 2)
@mcp.tool()
def crawl_fetcher(request_id: str) -> Dict[str, Any]:
    """
    Fetch the results of a crawling request using the request ID.

    Args:
        request_id: The request ID returned by crawl_requester

    Returns:
        Dictionary containing the crawl results or status
    """
    if scrapegraph_client is None:
        return {"error": "ScapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.crawl_fetcher(request_id)
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    """Run the ScapeGraph MCP server."""
    print("Starting ScapeGraph MCP server!")
    # Run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main() 