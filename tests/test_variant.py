"""Tests for the Variant model."""

import pytest
from autoacmg.core.variant import (
    ACMGClassification,
    ClinicalSignificance,
    GenomicRegion,
    PopulationFrequency,
    PredictionScore,
    Variant,
)


class TestVariantBasics:
    """Test basic Variant creation and properties."""

    def test_create_variant(self):
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        assert variant.chromosome == "1"
        assert variant.position == 100
        assert variant.ref == "A"
        assert variant.alt == "G"
        assert variant.sample_id == "unknown"
        assert variant.rsid is None

    def test_variant_key(self):
        variant = Variant(chromosome="X", position=12345, ref="C", alt="T")
        assert variant.get_key() == "X:12345:C:T"

    def test_variant_equality(self):
        v1 = Variant(chromosome="1", position=100, ref="A", alt="G")
        v2 = Variant(chromosome="1", position=100, ref="A", alt="G")
        v3 = Variant(chromosome="1", position=200, ref="A", alt="G")
        assert v1 == v2
        assert v1 != v3
        assert hash(v1) == hash(v2)

    def test_vcf_line(self):
        variant = Variant(chromosome="1", position=12345, ref="G", alt="A")
        line = variant.get_vcf_line()
        assert line.startswith("1\t12345\t.")
        assert "G" in line
        assert "A" in line

    def test_hgvsg(self):
        variant = Variant(chromosome="3", position=50000, ref="T", alt="C")
        assert variant.get_hgvsg() == "3 g.50000T>C"


class TestVariantTypes:
    """Test variant type detection methods."""

    def test_is_snv(self):
        v = Variant(chromosome="1", position=100, ref="A", alt="G")
        assert v.is_snv() is True
        v2 = Variant(chromosome="1", position=100, ref="A", alt="AG")
        assert v2.is_snv() is False

    def test_is_insertion(self):
        v = Variant(chromosome="1", position=100, ref="A", alt="AG")
        assert v.is_insertion() is True
        v2 = Variant(chromosome="1", position=100, ref="A", alt="G")
        assert v2.is_insertion() is False

    def test_is_deletion(self):
        v = Variant(chromosome="1", position=100, ref="AG", alt="A")
        assert v.is_deletion() is True
        v2 = Variant(chromosome="1", position=100, ref="A", alt="G")
        assert v2.is_deletion() is False

    def test_is_mnv(self):
        v = Variant(chromosome="1", position=100, ref="AG", alt="TC")
        assert v.is_mnv() is True
        v2 = Variant(chromosome="1", position=100, ref="A", alt="G")
        assert v2.is_mnv() is False


class TestPopulationFrequencies:
    """Test population frequency handling."""

    def test_max_population_af_empty(self):
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        assert variant.max_population_af == 0.0

    def test_max_population_af_single(self):
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad", af=0.001),
            ],
        )
        assert variant.max_population_af == 0.001

    def test_max_population_af_multiple(self):
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            population_frequencies=[
                PopulationFrequency(source="gnomad_genomes", af=0.0005),
                PopulationFrequency(source="gnomad_exomes", af=0.001),
                PopulationFrequency(source="gnomad_afr", af=0.002),
            ],
        )
        assert variant.max_population_af == 0.002

    def test_is_novel_with_rsid(self):
        variant = Variant(chromosome="1", position=100, ref="A", alt="G", rsid="rs123")
        assert variant.is_novel is False

    def test_is_novel_without_data(self):
        variant = Variant(chromosome="1", position=100, ref="A", alt="G", rsid=None)
        assert variant.is_novel is True

    def test_is_novel_with_freq_no_rsid(self):
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            rsid=None,
            population_frequencies=[PopulationFrequency(source="gnomad", af=0.001)],
        )
        assert variant.is_novel is False


class TestVariantClassifications:
    """Test ACMG classification tracking."""

    def test_add_classification(self):
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        variant.add_classification("PM2", "moderate", "Absent from populations")
        assert "PM2moderate" in variant.classifications
        assert "PM2" in variant.evidence_summary

    def test_multiple_classifications(self):
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        variant.add_classification("PM2", "moderate", "Absent")
        variant.add_classification("PP3", "supporting", "Computational")
        variant.add_classification("BA1", "very_strong", "High frequency")
        assert len(variant.classifications) == 3

    def test_set_final_classification(self):
        variant = Variant(chromosome="1", position=100, ref="A", alt="G")
        variant.final_classification = ACMGClassification.LIKELY_PATHOGENIC
        assert variant.final_classification == ACMGClassification.LIKELY_PATHOGENIC


class TestVariantSerialization:
    """Test variant serialization."""

    def test_to_dict(self):
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            genomic_region=GenomicRegion(
                gene_symbol="BRCA1",
                consequence="missense_variant",
            ),
        )
        d = variant.to_dict()
        assert d["variant_key"] == "1:100:A:G"
        assert d["gene"] == "BRCA1"
        assert d["consequence"] == "missense_variant"

    def test_from_vcf_record(self):
        vcf_dict = {
            "CHROM": "1",
            "POS": "12345",
            "ID": "rs123",
            "REF": "A",
            "ALT": "G",
            "INFO": {"GENE": "TP53", "CONSEQUENCE": "missense"},
        }
        variant = Variant.from_vcf_record(vcf_dict)
        assert variant.chromosome == "1"
        assert variant.position == 12345
        assert variant.rsid == "rs123"
        assert variant.genomic_region.gene_symbol == "TP53"


class TestClinicalSignificance:
    """Test ClinicalSignificance enum."""

    def test_all_values(self):
        assert ClinicalSignificance.PATHOGENIC.value == "pathogenic"
        assert ClinicalSignificance.LIKELY_PATHOGENIC.value == "likely_pathogenic"
        assert ClinicalSignificance.UNCERTAIN_SIGNIFICANCE.value == "uncertain_significance"
        assert ClinicalSignificance.LIKELY_BENIGN.value == "likely_benign"
        assert ClinicalSignificance.BENIGN.value == "benign"


class TestPredictionScore:
    """Test prediction score handling."""

    def test_prediction_score_creation(self):
        ps = PredictionScore(tool="CADD", score=25.3, label="deleterious")
        assert ps.tool == "CADD"
        assert ps.score == 25.3
        assert ps.label == "deleterious"

    def test_variant_with_predictions(self):
        variant = Variant(
            chromosome="1",
            position=100,
            ref="A",
            alt="G",
            prediction_scores=[
                PredictionScore(tool="CADD", score=25.3),
                PredictionScore(tool="REVEL", score=0.85),
            ],
        )
        assert len(variant.prediction_scores) == 2
        assert variant.prediction_scores[0].tool == "CADD"
        assert variant.prediction_scores[1].tool == "REVEL"
