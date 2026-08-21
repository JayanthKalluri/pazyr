FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy dependency files first for better layer caching
COPY services/analysing_engine/pyproject.toml \
     services/analysing_engine/uv.lock ./

# Copy local packages
COPY packages ./packages

# Copy application source
COPY services/analysing_engine/src ./src

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev \
    && uv pip install ./packages/pazyr_core-0.1.0-py3-none-any.whl

# Ensure the venv is used by default
ENV PATH="/app/.venv/bin:${PATH}"

# Run the application
CMD ["uv", "run", "analysing-engine"]