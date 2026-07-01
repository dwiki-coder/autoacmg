"""VCF file parser for AutoACMG.

Parses VCF files into Variant objects for ACMG classification.
Supports both standard VCF and annotated VCF formats.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from autoacmg.core.variant import GenomicRegion, Variant
from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)


class VCFRecord:
    """Represents a single VCF record."""

    CHROM_INDEX = 0
    POS_INDEX = 1
    ID_INDEX = 2
    REF_INDEX = 3
    ALT_INDEX = 4
    QUAL_INDEX = 5
    FILTER_INDEX = 6
    INFO_INDEX = 7
    FORMAT_INDEX = 8

    def __init__(self, line: str) -> None:
        """Parse a VCF record line.

        Args:
            line: A single VCF record line (not a header).
        """
        parts = line.strip().split("\t")
        self.chrom = parts[self.CHROM_INDEX]
        self.pos = int(parts[self.POS_INDEX])
        self.id = parts[self.ID_INDEX] if parts[self.ID_INDEX] != "." else None
        self.ref = parts[self.REF_INDEX]
        self.alt_str = parts[self.ALT_INDEX]
        self.quals = parts[self.QUAL_INDEX] if parts[self.QUAL_INDEX] != "." else None
        self.filter = parts[self.FILTER_INDEX] if parts[self.FILTER_INDEX] != "." else None
        self.info_str = parts[self.INFO_INDEX] if len(parts) > self.INFO_INDEX else ""
        self.format_str = parts[self.FORMAT_INDEX] if len(parts) > self.FORMAT_INDEX else ""
        self.sample_data = parts[self.FORMAT_INDEX + 1:] if len(parts) > self.FORMAT_INDEX + 1 else []
        self.info = self._parse_info(self.info_str)
        self.als = [a.strip() for a in self.alt_str.split(",") if a.strip() != "."]

    def _parse_info(self, info_str: str) -> dict:
        """Parse VCF INFO field into a dictionary."""
        result = {}
        if not info_str or info_str == ".":
            return result

        for item in info_str.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                result[key] = value
            else:
                result[item] = True
        return result

    def to_variant(self, sample_id: str = "unknown") -> Variant:
        """Convert VCF record to a Variant object."""
        # Try to extract gene/consequence from INFO
        region = None
        if "GENE" in self.info or "SYMBOL" in self.info:
            region = GenomicRegion(
                gene_symbol=self.info.get("GENE", self.info.get("SYMBOL", "")),
                consequence=self.info.get("CONSEQUENCE", self.info.get("TYPE", "")),
                protein_change=self.info.get("PROTEIN_CHANGE", self.info.get("EFFECT", None)),
            )

        return Variant(
            chromosome=self.chrom,
            position=self.pos,
            ref=self.ref,
            alt=self.als[0] if self.als else self.alt_str,
            sample_id=sample_id,
            rsid=self.id,
            genomic_region=region,
        )


class VCFParser:
    """Parses VCF files into lists of Variant objects."""

    def __init__(self) -> None:
        self.metadata: list[str] = []
        self.column_header: Optional[str] = None

    def parse_file(self, filepath: str) -> list[Variant]:
        """Parse a VCF file into Variant objects.

        Args:
            filepath: Path to the VCF file.

        Returns:
            List of Variant objects.
        """
        logger.info("Parsing VCF file: %s", filepath)
        variants = []
        record_count = 0

        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Skip metadata
                if line.startswith("##"):
                    self.metadata.append(line)
                    continue

                # Column header
                if line.startswith("#"):
                    self.column_header = line
                    continue

                # Data record
                try:
                    record = VCFRecord(line)
                    variant = record.to_variant()
                    variants.append(variant)
                    record_count += 1
                except Exception as e:
                    logger.warning("Failed to parse line: %s - %s", line[:100], e)
                    continue

        logger.info("Parsed %d variants from %s", record_count, filepath)
        return variants

    def parse_string(self, vcf_content: str) -> list[Variant]:
        """Parse VCF content from a string.

        Args:
            vcf_content: VCF-formatted string content.

        Returns:
            List of Variant objects.
        """
        variants = []
        for line in vcf_content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                record = VCFRecord(line)
                variant = record.to_variant()
                variants.append(variant)
            except Exception as e:
                logger.warning("Failed to parse: %s - %s", line[:100], e)
        return variants

    @staticmethod
    def from_vcf_dict_list(vcf_dicts: list[dict]) -> list[Variant]:
        """Create variants from a list of VCF dictionaries.

        Args:
            vcf_dicts: List of dictionaries with VCF fields.

        Returns:
            List of Variant objects.
        """
        return [Variant.from_vcf_record(d) for d in vcf_dicts]
