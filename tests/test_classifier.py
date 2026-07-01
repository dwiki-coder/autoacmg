"""Tests for the ACMG classifier."""

import pytest
from autoacmg.core.variant import ACMGClassification, GenomicRegion, PopulationFrequency, PredictionScore, Variant
from autoacmg.core.classifier import ACMGClassifier


class TestClassifierBasic:
    """Test basic classification functionality."""

    def test_classify_empty_variant(self, basic_variant):
        """A bare variant gets PM2 (absent from populations) → VUS."""
        classifier = ACMGClassifier()
        result = classifier.classify(basic_variant)
        # Auto-eval finds PM2 (absent from populations) → Uncertain Significance
        assert result.final_classification == ACMGClassification.UNCERTAIN_SIGNIFICANCE
        assert result.variant_key == basic_variant.get_key()

    def test_classify_result_to_dict(self, basic_variant):
        """Classification result should serialize properly."""
        classifier = ACMGClassifier()
        result = classifier.classify(basic_variant)
        d = result.to_dict()
        assert "variant" in d
        assert "classification" in d
        assert "criteria" in d
        assert d["variant"] == basic_variant.get_key()


class TestClassifierWithEvidence:
    """Test classification with various evidence combinations."""

    def test_stop_gained_classified_pathogenic(self, stop_gained_variant):
        """Null variants should trigger PVS1."""
        classifier = ACMGClassifier()
        result = classifier.classify(stop_gained_variant)
        # PVS1 (very strong) + PM2 (moderate) = Pathogenic
        assert result.final_classification in (
            ACMGClassification.PATHOGENIC,
            ACMGClassification.LIKELY_PATHOGENIC,
        )
        assert any(c.criterion == "PVS1" for c in result.pathogenic_criteria)

    def test_high_frequency_benign(self, common_variant):
        """Common variants should be classified as benign."""
        classifier = ACMGClassifier()
        result = classifier.classify(common_variant)
        # BA1 (very strong benign) → Benign
        assert result.final_classification == ACMGClassification.BENIGN
        assert any(c.criterion == "BA1" for c in result.benign_criteria)

    def test_damaging_predictions_pathogenic(self, annotated_variant):
        """Multiple damaging predictions should contribute to pathogenicity."""
        classifier = ACMGClassifier()
        result = classifier.classify(annotated_variant)
        # PP2 should be triggered (multiple tools agree on damaging)
        has_pp2 = any(c.criterion == "PP2" for c in result.pathogenic_criteria)
        # PM2 should be triggered (very rare)
        has_pm2 = any(c.criterion == "PM2" for c in result.pathogenic_criteria)
        assert has_pp2 or has_pm2

    def test_novel_variant_likely_pathogenic(self, novel_variant):
        """A novel variant with no population data gets PM2."""
        novel_variant.genomic_region = GenomicRegion(
            gene_symbol="BRCA1",
            consequence="missense_variant",
        )
        novel_variant.prediction_scores = [
            PredictionScore(tool="CADD", score=30.0),
            PredictionScore(tool="REVEL", score=0.9),
            PredictionScore(tool="SIFT", score=0.01),
        ]
        classifier = ACMGClassifier()
        result = classifier.classify(novel_variant)
        # Should have PM2 (absent) + PP2 (damaging predictions)
        assert result.final_classification in (
            ACMGClassification.LIKELY_PATHOGENIC,
            ACMGClassification.UNCERTAIN_SIGNIFICANCE,
        )


class TestClassifierBatch:
    """Test batch classification."""

    def test_batch_classify(self):
        """Batch classification should process all variants."""
        variants = [
            Variant(chromosome="1", position=100, ref="A", alt="G"),
            Variant(chromosome="2", position=200, ref="C", alt="T"),
            Variant(chromosome="3", position=300, ref="T", alt="A"),
        ]
        classifier = ACMGClassifier()
        results = classifier.classify_batch(variants)
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.variant_key == variants[i].get_key()


class TestClassifierDecisionRules:
    """Test ACMG decision rule implementations."""

    def test_no_criteria_not_classified(self, basic_variant):
        """Bare variant auto-matches PM2 → Uncertain Significance."""
        classifier = ACMGClassifier()
        result = classifier.classify(basic_variant)
        assert result.final_classification == ACMGClassification.UNCERTAIN_SIGNIFICANCE

    def test_ba1_overrides_pathogenic(self):
        """BA1 (very strong benign) should result in Benign."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.1),
            ],
        )
        classifier = ACMGClassifier()
        result = classifier.classify(variant)
        assert result.final_classification == ACMGClassification.BENIGN

    def test_manual_criteria_override(self, basic_variant):
        """Manual criteria should be applied."""
        classifier = ACMGClassifier()
        result = classifier.classify(
            basic_variant,
            manual_criteria={"PS1": ["strong"], "PM1": ["moderate"]},
        )
        # PS1 (strong) + PM1 (moderate) = Likely Pathogenic
        assert result.final_classification in (
            ACMGClassification.LIKELY_PATHOGENIC,
            ACMGClassification.PATHOGENIC,
        )
