"""ACMG/AMP Classification Engine.

Implements the classification decision rules from the 2015 ACMG/AMP guidelines
(Richards et al., Genetics in Medicine). Classification is determined by
counting and weighting applied evidence criteria:

Pathogenic/Benign decision rules (ACMG 2015, Table 2):
  - Pathogenic:      PVS1 + ≥1 PS  OR  2 PS  OR  1 PS + 3 PM  OR  1 PS + 2 PM  OR  1 PS + 1 PM + 2 PP
                      OR  4 PM  OR  3 PM + 2 PP  OR  2 PM + 4 PP  OR  1 PM + 6 PP
  - Likely Pathogenic: 1 PS + 1-2 PM  OR  1 PS + 1 PM + 1-2 PP  OR  1 PS + 3-4 PP
                       OR  2 PM + 2-4 PP  OR  1 PM + 2-5 PP  OR  3 PM + 1-3 PP
  - Likely Benign:  1 BS  OR  1 BS + 1-3 BP  OR  1 BP + 1 BS
  - Benign:         BA1  OR  ≥2 BS  OR  1 BS + 4 BP

Weight calculation (for borderline cases):
  Very Strong = 4, Strong = 3, Moderate = 2, Supporting = 1
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from autoacmg.core.acmg_criteria import (
    ACMGCriteria,
    ACMGCriterion,
    CriterionMatch,
    EvidenceCategory,
    EvidenceStrength,
)
from autoacmg.core.variant import ACMGClassification, Variant

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of ACMG classification for a single variant."""

    variant_key: str
    final_classification: ACMGClassification
    pathogenic_criteria: list[CriterionMatch] = field(default_factory=list)
    benign_criteria: list[CriterionMatch] = field(default_factory=list)
    criteria_string: str = ""
    evidence_summary: dict = field(default_factory=dict)
    confidence: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "variant": self.variant_key,
            "classification": self.final_classification.value,
            "criteria": self.criteria_string,
            "pathogenic_criteria": [
                {"code": c.criterion, "strength": c.strength.value,
                 "description": c.description}
                for c in self.pathogenic_criteria
            ],
            "benign_criteria": [
                {"code": c.criterion, "strength": c.strength.value,
                 "description": c.description}
                for c in self.benign_criteria
            ],
            "evidence_summary": self.evidence_summary,
            "confidence": self.confidence,
            "notes": self.notes,
        }


