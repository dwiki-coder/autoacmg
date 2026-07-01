# Graph Report - .  (2026-06-26)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 594 nodes · 1201 edges · 55 communities (33 shown, 22 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 208 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]

## God Nodes (most connected - your core abstractions)
1. `Variant` - 162 edges
2. `ACMGClassifier` - 47 edges
3. `GenomicRegion` - 43 edges
4. `ClassificationResult` - 40 edges
5. `PopulationFrequency` - 40 edges
6. `EvidenceGatherer` - 39 edges
7. `PredictionScore` - 35 edges
8. `ACMGClassification` - 31 edges
9. `BaseDBConnector` - 27 edges
10. `CriterionMatch` - 24 edges

## Surprising Connections (you probably didn't know these)
- `TestACMGCriteriaRegistry` --uses--> `EvidenceStrength`  [INFERRED]
  tests/test_acmg_criteria.py → autoacmg/core/acmg_criteria.py
- `TestBA1` --uses--> `EvidenceStrength`  [INFERRED]
  tests/test_acmg_criteria.py → autoacmg/core/acmg_criteria.py
- `TestBS1` --uses--> `EvidenceStrength`  [INFERRED]
  tests/test_acmg_criteria.py → autoacmg/core/acmg_criteria.py
- `TestCriterionMatch` --uses--> `EvidenceStrength`  [INFERRED]
  tests/test_acmg_criteria.py → autoacmg/core/acmg_criteria.py
- `TestPM2` --uses--> `EvidenceStrength`  [INFERRED]
  tests/test_acmg_criteria.py → autoacmg/core/acmg_criteria.py

## Import Cycles
- None detected.

## Communities (55 total, 22 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (55): Evidence gathering from multiple databases.  Coordinates queries to ClinVar, gno, Apply ClinVar results to variant., ACMGClassification, ClinicalSignificance, ClinVarAnnotation, GenomicRegion, PopulationFrequency, PredictionScore (+47 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (15): ClinVarConnector, ClinVar database connector.  Queries the NCBI E-utilities API for ClinVar varian, Search ClinVar by rsID., Select the most informative ClinVar result.          Prioritizes results with hi, Parse ClinVar JSON result into annotation data., ClinVar database connector using NCBI E-utilities.      Queries ClinVar via the, Query ClinVar for a variant.          Args:             variant: The variant to, Search ClinVar using E-utilities. (+7 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (21): create_app(), lifespan(), AutoACMG FastAPI server.  Provides a REST API for variant annotation and classif, Application lifespan handler., Create and configure the FastAPI application.      Returns:         Configured F, Run the AutoACMG API server.      Args:         host: Bind host.         port: B, run_server(), Start the AutoACMG REST API server.      Example:         autoacmg serve --host (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (14): Any, SQLite-based caching layer for AutoACMG.  Provides persistent caching of databas, Store a value in the cache.          Args:             key: Cache key., Remove a key from the cache.          Args:             key: Cache key to remove, Clear all cached entries.          Returns:             Number of entries cleare, Remove expired entries.          Returns:             Number of entries removed., Get cache statistics.          Returns:             Dictionary with cache statis, Close the database connection. (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (15): generate_report(), Generate a classification report from results.      Example:         autoacmg re, ClassificationResult, Result of ACMG classification for a single variant., Serialize to dictionary., HTMLReport, Generate HTML reports for variant classifications., Generate an HTML report.          Args:             results: List of classificat (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (11): gnomADConnector, gnomAD database connector.  Queries gnomAD v4.1 REST API for population allele f, gnomAD REST API connector.      Queries gnomAD v4.1 for population allele freque, Query gnomAD for variant frequencies.          Args:             variant: The va, Parse gnomAD API response into frequency data., Tests for gnomAD connector., Test parsing genomes data., Test parsing exomes data. (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (12): Create a Variant from a VCF record dictionary.          Args:             vcf_di, VCF file parser for AutoACMG.  Parses VCF files into Variant objects for ACMG cl, Parse VCF content from a string.          Args:             vcf_content: VCF-for, Create variants from a list of VCF dictionaries.          Args:             vcf_, Represents a single VCF record., Parse a VCF record line.          Args:             line: A single VCF record li, Parse VCF INFO field into a dictionary., Convert VCF record to a Variant object. (+4 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (12): JSONReport, Generate JSON reports for variant classifications., Tests for JSON report generator., Empty results should produce valid report., Test JSON report generation., Report should have required top-level fields., Summary should have correct counts., Each variant should appear in the output. (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.18
Nodes (10): CriterionMatch, Result of evaluating a single ACMG criterion., ACMGClassifier, Apply ACMG classification decision rules.          Implements the counting rules, Build the criteria string (e.g., 'PM2, PP3, PP5')., Parse strength string to EvidenceStrength enum., Determine if a criterion code is pathogenic or benign., Classify multiple variants.          Args:             variants: List of variant (+2 more)

