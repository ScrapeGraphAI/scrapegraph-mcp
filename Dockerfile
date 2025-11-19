# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python unbuffered mode
ENV PYTHONUNBUFFERED=1

# Copy pyproject.toml and README.md first for better caching
COPY pyproject.toml README.md ./

# Copy the source code
COPY src/ ./src/

# Install the package and its dependencies from pyproject.toml
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Run the server
CMD ["python", "-m", "scrapegraph_mcp.server"]

