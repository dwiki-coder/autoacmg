# AutoACMG

> Automated ACMG/AMP variant classification for clinical genome reporting.

AutoACMG automates the classification of genetic variants according to the
[ACMG/AMP 2015 guidelines](https://doi.org/10.1038/gim.2015.30) (Richards et
al.). It queries multiple clinical databases, applies evidence-based criteria,
and produces structured reports in JSON, CSV, HTML, and PDF formats.

## Features

- **ACMG/AMP 2015 guidelines** – Implements all pathogenic (PVS1–PP6) and
  benign (BA1–BP7) criteria with automated scoring logic
- **Multi-database integration** – ClinVar, gnomAD, CADD, ClinGen, dbSNP, COSMIC
- **VCF input** – Parse standard and annotated VCF files
- **CLI & REST API** – Typer-based CLI and FastAPI web server
- **Report generation** – JSON, CSV, HTML (Jinja2), PDF (WeasyPrint)
- **SQLite caching** – Persistent cache with TTL for fast re-runs
- **Docker support** – Containerized deployment with docker-compose

## Installation

```bash
# Clone the repository
git clone https://github.com/username/autoacmg.git
cd autoacmg

# Install with pip
pip install .

# Or for development with all extras
pip install -e ".[dev,api,report]"
```

### Docker

```bash
# Build and run the API server
docker-compose up -d

# Or build manually
docker build -t autoacmg:latest .
docker run -p 8000:8000 autoacmg serve --host 0.0.0.0 --port 8000
```

## Quick Start

```bash
# Annotate and classify a single variant
autoacmg annotate -c 1 -p 7674232 -r G -a A -s patient001

# Classify all variants in a VCF file
autoacmg classify variants.vcf -o results.json -f json

# Generate an HTML report
autoacmg report results.json -o report.html -f html

# Start the REST API server
autoacmg serve --host 0.0.0.0 --port 8000
```

## Usage

### Annotate a Single Variant

```bash
autoacmg annotate -c 17 -p 43061583 -r C -a T -s sample1 \
  --sources clinvar,gnomad,cadd
```

### Classify Variants from VCF

```bash
# Classify without external queries (offline mode)
autoacmg classify variants.vcf -o results.json --no-annotate

# Classify with full database queries
autoacmg classify variants.vcf -o results.json -f json

# Generate a report from results
autoacmg report results.json -o report.html -f html
```

### REST API

```bash
# Start the server
autoacmg serve --host 0.0.0.0 --port 8000

# Annotate a variant via API
curl -X POST http://localhost:8000/api/v1/annotate \
  -H "Content-Type: application/json" \
  -d '{"chromosome":"1","position":7674232,"ref":"G","alt":"A"}'

# Batch annotate
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"variants":[
    {"chromosome":"1","position":7674232,"ref":"G","alt":"A"},
    {"chromosome":"17","position":43061583,"ref":"C","alt":"T"}
  ]}'
```

### Python API

```python
from autoacmg.core.variant import Variant
from autoacmg.core.classifier import ACMGClassifier
from autoacmg.core.evidence import EvidenceGatherer

# Create a variant
variant = Variant(
    chromosome="17",
    position=43061583,
    ref="C",
    alt="T",
    sample_id="patient001",
)

# Gather evidence from databases
gatherer = EvidenceGatherer()
gatherer.annotate(variant)

# Classify
classifier = ACMGClassifier()
result = classifier.classify(variant)

print(f"Classification: {result.final_classification}")
print(f"Criteria: {result.criteria_string}")
```

## ACMG/AMP Criteria

AutoACMG implements all criteria from the 2015 guidelines:

| Category | Pathogenic | Benign |
|----------|-----------|--------|
| Very Strong | PVS1 | BA1 |
| Strong | PS1–PS7 | BS1 |
| Moderate | PM1–PM6 | BS2–BS4 |
| Supporting | PP1–PP5 | BP1–BP4, BP6–BP7 |

Classification decision rules follow Table 2 of Richards et al. (2015).

## Project Structure

```
autoacmg/
├── autoacmg/
│   ├── core/           # Variant model, classifier, ACMG criteria
│   ├── databases/      # Database connectors (ClinVar, gnomAD, etc.)
│   ├── reports/        # Report generators (JSON, CSV, HTML, PDF)
│   ├── cache/          # SQLite caching layer
│   ├── utils/          # VCF parser, config, logging
│   ├── api/            # FastAPI server
│   └── cli.py          # Typer CLI
├── tests/              # Pytest test suite
├── data/               # Example VCF files and expected outputs
├── docs/               # Documentation
└── notebooks/          # Jupyter notebooks
```

## Development

```bash
# Install development dependencies
make dev-install

# Run tests
make test

# Run with coverage
make test-cov

# Format code
make format

# Run linters
make lint
```

## References

1. Richards S, et al. (2015). Standards and guidelines for the interpretation
   of sequence variants. _Genetics in Medicine_ 17(5):555–566.
2. Abrol R, et al. (2015). ACMG Laboratory Quality Assurance Committee
   guidelines interpretation of loss of function variants. _Genet Med_.
3. Tavtigian S, et al. (2018). ACMG SF v3.1 specification for secondary
   findings v3.1. _Genet Med_.

## License

MIT
