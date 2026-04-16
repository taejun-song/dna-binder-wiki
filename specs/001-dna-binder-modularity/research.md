# Research: Modular DNA-Binding Protein Discovery

**Date**: 2026-04-16 | **Plan**: [plan.md](plan.md)

## R1: ESMFold Integration

**Decision**: Use the `esm` Python package from Meta/Facebook AI Research via HuggingFace, specifically `esm.pretrained.esmfold_v1()`.

**Rationale**: ESMFold is a single-sequence structure predictor (no MSA required), making it fast and self-contained. For ~100 protein sequences of length 110–145 residues, prediction is feasible on a single GPU in under an hour. CPU fallback works for small batches but is 10–50× slower.

**Alternatives considered**:
- ColabFold/AF2: higher accuracy but requires MSA construction (slow, external DB dependency). Overkill for design screening.
- ESM Atlas API: cloud-based, avoids local GPU requirement, but has rate limits and may not accept custom sequences.
- OmegaFold: similar single-sequence approach but less community adoption.

**Key details**:
- Input: amino acid sequence string
- Output: PDB structure + per-residue pLDDT array
- Global pLDDT = mean of per-residue pLDDT values
- Quality gate threshold: global average pLDDT > 70 (standard for "confident fold")

## R2: Sequence Similarity Computation

**Decision**: Use BioPython pairwise alignment (local or global) for sequence identity calculation. For structural similarity, use TM-score via TMalign on ESMFold-predicted PDBs.

**Rationale**: Pairwise sequence identity is the simplest and most interpretable metric for deduplication. TM-score captures fold-level similarity independent of sequence, enabling detection of convergent designs with different sequences but similar structures.

**Alternatives considered**:
- MMseqs2: much faster for large-scale clustering but overkill for ~100 sequences per target.
- BLAST: standard but slower than direct pairwise alignment for small sets.
- Foldseek: structural search engine — powerful but complex dependency for this scale.

**Key thresholds**:
- Near-duplicate: >90% sequence identity
- Shared scaffold: TM-score > 0.7 AND sequence identity < 90%
- Convergent design: TM-score > 0.5 at the interface region AND sequence identity < 50%

## R3: DNA-Contact Residue Prediction

**Decision**: Identify candidate DNA-contacting residues using a combination of: (1) surface-exposed positively charged residues (Arg, Lys) in ESMFold structures, (2) known DNA-binding motif signatures (HTH, winged-helix, zinc finger patterns), (3) positional conservation of residues across designs for the same target.

**Rationale**: Without a protein-DNA complex structure, direct contact prediction from monomeric folds requires heuristic approaches. The combination of electrostatics (Arg/Lys enrichment on one face), structural motif recognition, and cross-design conservation provides a reasonable proxy.

**Alternatives considered**:
- BindSiteS / ScanNet: ML-based binding-site predictors — would add accuracy but also dependency complexity.
- Docking (HADDOCK/ClusPro): computationally expensive and requires DNA model; out of scope.
- Contact prediction from AF3 complex prediction: most accurate but requires ColabFold/AF3 access (ruled out by clarification).

**Approach details**:
- Compute solvent-accessible surface area (SASA) per residue from ESMFold PDB using BioPython DSSP or FreeSASA
- Flag surface-exposed Arg/Lys clusters (>=3 within 10Å) as candidate DNA-contact regions
- Match secondary structure patterns against known DNA-binding motif libraries
- Cross-reference with positional conservation: residues conserved in type AND position across >=3 independent designs are strongest module candidates

## R4: Module Identification Strategy

**Decision**: Use multiple sequence alignment (MSA) of non-redundant candidates targeting the same DNA sequence, combined with ESMFold structural superposition of the predicted folds. Conserved regions in both sequence and structure are candidate modules.

**Rationale**: Neither sequence conservation alone nor structural similarity alone is sufficient — a true module should be conserved at both levels. MSA reveals sequence-level conservation patterns; structural superposition reveals fold-level conservation even when sequence diverges.

**Alternatives considered**:
- HMM profiles: more rigorous for motif detection but requires larger datasets (>20 diverse sequences per target).
- Contact-map comparison: captures interaction topology but harder to interpret for module boundaries.

**Approach details**:
- Align non-redundant sequences per target using MAFFT or Muscle (via BioPython)
- Compute per-position conservation score (Shannon entropy or simple % identity)
- Superpose ESMFold structures using TM-align; identify structurally conserved core
- Intersection of sequence-conserved + structurally-conserved regions = candidate module
- Module boundary: contiguous stretch of >=15 residues with conservation score > 0.6 AND structural RMSD < 2.0Å across designs

## R5: Wiki Page Output Format

**Decision**: Generate wiki pages following CLAUDE.md §§3–5. Analysis results map to page types:
- `synthesis` pages: per-target redundancy analysis, cross-design comparison, modularity assessment
- `entity` pages: identified DNA-recognition modules (if sufficiently characterized)
- Updates to existing pages: add cross-links to `rfdiffusion3`, `dna-binder-design-targets`

**Rationale**: The wiki is the project's persistent knowledge store. Encoding findings as wiki pages ensures they compound with future ingests and are discoverable via the index.

**Output file generation**:
- Use Python string templates to produce markdown with correct YAML frontmatter
- Validate frontmatter fields before writing
- Trigger index regeneration and log append via the wiki maintainer workflow
