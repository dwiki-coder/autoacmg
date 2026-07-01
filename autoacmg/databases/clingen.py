"""ClinGen database connector.

Queries the ClinGen REST API for:
- Gene-disease validity classifications
- Variant curation criteria (VCC) frameworks
- LoF intolerance scores
- Dosage sensitivity assessments
- Curation tags

API Docs: https://clinicalgenome.org/api/docs/
"""

from __future__ import annotations

import logging
from typing import Optional

from autoacmg.core.variant import Variant
from autoacmg.databases.base import BaseDBConnector

logger = logging.getLogger(__name__)


class ClinGenConnector(BaseDBConnector):
    """ClinGen REST API connector.

    Queries ClinGen for gene-disease relationships, curation
    criteria frameworks, and dosage sensitivity data.
    """

    NAME = "clingen"
    BASE_URL = "https://api.clinicalgenome.org"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Use the CCGE/SAHNI endpoints
        self.sahni_url = f"{self.BASE_URL}/ccv2/sahni"
        self.gene_url = f"{self.BASE_URL}/ccv2/api"

    def query(self, variant: Variant) -> Optional[dict]:
        """Query ClinGen for gene and variant data.

        Args:
            variant: The variant to query.

        Returns:
            Dictionary with ClinGen data.
        """
        logger.info("Querying ClinGen for %s", variant.get_key())
        results = {}

        # Query gene info if we have a gene symbol
        gene = None
        if variant.genomic_region:
            gene = variant.genomic_region.gene_symbol

        if gene:
            gene_result = self._query_gene(gene)
            if gene_result:
                results.update(gene_result)

        # Query by variant if we have rsID
        if variant.rsid:
            variant_result = self._query_variant(variant.rsid)
            if variant_result:
                results.update(variant_result)

        return results if results else None

    def _query_gene(self, gene_symbol: str) -> Optional[dict]:
        """Query ClinGen for gene information."""
        # Search for gene
        url = f"{self.gene_url}/search/gene"
        params = {"gene": gene_symbol}
        result = self._fetch_url(url, params=params)

        if not result:
            return None

        # Parse gene info
        gene_data = {}

        # Get gene ID from search
        genes = result.get("genes", []) if isinstance(result, dict) else []
        if genes and isinstance(genes, list):
            gene_info = genes[0]
            gene_data["gene_id"] = gene_info.get("id", "")
            gene_data["gene_symbol"] = gene_info.get("symbol", gene_symbol)

        # Get gene-disease relationships
        gd_relationships = self._get_gene_disease_relationships(gene_symbol)
        if gd_relationships:
            gene_data["gene_disease_classifications"] = gd_relationships

        # Get dosage sensitivity
        dosage = self._get_dosage_sensitivity(gene_symbol)
        if dosage:
            gene_data["dosage_sensitivity"] = dosage

        # Get LoF intolerance
        lof = self._get_lof_intolerance(gene_symbol)
        if lof:
            gene_data["lof_intolerance"] = lof

        return gene_data if gene_data else None

    def _get_gene_disease_relationships(self, gene_symbol: str) -> Optional[list]:
        """Get gene-disease validity classifications."""
        url = f"{self.gene_url}/search/gene-disease"
        params = {"gene": gene_symbol}
        result = self._fetch_url(url, params=params)

        if not result:
            return None

        classifications = []
        relationships = result.get("results", [])
        if isinstance(relationships, list):
            for rel in relationships[:10]:
                classifications.append({
                    "disease": rel.get("disease", {}).get("name", ""),
                    "classification": rel.get("gd_classification", ""),
                    "strength": rel.get("strength_of_evidence", ""),
                })
        return classifications if classifications else None

    def _get_dosage_sensitivity(self, gene_symbol: str) -> Optional[dict]:
        """Get dosage sensitivity classification from CGC."""
        url = f"{self.gene_url}/search/dosage"
        params = {"gene": gene_symbol}
        result = self._fetch_url(url, params=params)

        if not result:
            return None

        results = result.get("results", [])
        if isinstance(results, list) and results:
            return {
                "haploinsufficiency": results[0].get("haploinsufficiency", "Unknown"),
                "triplosensitivity": results[0].get("triplosensitivity", "Unknown"),
            }
        return None

    def _get_lof_intolerance(self, gene_symbol: str) -> Optional[dict]:
        """Get LoF intolerance scores (from gnomAD via ClinGen)."""
        # ClinGen provides LoF tolerance data
        url = f"{self.gene_url}/search/gene"
        params = {"gene": gene_symbol}
        result = self._fetch_url(url, params=params)

        if not result:
            return None

        genes = result.get("genes", [])
        if isinstance(genes, list) and genes:
            gene = genes[0]
            return {
                "pLI": gene.get("pli_score"),
                "pLoF": gene.get("pLoF_obs_exp"),
                "lof_filtering": gene.get("lof_filtering_status"),
            }
        return None

    def _query_variant(self, rsid: str) -> Optional[dict]:
        """Query ClinGen for variant-specific data."""
        url = f"{self.gene_url}/search/variant"
        params = {"rsid": rsid}
        result = self._fetch_url(url, params=params)

        if not result:
            return None

        variants = result.get("variants", [])
        if isinstance(variants, list) and variants:
            v = variants[0]
            return {
                "curated_classifications": v.get("classifications", []),
                "curation_tags": v.get("tags", []),
                "gene_symbol": v.get("gene_symbol"),
            }
        return None
