FROM python:3.11-slim

LABEL maintainer="AutoACMG Contributors"
LABEL description="Automated ACMG/AMP variant classification tool"

# System dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    pango1.0-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies first (layer caching)
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p /root/.autoacmg/cache

# Default command
ENTRYPOINT ["autoacmg"]
CMD ["--help"]

# API server mode
# docker run -p 8000:8000 autoacmg serve --host 0.0.0.0 --port 8000
