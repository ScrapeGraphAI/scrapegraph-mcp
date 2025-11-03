# ScrapeGraph MCP Server

![ScrapeGraph Smithery Integration](assets/sgai_smithery.png)
<a href="https://glama.ai/mcp/servers/37us0q2tr6">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/37us0q2tr6/badge" alt="ScrapeGraph Server MCP server" style="display: inline-block;"/>
</a>
<a href="https://mseep.ai/app/scrapegraphai-scrapegraph-mcp">
  <img src="https://mseep.net/pr/scrapegraphai-scrapegraph-mcp-badge.png" alt="MseeP.ai Security Assessment Badge" style="display: inline-block;"/>
</a>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![smithery badge](https://smithery.ai/badge/@ScrapeGraphAI/scrapegraph-mcp)](https://smithery.ai/server/@ScrapeGraphAI/scrapegraph-mcp)


A production-ready [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that provides seamless integration with the [ScrapeGraph AI](https://scrapegraphai.com) API. This server enables language models to leverage advanced AI-powered web scraping capabilities with enterprise-grade reliability.

## Table of Contents

- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Available Tools](#available-tools)
- [Setup Instructions](#setup-instructions)
- [Example Use Cases](#example-use-cases)
- [Error Handling](#error-handling)
- [Common Issues](#common-issues)
- [Development](#development)
- [Contributing](#contributing)
- [Documentation](#documentation)
- [Technology Stack](#technology-stack)
- [License](#license)

## Key Features

- **8 Powerful Tools**: From simple markdown conversion to complex multi-page crawling and agentic workflows
- **AI-Powered Extraction**: Intelligently extract structured data using natural language prompts
- **Multi-Page Crawling**: SmartCrawler supports asynchronous crawling with configurable depth and page limits
- **Infinite Scroll Support**: Handle dynamic content loading with configurable scroll counts
- **JavaScript Rendering**: Full support for JavaScript-heavy websites
- **Flexible Output Formats**: Get results as markdown, structured JSON, or custom schemas
- **Easy Integration**: Works seamlessly with Claude Desktop, Cursor, and any MCP-compatible client
- **Enterprise-Ready**: Robust error handling, timeout management, and production-tested reliability
- **Simple Deployment**: One-command installation via Smithery or manual setup
- **Comprehensive Documentation**: Detailed developer docs in `.agent/` folder

## Quick Start

### 1. Get Your API Key

Sign up and get your API key from the [ScrapeGraph Dashboard](https://dashboard.scrapegraphai.com)

### 2. Install with Smithery (Recommended)

```bash
npx -y @smithery/cli install @ScrapeGraphAI/scrapegraph-mcp --client claude
```

### 3. Start Using

Ask Claude or Cursor:
- "Convert https://scrapegraphai.com to markdown"
- "Extract all product prices from this e-commerce page"
- "Research the latest AI developments and summarize findings"

That's it! The server is now available to your AI assistant.

## Available Tools

The server provides **8 enterprise-ready tools** for AI-powered web scraping:

### Core Scraping Tools

#### 1. `markdownify`
Transform any webpage into clean, structured markdown format.

```python
markdownify(website_url: str)
```
- **Credits**: 2 per request
- **Use case**: Quick webpage content extraction in markdown

#### 2. `smartscraper`
Leverage AI to extract structured data from any webpage with support for infinite scrolling.

```python
smartscraper(
    user_prompt: str,
    website_url: str,
    number_of_scrolls: int = None,
    markdown_only: bool = None
)
```
- **Credits**: 10+ (base) + variable based on scrolling
- **Use case**: AI-powered data extraction with custom prompts

#### 3. `searchscraper`
Execute AI-powered web searches with structured, actionable results.

```python
searchscraper(
    user_prompt: str,
    num_results: int = None,
    number_of_scrolls: int = None
)
```
- **Credits**: Variable (3-20 websites × 10 credits)
- **Use case**: Multi-source research and data aggregation

### Advanced Scraping Tools

#### 4. `scrape`
Basic scraping endpoint to fetch page content with optional heavy JavaScript rendering.

```python
scrape(website_url: str, render_heavy_js: bool = None)
```
- **Use case**: Simple page content fetching with JS rendering support

#### 5. `sitemap`
Extract sitemap URLs and structure for any website.

```python
sitemap(website_url: str)
```
- **Use case**: Website structure analysis and URL discovery

### Multi-Page Crawling

#### 6. `smartcrawler_initiate`
Initiate intelligent multi-page web crawling (asynchronous operation).

```python
smartcrawler_initiate(
    url: str,
    prompt: str = None,
    extraction_mode: str = "ai",
    depth: int = None,
    max_pages: int = None,
    same_domain_only: bool = None
)
```
- **AI Extraction Mode**: 10 credits per page - extracts structured data
- **Markdown Mode**: 2 credits per page - converts to markdown
- **Returns**: `request_id` for polling
- **Use case**: Large-scale website crawling and data extraction

#### 7. `smartcrawler_fetch_results`
Retrieve results from asynchronous crawling operations.

```python
smartcrawler_fetch_results(request_id: str)
```
- **Returns**: Status and results when crawling is complete
- **Use case**: Poll for crawl completion and retrieve results

### Intelligent Agent-Based Scraping

#### 8. `agentic_scrapper`
Run advanced agentic scraping workflows with customizable steps and structured output schemas.

```python
agentic_scrapper(
    url: str,
    user_prompt: str = None,
    output_schema: dict = None,
    steps: list = None,
    ai_extraction: bool = None,
    persistent_session: bool = None,
    timeout_seconds: float = None
)
```
- **Use case**: Complex multi-step workflows with custom schemas and persistent sessions

## Setup Instructions

To utilize this server, you'll need a ScrapeGraph API key. Follow these steps to obtain one:

1. Navigate to the [ScrapeGraph Dashboard](https://dashboard.scrapegraphai.com)
2. Create an account and generate your API key

### Automated Installation via Smithery

For automated installation of the ScrapeGraph API Integration Server using [Smithery](https://smithery.ai/server/@ScrapeGraphAI/scrapegraph-mcp):

```bash
npx -y @smithery/cli install @ScrapeGraphAI/scrapegraph-mcp --client claude
```

### Claude Desktop Configuration

Update your Claude Desktop configuration file with the following settings (located on the top rigth of the Cursor page):

(remember to add your API key inside the config)

```json
{
    "mcpServers": {
        "@ScrapeGraphAI-scrapegraph-mcp": {
            "command": "npx",
            "args": [
                "-y",
                "@smithery/cli@latest",
                "run",
                "@ScrapeGraphAI/scrapegraph-mcp",
                "--config",
                "\"{\\\"scrapegraphApiKey\\\":\\\"YOUR-SGAI-API-KEY\\\"}\""
            ]
        }
    }
}
```

The configuration file is located at:
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`
- macOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

### Cursor Integration

Add the ScrapeGraphAI MCP server on the settings:

![Cursor MCP Integration](assets/cursor_mcp.png)

## Example Use Cases

The server enables sophisticated queries across various scraping scenarios:

### Single Page Scraping
- **Markdownify**: "Convert the ScrapeGraph documentation page to markdown"
- **SmartScraper**: "Extract all product names, prices, and ratings from this e-commerce page"
- **SmartScraper with scrolling**: "Scrape this infinite scroll page with 5 scrolls and extract all items"
- **Basic Scrape**: "Fetch the HTML content of this JavaScript-heavy page with full rendering"

### Search and Research
- **SearchScraper**: "Research and summarize recent developments in AI-powered web scraping"
- **SearchScraper**: "Search for the top 5 articles about machine learning frameworks and extract key insights"
- **SearchScraper**: "Find recent news about GPT-4 and provide a structured summary"

### Website Analysis
- **Sitemap**: "Extract the complete sitemap structure from the ScrapeGraph website"
- **Sitemap**: "Discover all URLs on this blog site"

### Multi-Page Crawling
- **SmartCrawler (AI mode)**: "Crawl the entire documentation site and extract all API endpoints with descriptions"
- **SmartCrawler (Markdown mode)**: "Convert all pages in the blog to markdown up to 2 levels deep"
- **SmartCrawler**: "Extract all product information from an e-commerce site, maximum 100 pages, same domain only"

### Advanced Agentic Scraping
- **Agentic Scraper**: "Navigate through a multi-step authentication form and extract user dashboard data"
- **Agentic Scraper with schema**: "Follow pagination links and compile a dataset with schema: {title, author, date, content}"
- **Agentic Scraper**: "Execute a complex workflow: login, navigate to reports, download data, and extract summary statistics"

## Error Handling

The server implements robust error handling with detailed, actionable error messages for:

- API authentication issues
- Malformed URL structures
- Network connectivity failures
- Rate limiting and quota management

## Common Issues

### Windows-Specific Connection

When running on Windows systems, you may need to use the following command to connect to the MCP server:

```bash
C:\Windows\System32\cmd.exe /c npx -y @smithery/cli@latest run @ScrapeGraphAI/scrapegraph-mcp --config "{\"scrapegraphApiKey\":\"YOUR-SGAI-API-KEY\"}"
```

This ensures proper execution in the Windows environment.

### Other Common Issues

**"ScrapeGraph client not initialized"**
- **Cause**: Missing API key
- **Solution**: Set `SGAI_API_KEY` environment variable or provide via `--config`

**"Error 401: Unauthorized"**
- **Cause**: Invalid API key
- **Solution**: Verify your API key at the [ScrapeGraph Dashboard](https://dashboard.scrapegraphai.com)

**"Error 402: Payment Required"**
- **Cause**: Insufficient credits
- **Solution**: Add credits to your ScrapeGraph account

**SmartCrawler not returning results**
- **Cause**: Still processing (asynchronous operation)
- **Solution**: Keep polling `smartcrawler_fetch_results()` until status is "completed"

**Tools not appearing in Claude Desktop**
- **Cause**: Server not starting or configuration error
- **Solution**: Check Claude logs at `~/Library/Logs/Claude/` (macOS) or `%APPDATA%\Claude\Logs\` (Windows)

For detailed troubleshooting, see the [.agent documentation](.agent/README.md).

## Development

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- ScrapeGraph API key

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/ScrapeGraphAI/scrapegraph-mcp
cd scrapegraph-mcp

# Install dependencies
pip install -e ".[dev]"

# Set your API key
export SGAI_API_KEY=your-api-key

# Run the server
scrapegraph-mcp
# or
python -m scrapegraph_mcp.server
```

### Testing with MCP Inspector

Test your server locally using the MCP Inspector tool:

```bash
npx @modelcontextprotocol/inspector scrapegraph-mcp
```

This provides a web interface to test all available tools.

### Code Quality

**Linting:**
```bash
ruff check src/
```

**Type Checking:**
```bash
mypy src/
```

**Format Checking:**
```bash
ruff format --check src/
```

### Project Structure

```
scrapegraph-mcp/
├── src/
│   └── scrapegraph_mcp/
│       ├── __init__.py      # Package initialization
│       └── server.py        # Main MCP server (all code in one file)
├── .agent/                  # Developer documentation
│   ├── README.md           # Documentation index
│   └── system/             # System architecture docs
├── assets/                  # Images and badges
├── pyproject.toml          # Project metadata & dependencies
├── smithery.yaml           # Smithery deployment config
└── README.md               # This file
```

## Contributing

We welcome contributions! Here's how you can help:

### Adding a New Tool

1. **Add method to `ScapeGraphClient` class** in [server.py](src/scrapegraph_mcp/server.py):

```python
def new_tool(self, param: str) -> Dict[str, Any]:
    """Tool description."""
    url = f"{self.BASE_URL}/new-endpoint"
    data = {"param": param}
    response = self.client.post(url, headers=self.headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    return response.json()
```

2. **Add MCP tool decorator**:

```python
@mcp.tool()
def new_tool(param: str) -> Dict[str, Any]:
    """
    Tool description for AI assistants.

    Args:
        param: Parameter description

    Returns:
        Dictionary containing results
    """
    if scrapegraph_client is None:
        return {"error": "ScrapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.new_tool(param)
    except Exception as e:
        return {"error": str(e)}
```

3. **Test with MCP Inspector**:
```bash
npx @modelcontextprotocol/inspector scrapegraph-mcp
```

4. **Update documentation**:
   - Add tool to this README
   - Update [.agent documentation](.agent/README.md)

5. **Submit a pull request**

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run linting and type checking
5. Test with MCP Inspector and Claude Desktop
6. Update documentation
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Style

- **Line length**: 100 characters
- **Type hints**: Required for all functions
- **Docstrings**: Google-style docstrings
- **Error handling**: Return error dicts, don't raise exceptions in tools
- **Python version**: Target 3.10+

For detailed development guidelines, see the [.agent documentation](.agent/README.md).

## Documentation

For comprehensive developer documentation, see:

- **[.agent/README.md](.agent/README.md)** - Complete developer documentation index
- **[.agent/system/project_architecture.md](.agent/system/project_architecture.md)** - System architecture and design
- **[.agent/system/mcp_protocol.md](.agent/system/mcp_protocol.md)** - MCP protocol integration details

## Technology Stack

### Core Framework
- **Python 3.10+** - Modern Python with type hints
- **FastMCP** - Lightweight MCP server framework
- **httpx 0.24.0+** - Modern async HTTP client

### Development Tools
- **Ruff** - Fast Python linter and formatter
- **mypy** - Static type checker
- **Hatchling** - Modern build backend

### Deployment
- **Smithery** - Automated MCP server deployment
- **Docker** - Container support with Alpine Linux
- **stdio transport** - Standard MCP communication

### API Integration
- **ScrapeGraph AI API** - Enterprise web scraping service
- **Base URL**: `https://api.scrapegraphai.com/v1`
- **Authentication**: API key-based

## License

This project is distributed under the MIT License. For detailed terms and conditions, please refer to the LICENSE file.

## Acknowledgments

Special thanks to [tomekkorbak](https://github.com/tomekkorbak) for his implementation of [oura-mcp-server](https://github.com/tomekkorbak/oura-mcp-server), which served as starting point for this repo.

## Resources

### Official Links
- [ScrapeGraph AI Homepage](https://scrapegraphai.com)
- [ScrapeGraph Dashboard](https://dashboard.scrapegraphai.com) - Get your API key
- [ScrapeGraph API Documentation](https://api.scrapegraphai.com/docs)
- [GitHub Repository](https://github.com/ScrapeGraphAI/scrapegraph-mcp)

### MCP Resources
- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP specification
- [FastMCP Framework](https://github.com/jlowin/fastmcp) - Framework used by this server
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) - Testing tool
- [Smithery](https://smithery.ai/server/@ScrapeGraphAI/scrapegraph-mcp) - MCP server distribution
- mcp-name: io.github.ScrapeGraphAI/scrapegraph-mcp"

### AI Assistant Integration
- [Claude Desktop](https://claude.ai/desktop) - Desktop app with MCP support
- [Cursor](https://cursor.sh/) - AI-powered code editor

### Support
- [GitHub Issues](https://github.com/ScrapeGraphAI/scrapegraph-mcp/issues) - Report bugs or request features
- [Developer Documentation](.agent/README.md) - Comprehensive dev docs

---

Made with ❤️ by [ScrapeGraphAI](https://scrapegraphai.com) Team
