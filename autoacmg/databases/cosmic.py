"""COSMIC database connector.

Queries the COSMIC (Catalogue Of Somatic Mutations In Cancer) API
for cancer-related somatic mutation data.

API Docs: https://cancer.sanger.ac.uk/cosmic/api
Note: COSMIC requires an API key for programmatic access.
"""

from __future__ import annotations

import logging
from typing import Optional

from autoacmg.core.variant import Variant
from autoacmg.databases.base import BaseDBConnector

logger = logging.getLogger(__name__)


class COSMICConnector(BaseDBConnector):
    """COSMIC API connector.

    Queries COSMIC for somatic mutation data in cancer.
    Requires a COSMIC API key for full access.

    Free API key: https://cancer.sanger.ac.uk/cosmic/register
    """

    NAME = "cosmic"
    BASE_URL = "https://cancer.sanger.ac.uk/cosmic/api3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize COSMIC connector.

        Args:
            api_key: COSMIC API key. Required for authenticated queries.
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def query(self, variant: Variant) -> Optional[dict]:
        """Query COSMIC for somatic mutation data.

        Args:
            variant: The variant to query.

        Returns:
            Dictionary with COSMIC mutation data.
        """
        logger.info("Querying COSMIC for %s", variant.get_key())

        chrom = variant.chromosome.replace("chr", "")

        # Search by position
        result = self._search_by_position(chrom, variant.position)
        if result:
            return result

        # Search by variant notation
        result = self._search_by_variant(variant)
        if result:
            return result

        logger.info("No COSMIC data found for %s", variant.get_key())
        return None

    def _search_by_position(self, chromosome: str, position: int) -> Optional[dict]:
        """Search COSMIC by genomic position."""
        url = f"{self.BASE_URL}/muts/loci/{chromosome}/{position}/{position}"

        result = self._fetch_url(url)
        if not result:
            return None

        return self._parse_results(result)

    def _search_by_variant(self, variant: Variant) -> Optional[dict]:
        """Search COSMIC by variant notation."""
        chrom = variant.chromosome.replace("chr", "")
        notation = f"{chrom}:{variant.position}:{variant.ref}>{variant.alt}"

        url = f"{self.BASE_URL}/muts/search"
        params = {
            "query": notation,
            "limit": "10",
        }

        result = self._fetch_url(url, params=params)
        if not result:
            return None

        return self._parse_results(result)

    def _parse_results(self, data: dict) -> Optional[dict]:
        """Parse COSMIC API response."""
        if not data:
            return None

        mutations = data.get("muts", data.get("results", []))
        if not mutations:
            return None

        if isinstance(mutations, dict):
            mutations = mutations.get("mut", [])

        if not mutations:
            return None

        cosmic_ids = []
        cancer_types = set()
        counts = {}

        for mut in mutations:
            if isinstance(mut, dict):
                cosmic_id = mut.get("cosmic_id", mut.get("id", ""))
                if cosmic_id:
                    cosmic_ids.append(str(cosmic_id))

                cancer_type = mut.get("tumour_type", mut.get("cancer_type", ""))
                if cancer_type:
                    cancer_types.add(str(cancer_type))

                count = mut.get("somatic_count", mut.get("count", 0))
                if count:
                    counts[str(cosmic_id)] = count

        return {
            "cosmic_ids": cosmic_ids,
            "cancer_type": list(cancer_types) if cancer_types else ["Unknown"],
            "somatic_count": sum(counts.values()) if counts else len(cosmic_ids),
            "total_cases": len(cosmic_ids),
        }
