"""AutoACMG CLI - Command-line interface for variant classification.

Commands:
    autoacmg annotate  - Annotate and classify a single variant
    autoacmg classify  - Classify variants from a VCF file
    autoacmg report    - Generate classification reports
    autoacmg serve     - Start the REST API server
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from autoacmg import __version__

cli = typer.Typer(
    name="autoacmg",
    help="Automated ACMG/AMP variant classification tool",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]AutoACMG[/] version [bold]{__version__}[/]")
        raise typer.Exit()


@cli.callback()
def main(
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """AutoACMG - Automated ACMG/AMP variant classification."""
    pass


# ─── annotate ───────────────────────────────────────────────────────────────

@cli.command("annotate")
def annotate_variant(
    chromosome: str = typer.Option("", "--chromosome", "-c", help="Chromosome"),
    position: int = typer.Option(0, "--position", "-p", help="Genomic position (1-based)"),
    ref: str = typer.Option("", "--ref", "-r", help="Reference allele"),
    alt: str = typer.Option("", "--alt", "-a", help="Alternate allele"),
    sample_id: str = typer.Option("unknown", "--sample-id", "-s", help="Sample ID"),
    annotate: bool = typer.Option(True, "--annotate/--no-annotate", help="Query external databases"),
    sources: str = typer.Option("clinvar,gnomad,cadd", "--sources", help="Comma-separated sources"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
) -> None:
    """Annotate and classify a single variant.

    Example:
        autoacmg annotate -c 1 -p 7674232 -r G -a A -s sample1
    """
    if not chromosome or position == 0 or not ref or not alt:
        console.print("[red]Error:[/] Please provide chromosome, position, ref, and alt.")
        console.print("\nUsage: autoacmg annotate -c 1 -p 12345 -r A -a T")
        raise typer.Exit(1)

    from autoacmg.core.variant import Variant
    from autoacmg.core.classifier import ACMGClassifier

    variant = Variant(
        chromosome=chromosome,
        position=position,
        ref=ref,
        alt=alt,
        sample_id=sample_id,
    )

    source_list = [s.strip() for s in sources.split(",") if s.strip()]

    if annotate:
        console.print(f"\n[cyan]Gathering evidence[/] for [bold]{variant.get_key()}[/]...")
        from autoacmg.core.evidence import EvidenceGatherer
        gatherer = EvidenceGatherer()
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Annotating...", total=None)
            gatherer.annotate(variant, sources=source_list)
            progress.update(task, completed=True)

    # Classify
    classifier = ACMGClassifier()
    result = classifier.classify(variant)

    # Display results
    _display_result(result, output=output)


# ─── classify ───────────────────────────────────────────────────────────────

@cli.command("classify")
def classify_vcf(
    input_file: str = typer.Argument(..., help="Input VCF file"),
    output: str = typer.Option("results.json", "--output", "-o", help="Output file"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, csv, html)"),
    annotate: bool = typer.Option(True, "--annotate/--no-annotate", help="Query databases"),
    sources: str = typer.Option("clinvar,gnomad,cadd", "--sources", help="Comma-separated sources"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output"),
) -> None:
    """Classify variants from a VCF file.

    Example:
        autoacmg classify variants.vcf -o results.json -f json
    """
    from pathlib import Path
    if not Path(input_file).exists():
        console.print(f"[red]Error:[/] File not found: {input_file}")
        raise typer.Exit(1)

    from autoacmg.utils.vcf_parser import VCFParser
    parser = VCFParser()
    variants = parser.parse_file(input_file)

    if not variants:
        console.print("[yellow]No variants found in input file.[/]")
        raise typer.Exit(1)

    console.print(f"\n[cyan]Processing {len(variants)} variants from {input_file}[/]")

    source_list = [s.strip() for s in sources.split(",") if s.strip()]

    from autoacmg.core.classifier import ACMGClassifier
    classifier = ACMGClassifier()
    results = []

    for i, variant in enumerate(variants, 1):
        if annotate:
            from autoacmg.core.evidence import EvidenceGatherer
            gatherer = EvidenceGatherer()
            if not quiet:
                console.print(f"  [{i}/{len(variants)}] Annotating {variant.get_key()}...")
            gatherer.annotate(variant, sources=source_list)

        result = classifier.classify(variant)
        results.append(result)

        if not quiet:
            classification = result.final_classification.value
            console.print(
                f"    → [bold]{classification}[/] [{result.criteria_string}]"
            )

    # Generate output
    _write_results(results, output, format)
    console.print(f"\n[green]✓[/] Classification complete. Results written to [bold]{output}[/]")


# ─── report ─────────────────────────────────────────────────────────────────

@cli.command("report")
def generate_report(
    input_file: str = typer.Argument(..., help="Input JSON results file"),
    output: str = typer.Option("report.html", "--output", "-o", help="Output file"),
    format: str = typer.Option("html", "--format", "-f", help="Report format (json, csv, html, pdf)"),
) -> None:
    """Generate a classification report from results.

    Example:
        autoacmg report results.json -o report.html -f html
    """
    from pathlib import Path
    import json

    if not Path(input_file).exists():
        console.print(f"[red]Error:[/] File not found: {input_file}")
        raise typer.Exit(1)

    with open(input_file) as f:
        data = json.load(f)

    # Handle both raw results and wrapped reports
    if "variants" in data:
        variants_data = data["variants"]
    elif isinstance(data, list):
        variants_data = data
    else:
        variants_data = [data]

    from autoacmg.core.classifier import ClassificationResult
    from autoacmg.core.variant import ACMGClassification

    results = []
    for v in variants_data:
        try:
            classification = ACMGClassification(v.get("classification", "Uncertain Significance"))
        except ValueError:
            classification = ACMGClassification.UNCERTAIN_SIGNIFICANCE

        cr = ClassificationResult(
            variant_key=v.get("variant", v.get("variant_key", "")),
            final_classification=classification,
            criteria_string=v.get("criteria", v.get("criteria_string", "")),
            evidence_summary=v.get("evidence_summary", {}),
            confidence=v.get("confidence", 0.0),
        )
        results.append(cr)

    # Generate report
    if format == "json":
        from autoacmg.reports.json_report import JSONReport
        report = JSONReport()
        content = report.generate(results, output_path=output)
    elif format == "csv":
        from autoacmg.reports.csv_report import CSVReport
        report = CSVReport()
        content = report.generate(results, output_path=output)
    elif format == "html":
        from autoacmg.reports.html_report import HTMLReport
        report = HTMLReport()
        content = report.generate(results, output_path=output)
    elif format == "pdf":
        from autoacmg.reports.pdf_report import PDFReport
        report = PDFReport()
        report.generate(results, output_path=output)
        content = ""
    else:
        console.print(f"[red]Unknown format:[/] {format}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/] Report generated: [bold]{output}[/]")


# ─── serve ──────────────────────────────────────────────────────────────────

@cli.command("serve")
def serve_api(
    host: str = typer.Option("0.0.0.0", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    workers: int = typer.Option(1, "--workers", help="Number of workers"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on changes"),
) -> None:
    """Start the AutoACMG REST API server.

    Example:
        autoacmg serve --host 0.0.0.0 --port 8000
    """
    from autoacmg.api.server import run_server
    console.print(f"\n[cyan]Starting AutoACMG API server on {host}:{port}[/]")
    run_server(host=host, port=port, workers=workers, reload=reload)


# ─── helpers ────────────────────────────────────────────────────────────────

def _display_result(result, output: Optional[str] = None) -> None:
    """Display classification result to console and/or file."""
    classification = result.final_classification
    color_map = {
        "Pathogenic": "red",
        "Likely Pathogenic": "orange3",
        "Uncertain Significance": "yellow",
        "Likely Benign": "blue",
        "Benign": "green",
        "Not Classified": "grey63",
    }
    color = color_map.get(classification.value, "white")

    panel = Panel(
        f"[bold]{result.variant_key}[/]\n"
        f"[{color}]{classification.value}[/]\n"
        f"Criteria: {result.criteria_string}\n"
        f"Confidence: {result.confidence:.0%}",
        title="Classification Result",
        border_style=color,
    )
    console.print(panel)

    # Show criteria details
    if result.pathogenic_criteria or result.benign_criteria:
        table = Table(title="Applied Criteria")
        table.add_column("Criterion", style="cyan")
        table.add_column("Strength", style="green")
        table.add_column("Description")

        for c in result.pathogenic_criteria:
            table.add_row(c.criterion, c.strength.value, c.description[:80])
        for c in result.benign_criteria:
            table.add_row(c.criterion, c.strength.value, c.description[:80])

        console.print(table)

    if output:
        _write_results([result], output, "json")


def _write_results(results, output: str, fmt: str) -> None:
    """Write results to file."""
    from autoacmg.core.classifier import ClassificationResult

    if fmt == "json":
        from autoacmg.reports.json_report import JSONReport
        JSONReport().generate(results, output_path=output)
    elif fmt == "csv":
        from autoacmg.reports.csv_report import CSVReport
        CSVReport().generate(results, output_path=output)
    elif fmt == "html":
        from autoacmg.reports.html_report import HTMLReport
        HTMLReport().generate(results, output_path=output)


if __name__ == "__main__":
    cli()
