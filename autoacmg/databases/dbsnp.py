"""dbSNP database connector.

Queries the NCBI dbSNP API for variant information including
rsIDs, allele frequencies, and population data.

API Docs: https://www.ncbi.nlm.nih.gov/snp/help/api
"""

from __future__ import annotations

import logging
from typing import Optional

from autoacmg.core.variant import Variant
from autoacmg.databases.base import BaseDBConnector

logger = logging.getLogger(__name__)


class dbSNPConnector(BaseDBConnector):
    """dbSNP connector using NCBI API.

    Queries dbSNP for variant information including rsIDs,
    allele data, and population frequencies.
    """

    NAME = "dbsnp"
    BASE_URL = "https://api.ncbi.nlm.nih.gov/snp"

    def __init__(self, build_version: str = "155", **kwargs) -> None:
        """Initialize dbSNP connector.

        Args:
            build_version: dbSNP build version (default: 155).
        """
        super().__init__(**kwargs)
        self.build_version = build_version

    def query(self, variant: Variant) -> Optional[dict]:
        """Query dbSNP for variant information.

        Args:
            variant: The variant to query.

        Returns:
            Dictionary with dbSNP data.
        """
        logger.info("Querying dbSNP for %s", variant.get_key())
        results = {}

        # If we already have an rsID, verify it
        if variant.rsid:
            result = self._lookup_rsid(variant.rsid)
            if result:
                results.update(result)
                return results

        # Search by position
        chrom = variant.chromosome.replace("chr", "")
        result = self._search_by_position(chrom, variant.position, variant.ref, variant.alt)
        if result:
            results.update(result)

        return results if results else None

    def _lookup_rsid(self, rsid: str) -> Optional[dict]:
        """Look up variant by rsID."""
        url = f"{self.BASE_URL}/rs/{rsid}"
        params = {"fields": "all"}
        result = self._fetch_url(url, params=params)

        if not result:
            return None

        # Parse rsID response
        alleles = result.get("alleles", [])
        allele_info = {}
        if isinstance(alleles, list) and alleles:
            allele_info = {
                "rsid": rsid,
                "allele": alleles[0].get("ref_allele", ""),
                "alt_alleles": [a.get("alt", "") for a in alleles if a.get("alt")],
                "allele_origin": alleles[0].get("allele_origin", []),
                "allele_frequency": [],
            }
            # Get population frequencies
            freqs = alleles[0].get("allele_freq", [])
            if isinstance(freqs, list):
                allele_info["allele_frequency"] = [
                    {
                        "population": f.get("population_name", f.get("population", "")),
                        "frequency": f.get("allele_freq", 0.0),
                        "sample_count": f.get("sample_count", 0),
                    }
                    for f in freqs
                ]

        return allele_info if allele_info else None

    def _search_by_position(
        self, chromosome: str, position: int, ref: str, alt: str
    ) -> Optional[dict]:
        """Search dbSNP by genomic position."""
        url = f"{self.BASE_URL}/region/{chromosome}/{position}/{position}"
        params = {"fields": "all"}
        result = self._fetch_url(url, params=params)

        if not result:
            return None

        variants = result.get("variants", [])
        if not isinstance(variants, list):
            return None

        # Find matching variant by ref/alt
        for v in variants:
            alleles = v.get("alleles", [])
            for allele in alleles:
                ref_allele = allele.get("ref_allele", "")
                alt_alleles = allele.get("alt", [])
                if isinstance(alt_alleles, list):
                    alt_list = alt_alleles
                else:
                    alt_list = [alt_alleles]

                if ref_allele == ref and alt in alt_list:
                    rsid = v.get("rs", "")
                    return {
                        "rsid": rsid,
                        "allele": ref_allele,
                        "alt_alleles": alt_list,
                        "allele_origin": allele.get("allele_origin", []),
                        "allele_frequency": allele.get("allele_freq", []),
                    }

        return None
