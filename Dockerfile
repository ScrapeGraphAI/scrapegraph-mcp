# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python unbuffered mode for real-time logs
ENV PYTHONUNBUFFERED=1

# Copy pyproject.toml and README.md first for better caching
COPY pyproject.toml README.md ./

# Copy the source code
COPY src/ ./src/

# Install the package and its dependencies from pyproject.toml
RUN pip install --no-cache-dir .

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables for remote deployment
# MCP_TRANSPORT: "http" for remote, "stdio" for local (default)
# PORT: Server port (Render sets this automatically)
ENV MCP_TRANSPORT=http
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Run the server
CMD ["python", "-m", "scrapegraph_mcp.server"]
