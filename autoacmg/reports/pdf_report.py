"""PDF report generator for AutoACMG.

Produces printable PDF reports using WeasyPrint.
Falls back to HTML string if WeasyPrint is not available.
"""

from __future__ import annotations

import os
from typing import Optional

from autoacmg.core.classifier import ClassificationResult
from autoacmg.reports.html_report import HTMLReport
from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)


class PDFReport:
    """Generate PDF reports for variant classifications.

    Uses WeasyPrint for PDF generation. Falls back gracefully
    if WeasyPrint is not installed.
    """

    def __init__(self) -> None:
        self.html_report = HTMLReport()
        self.weasyprint_available = False
        try:
            import weasyprint  # noqa: F401
            self.weasyprint_available = True
        except ImportError:
            logger.warning(
                "WeasyPrint not installed. Install with: pip install weasyprint"
            )

    def generate(
        self,
        results: list[ClassificationResult],
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """Generate a PDF report.

        Args:
            results: List of classification results.
            output_path: File path to write the PDF.

        Returns:
            PDF bytes as string path, or None if generation failed.
        """
        if not self.weasyprint_available:
            logger.warning(
                "WeasyPrint not available. Install with: pip install weasyprint"
            )
            # Return the HTML instead as fallback info
            return self._generate_fallback_html(results)

        if not output_path:
            raise ValueError("output_path is required for PDF generation")

        try:
            from weasyprint import HTML as WeasyHTML

            # Generate HTML content
            html_content = self.html_report.generate(results)

            # Convert to PDF
            doc = WeasyHTML(string=html_content)
            pdf_bytes = doc.write_pdf()

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

            logger.info("PDF report written to %s", output_path)
            return output_path

        except Exception as e:
            logger.error("Failed to generate PDF: %s", e)
            return None

    def _generate_fallback_html(self, results: list[ClassificationResult]) -> str:
        """Generate HTML as fallback when WeasyPrint is unavailable."""
        return self.html_report.generate(results)