### Community 9 - "Community 9"
Cohesion: 0.16
Nodes (17): annotate_variant(), batch_annotate(), BatchVariantRequest, API routes for AutoACMG.  Defines REST endpoints for variant annotation, batch p, Get API status and available sources.      Returns:         Status information., Request model for single variant annotation., Request model for batch variant annotation., Request model for report generation. (+9 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (9): ClinGenConnector, ClinGen database connector.  Queries the ClinGen REST API for: - Gene-disease va, Get gene-disease validity classifications., Get dosage sensitivity classification from CGC., Get LoF intolerance scores (from gnomAD via ClinGen)., Query ClinGen for variant-specific data., ClinGen REST API connector.      Queries ClinGen for gene-disease relationships,, Query ClinGen for gene and variant data.          Args:             variant: The (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.16
Nodes (12): annotate_variant(), classify_vcf(), _display_result(), main(), AutoACMG CLI - Command-line interface for variant classification.  Commands:, Classify variants from a VCF file.      Example:         autoacmg classify varia, Display classification result to console and/or file., Write results to file. (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (18): ACMGCriteria, _check_ba1(), EvidenceCategory, Registry and evaluation engine for ACMG/AMP criteria.      Implements all criter, Whether evidence supports pathogenic or benign classification., Check BA1: allele frequency >> disease prevalence (stand-alone benign)., Initialize the classifier.          Args:             criteria_source: Class pro, Tests for ACMG criteria evaluation logic. (+10 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (8): _check_pvs1(), Check PVS1: null variant in gene where LOF is disease mechanism., No genomic region should not trigger PVS1., stop_gained should trigger PVS1., frameshift_variant should trigger PVS1., nonsense should trigger PVS1., splice_donor should trigger PVS1., Missense should NOT trigger PVS1.

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (8): CADDConnector, CADD score connector.  CADD (Combined Annotation Dependent Deployment) scores ar, Query CADD via web API.          CADD provides a web form for individual variant, Search loaded CADD VCF for variant., CADD score connector.      Supports two modes:     1. Remote query via CADD API, Initialize CADD connector.          Args:             cadd_vcf_path: Path to loc, Load CADD scores from a local VCF file., Query CADD score for a variant.          Args:             variant: The variant

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (8): COSMICConnector, COSMIC database connector.  Queries the COSMIC (Catalogue Of Somatic Mutations I, Parse COSMIC API response., COSMIC API connector.      Queries COSMIC for somatic mutation data in cancer., Initialize COSMIC connector.          Args:             api_key: COSMIC API key., Query COSMIC for somatic mutation data.          Args:             variant: The, Search COSMIC by genomic position., Search COSMIC by variant notation.

### Community 16 - "Community 16"
Cohesion: 0.18
Nodes (8): ABC, BaseDBConnector, Base class for all database connectors.  Provides common functionality for datab, Query the database for variant information.          Args:             variant:, Close the connector and release resources., Abstract base class for database connectors.      All database connectors inheri, Initialize the connector.          Args:             cache_dir: Directory for SQ, Initialize SQLite cache.

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (8): ACMGCriterion, EvidenceStrength, ACMG/AMP criteria definitions and evaluation logic.  Implements the 2015 ACMG/AM, ACMG evidence strength levels., Numeric weight for scoring., Definition of a single ACMG/AMP criterion.      Attributes:         code: Criter, ACMG/AMP Classification Engine.  Implements the classification decision rules fr, AutoACMG core modules for variant classification.

### Community 18 - "Community 18"
Cohesion: 0.20
Nodes (7): Return all defined ACMG/AMP criteria., Test criteria registry., All criteria should be accessible., Key pathogenic criteria should exist., Key benign criteria should exist., Criterion strengths should have correct weights., TestACMGCriteriaRegistry

### Community 19 - "Community 19"
Cohesion: 0.17
Nodes (6): Apply database query result to variant.          Args:             variant: The, Apply gnomAD results to variant., Apply CADD scores to variant., Apply ClinGen results to variant., Apply dbSNP results to variant., Apply COSMIC results to variant.

### Community 20 - "Community 20"
Cohesion: 0.26
Nodes (5): Return VCF-formatted string for this variant., Represents a genetic variant for ACMG/AMP classification.      Attributes:, Variant, Test population frequency handling., TestPopulationFrequencies

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (7): dbSNPConnector, dbSNP database connector.  Queries the NCBI dbSNP API for variant information in, Search dbSNP by genomic position., dbSNP connector using NCBI API.      Queries dbSNP for variant information inclu, Initialize dbSNP connector.          Args:             build_version: dbSNP buil, Query dbSNP for variant information.          Args:             variant: The var, Look up variant by rsID.

### Community 22 - "Community 22"
Cohesion: 0.24
Nodes (7): _check_bs1(), Check BS1: allele frequency too high for disease prevalence., Test BS1 (frequency too high for disease)., AF > 1% → BS1 applies., AF < 1% → BS1 does not apply., No frequency data → BS1 does not apply., TestBS1

### Community 23 - "Community 23"
Cohesion: 0.24
Nodes (7): _check_pm2(), Check PM2: absent from population databases., Test PM2 (absent from population databases)., No population data → PM2 applies., AF < 0.0001 → PM2 applies., AF > 0.0001 → PM2 does not apply., TestPM2

### Community 24 - "Community 24"
Cohesion: 0.20
Nodes (6): _check_pp2(), Check PP2: multiple prediction tools agree variant is damaging., Multiple damaging predictions → PP2 applies., Only one damaging prediction → PP2 does not apply., No predictions → PP2 does not apply., Exactly two tools agree → PP2 applies.

### Community 25 - "Community 25"
Cohesion: 0.25
Nodes (6): generate_report(), Generate a classification report.      Args:         request: Report generation, CSVReport, Generate CSV reports for variant classifications., Generate a CSV report.          Args:             results: List of classificatio, Build a single CSV row from a classification result.

### Community 26 - "Community 26"
Cohesion: 0.22
Nodes (6): Logger, CSV report generator for AutoACMG.  Produces flat-file CSV reports for easy spre, HTML report generator for AutoACMG.  Produces styled HTML reports with variant c, JSON report generator for AutoACMG.  Produces structured JSON reports with all v, get_logger(), Get a configured logger.      Args:         name: Logger name (typically __name_

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (4): Annotate multiple variants.          Args:             variants: List of variant, Get or create a database connector.          Args:             source: Database, Enforce rate limiting between requests., Annotate a variant with evidence from all available databases.          Args:

### Community 29 - "Community 29"
Cohesion: 0.29
Nodes (4): Save result to cache., Fetch URL with retry logic and caching.          Args:             url: The URL, Generate cache key from URL., Retrieve cached result.

### Community 31 - "Community 31"
Cohesion: 0.33
Nodes (4): CacheConfig, Cache configuration for AutoACMG., Cache configuration settings., Get cache file path for a source.          Args:             source: Database so

## Knowledge Gaps
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Variant` connect `Community 20` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 16`, `Community 17`, `Community 18`, `Community 19`, `Community 21`, `Community 22`, `Community 23`, `Community 24`, `Community 26`, `Community 28`, `Community 30`, `Community 32`, `Community 33`, `Community 34`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 50`, `Community 51`, `Community 52`?**
  _High betweenness centrality (0.651) - this node is a cross-community bridge._
- **Why does `ClassificationResult` connect `Community 4` to `Community 0`, `Community 35`, `Community 7`, `Community 8`, `Community 9`, `Community 11`, `Community 12`, `Community 17`, `Community 20`, `Community 25`, `Community 26`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `get_logger()` connect `Community 26` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 16`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `Variant` (e.g. with `BatchVariantRequest` and `ReportRequest`) actually correct?**
  _`Variant` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `ACMGClassifier` (e.g. with `BatchVariantRequest` and `ReportRequest`) actually correct?**
  _`ACMGClassifier` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `GenomicRegion` (e.g. with `EvidenceGatherer` and `TestACMGCriteriaRegistry`) actually correct?**
  _`GenomicRegion` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `ClassificationResult` (e.g. with `BatchVariantRequest` and `ReportRequest`) actually correct?**
  _`ClassificationResult` has 15 INFERRED edges - model-reasoned connections that need verification._