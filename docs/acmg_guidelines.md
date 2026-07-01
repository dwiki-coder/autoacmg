# ACMG/AMP Guidelines Reference

## Overview

Based on: **Richards S, Aziz N, Bale S, et al.** (2015).
"Standards and guidelines for the interpretation of sequence variants."
_Genetics in Medicine_ 17(5):555–566.

## Classification Categories

| Classification | ACMG Criteria Combination |
|----------------|--------------------------|
| **Pathogenic** | PVS1 + ≥1 PS; 2 PS; 1 PS + 3 PM; 1 PS + 2 PM + ≥1 PP; 4 PM; 3 PM + 2 PP; 2 PM + 4 PP; 1 PM + 6 PP |
| **Likely Pathogenic** | 1 PS + 1–2 PM; 1 PS + 1 PM + 1–2 PP; 1 PS + 3–4 PP; 2 PM + 2–4 PP; 1 PM + 2–5 PP; 3 PM + 1–3 PP; 6 PP |
| **Uncertain Significance** | Insufficient evidence for above categories |
| **Likely Benign** | 1 BS; 1 BP + 1 BS |
| **Benign** | BA1; ≥2 BS; 1 BS + 4 BP |

## Evidence Strength

| Level | Weight | Pathogenic Codes | Benign Codes |
|-------|--------|-----------------|--------------|
| Very Strong | 4 | PVS1 | BA1 |
| Strong | 3 | PS1–PS7 | BS1 |
| Moderate | 2 | PM1–PM6 | BS2–BS4 |
| Supporting | 1 | PP1–PP5 | BP1–BP4, BP6–BP7 |

## Pathogenic Criteria

| Code | Description |
|------|-------------|
| **PVS1** | Null variant in gene where LOF is known disease mechanism |
| **PS1** | Same amino acid change as known pathogenic variant |
| **PS2** | Novel missense at residue with known pathogenic missense |
| **PS3** | Well-established functional studies show damaging effect |
| **PS4** | Variant prevalence significantly higher in cases than controls |
| **PS5** | Novel de novo with complete parental segregation |
| **PS6** | Assumed de novo without parental confirmation |
| **PS7** | Segregation with disease in family members |
| **PM1** | Located in mutational hotspot or critical functional domain |
| **PM2** | Absent from population databases |
| **PM3** | Detected in trans with pathogenic variant (AR) |
| **PM4** | Protein length changes (in-frame indels) |
| **PM5** | Novel missense at position with known pathogenic missense |
| **PP1** | Co-segregation with disease |
| **PP2** | Missense predicted damaging by multiple tools |
| **PP3** | Computational evidence supports deleterious effect |
| **PP4** | Phenotype highly specific to gene-disease |
| **PP5** | Reputable source reports pathogenicity |

## Benign Criteria

| Code | Description |
|------|-------------|
| **BA1** | AF ≥ expected disease prevalence (stand-alone) |
| **BS1** | AF inconsistent with disease prevalence |
| **BS2** | Observed in healthy adult for late-onset disorder |
| **BS3** | In silico tools predict no damaging effect |
| **BS4** | Lack of segregation in affected family members |
| **BP1** | Synonymous, intronic, or intergenic with no impact |
| **BP2** | Tolerated in gene dosage studies |
| **BP3** | Computational evidence suggests no damaging effect |
| **BP4** | Residue not known to be altered in disease |
| **BP6** | Reputable source reports benignity |
| **BP7** | Synonymous with no predicted splice impact |

## Score Thresholds

- **CADD**: ≥ 10 = top 10% most deleterious
- **REVEL**: ≥ 0.5 = damaging
- **PolyPhen-2**: ≥ 0.5 = possibly damaging
- **SIFT**: < 0.05 = damaging
