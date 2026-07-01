"""ClinVar database connector.

Queries the NCBI E-utilities API for ClinVar variant annotations.
Uses the E-utilities search → fetch pipeline to get variant data.

API Docs: https://www.ncbi.nlm.nih.gov/research/bionfo/API/
ClinVar API: https://www.ncbi.nlm.nih.gov/clinvar/
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from autoacmg.core.variant import Variant
from autoacmg.databases.base import BaseDBConnector

logger = logging.getLogger(__name__)


class ClinVarConnector(BaseDBConnector):
    """ClinVar database connector using NCBI E-utilities.

    Queries ClinVar via the NCBI E-utilities API:
    1. E-search to find matching variants
    2. E-fetch to retrieve variant details
    3. Parse JSON response for classification data
    """

    NAME = "clinvar"
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.session.headers.update({
            "User-Agent": "AutoACMG/0.1.0 ClinVarConnector",
        })

    def query(self, variant: Variant) -> Optional[dict]:
        """Query ClinVar for a variant.

        Args:
            variant: The variant to query.

        Returns:
            Dictionary with ClinVar annotation data.
        """
        logger.info("Querying ClinVar for %s", variant.get_key())

        # Try multiple search strategies
        results = []

        # Strategy 1: Search by chrom:pos:ref:alt
        search_term = f"{variant.chromosome}:{variant.position}:{variant.ref}>{variant.alt}"
        result = self._search_variants(search_term)
        if result:
            results.extend(result)

        # Strategy 2: Search by rsID if available
        if variant.rsid:
            result = self._search_by_id(variant.rsid)
            if result:
                results.extend(result)

        if not results:
            logger.info("No ClinVar data found for %s", variant.get_key())
            return None

        # Take the most informative result
        best = self._select_best_result(results)
        return self._parse_result(best)

    def _search_variants(self, search_term: str) -> Optional[list[dict]]:
        """Search ClinVar using E-utilities."""
        # E-search
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        params = {
            "db": "clinvar",
            "term": search_term,
            "retmax": "20",
            "usehistory": "y",
            "rettype": "json",
        }
        search_result = self._fetch_url(search_url, params=params)
        if not search_result:
            return None

        id_list = search_result.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return None

        # E-fetch
        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            "db": "clinvar",
            "id": ",".join(id_list[:5]),
            "rettype": "json",
            "retmode": "json",
        }
        fetch_result = self._fetch_url(fetch_url, params=params)
        if fetch_result and "result" in fetch_result:
            return fetch_result["result"]

        return None

    def _search_by_id(self, rsid: str) -> Optional[list[dict]]:
        """Search ClinVar by rsID."""
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        params = {
            "db": "clinvar",
            "term": rsid,
            "retmax": "5",
            "usehistory": "y",
            "rettype": "json",
        }
        search_result = self._fetch_url(search_url, params=params)
        if not search_result:
            return None

        id_list = search_result.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return None

        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            "db": "clinvar",
            "id": ",".join(id_list[:5]),
            "rettype": "json",
            "retmode": "json",
        }
        fetch_result = self._fetch_url(fetch_url, params=params)
        if fetch_result and "result" in fetch_result:
            return fetch_result["result"]

        return None

    def _select_best_result(self, results: list[dict]) -> dict:
        """Select the most informative ClinVar result.

        Prioritizes results with higher review status (gold stars).
        """
        if not results:
            return {}

        def score(result):
            stars = 0
            review = result.get("ReviewStatus", "")
            if "reviewed" in review.lower():
                stars = 4
            elif "criteria_provided" in review.lower():
                stars = 2
            elif "no_assertion" in review.lower():
                stars = 0
            return stars

        results.sort(key=score, reverse=True)
        return results[0] if results else {}

    def _parse_result(self, result: dict) -> Optional[dict]:
        """Parse ClinVar JSON result into annotation data."""
        if not result:
            return None

        submission = result.get("Submission", {})
        if isinstance(submission, list):
            submission = submission[0] if submission else {}

        review_status = result.get("ReviewStatus", "")
        clinical_sig = result.get("Trait", {}).get("Name", "unknown") if isinstance(result.get("Trait"), dict) else str(result.get("Trait", ""))

        # Count gold stars
        gold_stars = 0
        if "no_assertion" in review_status.lower():
            gold_stars = 0
        elif "criteria_provided" in review_status.lower() and "single_submitter" in review_status.lower():
            gold_stars = 1
        elif "criteria_provided" in review_status.lower():
            gold_stars = 2
        elif "reviewed" in review_status.lower() and "expert_panel" in review_status.lower():
            gold_stars = 3
        elif "reviewed" in review_status.lower():
            gold_stars = 4

        # Get condition from Trait
        condition = ""
        trait = result.get("Trait", {})
        if isinstance(trait, dict):
            condition = trait.get("Name", "")
        elif isinstance(trait, str):
            condition = trait

        # Get last evaluated
        last_eval = submission.get("LastEvaluated", "")

        # Allelic origins
        allelic_origins = []
        origin = result.get("Origin", [])
        if isinstance(origin, list):
            allelic_origins = [str(o) for o in origin]
        elif origin:
            allelic_origins = [str(origin)]

        return {
            "variant_id": result.get("VariantId", ""),
            "clinical_significance": clinical_sig,
            "condition": condition,
            "review_status": review_status,
            "submission_count": len(submission.get("Submitter", [])) if isinstance(submission.get("Submitter"), list) else 0,
            "last_eval": last_eval,
            "gold_stars": gold_stars,
            "allelic_origins": allelic_origins,
        }
