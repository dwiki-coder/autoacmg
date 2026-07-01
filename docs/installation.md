# Installation Guide

## Prerequisites

- **Python 3.11+**
- **pip** (or `conda`)
- Optional: Docker & Docker Compose for containerized deployment

## Standard Installation

```bash
pip install autoacmg
```

## Development Installation

```bash
git clone https://github.com/username/autoacmg.git
cd autoacmg
pip install -e ".[dev,api,report]"
```

This installs:
- Core dependencies (typer, requests, pydantic, pysam)
- API dependencies (fastapi, uvicorn)
- Report dependencies (weasyprint, reportlab)
- Development tools (pytest, black, ruff, mypy)

## Docker Installation

```bash
# Build the image
docker build -t autoacmg:latest .

# Run the CLI
docker run --rm autoacmg annotate -c 1 -p 100 -r A -a G

# Run the API server
docker run -p 8000:8000 autoacmg serve --host 0.0.0.0 --port 8000
```

## Docker Compose

```bash
docker-compose up -d
```

## System Dependencies

For PDF report generation (WeasyPrint):

```bash
# Debian/Ubuntu
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 libffi-dev libcairo2

# RHEL/CentOS
sudo yum install pango cairo pango-devel cairo-devel

# macOS
brew install pango cairo
```

## Verification

```bash
autoacmg --version
autoacmg annotate -c 1 -p 100 -r A -a G --no-annotate
```
