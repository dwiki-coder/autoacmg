"""Pytest configuration and shared fixtures for AutoACMG tests."""

import pytest
from autoacmg.core.variant import (
    ACMGClassification,
    ClinVarAnnotation,
    ClinicalSignificance,
    GenomicRegion,
    PopulationFrequency,
    PredictionScore,
    Variant,
)


@pytest.fixture
def basic_variant() -> Variant:
    """A basic SNV variant with no annotations."""
    return Variant(
        chromosome="1",
        position=7674232,
        ref="G",
        alt="A",
        sample_id="test_sample",
    )


@pytest.fixture
def annotated_variant() -> Variant:
    """A variant with population frequencies and predictions."""
    region = GenomicRegion(
        gene_symbol="BRCA1",
        gene_id="ENSG00000012048",
        region="exonic",
        consequence="missense_variant",
        protein_change="p.Gly605Asp",
    )
    return Variant(
        chromosome="17",
        position=43061583,
        ref="C",
        alt="T",
        sample_id="test_sample",
        rsid="rs80359032",
        genomic_region=region,
        population_frequencies=[
            PopulationFrequency(
                source="gnomad_genomes_all",
                af=0.00001,
                total_alleles=125000,
                total_samples=62500,
                heterozygote_count=2,
            ),
            PopulationFrequency(
                source="gnomad_genomes_eur",
                af=0.00002,
                total_alleles=80000,
                total_samples=40000,
                heterozygote_count=2,
            ),
        ],
        prediction_scores=[
            PredictionScore(tool="CADD", score=25.3),
            PredictionScore(tool="REVEL", score=0.85),
            PredictionScore(tool="SIFT", score=0.01),
            PredictionScore(tool="PolyPhen", score=0.95),
        ],
        clinvar_annotation=ClinVarAnnotation(
            variant_id="VCV000000000",
            clinical_significance=ClinicalSignificance.UNCERTAIN_SIGNIFICANCE,
            condition="Breast cancer",
            review_status="criteria_provided_single_submitter",
            gold_stars=1,
        ),
    )


@pytest.fixture
def stop_gained_variant() -> Variant:
    """A nonsense/stop-gained variant in BRCA1."""
    region = GenomicRegion(
        gene_symbol="BRCA1",
        gene_id="ENSG00000012048",
        region="exonic",
        consequence="stop_gained",
        protein_change="p.Arg1482Ter",
    )
    return Variant(
        chromosome="17",
        position=43064170,
        ref="C",
        alt="T",
        sample_id="test_sample",
        rsid="rs80359032",
        genomic_region=region,
        population_frequencies=[
            PopulationFrequency(
                source="gnomad_genomes_all",
                af=0.000001,
                total_alleles=125000,
                total_samples=62500,
            ),
        ],
        prediction_scores=[
            PredictionScore(tool="CADD", score=45.0),
        ],
    )


@pytest.fixture
def frameshift_variant() -> Variant:
    """A frameshift variant with no population data."""
    region = GenomicRegion(
        gene_symbol="TP53",
        gene_id="ENSG00000141510",
        region="exonic",
        consequence="frameshift_variant",
        protein_change="p.Arg199fs",
    )
    return Variant(
        chromosome="17",
        position=7577539,
        ref="G",
        alt="A",
        sample_id="test_sample",
        rsid="rs11540652",
        genomic_region=region,
        population_frequencies=[],
    )


@pytest.fixture
def common_variant() -> Variant:
    """A common variant with high population frequency."""
    return Variant(
        chromosome="1",
        position=12345,
        ref="A",
        alt="G",
        sample_id="test_sample",
        population_frequencies=[
            PopulationFrequency(
                source="gnomad_genomes_all",
                af=0.35,
                total_alleles=125000,
                total_samples=62500,
            ),
        ],
    )


@pytest.fixture
def novel_variant() -> Variant:
    """A novel variant with no population data or predictions."""
    return Variant(
        chromosome="X",
        position=67543821,
        ref="C",
        alt="A",
        sample_id="test_sample",
        rsid=None,
        population_frequencies=[],
        prediction_scores=[],
    )
