"""AutoACMG - Automated ACMG/AMP Variant Classification Tool.

AutoACMG automates the clinical classification of genetic variants
according to the ACMG/AMP 2015 guidelines. It integrates data from
multiple databases (ClinVar, gnomAD, CADD, ClinGen, dbSNP, COSMIC)
to assign evidence-based pathogenicity classifications.

Usage:
    autoacmg classify -v chr1 -p 7674232 -r G -a A
    autoacmg annotate -i variants.vcf -o results.json
    autoacmg report -i results.json -f html
    autoacmg serve --host 0.0.0.0 --port 8000
"""

__version__ = "0.1.0"
__author__ = "AutoACMG Contributors"
__email__ = "autoacmg@example.com"
