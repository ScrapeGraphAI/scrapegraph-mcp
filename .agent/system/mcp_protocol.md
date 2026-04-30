# Model Context Protocol (MCP) Integration

**Last Updated:** October 2025

## Table of Contents
- [What is MCP?](#what-is-mcp)
- [MCP in ScrapeGraph](#mcp-in-scrapegraph)
- [Communication Protocol](#communication-protocol)
- [Tool Schema](#tool-schema)
- [Error Handling](#error-handling)
- [Client Integration](#client-integration)

---

## What is MCP?

The **Model Context Protocol** (MCP) is an open standard that defines how AI assistants (like Claude, Cursor, etc.) can interact with external tools and services in a consistent, structured way.

**Official Documentation:** [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)

### Key Concepts

**1. Server**
- Exposes tools that AI assistants can use
- Implements MCP protocol
- Runs as a separate process
- **Example:** This ScrapeGraph MCP server

**2. Client**
- AI assistant that uses the tools
- Sends tool invocation requests
- Receives tool results
- **Examples:** Claude Desktop, Cursor, other AI assistants

**3. Transport**
- Communication layer between client and server
- **Types:** stdio (standard input/output), HTTP, SSE
- **This server uses:** stdio

**4. Tools**
- Functions exposed by the server
- Have typed parameters and return values
- Automatically discovered by AI assistants
- **Examples:** `scrape()`, `extract()`

**5. Resources**
- Data exposed by the server (optional)
- Not used in this implementation

**6. Prompts**
- Pre-defined prompts exposed by the server (optional)
- Not used in this implementation

---

## MCP in ScrapeGraph

### Architecture Overview

```
┌─────────────────────────────────┐
│   AI Assistant (Client)         │
│   - Claude Desktop              │
│   - Cursor                      │
│   - Other MCP-compatible AIs    │
└────────────┬────────────────────┘
             │ MCP Protocol (JSON-RPC over stdio)
             │ - Tool discovery
             │ - Tool invocation
             │ - Result streaming
             ▼
┌─────────────────────────────────┐
│   FastMCP Server                │
│   - Tool registry               │
│   - Parameter validation        │
│   - Serialization/              │
│     deserialization             │
└────────────┬────────────────────┘
             │ Python function calls
             ▼
┌─────────────────────────────────┐
│   ScapeGraphClient              │
│   - HTTP client (httpx)         │
│   - API authentication          │
│   - Error handling              │
└────────────┬────────────────────┘
             │ HTTPS API requests
             ▼
┌───────────────────────────────────┐
│   ScrapeGraphAI API               │
│   v2-api.scrapegraphai.com/api    │
└───────────────────────────────────┘
```

### FastMCP Framework

This server uses **FastMCP**, a lightweight Python framework for building MCP servers:

```python
from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("ScapeGraph API MCP Server")

# Define tools with decorators
@mcp.tool()
def scrape(website_url: str) -> Dict[str, Any]:
    """Convert a webpage to markdown."""
    # Implementation...
    return {"result": "..."}

# Run the server
mcp.run(transport="stdio")
```

**FastMCP Features:**
- Automatic tool discovery from decorated functions
- Type hint → MCP schema generation
- Request/response serialization
- Error handling
- Stdio transport out-of-the-box

---

## Communication Protocol

### Transport: stdio

**Standard Input/Output (stdio)** is used for client-server communication:

- **stdin (→ Server):** Client sends JSON-RPC requests
- **stdout (← Client):** Server sends JSON-RPC responses
- **stderr (← Client):** Server logs (not part of MCP protocol)

**Example Flow:**
```
Client → Server (stdin):
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "scrape", "arguments": {"website_url": "https://example.com"}}, "id": 1}

Server → Client (stdout):
{"jsonrpc": "2.0", "result": {"result": "# Example\n\nMarkdown content..."}, "id": 1}
```

### JSON-RPC 2.0

MCP uses JSON-RPC 2.0 for message structure:

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "extract",
    "arguments": {
      "user_prompt": "Extract product names",
      "website_url": "https://example.com"
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "result": {
      "products": ["Product A", "Product B"]
    }
  },
  "id": 1
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "Error 401: Unauthorized"
  },
  "id": 1
}
```

### MCP Methods

**Tool Discovery:**
```json
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}

Response:
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "scrape",
        "description": "Convert a webpage into clean, formatted markdown.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "website_url": {"type": "string"}
          },
          "required": ["website_url"]
        }
      },
      // ... other tools
    ]
  },
  "id": 1
}
```

**Tool Invocation:**
```json
{"jsonrpc": "2.0", "method": "tools/call", "params": {...}, "id": 1}
```

**Initialize:**
```json
{"jsonrpc": "2.0", "method": "initialize", "params": {...}, "id": 1}
```

---

## Tool Schema

Each tool exposed by the server has a schema that defines its parameters and return type.

### Example: `scrape` Tool

**Python Definition:**
```python
@mcp.tool()
def scrape(website_url: str) -> Dict[str, Any]:
    """
    Convert a webpage into clean, formatted markdown.

    Args:
        website_url: URL of the webpage to convert

    Returns:
        Dictionary containing the markdown result
    """
    # Implementation...
