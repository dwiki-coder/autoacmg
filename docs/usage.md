# Usage Guide

## CLI Commands

### annotate

Annotate and classify a single variant:

```bash
autoacmg annotate -c 17 -p 43061583 -r C -a T -s patient001
autoacmg annotate -c 1 -p 7674232 -r G -a A --sources clinvar,gnomad,cadd
autoacmg annotate -c 1 -p 100 -r A -a G --no-annotate  # offline mode
autoacmg annotate -c 1 -p 100 -r A -a G -o result.json  # save to file
```

### classify

Classify all variants in a VCF file:

```bash
autoacmg classify variants.vcf -o results.json -f json
autoacmg classify variants.vcf -o results.csv -f csv
autoacmg classify variants.vcf --no-annotate  # offline
autoacmg classify variants.vcf --sources clinvar,gnomad
```

### report

Generate reports from classification results:

```bash
autoacmg report results.json -o report.html -f html
autoacmg report results.json -o report.pdf -f pdf
autoacmg report results.json -o summary.csv -f csv
```

### serve

Start the REST API server:

```bash
autoacmg serve --host 0.0.0.0 --port 8000
autoacmg serve --workers 4
autoacmg serve --reload  # development mode
```

## REST API Endpoints

### POST /api/v1/annotate

```json
{
  "chromosome": "1",
  "position": 7674232,
  "ref": "G",
  "alt": "A",
  "sample_id": "patient001",
  "annotate": true,
  "sources": ["clinvar", "gnomad", "cadd"]
}
```

### POST /api/v1/batch

```json
{
  "variants": [
    {"chromosome": "1", "position": 7674232, "ref": "G", "alt": "A"},
    {"chromosome": "17", "position": 43061583, "ref": "C", "alt": "T"}
  ],
  "annotate": true,
  "sources": ["clinvar", "gnomad"]
}
```

### GET /api/v1/status

Returns API status and available sources.

### GET /health

Health check endpoint.

## Python API

```python
from autoacmg.core.variant import Variant
from autoacmg.core.classifier import ACMGClassifier
from autoacmg.core.evidence import EvidenceGatherer
from autoacmg.reports.json_report import JSONReport

# Create variant
variant = Variant(chromosome="17", position=43061583, ref="C", alt="T")

# Gather evidence
gatherer = EvidenceGatherer()
gatherer.annotate(variant)

# Classify
classifier = ACMGClassifier()
result = classifier.classify(variant)

# Generate report
report = JSONReport()
json_str = report.generate([result])
```

## VCF File Format

AutoACMG supports standard VCF 4.3 format with optional INFO annotations:

```vcf
##INFO=<ID=GENE,Number=1,Type=String,Description="Gene symbol">
##INFO=<ID=CONSEQUENCE,Number=1,Type=String,Description="Variant consequence">
##INFO=<ID=PROTEIN_CHANGE,Number=1,Type=String,Description="Protein change">
#CHROM  POS  ID  REF  ALT  QUAL  FILTER  INFO
chr1    123  .   A    G    .     .       GENE=BRCA1;CONSEQUENCE=missense_variant
```
