FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy dependency files first (for caching)
COPY services/discovery_engine/pyproject.toml \
     services/discovery_engine/uv.lock \
     services/discovery_engine/.python-version ./

# Copy wheel(s) into the image
COPY packages ./packages

# Install dependencies (including local wheel)
RUN uv sync --frozen --no-dev \
	&& uv pip install ./packages/pazyr_core-0.1.0-py3-none-any.whl

# Copy source code last
COPY services/discovery_engine/src ./src

CMD ["uv", "run", "discovery-engine"]
