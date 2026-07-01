"""Tests for ClinVar connector."""

import pytest
from unittest.mock import Mock, patch
from autoacmg.databases.clinvar import ClinVarConnector


class TestClinVarConnector:
    """Test ClinVar database connector."""

    @pytest.fixture
    def connector(self):
        return ClinVarConnector(timeout=10, max_retries=2, use_cache=False)

    def test_init(self, connector):
        assert connector.NAME == "clinvar"
        assert "eutils.ncbi.nlm.nih.gov" in connector.BASE_URL

    def test_close(self, connector):
        connector.close()

    def test_query_returns_none_for_missing(self, connector):
        """Query should return None when no data found."""
        from autoacmg.core.variant import Variant
        variant = Variant(chromosome="1", position=999, ref="A", alt="G")
        with patch.object(connector, '_fetch_url', return_value=None):
            result = connector.query(variant)
            assert result is None

    def test_parse_clinvar_result(self, connector):
        """Test parsing of ClinVar JSON result."""
        sample_result = {
            "VariantId": "VCV000001234",
            "ReviewStatus": "criteria_provided_single_submitter",
            "Trait": {"Name": "Breast cancer"},
            "Submission": {"LastEvaluated": "2023-01-01"},
            "Origin": ["germline"],
        }
        parsed = connector._parse_result(sample_result)
        assert parsed is not None
        assert "variant_id" in parsed
        assert parsed["allelic_origins"] == ["germline"]

    def test_parse_empty_result(self, connector):
        """Empty result should return None."""
        assert connector._parse_result({}) is None
        assert connector._parse_result(None) is None

    def test_select_best_result(self, connector):
        """Should select result with highest gold stars."""
        results = [
            {"ReviewStatus": "no_assertion"},
            {"ReviewStatus": "criteria_provided_single_submitter"},
            {"ReviewStatus": "reviewed_by_expert_panel"},
        ]
        best = connector._select_best_result(results)
        assert best["ReviewStatus"] == "reviewed_by_expert_panel"
