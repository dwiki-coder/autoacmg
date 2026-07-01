"""gnomAD database connector.

Queries gnomAD v4.1 REST API for population allele frequencies.
Supports both GRCh37 (hg19) and GRCh38 coordinate systems.

API Docs: https://gnomad.broadinstitute.org/api
"""

from __future__ import annotations

import logging
from typing import Optional

from autoacmg.core.variant import Variant
from autoacmg.databases.base import BaseDBConnector

logger = logging.getLogger(__name__)


class gnomADConnector(BaseDBConnector):
    """gnomAD REST API connector.

    Queries gnomAD v4.1 for population allele frequencies.
    Supports exomes and genomes data.
    """

    NAME = "gnomad"
    BASE_URL = "https://gnomad.broadinstitute.org/api"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Use exomes API by default; genomes is also available
        self.endpoint = f"{self.BASE_URL}/variant"

    def query(self, variant: Variant) -> Optional[dict]:
        """Query gnomAD for variant frequencies.

        Args:
            variant: The variant to query.

        Returns:
            Dictionary with frequency data from all populations.
        """
        logger.info("Querying gnomAD for %s", variant.get_key())

        # Format: /variant/{chromosome}-[0-9]+-{ref}-{alt}
        chrom = variant.chromosome.replace("chr", "")
        variant_id = f"{chrom}-{variant.position}-{variant.ref}-{variant.alt}"

        url = f"{self.BASE_URL}/variant/{variant_id}"
        result = self._fetch_url(url)

        if result is None:
            logger.info("Variant not found in gnomAD: %s", variant.get_key())
            return None

        return self._parse_result(result)

    def _parse_result(self, data: dict) -> dict:
        """Parse gnomAD API response into frequency data."""
        frequencies = []

        # gnomAD v4 API response structure
        # Contains 'genomes' and/or 'exomes' top-level keys
        for dataset_key in ("genomes", "exomes"):
            dataset = data.get(dataset_key)
            if not dataset:
                continue

            if not isinstance(dataset, dict):
                continue

            # Overall frequencies
            overall_af = dataset.get("af", 0.0)
            if overall_af is not None:
                frequencies.append({
                    "population": f"gnomad_{dataset_key}_all",
                    "af": float(overall_af),
                    "total_alleles": dataset.get("n", {}).get("alleles", 0) if isinstance(dataset.get("n"), dict) else 0,
                    "total_samples": dataset.get("n", {}).get("samples", 0) if isinstance(dataset.get("n"), dict) else 0,
                    "homozygote_count": dataset.get("n", {}).get("homozygotes", 0) if isinstance(dataset.get("n"), dict) else 0,
                    "heterozygote_count": dataset.get("n", {}).get("heterozygotes", 0) if isinstance(dataset.get("n"), dict) else 0,
                    "hemizygote_count": dataset.get("n", {}).get("hemizygotes", 0) if isinstance(dataset.get("n"), dict) else 0,
                })

            # Population-specific frequencies
            pops = dataset.get("pops", {})
            if isinstance(pops, dict):
                for pop_name, pop_data in pops.items():
                    if isinstance(pop_data, dict):
                        pop_af = pop_data.get("af")
                        if pop_af is not None:
                            frequencies.append({
                                "population": f"gnomad_{dataset_key}_{pop_name}",
                                "af": float(pop_af),
                                "total_alleles": pop_data.get("n", {}).get("alleles", 0) if isinstance(pop_data.get("n"), dict) else 0,
                                "total_samples": pop_data.get("n", {}).get("samples", 0) if isinstance(pop_data.get("n"), dict) else 0,
                                "homozygote_count": pop_data.get("n", {}).get("homozygotes", 0) if isinstance(pop_data.get("n"), dict) else 0,
                                "heterozygote_count": pop_data.get("n", {}).get("heterozygotes", 0) if isinstance(pop_data.get("n"), dict) else 0,
                            })

        if not frequencies:
            return {"frequencies": [], "raw": data}

        return {"frequencies": frequencies}