```

**Generated MCP Schema:**
```json
{
  "name": "scrape",
  "description": "Convert a webpage into clean, formatted markdown.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "website_url": {
        "type": "string",
        "description": "URL of the webpage to convert"
      }
    },
    "required": ["website_url"]
  }
}
```

**Type Mapping:**
- Python `str` → JSON Schema `"type": "string"`
- Python `int` → JSON Schema `"type": "integer"`
- Python `bool` → JSON Schema `"type": "boolean"`
- Python `Dict[str, Any]` → JSON Schema `"type": "object"`
- Python `Optional[str]` → JSON Schema `"type": ["string", "null"]`

### Example: `extract` Tool (with optional parameters)

**Python Definition:**
```python
@mcp.tool()
def extract(
    user_prompt: str,
    website_url: str,
    number_of_scrolls: int = None,
    markdown_only: bool = None
) -> Dict[str, Any]:
    """Extract structured data from a webpage using AI."""
    # Implementation...
```

**Generated MCP Schema:**
```json
{
  "name": "extract",
  "description": "Extract structured data from a webpage using AI.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_prompt": {"type": "string"},
      "website_url": {"type": "string"},
      "number_of_scrolls": {"type": ["integer", "null"]},
      "markdown_only": {"type": ["boolean", "null"]}
    },
    "required": ["user_prompt", "website_url"]
  }
}
```

---

## Error Handling

### Error Strategy

The server implements **graceful error handling** to prevent crashes and provide meaningful feedback to AI assistants.

**Approach:**
1. **No exceptions to client** - All errors caught in tool functions
2. **Error dictionaries** - Return `{"error": "message"}` instead of raising
3. **Detailed messages** - Include HTTP status codes and API error messages

### Error Handling Pattern

```python
@mcp.tool()
def tool_name(param: str) -> Dict[str, Any]:
    """Tool description."""
    if scrapegraph_client is None:
        return {"error": "ScapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.method(param)
    except Exception as e:
        return {"error": str(e)}
```

**Why this approach?**
- Prevents server crashes
- Allows AI to handle errors gracefully
- Enables retry logic
- Provides context for user troubleshooting

### Error Types

**1. Client Not Initialized:**
```json
{
  "error": "ScapeGraph client not initialized. Please provide an API key."
}
```

**Cause:** Missing `SGAI_API_KEY` environment variable

**2. API Errors:**
```json
{
  "error": "Error 401: Unauthorized"
}
```

**Cause:** Invalid API key

```json
{
  "error": "Error 402: Payment Required - Insufficient credits"
}
```

**Cause:** Not enough credits

```json
{
  "error": "Error 404: Not Found"
}
```

**Cause:** Invalid URL or API endpoint

**3. Network Errors:**
```json
{
  "error": "httpx.ConnectTimeout: Connection timed out"
}
```

**Cause:** Network issues or slow website

**4. Validation Errors (SmartCrawler):**
```json
{
  "error": "prompt is required when extraction_mode is 'ai'"
}
```

**Cause:** Missing required parameter for AI extraction mode

### AI Assistant Error Handling

When a tool returns an error, AI assistants typically:

1. **Parse the error message**
2. **Determine if retryable** (network error) or not (invalid API key)
3. **Inform the user** with actionable guidance
4. **Suggest fixes** (e.g., "Please add credits to your account")

**Example AI Response:**
```
User: "Convert https://example.com to markdown"

Tool result: {"error": "Error 402: Payment Required - Insufficient credits"}

AI: "I wasn't able to convert the webpage because your ScrapeGraphAI account has insufficient credits. Please add credits at https://dashboard.scrapegraphai.com and try again."
```

---

## Client Integration

### Claude Desktop Integration

**Configuration File Location:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

**Configuration:**
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

**How It Works:**
1. Claude Desktop reads the config file on startup
2. Starts the MCP server as a child process using the specified command
3. Establishes stdio communication
4. Discovers available tools via `tools/list`
5. User asks a question that requires web scraping
6. Claude calls the appropriate tool via `tools/call`
7. Server executes the tool and returns results
8. Claude incorporates results into its response

**Example Interaction:**
```
User: "What are the main features of ScrapeGraphAI?"

Claude (internal):
1. Determines that scrape tool could help
2. Calls: scrape("https://scrapegraphai.com")
3. Receives markdown content
4. Analyzes content
5. Responds to user

Claude (to user): "Based on the ScrapeGraphAI website, the main features are:
- AI-powered web scraping
- Multiple scraping modes (SmartScraper, SearchScraper, etc.)
- ...
"
```

### Cursor Integration

**Setup:**
1. Open Cursor settings
2. Navigate to "MCP Servers" section
3. Click "Add MCP Server"
4. Select or configure ScrapeGraphAI MCP
5. Enter API key

**Usage:**
- Cursor's AI chat can automatically invoke MCP tools
- Similar interaction pattern to Claude Desktop
- Tool calls visible in chat interface (optional)

### Custom Client Integration

To integrate with a custom MCP client:

**1. Install the MCP SDK:**
```bash
pip install mcp
```

**2. Create a client:**
```python
import asyncio
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    # Start the server process
    server_params = StdioServerParameters(
        command="scrapegraph-mcp",
        env={"SGAI_API_KEY": "your-api-key"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools]}")

            # Call a tool
            result = await session.call_tool(
                "scrape",
                arguments={"website_url": "https://example.com"}
            )
            print(f"Result: {result}")

asyncio.run(main())
```

**3. Handle tool results:**
```python
if "error" in result:
    print(f"Tool error: {result['error']}")
else:
    print(f"Tool success: {result['result']}")
```

---

## Advanced Topics

### Tool Versioning

Currently, the server does not implement tool versioning. All tools are v1 implicitly.

**Future Consideration:**
- Add version to tool names: `extract_v2()`
- Maintain backward compatibility with deprecated tools
- Use MCP metadata for version info

### Streaming Results

MCP supports streaming results for long-running operations. This could be useful for SmartCrawler:

**Current Approach (polling):**
1. Call `crawl_start()` → get `request_id`
2. Repeatedly call `crawl_get_status(request_id)` until complete

**Potential Streaming Approach:**
1. Call `crawl_start()` → server keeps connection open
2. Server streams progress updates: `{"status": "processing", "pages": 10}`
3. Server sends final result: `{"status": "completed", "results": [...]}`

**Not currently implemented** due to FastMCP limitations.

### Authentication

**Current Approach:**
- API key passed via environment variable or config parameter
- Single API key for entire server instance
- No per-tool authentication

**Future Consideration:**
- Support multiple API keys (user-specific)
- OAuth integration
- JWT tokens

### Rate Limiting

**Current State:**
- No rate limiting in the MCP server
- Rate limiting handled by ScrapeGraphAI API
- Server is a simple pass-through

**Future Consideration:**
- Client-side rate limiting to prevent API quota exhaustion
- Configurable request throttling
- Request queuing

---

## Debugging MCP

### MCP Inspector

The MCP Inspector is a tool for testing MCP servers:

```bash
npx @modelcontextprotocol/inspector scrapegraph-mcp
```

**Features:**
- Interactive tool discovery
- Manual tool invocation
- Request/response inspection
- Error debugging

### Server Logs

**FastMCP Logging:**
```python
# Add logging to server.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@mcp.tool()
def scrape(website_url: str) -> Dict[str, Any]:
    logger.info(f"scrape called with URL: {website_url}")
    # ...
```

**View Logs:**
- Logs printed to stderr (not part of MCP protocol)
- Visible in Claude Desktop logs: `~/Library/Logs/Claude/` (macOS)
- Use MCP Inspector to see real-time logs

### Common Debugging Issues

**Issue: Tools not appearing in Claude**
- **Check:** Is the server running? Look in Claude logs
- **Check:** Is the config file correct? Verify JSON syntax
- **Check:** Does `tools/list` return the tools? Use MCP Inspector

**Issue: Tool calls failing**
- **Check:** Is the API key valid? Test with curl
- **Check:** Are parameters correct? Review tool schema
- **Check:** Network connectivity? Check firewall/proxy

**Issue: Server crashes**
- **Check:** Python version (≥3.10)?
- **Check:** Dependencies installed? `pip list`
- **Check:** Error in logs? Check stderr output

---

## Best Practices

### Tool Design

**1. Clear Descriptions**
- Write docstrings that explain what the tool does
- Include parameter descriptions
- Specify expected input/output formats

**2. Type Hints**
- Always use type hints for parameters and return values
- FastMCP generates schemas from type hints
- Helps AI understand tool contracts

**3. Error Messages**
- Provide actionable error messages
- Include HTTP status codes
- Suggest fixes when possible

**4. Optional Parameters**
- Use `= None` for optional parameters
- Document default behavior
- Don't require unnecessary inputs

### Server Design

**1. Statelessness**
- Each tool invocation should be independent
- Don't rely on shared state between calls
- Use API key from config, not global variable

**2. Idempotency**
- Same inputs should produce same outputs (when possible)
- Helps with retries and debugging
- Cache results when appropriate

**3. Performance**
- Keep tool invocations fast (<60s)
- Use async operations for I/O (future improvement)
- Consider timeouts for slow operations

**4. Security**
- Never log API keys
- Validate all inputs
- Use HTTPS for API calls
- Rotate API keys regularly

---

## References

- **MCP Specification:** [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
- **MCP Python SDK:** [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- **FastMCP:** [https://github.com/jlowin/fastmcp](https://github.com/jlowin/fastmcp)
- **JSON-RPC 2.0:** [https://www.jsonrpc.org/specification](https://www.jsonrpc.org/specification)
- **ScrapeGraphAI API:** [https://api.scrapegraphai.com/docs](https://api.scrapegraphai.com/docs)

---

**Made with ❤️ by [ScrapeGraphAI](https://scrapegraphai.com) Team**
