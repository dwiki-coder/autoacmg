"""Tests for ACMG criteria evaluation logic."""

import pytest
from autoacmg.core.acmg_criteria import (
    ACMGCriteria,
    CriterionMatch,
    EvidenceCategory,
    EvidenceStrength,
    _check_ba1,
    _check_bs1,
    _check_pvs1,
    _check_pm2,
    _check_pp2,
)
from autoacmg.core.variant import (
    GenomicRegion,
    PopulationFrequency,
    PredictionScore,
    Variant,
)


class TestACMGCriteriaRegistry:
    """Test criteria registry."""

    def test_all_criteria_defined(self):
        """All criteria should be accessible."""
        all_criteria = ACMGCriteria.get_all_criteria()
        assert len(all_criteria) > 20

    def test_pathogenic_criteria_exist(self):
        """Key pathogenic criteria should exist."""
        criteria = ACMGCriteria.get_all_criteria()
        codes = [c.code for c in criteria]
        assert "PVS1" in codes
        assert "PS1" in codes
        assert "PM1" in codes
        assert "PM2" in codes
        assert "PP1" in codes
        assert "PP2" in codes

    def test_benign_criteria_exist(self):
        """Key benign criteria should exist."""
        criteria = ACMGCriteria.get_all_criteria()
        codes = [c.code for c in criteria]
        assert "BA1" in codes
        assert "BS1" in codes
        assert "BP1" in codes

    def test_criterion_strengths(self):
        """Criterion strengths should have correct weights."""
        assert EvidenceStrength.VERY_STRONG.weight == 4.0
        assert EvidenceStrength.STRONG.weight == 3.0
        assert EvidenceStrength.MODERATE.weight == 2.0
        assert EvidenceStrength.SUPPORTING.weight == 1.0


class TestPVS1:
    """Test PVS1 evaluation."""

    def test_pvs1_stop_gained(self):
        """stop_gained should trigger PVS1."""
        region = GenomicRegion(consequence="stop_gained", gene_symbol="BRCA1")
        variant = Variant(
            chromosome="17", position=100, ref="C", alt="T", genomic_region=region
        )
        applies, reason = _check_pvs1(variant)
        assert applies is True

    def test_pvs1_frameshift(self):
        """frameshift_variant should trigger PVS1."""
        region = GenomicRegion(consequence="frameshift_variant", gene_symbol="TP53")
        variant = Variant(
            chromosome="17", position=100, ref="G", alt="A", genomic_region=region
        )
        applies, reason = _check_pvs1(variant)
        assert applies is True

    def test_pvs1_nonsense(self):
        """nonsense should trigger PVS1."""
        region = GenomicRegion(consequence="nonsense", gene_symbol="BRCA2")
        variant = Variant(
            chromosome="13", position=100, ref="A", alt="T", genomic_region=region
        )
        applies, reason = _check_pvs1(variant)
        assert applies is True

    def test_pvs1_splice_site(self):
        """splice_donor should trigger PVS1."""
        region = GenomicRegion(consequence="splice_donor", gene_symbol="ATM")
        variant = Variant(
            chromosome="11", position=100, ref="G", alt="A", genomic_region=region
        )
        applies, reason = _check_pvs1(variant)
        assert applies is True

    def test_pvs1_missense_not_triggered(self):
        """Missense should NOT trigger PVS1."""
        region = GenomicRegion(consequence="missense_variant", gene_symbol="BRCA1")
        variant = Variant(
            chromosome="17", position=100, ref="A", alt="G", genomic_region=region
        )
        applies, reason = _check_pvs1(variant)
        assert applies is False

    def test_pvs1_no_region(self):
        """No genomic region should not trigger PVS1."""
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        applies, reason = _check_pvs1(variant)
        assert applies is False


class TestPM2:
    """Test PM2 (absent from population databases)."""

    def test_pm2_absent(self):
        """No population data → PM2 applies."""
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        applies, reason = _check_pm2(variant)
        assert applies is True

    def test_pm2_very_rare(self):
        """AF < 0.0001 → PM2 applies."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.00005),
            ],
        )
        applies, reason = _check_pm2(variant)
        assert applies is True

    def test_pm2_not_applicable(self):
        """AF > 0.0001 → PM2 does not apply."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.01),
            ],
        )
        applies, reason = _check_pm2(variant)
        assert applies is False


class TestPP2:
    """Test PP2 (computational evidence of damaging effect)."""

    def test_pp2_multiple_damaging(self):
        """Multiple damaging predictions → PP2 applies."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            prediction_scores=[
                PredictionScore(tool="CADD", score=25.0),
                PredictionScore(tool="REVEL", score=0.9),
                PredictionScore(tool="SIFT", score=0.01),
                PredictionScore(tool="PolyPhen", score=0.95),
            ],
        )
        applies, reason = _check_pp2(variant)
        assert applies is True

    def test_pp2_insufficient(self):
        """Only one damaging prediction → PP2 does not apply."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            prediction_scores=[
                PredictionScore(tool="CADD", score=2.0),
                PredictionScore(tool="REVEL", score=0.1),
            ],
        )
        applies, reason = _check_pp2(variant)
        assert applies is False

    def test_pp2_no_predictions(self):
        """No predictions → PP2 does not apply."""
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        applies, reason = _check_pp2(variant)
        assert applies is False

    def test_pp2_exactly_two_damaging(self):
        """Exactly two tools agree → PP2 applies."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            prediction_scores=[
                PredictionScore(tool="CADD", score=30.0),
                PredictionScore(tool="REVEL", score=0.6),
            ],
        )
        applies, reason = _check_pp2(variant)
        assert applies is True


class TestBS1:
    """Test BS1 (frequency too high for disease)."""

    def test_bs1_high_frequency(self):
        """AF > 1% → BS1 applies."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.05),
            ],
        )
        applies, reason = _check_bs1(variant)
        assert applies is True

    def test_bs1_low_frequency(self):
        """AF < 1% → BS1 does not apply."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.001),
            ],
        )
        applies, reason = _check_bs1(variant)
        assert applies is False

    def test_bs1_no_data(self):
        """No frequency data → BS1 does not apply."""
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        applies, reason = _check_bs1(variant)
        assert applies is False


class TestBA1:
    """Test BA1 (stand-alone very strong benign)."""

    def test_ba1_very_high_frequency(self):
        """AF >= 5% → BA1 applies."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.1),
            ],
        )
        applies, reason = _check_ba1(variant)
        assert applies is True

    def test_ba1_below_threshold(self):
        """AF < 5% → BA1 does not apply."""
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.03),
            ],
        )
        applies, reason = _check_ba1(variant)
        assert applies is False


class TestCriterionMatch:
    """Test CriterionMatch data class."""

    def test_criterion_match_creation(self):
        match = CriterionMatch(
            criterion="PVS1",
            strength=EvidenceStrength.VERY_STRONG,
            category=EvidenceCategory.PATHOGENIC,
            description="Null variant",
        )
        assert match.criterion == "PVS1"
        assert match.strength == EvidenceStrength.VERY_STRONG
        assert match.category == EvidenceCategory.PATHOGENIC
        assert match.applied is True