class ACMGClassifier:
    """ACMG/AMP Classification Engine.

    Applies the 2015 ACMG/AMP guidelines to classify variants based on
    gathered evidence. Supports both automatic classification (using
    auto-applicable criteria) and manual/curated classification.

    Usage:
        classifier = ACMGClassifier()
        result = classifier.classify(variant)
    """

    def __init__(self, criteria_source: type[ACMGCriteria] = ACMGCriteria) -> None:
        """Initialize the classifier.

        Args:
            criteria_source: Class providing ACMG criteria definitions.
        """
        self.criteria_source = criteria_source
        self.manual_criteria: dict[str, list[str]] = {}

    def classify(
        self, variant: Variant, manual_criteria: Optional[dict[str, list[str]]] = None
    ) -> ClassificationResult:
        """Classify a variant according to ACMG/AMP guidelines.

        Args:
            variant: The variant to classify.
            manual_criteria: Optional manual criteria overrides. Keys are
                criterion codes, values are lists of strength levels.

        Returns:
            ClassificationResult with the final classification and all evidence.
        """
        logger.info("Classifying variant: %s", variant.get_key())

        # Evaluate all auto-applicable criteria
        matches = self.criteria_source.evaluate_all(variant)

        # Add manual criteria overrides
        if manual_criteria:
            for code, strengths in manual_criteria.items():
                for strength_str in strengths:
                    strength = self._parse_strength(strength_str)
                    category = self._criterion_category(code)
                    match = CriterionMatch(
                        criterion=code,
                        strength=strength,
                        category=category,
                        description=f"Manual: {code} ({strength_str})",
                    )
                    matches.append(match)
                    variant.add_classification(code, strength_str, match.description)

        # Split into pathogenic and benign
        pathogenic = [m for m in matches if m.category == EvidenceCategory.PATHOGENIC]
        benign = [m for m in matches if m.category == EvidenceCategory.BENIGN]

        # Apply ACMG classification rules
        classification, criteria_str, confidence = self._determine_classification(
            pathogenic, benign
        )

        # Update variant with classifications
        for match in matches:
            variant.add_classification(
                match.criterion,
                match.strength.value,
                match.description,
            )
        variant.final_classification = classification

        logger.info(
            "Variant %s classified as %s [%s]",
            variant.get_key(),
            classification.value,
            criteria_str,
        )

        return ClassificationResult(
            variant_key=variant.get_key(),
            final_classification=classification,
            pathogenic_criteria=pathogenic,
            benign_criteria=benign,
            criteria_string=criteria_str,
            evidence_summary=variant.evidence_summary,
            confidence=confidence,
        )

    def _determine_classification(
        self, pathogenic: list[CriterionMatch], benign: list[CriterionMatch]
    ) -> tuple[ACMGClassification, str, float]:
        """Apply ACMG classification decision rules.

        Implements the counting rules from Table 2 of Richards et al. (2015).
        Criteria are counted by strength category:
          - PVS1/BA1: Very Strong (VS)
          - PS/BS: Strong (S)
          - PM/BP: Moderate (M)
          - PP/BP: Supporting (P)

        Returns:
            Tuple of (classification, criteria_string, confidence_score).
        """
        # Count by strength
        pvs1 = 1 if self._has_criterion(pathogenic, "PVS1") else 0
        ba1 = 1 if self._has_criterion(benign, "BA1") else 0

        strong_p = self._count_strong(pathogenic)
        moderate_p = self._count_moderate(pathogenic)
        supporting_p = self._count_supporting(pathogenic)

        strong_b = self._count_strong(benign)
        moderate_b = self._count_moderate(benign)
        supporting_b = self._count_supporting(benign)

        # --- Benign rules (checked first as per guidelines) ---
        if ba1 >= 1:
            return ACMGClassification.BENIGN, "BA1", 1.0

        if strong_b >= 2:
            criteria = f"{strong_b} BS"
            return ACMGClassification.BENIGN, criteria, 0.9

        if strong_b >= 1 and supporting_b >= 4:
            criteria = f"{strong_b} BS, {supporting_b} BP"
            return ACMGClassification.BENIGN, criteria, 0.9

        # Likely Benign: 1 BS OR 1 BP + 1 BS (old rules)
        if strong_b >= 1:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_BENIGN, criteria, 0.7

        if supporting_b >= 1 and strong_b >= 1:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_BENIGN, criteria, 0.65

        # --- Pathogenic rules ---
        # Pathogenic combinations
        if pvs1 >= 1 and strong_p >= 1:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.PATHOGENIC, criteria, 0.95

        if strong_p >= 2:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.PATHOGENIC, criteria, 0.9

        if strong_p >= 1 and moderate_p >= 3:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.PATHOGENIC, criteria, 0.9

        if strong_p >= 1 and moderate_p >= 2 and supporting_p >= 1:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.PATHOGENIC, criteria, 0.85

        if strong_p >= 1 and moderate_p >= 1 and supporting_p >= 2:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.PATHOGENIC, criteria, 0.85

        if moderate_p >= 4:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.PATHOGENIC, criteria, 0.8

        # Likely Pathogenic combinations
        if strong_p >= 1 and moderate_p >= 1:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_PATHOGENIC, criteria, 0.75

        if strong_p >= 1 and supporting_p >= 1 and moderate_p >= 1:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_PATHOGENIC, criteria, 0.7

        if strong_p >= 1 and supporting_p >= 3:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_PATHOGENIC, criteria, 0.7

        if moderate_p >= 2 and supporting_p >= 2:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_PATHOGENIC, criteria, 0.7

        if moderate_p >= 1 and supporting_p >= 2:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_PATHOGENIC, criteria, 0.65

        if moderate_p >= 3 and supporting_p >= 1:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_PATHOGENIC, criteria, 0.65

        if supporting_p >= 6:
            criteria = self._build_criteria_str(pathogenic, benign)
            return ACMGClassification.LIKELY_PATHOGENIC, criteria, 0.6

        # Uncertain Significance
        total_p = len(pathogenic)
        total_b = len(benign)
        if total_p == 0 and total_b == 0:
            return ACMGClassification.NOT_CLASSIFIED, "No criteria applied", 0.0

        criteria = self._build_criteria_str(pathogenic, benign)
        # If we have some evidence but not enough for a call
        return ACMGClassification.UNCERTAIN_SIGNIFICANCE, criteria, 0.5

    def _build_criteria_str(
        self, pathogenic: list[CriterionMatch], benign: list[CriterionMatch]
    ) -> str:
        """Build the criteria string (e.g., 'PM2, PP3, PP5')."""
        parts = []
        for m in pathogenic + benign:
            parts.append(m.criterion)
        return ", ".join(parts) if parts else "No criteria"

    def _has_criterion(self, matches: list[CriterionMatch], code: str) -> bool:
        return any(m.criterion == code for m in matches)

    def _count_strong(self, matches: list[CriterionMatch]) -> int:
        return sum(
            1 for m in matches
            if m.strength in (EvidenceStrength.STRONG, EvidenceStrength.VERY_STRONG)
        )

    def _count_moderate(self, matches: list[CriterionMatch]) -> int:
        return sum(1 for m in matches if m.strength == EvidenceStrength.MODERATE)

    def _count_supporting(self, matches: list[CriterionMatch]) -> int:
        return sum(1 for m in matches if m.strength == EvidenceStrength.SUPPORTING)

    def _parse_strength(self, strength_str: str) -> EvidenceStrength:
        """Parse strength string to EvidenceStrength enum."""
        mapping = {
            "very_strong": EvidenceStrength.VERY_STRONG,
            "strong": EvidenceStrength.STRONG,
            "moderate": EvidenceStrength.MODERATE,
            "supporting": EvidenceStrength.SUPPORTING,
        }
        return mapping.get(strength_str.lower(), EvidenceStrength.SUPPORTING)

    def _criterion_category(self, code: str) -> EvidenceCategory:
        """Determine if a criterion code is pathogenic or benign."""
        pathogenic_prefixes = ("PVS", "PS", "PM", "PP")
        benign_prefixes = ("BA", "BS", "BP")
        for prefix in pathogenic_prefixes:
            if code.startswith(prefix):
                return EvidenceCategory.PATHOGENIC
        for prefix in benign_prefixes:
            if code.startswith(prefix):
                return EvidenceCategory.BENIGN
        return EvidenceCategory.PATHOGENIC  # default

    def classify_batch(
        self, variants: list[Variant]
    ) -> list[ClassificationResult]:
        """Classify multiple variants.

        Args:
            variants: List of variants to classify.

        Returns:
            List of ClassificationResult objects.
        """
        results = []
        for variant in variants:
            result = self.classify(variant)
            results.append(result)
        logger.info(
            "Batch classification complete: %d variants processed", len(results)
        )
        return results
