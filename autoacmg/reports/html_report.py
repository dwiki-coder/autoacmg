"""HTML report generator for AutoACMG.

Produces styled HTML reports with variant classification details
using Jinja2 templating.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from autoacmg.core.classifier import ClassificationResult
from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoACMG - Variant Classification Report</title>
    <style>
        :root {
            --pathogenic: #dc3545;
            --likely-pathogenic: #fd7e14;
            --vus: #ffc107;
            --likely-benign: #17a2b8;
            --benign: #28a745;
            --not-classified: #6c757d;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        header h1 { font-size: 28px; margin-bottom: 5px; }
        header p { opacity: 0.9; }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card .count { font-size: 36px; font-weight: bold; }
        .card .label { font-size: 14px; color: #666; margin-top: 5px; }
        .card.pathogenic .count { color: var(--pathogenic); }
        .card.likely-pathogenic .count { color: var(--likely-pathogenic); }
        .card.vus .count { color: #856404; }
        .card.likely-benign .count { color: var(--likely-benign); }
        .card.benign .count { color: var(--benign); }
        table {
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-collapse: collapse;
        }
        th {
            background: #2d3748;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-size: 13px;
        }
        td {
            padding: 10px 15px;
            border-bottom: 1px solid #eee;
            font-size: 13px;
        }
        tr:hover { background: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            color: white;
        }
        .badge-pathogenic { background: var(--pathogenic); }
        .badge-likely-pathogenic { background: var(--likely-pathogenic); }
        .badge-vus { background: var(--vus); color: #333; }
        .badge-likely-benign { background: var(--likely-benign); }
        .badge-benign { background: var(--benign); }
        .criteria { font-size: 11px; color: #666; }
        footer { text-align: center; padding: 20px; color: #999; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AutoACMG Classification Report</h1>
            <p>Generated: {{ generated_at }} | Total Variants: {{ total_variants }}</p>
        </header>

        <div class="summary-cards">
            <div class="card pathogenic">
                <div class="count">{{ summary.pathogenic }}</div>
                <div class="label">Pathogenic</div>
            </div>
            <div class="card likely-pathogenic">
                <div class="count">{{ summary.likely_pathogenic }}</div>
                <div class="label">Likely Pathogenic</div>
            </div>
            <div class="card vus">
                <div class="count">{{ summary.vus }}</div>
                <div class="label">VUS</div>
            </div>
            <div class="card likely-benign">
                <div class="count">{{ summary.likely_benign }}</div>
                <div class="label">Likely Benign</div>
            </div>
            <div class="card benign">
                <div class="count">{{ summary.benign }}</div>
                <div class="label">Benign</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Variant</th>
                    <th>Gene</th>
                    <th>Consequence</th>
                    <th>Classification</th>
                    <th>Criteria</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody>
                {% for v in variants %}
                <tr>
                    <td><code>{{ v.variant }}</code></td>
                    <td>{{ v.gene }}</td>
                    <td>{{ v.consequence }}</td>
                    <td><span class="badge badge-{{ v.badge_class }}">{{ v.classification }}</span></td>
                    <td class="criteria">{{ v.criteria }}</td>
                    <td>{{ "%.0f%%"|format(v.confidence * 100) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <footer>
            <p>Generated by <strong>AutoACMG</strong> v0.1.0 |
            Based on ACMG/AMP 2015 guidelines (Richards et al.)</p>
        </footer>
    </div>
</body>
</html>
"""


class HTMLReport:
    """Generate HTML reports for variant classifications."""

    def __init__(self) -> None:
        self.template = HTML_TEMPLATE

    def generate(
        self,
        results: list[ClassificationResult],
        output_path: Optional[str] = None,
    ) -> str:
        """Generate an HTML report.

        Args:
            results: List of classification results.
            output_path: Optional file path to write report.

        Returns:
            HTML string content.
        """
        # Build template data
        summary = self._build_summary(results)
        variants = [self._format_variant(r, summary) for r in results]

        html = self.template.replace("{{ generated_at }}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        html = html.replace("{{ total_variants }}", str(len(results)))
        html = html.replace("{{ summary.pathogenic }}", str(summary.get("pathogenic", 0)))
        html = html.replace("{{ summary.likely_pathogenic }}", str(summary.get("likely_pathogenic", 0)))
        html = html.replace("{{ summary.vus }}", str(summary.get("vus", 0)))
        html = html.replace("{{ summary.likely_benign }}", str(summary.get("likely_benign", 0)))
        html = html.replace("{{ summary.benign }}", str(summary.get("benign", 0)))

        # Build table rows
        table_rows = []
        for v in variants:
            table_rows.append(
                f"""                <tr>
                    <td><code>{v['variant']}</code></td>
                    <td>{v.get('gene', 'N/A')}</td>
                    <td>{v.get('consequence', 'N/A')}</td>
                    <td><span class="badge badge-{v['badge_class']}">{v['classification']}</span></td>
                    <td class="criteria">{v['criteria']}</td>
                    <td>{v['confidence']:.0%}</td>
                </tr>"""
            )

        # Replace the template body section
        tbody_section = "            </tbody>\n        </table>"
        table_rows_html = "\n".join(table_rows)
        html = html.replace("            </tbody>\n        </table>", f"{table_rows_html}\n            </tbody>\n        </table>")

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(html)
            logger.info("HTML report written to %s", output_path)

        return html

    def _build_summary(self, results: list[ClassificationResult]) -> dict:
        """Build summary statistics."""
        from collections import Counter

        classifications = Counter(r.final_classification.value for r in results)
        return {
            "pathogenic": classifications.get("Pathogenic", 0),
            "likely_pathogenic": classifications.get("Likely Pathogenic", 0),
            "vus": classifications.get("Uncertain Significance", 0),
            "likely_benign": classifications.get("Likely Benign", 0),
            "benign": classifications.get("Benign", 0),
        }

    def _format_variant(self, result: ClassificationResult, summary: dict) -> dict:
        """Format a single variant for the report."""
        classification = result.final_classification.value
        badge_map = {
            "Pathogenic": "pathogenic",
            "Likely Pathogenic": "likely-pathogenic",
            "Uncertain Significance": "vus",
            "Likely Benign": "likely-benign",
            "Benign": "benign",
            "Not Classified": "vus",
        }
        return {
            "variant": result.variant_key,
            "classification": classification,
            "badge_class": badge_map.get(classification, "vus"),
            "criteria": result.criteria_string,
            "confidence": result.confidence,
            "gene": result.evidence_summary.get("gene", ""),
            "consequence": result.evidence_summary.get("consequence", ""),
        }
