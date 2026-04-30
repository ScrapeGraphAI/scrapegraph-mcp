# ScrapeGraph MCP Server Documentation

Welcome to the ScrapeGraph MCP Server documentation hub. This directory contains comprehensive documentation for understanding, developing, and maintaining the ScrapeGraph MCP Server.

## 📚 Available Documentation

### System Documentation (`system/`)

#### [Project Architecture](./system/project_architecture.md)
Complete system architecture documentation including:
- **System Overview** - MCP server purpose and capabilities
- **Technology Stack** - Python 3.10+, FastMCP, httpx dependencies
- **Project Structure** - File organization and key files
- **Core Architecture** - MCP design, server architecture, patterns
- **MCP Tools** - API v3 tools (scrape, extract, search, crawl_start, crawl_get_status, schema, credits, history, monitor_*)
- **API Integration** - ScrapeGraphAI API endpoints and credit system
- **Deployment** - Smithery, Claude Desktop, Cursor, Docker setup
- **Recent Updates** - SmartCrawler integration and latest features

#### [MCP Protocol](./system/mcp_protocol.md)
Complete Model Context Protocol integration documentation:
- **What is MCP?** - Protocol overview and key concepts
- **MCP in ScrapeGraph** - Architecture and FastMCP usage
- **Communication Protocol** - JSON-RPC over stdio transport
- **Tool Schema** - Schema generation from Python type hints
- **Error Handling** - Graceful error handling patterns
- **Client Integration** - Claude Desktop, Cursor, custom clients
- **Advanced Topics** - Versioning, streaming, authentication, rate limiting
- **Debugging** - MCP Inspector, logs, troubleshooting

### Task Documentation (`tasks/`)

*Future: PRD and implementation plans for specific features*

### SOP Documentation (`sop/`)

*Future: Standard operating procedures (e.g., adding new tools, testing)*

---

## 🚀 Quick Start

### For New Engineers

