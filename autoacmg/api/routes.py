"""API routes for AutoACMG.

Defines REST endpoints for variant annotation, batch processing,
and status reporting.
"""

from __future__ import annotations

from typing import Optional

import fastapi
from pydantic import BaseModel, Field

from autoacmg.core.variant import Variant

router = fastapi.APIRouter()


# Request/Response models
class VariantRequest(BaseModel):
    """Request model for single variant annotation."""

    chromosome: str = Field(..., description="Chromosome (e.g., '1', 'X', 'MT')")
    position: int = Field(..., description="1-based genomic position")
    ref: str = Field(..., description="Reference allele")
    alt: str = Field(..., description="Alternate allele")
    sample_id: str = Field(default="unknown", description="Sample identifier")
    annotate: bool = Field(default=True, description="Query external databases")
    sources: list[str] = Field(
        default_factory=lambda: [
            "clinvar", "gnomad", "cadd", "clingen", "dbsnp", "cosmic"
        ],
        description="Database sources to query",
    )


class BatchVariantRequest(BaseModel):
    """Request model for batch variant annotation."""

    variants: list[VariantRequest] = Field(..., description="List of variants")
    annotate: bool = Field(default=True, description="Query external databases")
    sources: list[str] = Field(
        default_factory=lambda: ["clinvar", "gnomad"],
        description="Database sources to query",
    )


class ReportRequest(BaseModel):
    """Request model for report generation."""

    results: list[dict] = Field(..., description="Classification results")
    format: str = Field(default="json", description="Report format (json, csv, html, pdf)")


@router.post("/annotate", response_model=dict)
async def annotate_variant(request: VariantRequest) -> dict:
    """Annotate and classify a single variant.

    Args:
        request: Variant annotation request.

    Returns:
        Classification result with evidence.
    """
    variant = Variant(
        chromosome=request.chromosome,
        position=request.position,
        ref=request.ref,
        alt=request.alt,
        sample_id=request.sample_id,
    )

    # Annotate if requested
    if request.annotate:
        from autoacmg.core.evidence import EvidenceGatherer
        gatherer = EvidenceGatherer()
        gatherer.annotate(variant, sources=request.sources)

    # Classify
    from autoacmg.core.classifier import ACMGClassifier
    classifier = ACMGClassifier()
    result = classifier.classify(variant)

    return result.to_dict()


@router.post("/batch", response_model=list)
async def batch_annotate(request: BatchVariantRequest) -> list[dict]:
    """Annotate and classify multiple variants.

    Args:
        request: Batch annotation request.

    Returns:
        List of classification results.
    """
    results = []
    for vreq in request.variants:
        variant = Variant(
            chromosome=vreq.chromosome,
            position=vreq.position,
            ref=vreq.ref,
            alt=vreq.alt,
            sample_id=vreq.sample_id,
        )

        if vreq.annotate:
            from autoacmg.core.evidence import EvidenceGatherer
            gatherer = EvidenceGatherer()
            gatherer.annotate(variant, sources=vreq.sources)

        from autoacmg.core.classifier import ACMGClassifier
        classifier = ACMGClassifier()
        result = classifier.classify(variant)
        results.append(result.to_dict())

    return results


@router.get("/status", response_model=dict)
async def status() -> dict:
    """Get API status and available sources.

    Returns:
        Status information.
    """
    return {
        "status": "running",
        "version": "0.1.0",
        "available_sources": [
            "clinvar", "gnomad", "cadd", "clingen", "dbsnp", "cosmic",
        ],
        "endpoints": {
            "POST /api/v1/annotate": "Annotate and classify a variant",
            "POST /api/v1/batch": "Batch annotate multiple variants",
            "GET /api/v1/status": "Get API status",
        },
    }


@router.post("/report", response_model=dict)
async def generate_report(request: ReportRequest) -> dict:
    """Generate a classification report.

    Args:
        request: Report generation request.

    Returns:
        Report content.
    """
    from autoacmg.core.classifier import ClassificationResult
    from autoacmg.reports.json_report import JSONReport
    from autoacmg.reports.csv_report import CSVReport
    from autoacmg.reports.html_report import HTMLReport

    # Convert dict results to ClassificationResult objects
    results = []
    for r in request.results:
        from autoacmg.core.variant import ACMGClassification
        try:
            classification = ACMGClassification(r.get("classification", "Uncertain Significance"))
        except ValueError:
            classification = ACMGClassification.UNCERTAIN_SIGNIFICANCE

        cr = ClassificationResult(
            variant_key=r.get("variant", ""),
            final_classification=classification,
            criteria_string=r.get("criteria", ""),
            evidence_summary=r.get("evidence_summary", {}),
            confidence=r.get("confidence", 0.0),
        )
        results.append(cr)

    content = ""
    content_type = "text/plain"

    if request.format == "json":
        report = JSONReport()
        content = report.generate(results)
        content_type = "application/json"
    elif request.format == "csv":
        report = CSVReport()
        content = report.generate(results)
        content_type = "text/csv"
    elif request.format == "html":
        report = HTMLReport()
        content = report.generate(results)
        content_type = "text/html"
    else:
        content = report.generate(results)

    return {
        "content": content,
        "content_type": content_type,
        "format": request.format,
    }
