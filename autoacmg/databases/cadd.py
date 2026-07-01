"""CADD score connector.

CADD (Combined Annotation Dependent Deployment) scores are used
to predict the deleteriousness of genetic variants. This connector
supports both the CADD web API and local VCF file lookup.

API: https://cadd.gs.washington.edu/
Scores available as precomputed VCF files for download.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from autoacmg.core.variant import Variant
from autoacmg.databases.base import BaseDBConnector

logger = logging.getLogger(__name__)


class CADDConnector(BaseDBConnector):
    """CADD score connector.

    Supports two modes:
    1. Remote query via CADD API (limited)
    2. Local VCF file lookup (recommended for batch processing)

    CADD scores:
    - Phred-scaled C-score: >= 10 = top 10% most deleterious
    - Raw C-score: higher = more deleterious
    - In CADD v1.4+, scores are scaled to -15 (best) to +64 (worst)
    """

    NAME = "cadd"

    def __init__(
        self,
        cadd_vcf_path: Optional[str] = None,
        use_api: bool = True,
        **kwargs,
    ) -> None:
        """Initialize CADD connector.

        Args:
            cadd_vcf_path: Path to local CADD VCF file (pre-downloaded).
            use_api: Whether to use the CADD web API (default: True).
        """
        super().__init__(**kwargs)
        self.cadd_vcf_path = cadd_vcf_path
        self.use_api = use_api
        self._cadd_cache: dict[str, float] = {}

        if cadd_vcf_path and os.path.exists(cadd_vcf_path):
            self._load_local_vcf(cadd_vcf_path)

    def _load_local_vcf(self, vcf_path: str) -> None:
        """Load CADD scores from a local VCF file."""
        logger.info("Loading CADD scores from %s", vcf_path)
        loaded = 0
        try:
            with open(vcf_path, "r") as f:
                for line in f:
                    if line.startswith("#"):
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) < 9:
                        continue
                    chrom, pos, _, ref, alt = parts[0], parts[1], parts[2], parts[3], parts[4]
                    info = parts[7]
                    # CADD info format: RAW=score;RAW_SIGNED=score;PHRED=score
                    for item in info.split(";"):
                        if item.startswith("PHRED="):
                            try:
                                score = float(item.split("=")[1])
                                key = f"{chrom}:{pos}:{ref}:{alt}"
                                self._cadd_cache[key] = score
                                loaded += 1
                            except (ValueError, IndexError):
                                continue
            logger.info("Loaded %d CADD scores", loaded)
        except Exception as e:
            logger.error("Failed to load CADD VCF: %s", e)

    def query(self, variant: Variant) -> Optional[dict]:
        """Query CADD score for a variant.

        Args:
            variant: The variant to score.

        Returns:
            Dictionary with CADD score data.
        """
        logger.info("Querying CADD for %s", variant.get_key())

        # Check local cache/loaded VCF
        variant_key = variant.get_key()
        if variant_key in self._cadd_cache:
            return {
                "cadd_score": self._cadd_cache[variant_key],
                "source": "local_vcf",
            }

        # Try API if enabled
        if self.use_api:
            return self._query_api(variant)

        # Fallback: check if we have a local VCF and search it
        if self.cadd_vcf_path and os.path.exists(self.cadd_vcf_path):
            return self._search_local_vcf(variant)

        logger.warning("No CADD data available for %s", variant.get_key())
        return None

    def _query_api(self, variant: Variant) -> Optional[dict]:
        """Query CADD via web API.

        CADD provides a web form for individual variant lookup.
        For batch queries, the recommended approach is downloading
        precomputed VCF files.
        """
        # CADD web interface doesn't have a formal REST API,
        # so we use the in-silico predictor endpoint
        chrom = variant.chromosome.replace("chr", "")
        url = "https://cadd.gs.washington.org/api"

        params = {
            "chr": chrom,
            "pos": str(variant.position),
            "ref": variant.ref,
            "alt": variant.alt,
        }

        result = self._fetch_url(url, params=params)
        if result:
            score = result.get("cadd_phred", result.get("score"))
            if score is not None:
                return {
                    "cadd_score": float(score),
                    "cadd_rank": result.get("rank_proportion"),
                    "source": "api",
                }

        return None

    def _search_local_vcf(self, variant: Variant) -> Optional[dict]:
        """Search loaded CADD VCF for variant."""
        variant_key = variant.get_key()
        if variant_key in self._cadd_cache:
            return {
                "cadd_score": self._cadd_cache[variant_key],
                "source": "local_vcf",
            }
        return None
