"""CSV report generator for AutoACMG.

Produces flat-file CSV reports for easy spreadsheet viewing.
"""

from __future__ import annotations

import csv
import io
import os
from typing import Optional

from autoacmg.core.classifier import ClassificationResult
from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)


class CSVReport:
    """Generate CSV reports for variant classifications."""

    HEADERS = [
        "Variant", "Chromosome", "Position", "Ref", "Alt",
        "Gene", "Consequence", "Classification", "Criteria",
        "Pathogenic_Criteria", "Benign_Criteria", "Confidence",
        "Population_AF", "ClinVar_Significance", "CADD_Score",
        "Notes",
    ]

    def __init__(self, delimiter: str = ",") -> None:
        self.delimiter = delimiter

    def generate(
        self,
        results: list[ClassificationResult],
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a CSV report.

        Args:
            results: List of classification results.
            output_path: Optional file path to write report.

        Returns:
            CSV string content.
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)
        writer.writerow(self.HEADERS)

        for result in results:
            row = self._build_row(result)
            writer.writerow(row)

        csv_str = output.getvalue()

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", newline="") as f:
                f.write(csv_str)
            logger.info("CSV report written to %s", output_path)

        return csv_str

    def _build_row(self, result: ClassificationResult) -> list[str]:
        """Build a single CSV row from a classification result."""
        # Parse variant key
        variant_key = result.variant_key
        parts = variant_key.split(":")
        chrom = parts[0] if len(parts) > 0 else ""
        pos = parts[1] if len(parts) > 1 else ""
        ref = parts[2] if len(parts) > 2 else ""
        alt = parts[3] if len(parts) > 3 else ""

        # Extract gene and consequence from evidence
        gene = ""
        consequence = ""
        pop_af = ""
        clinvar_sig = ""
        cadd_score = ""

        if result.evidence_summary:
            # Try to extract from evidence summary
            pass

        path_criteria = ", ".join(
            f"{c.criterion}({c.strength.value})" for c in result.pathogenic_criteria
        ) or "None"
        benign_criteria = ", ".join(
            f"{c.criterion}({c.strength.value})" for c in result.benign_criteria
        ) or "None"

        return [
            variant_key,
            chrom,
            pos,
            ref,
            alt,
            gene,
            consequence,
            result.final_classification.value,
            result.criteria_string,
            path_criteria,
            benign_criteria,
            f"{result.confidence:.2f}",
            pop_af,
            clinvar_sig,
            cadd_score,
            result.notes,
        ]
