# SOP: Run the MCP Server Locally in Claude Code

How to run this repo's server over stdio and register it with Claude Code for this project only.

## Prerequisites

- Python 3.10+ (`requires-python` in `pyproject.toml`). macOS system Python is 3.9, so use uv to get a managed interpreter.
- A ScrapeGraph API key from [dashboard.scrapegraphai.com](https://dashboard.scrapegraphai.com)

## Steps

1. **Install uv** (installs to `~/.local/bin`, no sudo needed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create the environment** from `uv.lock` (uv downloads CPython 3.12 if it's missing):
   ```bash
   uv sync --python 3.12
   ```

3. **Smoke test over stdio.** The last line of output should be a `tools/list` result with 17 tools:
   ```bash
   (printf '%s\n' \
     '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
     '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
     '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'; sleep 5) \
     | SGAI_API_KEY=dummy uv run scrapegraph-mcp 2>/dev/null | tail -1
   ```

4. **Register with Claude Code** by adding `.mcp.json` at the repo root:
   ```json
   {
     "mcpServers": {
       "scrapegraph-local": {
         "command": "uv",
         "args": ["run", "scrapegraph-mcp"],
         "env": { "SGAI_API_KEY": "${SGAI_API_KEY}" }
       }
     }
   }
   ```
   Claude Code fills in `${SGAI_API_KEY}` from your shell when it launches the server, so the key never goes into the file. `uv run` resolves the project from the working directory, which Claude Code sets to the repo root.

5. **Provide the key and approve the server:**
   ```bash
   echo 'export SGAI_API_KEY=your-api-key' >> ~/.zshrc && source ~/.zshrc
   claude   # approve "scrapegraph-local" when prompted
   ```

## Verify

- `claude mcp list` shows `scrapegraph-local: uv run scrapegraph-mcp - ✔ Connected`
- Calling the `credits` tool in a session returns your balance instead of a 401.

## Troubleshooting

- **`Missing environment variables: SGAI_API_KEY`**: the key isn't exported in the shell that started `claude`.
- **`ScapeGraph API key is required`**: `get_api_key()` in `server.py` checks, in order, the `X-API-Key` header, the Smithery `scrapegraphApiKey` session config, and then `SGAI_API_KEY`. If you see this error, none of the three is set in the server's environment.
- **`⏸ Pending approval`**: start `claude` in the repo and approve the project server (or use `/mcp`).
- **Server fails to start from another cwd**: change the args to `["run", "--directory", "/abs/path/to/repo", "scrapegraph-mcp"]`.
