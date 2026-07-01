"""ACMG/AMP criteria definitions and evaluation logic.

Implements the 2015 ACMG/AMP variant classification guidelines:
Richards et al. (2015) Standards and guidelines for the interpretation
of sequence variants. Genetics in Medicine, 17(5), 55-66.

Each criterion has:
  - A code (PVS1, PS1, PM1, PP1, etc.)
  - A strength (Strong, Moderate, Supporting, or Very Strong)
  - A category (Pathogenic or Benign)
  - Evaluation logic that checks whether the criterion applies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from autoacmg.core.variant import Variant


class EvidenceStrength(str, Enum):
    """ACMG evidence strength levels."""

    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"

    @property
    def weight(self) -> float:
        """Numeric weight for scoring."""
        return {
            "very_strong": 4.0,
            "strong": 3.0,
            "moderate": 2.0,
            "supporting": 1.0,
        }[self.value]

    @property
    def label(self) -> str:
        return {
            "very_strong": "+",
            "strong": "++",
            "moderate": "+++",
            "supporting": "+",
        }[self.value]


class EvidenceCategory(str, Enum):
    """Whether evidence supports pathogenic or benign classification."""

    PATHOGENIC = "pathogenic"
    BENIGN = "benign"


@dataclass
class CriterionMatch:
    """Result of evaluating a single ACMG criterion."""

    criterion: str
    strength: EvidenceStrength
    category: EvidenceCategory
    description: str
    applied: bool = True


@dataclass
class ACMGCriterion:
    """Definition of a single ACMG/AMP criterion.

    Attributes:
        code: Criterion code (e.g., 'PVS1', 'PS1', 'PM1', 'PP1', 'BA1', 'BS1').
        description: Human-readable description.
        category: Whether it supports pathogenic or benign classification.
        strength: Evidence strength level.
        auto_apply: Whether the criterion can be auto-applied.
        check_fn: Optional callable to check if criterion applies to a variant.
    """

    code: str
    description: str
    category: EvidenceCategory
    strength: EvidenceStrength
    auto_apply: bool = False
    check_fn: Optional = None  # Callable[[Variant], tuple[bool, str]]

    def evaluate(self, variant: Variant) -> Optional[CriterionMatch]:
        """Evaluate this criterion against a variant.

        Returns a CriterionMatch if the criterion applies, None otherwise.
        """
        if self.check_fn is not None:
            applies, reason = self.check_fn(variant)
            if applies:
                return CriterionMatch(
                    criterion=self.code,
                    strength=self.strength,
                    category=self.category,
                    description=f"{self.description}: {reason}",
                )
        elif self.auto_apply:
            return CriterionMatch(
                criterion=self.code,
                strength=self.strength,
                category=self.category,
                description=self.description,
            )
        return None


class ACMGCriteria:
    """Registry and evaluation engine for ACMG/AMP criteria.

    Implements all criteria from the 2015 ACMG/AMP guidelines:
    - Very Strong Pathogenic: PVS1
    - Strong Pathogenic: PS1-PS4, PS5, PS6, PS7
    - Moderate Pathogenic: PM1-PM6
    - Supporting Pathogenic: PP1-PP5
    - Strong Benign: BS1
    - Supporting Benign: BS2-BS4, BP1-BP7
    - Very Strong Benign: BA1
    """

    # --- Pathogenic Criteria ---

    # PVS1: Null variant in a gene where LOF is a known mechanism
    PVS1 = ACMGCriterion(
        code="PVS1",
        description="Null variant (nonsense, frameshift, essential splice-site) "
                     "in a gene where loss of function is a known mechanism of disease",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.VERY_STRONG,
        check_fn=lambda v: _check_pvs1(v),
    )

    # PS1: Same amino acid change as known pathogenic
    PS1 = ACMGCriterion(
        code="PS1",
        description="Same amino acid change as a previously established pathogenic variant",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PS2: Novel missense in same residue as known pathogenic
    PS2 = ACMGCriterion(
        code="PS2",
        description="Novel missense change at a residue with a known pathogenic missense change",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PS3: Functional studies show damaging effect
    PS3 = ACMGCriterion(
        code="PS3",
        description="Well-established functional studies show a damaging effect",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PS4: Disease association in cases, not controls
    PS4 = ACMGCriterion(
        code="PS4",
        description="Prevalence of variant in affected individuals significantly higher "
                     "than in controls, with statistical support",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PS5: Novel de novo with curation-grade evidence
    PS5 = ACMGCriterion(
        code="PS5",
        description="Novel de novo mutation with complete parental segregation analysis",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PS6: Assumed de novo without full confirmation
    PS6 = ACMGCriterion(
        code="PS6",
        description="De novo occurrence in patient without confirmation of paternity/maternality",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PS7: Segregation with disease
    PS7 = ACMGCriterion(
        code="PS7",
        description="Segregation with disease in multiple affected family members",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PS7_Strong: Segregation with disease, strong
    PS7_S = ACMGCriterion(
        code="PS7_S",
        description="Robustly reported segregation with the disease in multiple family members "
                     "(ACMG/AMP SF v3.1, 2020)",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PM1: Known mutational hotspot / functional domain
    PM1 = ACMGCriterion(
        code="PM1",
        description="Located in a mutational hotspot or critical functional domain",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PM2: Absent from population databases
    PM2 = ACMGCriterion(
        code="PM2",
        description="Absent from population databases (or at very low frequency)",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
        check_fn=lambda v: _check_pm2(v),
    )

    # PM3: Co-occurrence with established pathogenic variant
    PM3 = ACMGCriterion(
        code="PM3",
        description="Detected in trans with a pathogenic variant for autosomal recessive disease",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PM4: Protein length change
    PM4 = ACMGCriterion(
        code="PM4",
        description="Protein length changes due to in-frame deletions/insertions in coding region",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PM5: Novel amino acid change at identical position
    PM5 = ACMGCriterion(
        code="PM5",
        description="Novel missense change at an amino acid position where another "
                     "disease-causing missense change was already observed",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PM6: Assumed de novo
    PM6 = ACMGCriterion(
        code="PM6",
        description="Assumed de novo, but without confirmation of paternity and maternity",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PM5 (historical, deprecated in some contexts)
    PM5_ALT = ACMGCriterion(
        code="PM5",
        description="Observed in trans with a pathogenic variant",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.MODERATE,
    )

    # PP1: Segregation with disease
    PP1 = ACMGCriterion(
        code="PP1",
        description="Co-segregation with disease in multiple affected family members",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.SUPPORTING,
    )

    # PP1_Strong: Strong segregation
    PP1_S = ACMGCriterion(
        code="PP1_S",
        description="Strongly supports pathogenicity based on segregation data "
                     "(ACMG/AMP SF v3.1, 2020)",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PP2: Damaging prediction
    PP2 = ACMGCriterion(
        code="PP2",
        description="Missense variant predicted damaging by multiple in silico tools "
                     "(e.g., SIFT, PolyPhen, CADD, REVEL)",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.SUPPORTING,
        check_fn=lambda v: _check_pp2(v),
    )

    # PP3: Computational evidence for damaging
    PP3 = ACMGCriterion(
        code="PP3",
        description="Multiple lines of computational evidence support a deleterious effect",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.SUPPORTING,
    )

    # PP4: Replicated phenotype
    PP4 = ACMGCriterion(
        code="PP4",
        description="Phenotype highly specific to a disease caused by this gene",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.SUPPORTING,
    )

    # PP5: Expert panel
    PP5 = ACMGCriterion(
        code="PP5",
        description="Reputable source recently reports pathogenicity, but evidence not validated",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.SUPPORTING,
    )

    # PP4_Strong: Strong phenotypic match
    PP4_S = ACMGCriterion(
        code="PP4_S",
        description="Strong phenotypic match to disease",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.STRONG,
    )

    # PP6: Reputable source
    PP6 = ACMGCriterion(
        code="PP6",
        description="Reputable source recently reports pathogenicity (not validated by lab)",
        category=EvidenceCategory.PATHOGENIC,
        strength=EvidenceStrength.SUPPORTING,
    )

    # --- Benign Criteria ---

    # BS1: Frequency too high for disease
    BS1 = ACMGCriterion(
        code="BS1",
        description="Allele frequency is inconsistent with disease prevalence",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.STRONG,
        check_fn=lambda v: _check_bs1(v),
    )

    # BS2: Healthy population without disease
    BS2 = ACMGCriterion(
        code="BS2",
        description="Observed in healthy adult for recessive (or dominant) disorder with "
                     "late age of onset",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BS3: Functional studies show no damage
    BS3 = ACMGCriterion(
        code="BS3",
        description="Well-established in silico tools predict no damaging effect",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BS3_Strong: Strong functional evidence
    BS3_S = ACMGCriterion(
        code="BS3_S",
        description="Well-established functional studies show no damaging effect",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.STRONG,
    )

    # BS4: Lack of segregation
    BS4 = ACMGCriterion(
        code="BS4",
        description="Lack of segregation in affected family members",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BP1: Synonymous, intronic, or intergenic
    BP1 = ACMGCriterion(
        code="BP1",
        description="Synonymous, intronic, or intergenic variant with no predicted impact",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BP2: Tolerated in gene dosage studies
    BP2 = ACMGCriterion(
        code="BP2",
        description="Observed in trans with a pathogenic variant for autosomal recessive disease",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BP3: Missense in well-studied gene without missense variants
    BP3 = ACMGCriterion(
        code="BP3",
        description="Multiple lines of computational evidence suggest no damaging effect",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BP4: Functional evidence supports benign
    BP4 = ACMGCriterion(
        code="BP4",
        description="Residue is not known to be altered in individuals without disease",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BP6: Reputable source reports benign
    BP6 = ACMGCriterion(
        code="BP6",
        description="Reputable source recently reports benignity (not validated by lab)",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BP7: Synonymous, intronic, or intergenic with no splice impact
    BP7 = ACMGCriterion(
        code="BP7",
        description="Synonymous variant with no predicted splice impact",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.SUPPORTING,
    )

    # BA1: Allele frequency >> disease prevalence
    BA1 = ACMGCriterion(
        code="BA1",
        description="Allele frequency is ≥ expected prevalence of the disease "
                     "(stand-alone very strong benign)",
        category=EvidenceCategory.BENIGN,
        strength=EvidenceStrength.VERY_STRONG,
        check_fn=lambda v: _check_ba1(v),
    )

    # All criteria registry
    ALL_PATHOGENIC: list[ACMGCriterion] = [
        PVS1, PS1, PS2, PS3, PS4, PS5, PS6, PS7, PS7_S,
        PM1, PM2, PM3, PM4, PM5, PM5_ALT,
        PP1, PP1_S, PP2, PP3, PP4, PP4_S, PP5, PP6,
    ]
    ALL_BENIGN: list[ACMGCriterion] = [
        BA1, BS1, BS2, BS3, BS3_S, BS4,
        BP1, BP2, BP3, BP4, BP6, BP7,
    ]
    ALL_CRITERIA: list[ACMGCriterion] = ALL_PATHOGENIC + ALL_BENIGN

    @classmethod
    def get_all_criteria(cls) -> list[ACMGCriterion]:
        """Return all defined ACMG/AMP criteria."""
        return cls.ALL_CRITERIA.copy()

    @classmethod
    def evaluate_all(cls, variant: Variant) -> list[CriterionMatch]:
        """Evaluate all criteria against a variant.

        Args:
            variant: The variant to evaluate.

        Returns:
            List of CriterionMatch for criteria that apply to this variant.
        """
        matches = []
        for criterion in cls.ALL_CRITERIA:
            result = criterion.evaluate(variant)
            if result is not None:
                matches.append(result)
        return matches


def _check_pvs1(variant: Variant) -> tuple[bool, str]:
    """Check PVS1: null variant in gene where LOF is disease mechanism."""
    if variant.genomic_region is None:
        return False, "no genomic region info"

    consequence = variant.genomic_region.consequence.lower()
    null_consequences = [
        "stopgained", "frameshift", "splice_acceptor", "splice_donor",
        "nonsense", "frameshift_variant", "splice_site",
        "start_lost", "stop_gained", "frameshift_variant",
    ]
    for cons in null_consequences:
        if cons in consequence:
            return True, (
                f"Null variant detected: {variant.genomic_region.consequence}. "
                f"Gene: {variant.genomic_region.gene_symbol}"
            )
    return False, "variant is not a null variant"


def _check_pm2(variant: Variant) -> tuple[bool, str]:
    """Check PM2: absent from population databases."""
    if not variant.population_frequencies:
        return True, "Variant absent from all population frequency databases"
    # Very rare: AF < 0.0001 (0.01%)
    max_af = variant.max_population_af
    if max_af < 0.0001:
        return True, f"Extremely rare in population databases (max AF: {max_af:.6f})"
    return False, f"Variant present in populations (max AF: {max_af:.6f})"


def _check_pp2(variant: Variant) -> tuple[bool, str]:
    """Check PP2: multiple prediction tools agree variant is damaging."""
    if not variant.prediction_scores:
        return False, "no prediction scores available"

    damaging_count = 0
    tools_checked = 0
    damaging_labels = {"deleterious", "probably_damaging", "damaging", "disease_causing", "pathogenic"}

    for ps in variant.prediction_scores:
        tools_checked += 1
        is_damaging = False
        # CADD: score >= 10 is damaging
        if ps.tool == "CADD":
            is_damaging = ps.score >= 10.0
        # REVEL: score >= 0.5
        elif ps.tool == "REVEL":
            is_damaging = ps.score >= 0.5
        # PolyPhen: score >= 0.5 or label damaging
        elif ps.tool in ("PolyPhen", "PolyPhen-2"):
            is_damaging = ps.score >= 0.5 or (
                ps.label and any(l in (ps.label or "").lower() for l in damaging_labels)
            )
        # SIFT: score < 0.05 is damaging
        elif ps.tool == "SIFT":
            is_damaging = ps.score < 0.05
        # MutPred: score >= 0.5
        elif ps.tool == "MutPred":
            is_damaging = ps.score >= 0.5
        else:
            # Generic: check label
            if ps.label:
                is_damaging = any(
                    l in ps.label.lower() for l in damaging_labels
                )

        if is_damaging:
            damaging_count += 1

    if tools_checked >= 2 and damaging_count >= 2:
        return True, (
            f"{damaging_count}/{tools_checked} prediction tools indicate damaging effect: "
            + ", ".join(ps.tool for ps in variant.prediction_scores)
        )
    return False, (
        f"Insufficient damaging predictions: {damaging_count}/{tools_checked} tools agree"
    )


def _check_bs1(variant: Variant) -> tuple[bool, str]:
    """Check BS1: allele frequency too high for disease prevalence."""
    if not variant.population_frequencies:
        return False, "no frequency data"
    max_af = variant.max_population_af
    # For most Mendelian diseases, AF > 0.01 (1%) rules out pathogenicity
    if max_af > 0.01:
        return True, f"Allele frequency ({max_af:.4f}) exceeds threshold for Mendelian disease"
    return False, f"Allele frequency ({max_af:.6f}) below BS1 threshold"


def _check_ba1(variant: Variant) -> tuple[bool, str]:
    """Check BA1: allele frequency >> disease prevalence (stand-alone benign)."""
    if not variant.population_frequencies:
        return False, "no frequency data"
    max_af = variant.max_population_af
    # BA1: AF >= 5% for common diseases, or 1% for rare diseases
    # Using 5% as a conservative stand-alone benign threshold
    if max_af >= 0.05:
        return True, f"Allele frequency ({max_af:.4f}) is far above disease prevalence expectations"
    return False, f"Allele frequency ({max_af:.6f}) below BA1 threshold"
