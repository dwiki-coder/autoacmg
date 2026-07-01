"""Tests for JSON report generator."""

import json
import pytest
from autoacmg.core.classifier import ClassificationResult
from autoacmg.core.variant import ACMGClassification
from autoacmg.reports.json_report import JSONReport


class TestJSONReport:
    """Test JSON report generation."""

    @pytest.fixture
    def sample_results(self):
        return [
            ClassificationResult(
                variant_key="1:100:A:G",
                final_classification=ACMGClassification.PATHOGENIC,
                criteria_string="PVS1, PM2, PP3",
                confidence=0.95,
            ),
            ClassificationResult(
                variant_key="2:200:C:T",
                final_classification=ACMGClassification.UNCERTAIN_SIGNIFICANCE,
                criteria_string="PM2",
                confidence=0.5,
            ),
            ClassificationResult(
                variant_key="3:300:G:A",
                final_classification=ACMGClassification.BENIGN,
                criteria_string="BA1",
                confidence=1.0,
            ),
            ClassificationResult(
                variant_key="4:400:T:C",
                final_classification=ACMGClassification.LIKELY_PATHOGENIC,
                criteria_string="PS4, PM1, PP3",
                confidence=0.75,
            ),
        ]

    def test_report_structure(self, sample_results):
        """Report should have required top-level fields."""
        report = JSONReport()
        json_str = report.generate(sample_results)
        data = json.loads(json_str)

        assert "report_type" in data
        assert "generated_at" in data
        assert "tool" in data
        assert "summary" in data
        assert "variants" in data

    def test_summary_counts(self, sample_results):
        """Summary should have correct counts."""
        report = JSONReport()
        json_str = report.generate(sample_results)
        data = json.loads(json_str)

        assert data["summary"]["total_variants"] == 4
        assert data["summary"]["pathogenic"] == 1
        assert data["summary"]["benign"] == 1

    def test_variant_entries(self, sample_results):
        """Each variant should appear in the output."""
        report = JSONReport()
        json_str = report.generate(sample_results)
        data = json.loads(json_str)

        assert len(data["variants"]) == 4
        keys = [v["variant"] for v in data["variants"]]
        assert "1:100:A:G" in keys
        assert "2:200:C:T" in keys

    def test_json_is_valid(self, sample_results):
        """Output should be valid JSON."""
        report = JSONReport()
        json_str = report.generate(sample_results)
        # Should not raise
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_file_output(self, sample_results, tmp_path):
        """Report should write to file when output_path is provided."""
        output_file = tmp_path / "test_report.json"
        report = JSONReport()
        report.generate(sample_results, output_path=str(output_file))

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert data["summary"]["total_variants"] == 4

    def test_pretty_printing(self):
        """JSON should be pretty-printed by default."""
        result = ClassificationResult(
            variant_key="1:100:A:G",
            final_classification=ACMGClassification.BENIGN,
            criteria_string="BA1",
        )
        report = JSONReport(pretty=True, indent=4)
        json_str = report.generate([result])
        assert "\n" in json_str
        assert "    " in json_str

    def test_empty_results(self):
        """Empty results should produce valid report."""
        report = JSONReport()
        json_str = report.generate([])
        data = json.loads(json_str)
        assert data["summary"]["total_variants"] == 0
        assert data["variants"] == []
