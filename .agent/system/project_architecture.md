# ScrapeGraph MCP Server - Project Architecture

**Last Updated:** April 2026
**Version:** 3.0.0

## Table of Contents
- [System Overview](#system-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Core Architecture](#core-architecture)
- [MCP Tools](#mcp-tools)
- [API Integration](#api-integration)
- [Deployment](#deployment)
- [Recent Updates](#recent-updates)

---

## System Overview

The ScrapeGraph MCP Server is a production-ready [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that provides seamless integration between AI assistants (like Claude, Cursor, etc.) and the [ScrapeGraphAI API](https://scrapegraphai.com). This server enables language models to leverage advanced AI-powered web scraping capabilities with enterprise-grade reliability.

**Key Capabilities (API v2):**
- **Scrape** (`scrape`, `scrape`) — POST `/v2/scrape`
- **Extract** (`extract`) — POST `/v2/extract` (URL-only)
- **Search** (`search`) — POST `/v2/search`
- **Crawl** — POST/GET `/v2/crawl` (+ stop/resume); markdown/html crawl only
- **Monitor, credits, history** — `/v2/monitor`, `/credits`, `/history`

**Purpose:**
- Bridge AI assistants (Claude, Cursor, etc.) with web scraping capabilities
- Enable LLMs to extract structured data from any website
- Provide clean, formatted markdown conversion of web content
- Execute multi-page crawling operations with AI-powered extraction

---

## Technology Stack

### Core Framework
- **Python 3.10+** - Programming language (minimum version)
- **mcp[cli] 1.3.0+** - Model Context Protocol SDK for Python
- **FastMCP** - Lightweight MCP server framework built on top of mcp

### HTTP Client
- **httpx 0.24.0+** - Modern async HTTP client for API requests
- **Timeout:** 60 seconds for all API requests

### Development Tools
- **Ruff 0.1.0+** - Fast Python linter
- **mypy 1.0.0+** - Static type checker

### Build System
- **Hatchling** - Modern Python build backend
- **pyproject.toml** - PEP 621 compliant project metadata

### Deployment
- **Docker** - Containerization with Alpine Linux base
- **Smithery** - Automated MCP server deployment and distribution
- **stdio transport** - Standard input/output for MCP communication

---

## Project Structure

```
scrapegraph-mcp/
├── src/
│   └── scrapegraph_mcp/
│       ├── __init__.py           # Package initialization
│       └── server.py             # Main MCP server implementation
│
├── assets/
│   ├── sgai_smithery.png         # Smithery integration badge
│   └── cursor_mcp.png            # Cursor integration screenshot
│
├── .github/
│   └── workflows/                # CI/CD workflows (if any)
│
├── pyproject.toml                # Project metadata and dependencies
├── Dockerfile                    # Docker container definition
├── smithery.yaml                 # Smithery deployment configuration
├── README.md                     # User-facing documentation
├── LICENSE                       # MIT License
└── .python-version               # Python version specification
```

### Key Files

**`src/scrapegraph_mcp/server.py`**
- Main server implementation
- `ScapeGraphClient` - API client wrapper
- MCP tool definitions (`@mcp.tool()` decorators)
- Server initialization and main entry point

**`pyproject.toml`**
- Project metadata (name, version, authors)
- Dependencies (mcp, httpx)
- Build configuration (hatchling)
- Tool configuration (ruff, mypy)
- Entry point: `scrapegraph-mcp` → `scrapegraph_mcp.server:main`

**`Dockerfile`**
- Python 3.12 Alpine base image
- Build dependencies (gcc, musl-dev, libffi-dev)
- Package installation
- Entrypoint: `scrapegraph-mcp`

**`smithery.yaml`**
- Smithery deployment configuration
- NPM package metadata
- Installation instructions

---

## Core Architecture

### Model Context Protocol (MCP)

The server implements the Model Context Protocol, which defines a standard way for AI assistants to interact with external tools and services.

**MCP Components:**
1. **Server** - Exposes tools to AI assistants (this project)
2. **Client** - AI assistant that uses the tools (Claude, Cursor, etc.)
3. **Transport** - Communication layer (stdio)
4. **Tools** - Functions that the AI can call

**Communication Flow:**
```
AI Assistant (Claude/Cursor)
    ↓ (stdio via MCP)
FastMCP Server (this project)
    ↓ (HTTPS API calls)
ScrapeGraphAI API (default https://v2-api.scrapegraphai.com/api)
    ↓ (web scraping)
Target Websites
```

### Server Architecture

The server follows a simple, single-file architecture:

**`ScapeGraphClient` Class:**
- HTTP client wrapper for ScrapeGraphAI API v2 ([scrapegraph-py#84](https://github.com/ScrapeGraphAI/scrapegraph-py/pull/84))
- Base URL: `https://v2-api.scrapegraphai.com/api` (override with env `SGAI_API_URL`)
- Auth: `SGAI-APIKEY`, `X-SDK-Version: scrapegraph-mcp@2.0.0` (matches scrapegraph-py v2)
- v2 methods include `scrape_v2`, `extract`, `search_api`, `crawl_*`, `monitor_*`, `credits`, `history`, plus compatibility wrappers used by MCP tools

**FastMCP Server:**
- Created with `FastMCP("ScapeGraph API MCP Server")`
- Exposes tools via `@mcp.tool()` decorators
- Tool functions wrap `ScapeGraphClient` methods
- Error handling with try/except blocks
- Returns dictionaries with results or error messages

**Initialization Flow:**
1. Import dependencies (`httpx`, `mcp.server.fastmcp`)
2. Define `ScapeGraphClient` class
3. Create `FastMCP` server instance
4. Initialize `ScapeGraphClient` with API key from env or config
5. Define MCP tools with `@mcp.tool()` decorators
6. Start server with `mcp.run(transport="stdio")`

### Design Patterns

**1. Wrapper Pattern**
- `ScapeGraphClient` wraps the ScrapeGraphAI REST API
- Simplifies API interactions with typed methods
- Centralizes authentication and error handling

**2. Decorator Pattern**
- `@mcp.tool()` decorators expose functions as MCP tools
- Automatic serialization/deserialization
- Type hints → MCP schema generation

**3. Singleton Pattern**
- Single `scrapegraph_client` instance
- Shared across all tool invocations
- Reused HTTP client connection

**4. Error Handling Pattern**
- Try/except blocks in all tool functions
- Return error dictionaries instead of raising exceptions
- Ensures graceful degradation for AI assistants

---

## MCP Tools

The server exposes many `@mcp.tool()` handlers (see repository `README.md` for the full table). The detailed subsections below still use **v1-style endpoint names** in several places; treat them as illustrative and prefer the v2 mapping in **API Integration**.

**v2 tool names:** `scrape`, `scrape`, `extract`, `search`, `crawl_start`, `crawl_get_status`, `crawl_stop`, `crawl_resume`, `credits`, `history`, `monitor_create`, `monitor_list`, `monitor_get`, `monitor_pause`, `monitor_resume`, `monitor_delete`, `monitor_activity`.

### 1. `scrape(website_url: str)`

**Purpose:** Convert a webpage into clean, formatted markdown

**Parameters:**
- `website_url` (str) - URL of the webpage to convert

**Returns:**
```json
{
  "result": "# Page Title\n\nContent in markdown format..."
}
```

**Error Response:**
```json
{
  "error": "Error 404: Not Found"
}
```

**Example Usage (from AI):**
```
"Convert https://scrapegraphai.com to markdown"
→ AI calls: scrape("https://scrapegraphai.com")
```

**API Endpoint:** `POST /v1/scrape`

**Credits:** 2 credits per request

---

### 2. `extract(user_prompt: str, website_url: str, number_of_scrolls: int = None, markdown_only: bool = None)`

**Purpose:** Extract structured data from a webpage using AI

**Parameters:**
- `user_prompt` (str) - Instructions for what data to extract
- `website_url` (str) - URL of the webpage to scrape
- `number_of_scrolls` (int, optional) - Number of infinite scrolls to perform
- `markdown_only` (bool, optional) - Return only markdown without AI processing

**Returns:**
```json
{
  "result": {
    "extracted_field_1": "value1",
    "extracted_field_2": "value2"
  }
}
```

**Example Usage:**
```
"Extract all product names and prices from https://example.com/products"
→ AI calls: extract(
    user_prompt="Extract product names and prices",
    website_url="https://example.com/products"
)
```

**API Endpoint:** `POST /v1/extract`

**Credits:** 10 credits (base) + 1 credit per scroll + additional charges

---

### 3. `search(user_prompt: str, num_results: int = None, number_of_scrolls: int = None, time_range: str = None)`

**Purpose:** Perform AI-powered web searches with structured results

**Parameters:**
- `user_prompt` (str) - Search query or instructions
- `num_results` (int, optional) - Number of websites to search (default: 3 = 30 credits)
- `number_of_scrolls` (int, optional) - Number of infinite scrolls per website
- `time_range` (str, optional) - Filter results by recency. Valid values: `past_hour`, `past_24_hours`, `past_week`, `past_month`, `past_year`

**Returns:**
```json
{
  "result": {
    "answer": "Aggregated answer from multiple sources",
    "sources": [
      {"url": "https://source1.com", "data": {...}},
      {"url": "https://source2.com", "data": {...}}
    ]
  }
}
```

**Example Usage:**
```
"Research the latest AI developments in 2025"
→ AI calls: search(
    user_prompt="Latest AI developments in 2025",
    num_results=5,
    time_range="past_week"
)
```

**API Endpoint:** `POST /v1/search`

**Credits:** Variable (3-20 websites × 10 credits per website)

---

### 4. `crawl_start(url: str, prompt: str = None, extraction_mode: str = "ai", depth: int = None, max_pages: int = None, same_domain_only: bool = None)`

**Purpose:** Initiate intelligent multi-page web crawling (asynchronous)

**Parameters:**
- `url` (str) - Starting URL to crawl
- `prompt` (str, optional) - AI prompt for data extraction (required for AI mode)
- `extraction_mode` (str) - "ai" for AI extraction (10 credits/page) or "markdown" for markdown conversion (2 credits/page)
- `depth` (int, optional) - Maximum link traversal depth
- `max_pages` (int, optional) - Maximum number of pages to crawl
- `same_domain_only` (bool, optional) - Crawl only within the same domain

**Returns:**
```json
{
  "request_id": "uuid-here",
  "status": "processing"
}
```

**Example Usage:**
```
"Crawl https://docs.python.org and extract all function signatures"
→ AI calls: crawl_start(
    url="https://docs.python.org",
    prompt="Extract function signatures and descriptions",
    extraction_mode="ai",
    max_pages=50,
    same_domain_only=True
)
```

**API Endpoint:** `POST /v1/crawl`

**Credits:** 100 credits (base) + 10 credits per page (AI mode) or 2 credits per page (markdown mode)

**Note:** This is an asynchronous operation. Use `crawl_get_status()` to retrieve results.

---

### 5. `crawl_get_status(request_id: str)`

**Purpose:** Fetch the results of a SmartCrawler operation

**Parameters:**
- `request_id` (str) - The request ID returned by `crawl_start()`

**Returns (while processing):**
```json
{
  "status": "processing",
  "pages_processed": 15,
  "total_pages": 50
}
```

**Returns (completed):**
```json
{
  "status": "completed",
  "results": [
    {"url": "https://page1.com", "data": {...}},
    {"url": "https://page2.com", "data": {...}}
  ],
  "pages_processed": 50,
  "total_pages": 50
}
```

**Example Usage:**
```
AI: "Check the status of crawl request abc-123"
→ AI calls: crawl_get_status("abc-123")

If status is "processing":
→ AI: "Still processing, 15/50 pages completed"

If status is "completed":
→ AI: "Crawl complete! Here are the results..."
```

**API Endpoint:** `GET /v1/crawl/{request_id}`

**Polling Strategy:**
- AI assistants should poll this endpoint until `status == "completed"`
- Recommended polling interval: 5-10 seconds
- Maximum wait time: ~30 minutes for large crawls

---

## API Integration

### ScrapeGraphAI API

**Base URL:** `https://v2-api.scrapegraphai.com/api` (configurable via `SGAI_API_URL`)

**Authentication:**
- Headers: `SGAI-APIKEY: <key>` (matches scrapegraph-py v2 wire format)
- Obtain API key from: [ScrapeGraph Dashboard](https://dashboard.scrapegraphai.com)

**Endpoints used (v2):**

| Endpoint | Method | MCP tools (typical) |
|----------|--------|---------------------|
| `/scrape` | POST | `scrape`, `scrape` |
| `/extract` | POST | `extract` |
| `/search` | POST | `search` |
| `/crawl` | POST | `crawl_start` |
| `/crawl/{id}` | GET | `crawl_get_status` |
| `/crawl/{id}/stop` | POST | `crawl_stop` |
| `/crawl/{id}/resume` | POST | `crawl_resume` |
| `/credits` | GET | `credits` |
| `/history` | GET | `history` |
| `/monitor` | POST, GET | `monitor_create`, `monitor_list` |
| `/monitor/{id}` | GET, DELETE | `monitor_get`, `monitor_delete` |
| `/monitor/{id}/pause` | POST | `monitor_pause` |
| `/monitor/{id}/resume` | POST | `monitor_resume` |
| `/monitor/{id}/activity` | GET | `monitor_activity` |

**Request Format:**
```json
{
  "website_url": "https://example.com",
  "user_prompt": "Extract product names"
}
```

**Response Format:**
```json
{
  "result": {...},
  "credits_used": 10
}
```

**Error Handling:**
```python
response = self.client.post(url, headers=self.headers, json=data)

if response.status_code != 200:
    error_msg = f"Error {response.status_code}: {response.text}"
    raise Exception(error_msg)

return response.json()
```

**HTTP Client Configuration:**
- Library: `httpx`
- Timeout: 60 seconds
- Synchronous client (not async)

### Credit System

The MCP server is a pass-through to the ScrapeGraphAI API, so all credit costs are determined by the API:

- **Markdownify:** 2 credits
- **SmartScraper:** 10 credits (base) + variable
- **SearchScraper:** Variable (websites × 10 credits)
- **SmartCrawler (AI mode):** 100 + (pages × 10) credits
- **SmartCrawler (Markdown mode):** 100 + (pages × 2) credits

Credits are deducted from the API key balance on the ScrapeGraphAI platform.

---

## Deployment

### Installation Methods

#### 1. Automated Installation via Smithery

**Smithery** is the recommended deployment method for MCP servers.

```bash
npx -y @smithery/cli install @ScrapeGraphAI/scrapegraph-mcp --client claude
```

This automatically:
- Installs the MCP server
- Configures the AI client (Claude Desktop)
- Prompts for API key

#### 2. Manual Claude Desktop Configuration

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

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
                "{\"scrapegraphApiKey\":\"YOUR-SGAI-API-KEY\"}"
            ]
        }
    }
}
```

**Windows-Specific Command:**
```bash
C:\Windows\System32\cmd.exe /c npx -y @smithery/cli@latest run @ScrapeGraphAI/scrapegraph-mcp --config "{\"scrapegraphApiKey\":\"YOUR-SGAI-API-KEY\"}"
```

#### 3. Cursor Integration

Add the MCP server in Cursor settings:

1. Open Cursor settings
2. Navigate to MCP section
3. Add ScrapeGraphAI MCP server
4. Configure API key

(See `assets/cursor_mcp.png` for screenshot)

#### 4. Docker Deployment

**Build:**
```bash
docker build -t scrapegraph-mcp .
```

**Run:**
```bash
docker run -e SGAI_API_KEY=your-api-key scrapegraph-mcp
```

**Dockerfile:**
- Base: Python 3.12 Alpine
- Build deps: gcc, musl-dev, libffi-dev
- Install via pip: `pip install .`
- Entrypoint: `scrapegraph-mcp`

#### 5. Python Package Installation

**From PyPI (once published):**
```bash
pip install scrapegraph-mcp
```

**From Source:**
```bash
git clone https://github.com/ScrapeGraphAI/scrapegraph-mcp
cd scrapegraph-mcp
pip install .
```

**Run:**
```bash
export SGAI_API_KEY=your-api-key
scrapegraph-mcp
```

### Configuration

**API Key Sources (in order of precedence):**
1. `--config` parameter (Smithery): `"{\"scrapegraphApiKey\":\"key\"}"`
2. Environment variable: `SGAI_API_KEY`
3. Default: `None` (server fails to initialize)

**Server Transport:**
- **stdio** - Standard input/output (default for MCP)
- Communication via JSON-RPC over stdin/stdout
- **http** - Remote deployment (set `MCP_TRANSPORT=http`). Streamable-HTTP endpoint
  served at `/mcp`; health check at `/health`. Used by the Render deployment at
  `mcp.scrapegraphai.com`.

**Browser redirect (base domain `/`):**
- `/mcp` is the live MCP streamable-HTTP endpoint (JSON-RPC `POST`, SSE `GET`
  with `Accept: text/event-stream`) and is left untouched.
- `BrowserRedirectMiddleware` (in `server.py`, HTTP mode only) redirects **only**
  human browser navigations to the base domain — `GET`/`HEAD` on `/` with
  `Accept: text/html` — to the docs (`302`). Real MCP traffic (`/mcp`) and the
  `/health` endpoint are untouched.
- Target is `https://docs.scrapegraphai.com/services/mcp-server/introduction`,
  overridable via the `MCP_DOCS_URL` env var.

### Production Considerations

**Error Handling:**
- All tool functions return error dictionaries instead of raising exceptions
- Prevents server crashes on API errors
- Graceful degradation for AI assistants

**Timeout:**
- 60-second timeout for all API requests
- Prevents hanging on slow websites
- Consider increasing for large crawls

**API Key Security:**
- Never commit API keys to version control
- Use environment variables or config files
- Rotate keys periodically

**Rate Limiting:**
- Handled by the ScrapeGraphAI API
- MCP server has no built-in rate limiting
- Consider implementing client-side throttling for high-volume use

---

## Recent Updates

### October 2025

**SmartCrawler Integration (Latest):**
- Added `crawl_start()` tool for multi-page crawling
- Added `crawl_get_status()` tool for async result retrieval
- Support for AI extraction mode (10 credits/page) and markdown mode (2 credits/page)
- Configurable depth, max_pages, and same_domain_only parameters
- Enhanced error handling for extraction mode validation

**Recent Commits:**
- `aebeebd` - Merge PR #5: Update to new features and add SmartCrawler
- `b75053d` - Merge PR #4: Fix SmartCrawler issues
- `54b330d` - Enhance error handling in ScapeGraphClient for extraction modes
- `b3139dc` - Refactor web crawling methods to SmartCrawler terminology
- `94173b0` - Add MseeP.ai security assessment badge
- `53c2d99` - Add MCP server badge

**Key Features:**
1. **SmartCrawler Support** - Multi-page crawling with AI or markdown modes
2. **Enhanced Error Handling** - Validation for extraction modes and prompts
3. **Async Operation Support** - Initiate/fetch pattern for long-running crawls
4. **Security Badges** - MseeP.ai security assessment and MCP server badges

---

## Development

### Running Locally

**Prerequisites:**
- Python 3.10+
- pip or pipx

**Install Dependencies:**
```bash
pip install -e ".[dev]"
```

**Run Server:**
```bash
export SGAI_API_KEY=your-api-key
python -m scrapegraph_mcp.server
# or
scrapegraph-mcp
```

**Test with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector scrapegraph-mcp
```

### Code Quality

**Linting:**
```bash
ruff check src/
```

**Type Checking:**
```bash
mypy src/
```

**Configuration:**
- **Ruff:** Line length 100, target Python 3.12, rules: E, F, I, B, W
- **mypy:** Python 3.12, strict mode, disallow untyped defs

### Project Structure Best Practices

**Single-File Architecture:**
- All code in `src/scrapegraph_mcp/server.py`
- Simple, easy to understand
- Minimal dependencies
- No complex abstractions

**When to Refactor:**
- If adding 5+ new tools, consider splitting into modules
- If adding authentication logic, create separate auth module
- If adding caching, create separate cache module

---

## Testing

### Manual Testing

**Test scrape:**
```bash
echo '{"method":"tools/call","params":{"name":"scrape","arguments":{"website_url":"https://scrapegraphai.com"}}}' | scrapegraph-mcp
```

**Test extract:**
```bash
echo '{"method":"tools/call","params":{"name":"extract","arguments":{"user_prompt":"Extract main features","website_url":"https://scrapegraphai.com"}}}' | scrapegraph-mcp
```

**Test search:**
```bash
echo '{"method":"tools/call","params":{"name":"search","arguments":{"user_prompt":"Latest AI news"}}}' | scrapegraph-mcp
```

### Integration Testing

**Claude Desktop:**
1. Configure MCP server in Claude Desktop
2. Restart Claude
3. Ask: "Convert https://scrapegraphai.com to markdown"
4. Verify tool is called and results returned

**Cursor:**
1. Add MCP server in settings
2. Test with chat prompts
3. Verify tool integration

---

## Troubleshooting

### Common Issues

**Issue: "ScapeGraph client not initialized"**
- **Cause:** Missing API key
- **Solution:** Set `SGAI_API_KEY` environment variable or pass via `--config`

**Issue: "Error 401: Unauthorized"**
- **Cause:** Invalid API key
- **Solution:** Verify API key at [dashboard.scrapegraphai.com](https://dashboard.scrapegraphai.com)

**Issue: "Error 402: Payment Required"**
- **Cause:** Insufficient credits
- **Solution:** Add credits to your account

**Issue: "Error 504: Gateway Timeout"**
- **Cause:** Website took too long to scrape
- **Solution:** Retry or use `markdown_only=True` for faster processing

**Issue: Windows cmd.exe not found**
- **Cause:** Smithery can't find Windows command prompt
- **Solution:** Use full path `C:\Windows\System32\cmd.exe`

**Issue: SmartCrawler not returning results**
- **Cause:** Still processing (async operation)
- **Solution:** Keep polling `crawl_get_status()` until `status == "completed"`

---

## Contributing

### Adding New Tools

1. Add method to `ScapeGraphClient` class:
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

2. Add MCP tool decorator:
```python
@mcp.tool()
def new_tool(param: str) -> Dict[str, Any]:
    """Tool description for AI."""
    if scrapegraph_client is None:
        return {"error": "Client not initialized"}
    try:
        return scrapegraph_client.new_tool(param)
    except Exception as e:
        return {"error": str(e)}
```

3. Update documentation:
- Add tool to [MCP Tools](#mcp-tools) section
- Update README.md
- Update API integration section

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run linting and type checking
5. Test with Claude Desktop or Cursor
6. Submit pull request

---

## License

This project is distributed under the MIT License. See [LICENSE](../../LICENSE) file for details.

---

## Acknowledgments

- **[tomekkorbak](https://github.com/tomekkorbak)** - For [oura-mcp-server](https://github.com/tomekkorbak/oura-mcp-server) implementation inspiration
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - For the MCP specification
- **[Smithery](https://smithery.ai/)** - For MCP server distribution platform
- **[ScrapeGraphAI Team](https://scrapegraphai.com)** - For the API and support

---

**Made with ❤️ by [ScrapeGraphAI](https://scrapegraphai.com) Team**