1. **Read First:**
   - [Project Architecture - System Overview](./system/project_architecture.md#system-overview)
   - [MCP Protocol - What is MCP?](./system/mcp_protocol.md#what-is-mcp)

2. **Setup Development Environment:**
   - Install Python 3.10+
   - Clone repository: `git clone https://github.com/ScrapeGraphAI/scrapegraph-mcp`
   - Install dependencies: `pip install -e ".[dev]"`
   - Get API key from: [dashboard.scrapegraphai.com](https://dashboard.scrapegraphai.com)

3. **Run the Server:**
   ```bash
   export SGAI_API_KEY=your-api-key
   scrapegraph-mcp
   ```

4. **Test with MCP Inspector:**
   ```bash
   npx @modelcontextprotocol/inspector scrapegraph-mcp
   ```

5. **Integrate with Claude Desktop:**
   - See: [Project Architecture - Deployment](./system/project_architecture.md#deployment)
   - Add config to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

---

## 🔍 Finding Information

### I want to understand...

**...what MCP is:**
- Read: [MCP Protocol - What is MCP?](./system/mcp_protocol.md#what-is-mcp)
- Read: [Project Architecture - Core Architecture](./system/project_architecture.md#core-architecture)

**...how to add a new tool:**
- Read: [Project Architecture - Contributing - Adding New Tools](./system/project_architecture.md#adding-new-tools)
- Example: See existing tools in `src/scrapegraph_mcp/server.py`

**...how tools are defined:**
- Read: [MCP Protocol - Tool Schema](./system/mcp_protocol.md#tool-schema)
- Code: `src/scrapegraph_mcp/server.py` (lines 232-372)

**...how to debug MCP issues:**
- Read: [MCP Protocol - Debugging MCP](./system/mcp_protocol.md#debugging-mcp)
- Tools: MCP Inspector, Claude Desktop logs

**...how to deploy:**
- Read: [Project Architecture - Deployment](./system/project_architecture.md#deployment)
- Options: Smithery (automated), Docker, pip install

**...available tools and their parameters:**
- Read: [Project Architecture - MCP Tools](./system/project_architecture.md#mcp-tools)
- Quick reference: see README “Available Tools” table (v2: + scrape, crawl_stop/resume, credits, history, monitor_*; removed sitemap, agentic_scrapper, *\_status tools)

**...error handling:**
- Read: [MCP Protocol - Error Handling](./system/mcp_protocol.md#error-handling)
- Pattern: Return `{"error": "message"}` instead of raising exceptions

**...how SmartCrawler works:**
- Read: [Project Architecture - Tool #4 & #5](./system/project_architecture.md#4-crawl_start)
- Pattern: Initiate (async) → Poll fetch_results until complete

---

## 🛠️ Development Workflows

### Running Locally

```bash
# Install dependencies
pip install -e ".[dev]"

# Set API key
export SGAI_API_KEY=your-api-key

# Run server
scrapegraph-mcp
# or
python -m scrapegraph_mcp.server
```

### Testing

**Manual Testing (MCP Inspector):**
```bash
npx @modelcontextprotocol/inspector scrapegraph-mcp
```

**Manual Testing (stdio):**
```bash
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"scrape","arguments":{"website_url":"https://scrapegraphai.com","output_format":"markdown"}},"id":1}' | scrapegraph-mcp
# (v2: same tool name; backend calls POST /scrape)
```

**Integration Testing (Claude Desktop):**
1. Configure MCP server in Claude Desktop
2. Restart Claude
3. Ask: "Convert https://scrapegraphai.com to markdown"
4. Verify tool invocation and results

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Format checking
ruff format --check src/
```

### Building Docker Image

```bash
# Build
docker build -t scrapegraph-mcp .

# Run
docker run -e SGAI_API_KEY=your-api-key scrapegraph-mcp

# Test
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | docker run -i -e SGAI_API_KEY=your-api-key scrapegraph-mcp
```

---

## 📊 MCP Tools Reference

Quick reference to all MCP tools:

| Tool | Notes |
|------|--------|
| `scrape` | POST /scrape (v2) |
| `extract` | POST /extract; URL only |
| `search` | POST /search; num_results 3–20 |
| `smartcrawler_*`, `crawl_stop`, `crawl_resume` | POST/GET /crawl |
| `credits`, `history` | GET /credits, /history |
| `monitor_*` | /monitor namespace |

For detailed tool documentation, see [Project Architecture - MCP Tools](./system/project_architecture.md#mcp-tools).

---

## 🔧 Key Files Reference

### Core Files
- `src/scrapegraph_mcp/server.py` - Main server implementation (all code)
- `src/scrapegraph_mcp/__init__.py` - Package initialization

### Configuration
- `pyproject.toml` - Project metadata, dependencies, build config
- `Dockerfile` - Docker container definition
- `smithery.yaml` - Smithery deployment config

### Documentation
- `README.md` - User-facing documentation
- `.agent/README.md` - This file (developer documentation index)
- `.agent/system/project_architecture.md` - Architecture documentation
- `.agent/system/mcp_protocol.md` - MCP protocol documentation

---

## 🚨 Troubleshooting

### Common Issues

**Issue: "ScapeGraph client not initialized"**
- **Cause:** Missing `SGAI_API_KEY` environment variable
- **Solution:** Set `export SGAI_API_KEY=your-api-key` or pass via `--config`

**Issue: "Error 401: Unauthorized"**
- **Cause:** Invalid API key
- **Solution:** Verify API key at [dashboard.scrapegraphai.com](https://dashboard.scrapegraphai.com)

**Issue: "Error 402: Payment Required"**
- **Cause:** Insufficient credits
- **Solution:** Add credits to your ScrapeGraphAI account

**Issue: Tools not appearing in Claude Desktop**
- **Cause:** Server not starting or config error
- **Solution:** Check Claude logs at `~/Library/Logs/Claude/` (macOS)

**Issue: SmartCrawler not returning results**
- **Cause:** Still processing (async operation)
- **Solution:** Keep polling `crawl_get_status()` until `status == "completed"`

**Issue: Python version error**
- **Cause:** Python < 3.10
- **Solution:** Upgrade Python to 3.10+

For more troubleshooting, see:
- [Project Architecture - Troubleshooting](./system/project_architecture.md#troubleshooting)
- [MCP Protocol - Debugging MCP](./system/mcp_protocol.md#debugging-mcp)

---

## 🤝 Contributing

### Before Making Changes

1. **Read relevant documentation** - Understand MCP and the server architecture
2. **Check existing issues** - Avoid duplicate work
3. **Test locally** - Use MCP Inspector to verify changes
4. **Test with clients** - Verify with Claude Desktop or Cursor

### Adding a New Tool

**Step-by-step guide:**

1. **Add method to `ScapeGraphClient` class:**
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

2. **Add MCP tool decorator:**
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
        return {"error": "ScapeGraph client not initialized. Please provide an API key."}

    try:
        return scrapegraph_client.new_tool(param)
    except Exception as e:
        return {"error": str(e)}
```

3. **Test with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector scrapegraph-mcp
```

4. **Update documentation:**
- Add tool to [Project Architecture - MCP Tools](./system/project_architecture.md#mcp-tools)
- Add schema to [MCP Protocol - Tool Schema](./system/mcp_protocol.md#tool-schema)
- Update tool reference table in this README

5. **Submit pull request**

### Development Process

1. **Make changes** - Edit `src/scrapegraph_mcp/server.py`
2. **Run linting** - `ruff check src/`
3. **Run type checking** - `mypy src/`
4. **Test locally** - MCP Inspector + Claude Desktop
5. **Update docs** - Keep `.agent/` docs in sync
6. **Commit** - Clear commit message
7. **Create PR** - Describe changes thoroughly

### Code Style

- **Ruff:** Line length 100, target Python 3.12
- **mypy:** Strict mode, disallow untyped defs
- **Type hints:** Always use type hints for parameters and return values
- **Docstrings:** Google-style docstrings for all public functions
- **Error handling:** Return error dicts, don't raise exceptions in tools

---

## 📖 External Documentation

### MCP Resources
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)

### ScrapeGraphAI Resources
- [ScrapeGraphAI Homepage](https://scrapegraphai.com)
- [ScrapeGraphAI Dashboard](https://dashboard.scrapegraphai.com)
- [ScrapeGraphAI API Documentation](https://api.scrapegraphai.com/docs)

### AI Assistant Integration
- [Claude Desktop](https://claude.ai/desktop)
- [Cursor](https://cursor.sh/)
- [Smithery MCP Distribution](https://smithery.ai/)

### Development Tools
- [Python httpx](https://www.python-httpx.org/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [mypy Type Checker](https://mypy-lang.org/)

---

## 📝 Documentation Maintenance

### When to Update Documentation

**Update `.agent/system/project_architecture.md` when:**
- Adding new MCP tools
- Changing tool parameters or return types
- Updating deployment methods
- Modifying technology stack

**Update `.agent/system/mcp_protocol.md` when:**
- Changing MCP protocol implementation
- Adding new communication patterns
- Modifying error handling strategy
- Updating authentication method

**Update `.agent/README.md` when:**
- Adding new documentation files
- Changing development workflows
- Updating quick start instructions

### Documentation Best Practices

1. **Keep it current** - Update docs with code changes in the same PR
2. **Be specific** - Include code snippets, file paths, line numbers
3. **Include examples** - Show real-world usage patterns
4. **Link related sections** - Cross-reference between documents
5. **Test examples** - Verify all code examples work

---

## 📅 Changelog

### April 2026
- ✅ Migrated MCP client and tools to **API v2** ([scrapegraph-py#84](https://github.com/ScrapeGraphAI/scrapegraph-py/pull/84)): base `https://v2-api.scrapegraphai.com/api`, `SGAI-APIKEY` header (matches SDK wire format), new crawl/monitor/credits/history tools; removed sitemap, agentic_scrapper, status polling tools. Env vars aligned with SDK: `SGAI_API_URL`, `SGAI_TIMEOUT` (legacy alias `SGAI_TIMEOUT_S` still honored).
- ✅ Added `monitor_activity` tool for paginated tick history (GET /monitor/:id/activity), mirroring `sgai.monitor.activity()` in scrapegraph-py v2.

### January 2026
- ✅ Added `time_range` parameter to SearchScraper for filtering results by recency (v1-era; **ignored on API v2**)
- ✅ Supported time ranges: `past_hour`, `past_24_hours`, `past_week`, `past_month`, `past_year`
- ✅ Documentation updated to reflect SDK changes (scrapegraph-py#77, scrapegraph-js#2)

### October 2025
- ✅ Initial comprehensive documentation created
- ✅ Project architecture fully documented
- ✅ MCP protocol integration documented
- ✅ All 5 MCP tools documented
- ✅ SmartCrawler integration (initiate + fetch_results)
- ✅ Deployment guides (Smithery, Docker, Claude Desktop, Cursor)
- ✅ Recent updates: Enhanced error handling, extraction mode validation

---

## 🔗 Quick Links

- [Main README](../README.md) - User-facing documentation
- [Server Implementation](../src/scrapegraph_mcp/server.py) - All code (single file)
- [pyproject.toml](../pyproject.toml) - Project metadata
- [Dockerfile](../Dockerfile) - Docker configuration
- [smithery.yaml](../smithery.yaml) - Smithery config
- [GitHub Repository](https://github.com/ScrapeGraphAI/scrapegraph-mcp)

---

## 📧 Support

For questions or issues:
1. Check this documentation first
2. Review [Project Architecture](./system/project_architecture.md) and [MCP Protocol](./system/mcp_protocol.md)
3. Test with [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
4. Search [GitHub issues](https://github.com/ScrapeGraphAI/scrapegraph-mcp/issues)
5. Create a new issue with detailed information

---

**Made with ❤️ by [ScrapeGraphAI](https://scrapegraphai.com) Team**

**Happy Coding! 🚀**
