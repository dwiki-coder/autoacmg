"""JSON report generator for AutoACMG.

Produces structured JSON reports with all variant classification data.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

from autoacmg.core.classifier import ClassificationResult
from autoacmg.core.variant import Variant
from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)


class JSONReport:
    """Generate JSON reports for variant classifications."""

    def __init__(self, pretty: bool = True, indent: int = 2) -> None:
        self.pretty = pretty
        self.indent = indent

    def generate(
        self,
        results: list[ClassificationResult],
        output_path: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Generate a JSON report.

        Args:
            results: List of classification results.
            output_path: Optional file path to write report.
            metadata: Optional metadata to include in report.

        Returns:
            JSON string of the report.
        """
        report = {
            "report_type": "acmg_classification",
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "tool": "AutoACMG",
            "tool_version": "0.1.0",
            "metadata": metadata or {},
            "summary": self._build_summary(results),
            "variants": [r.to_dict() for r in results],
        }

        json_str = json.dumps(report, indent=self.indent, default=str)

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(json_str)
            logger.info("JSON report written to %s", output_path)

        return json_str

    def _build_summary(self, results: list[ClassificationResult]) -> dict:
        """Build summary statistics."""
        from collections import Counter

        classifications = Counter(r.final_classification.value for r in results)
        return {
            "total_variants": len(results),
            "classifications": dict(classifications),
            "pathogenic": classifications.get("Pathogenic", 0),
            "likely_pathogenic": classifications.get("Likely Pathogenic", 0),
            "uncertain_significance": classifications.get("Uncertain Significance", 0),
            "likely_benign": classifications.get("Likely Benign", 0),
            "benign": classifications.get("Benign", 0),
        }
