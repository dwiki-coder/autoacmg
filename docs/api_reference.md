# API Reference

## Core Modules

### `autoacmg.core.variant`

#### `Variant`

```python
class Variant(BaseModel):
    chromosome: str          # Chromosome name ("1", "X", "MT")
    position: int             # 1-based genomic position
    ref: str                 # Reference allele
    alt: str                 # Alternate allele
    sample_id: str           # Sample identifier
    rsid: Optional[str]      # dbSNP rsID
    genomic_region: Optional[GenomicRegion]  # Gene context
    population_frequencies: list[PopulationFrequency]
    clinvar_annotation: Optional[ClinVarAnnotation]
    prediction_scores: list[PredictionScore]
    classifications: list[str]    # Applied ACMG criteria
    final_classification: Optional[ACMGClassification]
    evidence_summary: dict
```

Methods:
- `get_key()` → `"chr:pos:ref:alt"`
- `is_snv()`, `is_insertion()`, `is_deletion()`, `is_mnv()`
- `max_population_af` → float
- `is_novel` → bool
- `to_dict()` → dict

### `autoacmg.core.classifier`

#### `ACMGClassifier`

```python
classifier = ACMGClassifier()
result = classifier.classify(variant)
results = classifier.classify_batch(variants)
```

#### `ClassificationResult`

```python
result.variant_key           # "chr:pos:ref:alt"
result.final_classification  # ACMGClassification enum
result.pathogenic_criteria   # list[CriterionMatch]
result.benign_criteria       # list[CriterionMatch]
result.criteria_string       # "PVS1, PM2, PP3"
result.confidence            # float (0.0–1.0)
result.to_dict()             # Serializable dict
```

### `autoacmg.core.acmg_criteria`

#### `ACMGCriteria`

```python
matches = ACMGCriteria.evaluate_all(variant)
all_criteria = ACMGCriteria.get_all_criteria()
```

## Database Connectors

All connectors implement `BaseDBConnector`:
- `query(variant) → Optional[dict]`
- `close()`

| Connector | Description |
|-----------|-------------|
| `ClinVarConnector` | NCBI E-utilities |
| `gnomADConnector` | gnomAD v4 REST API |
| `CADDConnector` | CADD scores |
| `ClinGenConnector` | ClinGen API |
| `dbSNPConnector` | dbSNP API |
| `COSMICConnector` | COSMIC API |

## Reports

```python
from autoacmg.reports import JSONReport, CSVReport, HTMLReport, PDFReport

report = JSONReport()
json_str = report.generate(results, output_path="report.json")

report = HTMLReport()
html_str = report.generate(results, output_path="report.html")
```

## Cache

```python
from autoacmg.cache.sqlite_cache import SQLiteCache

cache = SQLiteCache(cache_path="~/.autoacmg/cache.db")
cache.set("key", {"data": "value"})
value = cache.get("key")
cache.stats()
cache.close()
```
