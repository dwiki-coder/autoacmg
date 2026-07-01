"""Evidence gathering from multiple databases.

Coordinates queries to ClinVar, gnomAD, CADD, ClinGen, dbSNP, and COSMIC
to gather all relevant evidence for ACMG/AMP classification.
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from autoacmg.core.variant import (
    ClinVarAnnotation,
    ClinicalSignificance,
    GenomicRegion,
    PopulationFrequency,
    PredictionScore,
    Variant,
)
from autoacmg.databases.base import BaseDBConnector
from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)


class EvidenceGatherer:
    """Gathers evidence from multiple databases for ACMG classification.

    Coordinates parallel queries to external databases and aggregates
    results into the Variant model. Handles rate limiting, caching,
    and error recovery.

    Usage:
        gatherer = EvidenceGatherer(cache_dir="~/.autoacmg/cache")
        variant = Variant(chromosome="1", position=7674232, ref="G", alt="A")
        gatherer.annotate(variant)
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5,
        use_cache: bool = True,
    ) -> None:
        """Initialize the evidence gatherer.

        Args:
            cache_dir: Directory for SQLite cache. None disables caching.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts per request.
            rate_limit_delay: Delay between requests (seconds).
            use_cache: Whether to use the SQLite cache.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.use_cache = use_cache
        self._last_request_time: float = 0.0

        # Initialize database connectors
        # These will be lazily loaded to avoid import errors if deps missing
        self._connectors: dict[str, Optional[BaseDBConnector]] = {}
        self._cache_dir = cache_dir

    def annotate(self, variant: Variant, sources: Optional[list[str]] = None) -> Variant:
        """Annotate a variant with evidence from all available databases.

        Args:
            variant: The variant to annotate.
            sources: Optional list of database sources to query.
                     If None, all available sources are queried.

        Returns:
            The annotated variant with all gathered evidence.
        """
        logger.info("Gathering evidence for %s", variant.get_key())
        start_time = time.time()

        if sources is None:
            sources = [
                "clinvar", "gnomad", "cadd", "clingen",
                "dbsnp", "cosmic",
            ]

        for source in sources:
            try:
                connector = self._get_connector(source)
                if connector is None:
                    logger.warning("Source '%s' not available, skipping", source)
                    continue

                self._rate_limit()
                result = connector.query(variant)
                self._apply_result(variant, source, result)
                logger.info(
                    "Annotated %s from %s in %.2fs",
                    variant.get_key(), source, time.time() - start_time,
                )
            except Exception as e:
                logger.warning(
                    "Failed to annotate from %s: %s", source, e
                )
                continue

        elapsed = time.time() - start_time
        logger.info(
            "Evidence gathering complete for %s in %.2fs",
            variant.get_key(), elapsed,
        )
        variant.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return variant

    def annotate_batch(
        self, variants: list[Variant], sources: Optional[list[str]] = None
    ) -> list[Variant]:
        """Annotate multiple variants.

        Args:
            variants: List of variants to annotate.
            sources: Optional list of database sources.

        Returns:
            List of annotated variants.
        """
        logger.info("Batch annotating %d variants", len(variants))
        results = []
        for variant in variants:
            try:
                annotated = self.annotate(variant, sources)
                results.append(annotated)
            except Exception as e:
                logger.error("Failed to annotate %s: %s", variant.get_key(), e)
                results.append(variant)
        return results

    def _get_connector(self, source: str) -> Optional[BaseDBConnector]:
        """Get or create a database connector.

        Args:
            source: Database source name.

        Returns:
            Connector instance or None if not available.
        """
        if source in self._connectors:
            return self._connectors[source]

        connector = None
        try:
            if source == "clinvar":
                from autoacmg.databases.clinvar import ClinVarConnector
                connector = ClinVarConnector(
                    cache_dir=self._cache_dir,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    use_cache=self.use_cache,
                )
            elif source == "gnomad":
                from autoacmg.databases.gnomad import gnomADConnector
                connector = gnomADConnector(
                    cache_dir=self._cache_dir,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    use_cache=self.use_cache,
                )
            elif source == "cadd":
                from autoacmg.databases.cadd import CADDConnector
                connector = CADDConnector(
                    cache_dir=self._cache_dir,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    use_cache=self.use_cache,
                )
            elif source == "clingen":
                from autoacmg.databases.clingen import ClinGenConnector
                connector = ClinGenConnector(
                    cache_dir=self._cache_dir,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    use_cache=self.use_cache,
                )
            elif source == "dbsnp":
                from autoacmg.databases.dbsnp import dbSNPConnector
                connector = dbSNPConnector(
                    cache_dir=self._cache_dir,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    use_cache=self.use_cache,
                )
            elif source == "cosmic":
                from autoacmg.databases.cosmic import COSMICConnector
                connector = COSMICConnector(
                    cache_dir=self._cache_dir,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    use_cache=self.use_cache,
                )
        except ImportError as e:
            logger.debug("Failed to import connector for %s: %s", source, e)
            connector = None

        self._connectors[source] = connector
        return connector

    def _apply_result(
        self, variant: Variant, source: str, result: Optional[dict]
    ) -> None:
        """Apply database query result to variant.

        Args:
            variant: The variant to update.
            source: Database source name.
            result: Query result dictionary.
        """
        if result is None:
            return

        if source == "clinvar":
            self._apply_clinvar(variant, result)
        elif source == "gnomad":
            self._apply_gnomad(variant, result)
        elif source == "cadd":
            self._apply_cadd(variant, result)
        elif source == "clingen":
            self._apply_clingen(variant, result)
        elif source == "dbsnp":
            self._apply_dbsnp(variant, result)
        elif source == "cosmic":
            self._apply_cosmic(variant, result)

    def _apply_clinvar(self, variant: Variant, result: dict) -> None:
        """Apply ClinVar results to variant."""
        if "clinical_significance" in result:
            cs = result["clinical_significance"]
            try:
                significance = ClinicalSignificance(cs.lower().replace(" ", "_"))
            except ValueError:
                significance = ClinicalSignificance.OTHER

            annotation = ClinVarAnnotation(
                variant_id=result.get("variant_id", ""),
                clinical_significance=significance,
                condition=result.get("condition"),
                review_status=result.get("review_status"),
                submission_count=result.get("submission_count", 0),
                last_eval=result.get("last_eval"),
                gold_stars=result.get("gold_stars", 0),
                allelic_origins=result.get("allelic_origins", []),
            )
            variant.clinvar_annotation = annotation

        if "gene" in result:
            if variant.genomic_region is None:
                variant.genomic_region = GenomicRegion()
            variant.genomic_region.gene_symbol = result["gene"]
            variant.genomic_region.gene_id = result.get("gene_id", "")

    def _apply_gnomad(self, variant: Variant, result: dict) -> None:
        """Apply gnomAD results to variant."""
        if "frequencies" in result:
            for freq_data in result["frequencies"]:
                pf = PopulationFrequency(
                    source=freq_data.get("population", "gnomad"),
                    af=freq_data.get("af", 0.0),
                    homozygote_count=freq_data.get("homozygote_count", 0),
                    hemizygote_count=freq_data.get("hemizygote_count", 0),
                    heterozygote_count=freq_data.get("heterozygote_count", 0),
                    total_alleles=freq_data.get("total_alleles", 0),
                    total_samples=freq_data.get("total_samples", 0),
                )
                variant.population_frequencies.append(pf)

    def _apply_cadd(self, variant: Variant, result: dict) -> None:
        """Apply CADD scores to variant."""
        if "cadd_score" in result:
            variant.prediction_scores.append(PredictionScore(
                tool="CADD",
                score=result["cadd_score"],
                label="damaging" if result["cadd_score"] >= 10.0 else "tolerated",
            ))
        if "cadd_rank" in result:
            variant.prediction_scores.append(PredictionScore(
                tool="CADD-Rank",
                score=result["cadd_rank"],
            ))

    def _apply_clingen(self, variant: Variant, result: dict) -> None:
        """Apply ClinGen results to variant."""
        if variant.genomic_region is None:
            variant.genomic_region = GenomicRegion()

        if "gene_symbol" in result:
            variant.genomic_region.gene_symbol = result["gene_symbol"]
        if "gene_id" in result:
            variant.genomic_region.gene_id = result["gene_id"]

        if "pathogenicity_specification" in result:
            variant.evidence_summary["clingen_path_spec"] = result[
                "pathogenicity_specification"
            ]
        if "lof_intolerance" in result:
            variant.evidence_summary["lof_intolerance"] = result["lof_intolerance"]

    def _apply_dbsnp(self, variant: Variant, result: dict) -> None:
        """Apply dbSNP results to variant."""
        if "rsid" in result:
            variant.rsid = result["rsid"]
        if "allele" in result:
            variant.evidence_summary["dbsnp_allele"] = result["allele"]

    def _apply_cosmic(self, variant: Variant, result: dict) -> None:
        """Apply COSMIC results to variant."""
        if "cosmic_ids" in result:
            variant.evidence_summary["cosmic_ids"] = result["cosmic_ids"]
        if "cancer_type" in result:
            variant.evidence_summary["cosmic_cancer_type"] = result["cancer_type"]
        if "somatic_count" in result:
            variant.evidence_summary["cosmic_somatic_count"] = result["somatic_count"]

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()
