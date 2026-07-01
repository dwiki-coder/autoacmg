"""Tests for gnomAD connector."""

import pytest
from unittest.mock import Mock, patch
from autoacmg.databases.gnomad import gnomADConnector


class TestGnomADConnector:
    """Test gnomAD database connector."""

    @pytest.fixture
    def connector(self):
        return gnomADConnector(timeout=10, max_retries=2, use_cache=False)

    def test_init(self, connector):
        assert connector.NAME == "gnomad"
        assert "gnomad.broadinstitute.org" in connector.BASE_URL

    def test_close(self, connector):
        connector.close()

    def test_query_returns_none_for_missing(self, connector):
        from autoacmg.core.variant import Variant
        variant = Variant(chromosome="1", position=999, ref="A", alt="G")
        with patch.object(connector, '_fetch_url', return_value=None):
            result = connector.query(variant)
            assert result is None

    def test_parse_gnomad_genomes(self, connector):
        """Test parsing genomes data."""
        sample_data = {
            "genomes": {
                "af": 0.0001,
                "n": {"alleles": 100000, "samples": 50000, "homozygotes": 1, "heterozygotes": 20},
                "pops": {
                    "afr": {"af": 0.0002, "n": {"alleles": 20000, "samples": 10000}},
                    "eur": {"af": 0.0001, "n": {"alleles": 60000, "samples": 30000}},
                },
            }
        }
        result = connector._parse_result(sample_data)
        assert "frequencies" in result
        assert len(result["frequencies"]) >= 3

    def test_parse_gnomad_exomes(self, connector):
        """Test parsing exomes data."""
        sample_data = {
            "exomes": {
                "af": 0.00005,
                "n": {"alleles": 200000, "samples": 100000},
                "pops": {"fin": {"af": 0.001}},
            }
        }
        result = connector._parse_result(sample_data)
        assert "frequencies" in result

    def test_parse_empty_result(self, connector):
        """Empty data should return empty frequencies."""
        result = connector._parse_result({})
        assert result == {"frequencies": [], "raw": {}}
