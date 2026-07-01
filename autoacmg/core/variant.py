"""Variant model for AutoACMG.

Represents a genetic variant with all relevant fields needed
for ACMG/AMP classification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _utc_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


class ClinicalSignificance(str, Enum):
    """Clinical significance categories per ClinVar."""

    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"
    CONFLICTING = "conflicting_interpretations"
    DRUG_RESPONSE = "drug_response"
    OTHER = "other"


class ACMGClassification(str, Enum):
    """ACMG classification categories."""

    PATHOGENIC = "Pathogenic"
    LIKELY_PATHOGENIC = "Likely Pathogenic"
    UNCERTAIN_SIGNIFICANCE = "Uncertain Significance"
    LIKELY_BENIGN = "Likely Benign"
    BENIGN = "Benign"
    NOT_CLASSIFIED = "Not Classified"


@dataclass
class PopulationFrequency:
    """Population frequency data from gnomAD or similar databases."""

    source: str
    af: float  # allele frequency
    homozygote_count: int = 0
    hemizygote_count: int = 0
    heterozygote_count: int = 0
    total_alleles: int = 0
    total_samples: int = 0
    subpopulations: dict[str, float] = field(default_factory=dict)


@dataclass
class ClinVarAnnotation:
    """ClinVar annotation for a variant."""

    variant_id: str = ""
    clinical_significance: Optional[ClinicalSignificance] = None
    condition: Optional[str] = None
    review_status: Optional[str] = None
    submission_count: int = 0
    last_eval: Optional[str] = None
    gold_stars: int = 0
    allelic_origins: list[str] = field(default_factory=list)


@dataclass
class PredictionScore:
    """Computational prediction score."""

    tool: str
    score: float
    label: Optional[str] = None  # 'deleterious', 'benign', etc.


@dataclass
class GenomicRegion:
    """Genomic region information for a variant."""

    gene_id: str = ""
    gene_symbol: str = ""
    region: str = ""  # coding, UTR5, UTR3, intron, intergenic, etc.
    consequence: str = ""  # missense, nonsense, frameshift, etc.
    protein_change: Optional[str] = None
    canonical_transcript: Optional[str] = None
    codons: Optional[str] = None
    genomic_hgvsg: Optional[str] = None


class Variant(BaseModel):
    """Represents a genetic variant for ACMG/AMP classification.

    Attributes:
        chromosome: Chromosome name (e.g., '1', 'X', 'MT').
        position: 1-based genomic position.
        ref: Reference allele.
        alt: Alternate allele.
        sample_id: Identifier for the sample.
        rsid: dbSNP rs ID if available.
        genomic_region: Genomic context (gene, region, consequence).
        population_frequencies: Population allele frequencies.
        clinvar_annotation: ClinVar data if available.
        prediction_scores: In silico prediction scores.
        classifications: List of ACMG criteria applied.
        final_classification: Final ACMG classification.
        notes: Free-text notes about the variant.
        created_at: Timestamp when the variant record was created.
        updated_at: Timestamp of last update.
    """

    chromosome: str
    position: int
    ref: str
    alt: str
    sample_id: str = "unknown"
    rsid: Optional[str] = None
    genomic_region: Optional[GenomicRegion] = None
    population_frequencies: list[PopulationFrequency] = Field(default_factory=list)
    clinvar_annotation: Optional[ClinVarAnnotation] = None
    prediction_scores: list[PredictionScore] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)
    final_classification: Optional[ACMGClassification] = None
    evidence_summary: dict = Field(default_factory=dict)
    notes: str = ""
    created_at: str = Field(default_factory=_utc_iso)
    updated_at: str = Field(default_factory=_utc_iso)

    def __hash__(self) -> int:
        return hash(self.get_key())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Variant):
            return NotImplemented
        return self.get_key() == other.get_key()

    def get_key(self) -> str:
        """Return a unique key for this variant (no sample_id)."""
        return f"{self.chromosome}:{self.position}:{self.ref}:{self.alt}"

    def get_vcf_line(self) -> str:
        """Return VCF-formatted string for this variant."""
        return f"{self.chromosome}\t{self.position}\t.\t{self.ref}\t{self.alt}\t.\t.\t."

    def get_hgvsg(self) -> str:
        """Construct HGVS g.nomenclature string."""
        return f"{self.chromosome} g.{self.position}{self.ref}>{self.alt}"

    def is_snv(self) -> bool:
        """Check if variant is a single nucleotide variant."""
        return len(self.ref) == 1 and len(self.alt) == 1

    def is_insertion(self) -> bool:
        """Check if variant is an insertion."""
        return len(self.ref) == 1 and len(self.alt) > 1

    def is_deletion(self) -> bool:
        """Check if variant is a deletion."""
        return len(self.ref) > 1 and len(self.alt) == 1

    def is_mnv(self) -> bool:
        """Check if variant is a multiple nucleotide variant."""
        return len(self.ref) > 1 and len(self.alt) > 1

    @property
    def max_population_af(self) -> float:
        """Return the maximum allele frequency across all populations."""
        if not self.population_frequencies:
            return 0.0
        return max(pf.af for pf in self.population_frequencies)

    @property
    def is_novel(self) -> bool:
        """Check if variant has been seen in any population database."""
        return not self.population_frequencies and not self.rsid

    def add_classification(self, criterion: str, strength: str, description: str) -> None:
        """Add an ACMG classification criterion.

        Args:
            criterion: Criterion code (e.g., 'PVS1', 'PM1', 'BP1').
            strength: Strength level (e.g., '+', '++', '+++').
            description: Human-readable description.
        """
        label = f"{criterion}{strength}"
        self.classifications.append(label)
        self.evidence_summary.setdefault(criterion, []).append({
            "strength": strength,
            "description": description,
        })

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = self.model_dump()
        data["variant_key"] = self.get_key()
        if self.genomic_region:
            data["gene"] = self.genomic_region.gene_symbol
            data["consequence"] = self.genomic_region.consequence
        return data

    @classmethod
    def from_vcf_record(cls, vcf_dict: dict) -> Variant:
        """Create a Variant from a VCF record dictionary.

        Args:
            vcf_dict: Dictionary with keys matching VCF fields.

        Returns:
            A Variant instance.
        """
        info = vcf_dict.get("INFO", {})
        sample_id = vcf_dict.get("SAMPLE", "unknown")

        region = None
        if "GENE" in info or "SYMBOL" in info:
            region = GenomicRegion(
                gene_symbol=info.get("GENE", info.get("SYMBOL", "")),
                consequence=info.get("CONSEQUENCE", ""),
                region=info.get("REGION", ""),
                protein_change=info.get("PROTEIN_CHANGE"),
            )

        return cls(
            chromosome=vcf_dict["CHROM"],
            position=int(vcf_dict["POS"]),
            ref=vcf_dict["REF"],
            alt=vcf_dict["ALT"],
            sample_id=sample_id,
            rsid=vcf_dict.get("ID") or info.get("RSID"),
            genomic_region=region,
        )
