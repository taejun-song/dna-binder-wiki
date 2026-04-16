# Feature Specification: Modular DNA-Binding Protein Discovery and Redundancy Analysis

**Feature Branch**: `001-dna-binder-modularity`
**Created**: 2026-04-16
**Status**: Draft
**Input**: User description: "Modular DNA-binding protein discovery and redundancy analysis using RFdiffusion3 designs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Curate High-Confidence Binder Set from Noisy Input (Priority: P1)

A computational protein designer receives a batch of RFdiffusion3-generated DNA-binding protein candidates targeting a single DNA sequence. The input may contain duplicates, near-duplicates, inconsistent naming, and candidates of varying quality. The designer needs a cleaned, deduplicated, quality-filtered set of candidates to work with.

**Why this priority**: Without a clean, high-confidence candidate set, all downstream analysis (redundancy detection, module identification) is unreliable. This is the foundational data quality step.

**Independent Test**: Can be fully tested by providing a raw CSV of RFD3 binder candidates and verifying that the output contains only unique, quality-passing designs with standardized names.

**Acceptance Scenarios**:

1. **Given** a dataset of RFD3 binder candidates with duplicate entries, **When** the normalization step runs, **Then** exact duplicates (identical sequences) are merged into a single entry retaining all provenance metadata.
2. **Given** candidates with varying naming conventions (e.g., `PNRP1_design21` vs full pipeline identifiers), **When** normalization completes, **Then** each candidate has a standardized short name and the original name is preserved as an alias.
3. **Given** a deduplicated candidate set, **When** ESMFold structure prediction runs, **Then** each candidate receives a predicted structure with per-residue pLDDT scores.
4. **Given** ESMFold predictions, **When** the quality gate is applied, **Then** only candidates with global average pLDDT > 70 and reasonable sequence properties are retained.
5. **Given** a filtered candidate set, **When** diversity checks run, **Then** the set is verified to contain representatives from multiple independent generation batches.

---

### User Story 2 - Detect Redundancy and Convergent Design Patterns (Priority: P2)

The designer wants to understand how many truly independent design solutions exist within the candidate set. Near-duplicates and shared-scaffold variants should be grouped so that diversity is accurately assessed without overcounting.

**Why this priority**: Overcounting similar designs as independent inflates confidence in design convergence. Accurate redundancy analysis is essential before module identification.

**Independent Test**: Can be tested by providing a set of curated candidates and verifying that sequence-similar clusters, shared-scaffold groups, and convergent-design cases are correctly identified and classified.

**Acceptance Scenarios**:

1. **Given** a curated set of binder candidates, **When** pairwise sequence similarity is computed, **Then** candidates sharing >90% sequence identity are grouped as near-duplicates.
2. **Given** candidates with `_specblock_` in their design names, **When** similarity analysis runs, **Then** these are identified as scaffold-variation pairs derived from the same parent backbone.
3. **Given** two candidates with low global sequence identity but similar DNA-contacting residue patterns, **When** interface-focused comparison runs, **Then** these are flagged as convergent design cases.
4. **Given** the full redundancy analysis, **When** results are reported, **Then** each similarity group is classified by origin: duplication, motif reuse, scaffold variation, or convergent design.

---

### User Story 3 - Identify Modular DNA-Recognition Elements (Priority: P2)

The designer wants to determine whether independently generated binders share a common structural element responsible for DNA recognition, and whether that element could be reused in new protein contexts.

**Why this priority**: Module identification is the core scientific objective — it tests the hypothesis that RFD3 converges on reusable DNA-recognition features. Equal priority with redundancy analysis since they are interdependent.

**Independent Test**: Can be tested by providing a set of non-redundant binders targeting the same DNA sequence and verifying that conserved interface regions are identified and structurally characterized.

**Acceptance Scenarios**:

1. **Given** a set of non-redundant binders for the same DNA target, **When** ESMFold structures are compared, **Then** candidate DNA-contacting regions are identified for each binder using surface-exposed charged residue clusters, structural motif analysis, and positional conservation.
2. **Given** predicted interface regions for multiple binders, **When** conservation analysis runs, **Then** structural segments with conserved fold geometry AND conserved residue composition across >=3 independent designs are flagged as module candidates.
3. **Given** a proposed module region, **When** it is characterized, **Then** it includes a clear structural definition (e.g., helix-turn-helix span, residue range, key contact positions, pLDDT confidence of the region).
4. **Given** a proposed module, **When** variable regions are identified, **Then** the remainder of each binder outside the module is classified as scaffold-dependent structural support.

---

### User Story 4 - Assess Modularity and Programmability Potential (Priority: P3)

The designer wants to evaluate whether identified modules are genuinely transferable — could they be grafted onto different scaffolds or redesigned for different DNA sequences?

**Why this priority**: This is the strategic assessment that determines whether the discovery has practical value for programmable DNA-binding protein design. Depends on successful completion of earlier stories.

**Independent Test**: Can be tested by providing a defined module with its structural context and verifying that transferability criteria are evaluated and experimental validation steps are proposed.

**Acceptance Scenarios**:

1. **Given** a defined module appearing in N independent designs, **When** modularity is assessed, **Then** the report states how many independent scaffolds contain the module and whether its structural geometry (ESMFold-predicted) and sequence signature are preserved across designs.
2. **Given** a module assessment, **When** programmability is evaluated, **Then** the report identifies which residues encode sequence-specific recognition logic (base-reading residues) vs. scaffold-anchoring residues.
3. **Given** a completed modularity assessment, **When** recommendations are generated, **Then** specific experimental tests are proposed (e.g., module transplantation, variable-region swapping, mutagenesis of module residues, redesign for related DNA sequences).

---

### Edge Cases

- What happens when all candidates for a DNA target are near-identical (single design family, no convergence signal)?
- How does the analysis handle candidates with no structural prediction metrics (ipTM/pTM unavailable)?
- What if the identified "module" is simply a known DNA-binding fold (e.g., homeodomain HTH) already present in nature — is that still a useful finding?
- How does the workflow handle targets with very few candidates (<5) where statistical convergence claims are weak?
- What if candidates use fundamentally different binding modes (major groove vs. minor groove) for the same DNA target?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a target DNA sequence and a set of candidate binder protein sequences as input.
- **FR-002**: System MUST identify and merge exact duplicate entries (identical amino acid sequences) while preserving all source metadata.
- **FR-003**: System MUST consolidate near-duplicate entries (>90% sequence identity) into representative clusters.
- **FR-004**: System MUST predict structures for all candidate binders using ESMFold and score them by pLDDT (per-residue and global average).
- **FR-004a**: System MUST apply a quality gate filtering candidates by ESMFold pLDDT (global average > 70) and sequence-level plausibility (reasonable length, no anomalous composition).
- **FR-005**: System MUST classify each retained candidate by predicted DNA-binding class based on sequence motif analysis (e.g., HTH-like, zinc finger-like, novel fold).
- **FR-006**: System MUST identify candidate DNA-contacting residues using ESMFold-predicted structures (surface-exposed positively charged residues, known DNA-binding structural motifs) and sequence conservation across designs.
- **FR-007**: System MUST compute pairwise similarity between all retained candidates at the full-sequence level and at the structural level (ESMFold-predicted fold comparison).
- **FR-008**: System MUST classify similarity groups by origin: duplication, motif reuse, scaffold variation, or convergent design.
- **FR-009**: System MUST identify conserved structural features (residues, motifs, geometries) that recur across >=3 independent designs targeting the same DNA sequence.
- **FR-010**: System MUST partition each binder into a proposed conserved module region and variable scaffold regions.
- **FR-011**: System MUST assess module transferability based on structural conservation (ESMFold-predicted fold similarity of module region across scaffolds), residue conservation, and presence of sequence-specific recognition logic.
- **FR-012**: System MUST produce results as wiki pages following CLAUDE.md conventions: synthesis pages for cross-design analysis, entity pages for identified modules, and appropriate cross-linking and index updates.
- **FR-013**: System MUST clearly label all assumptions, confidence levels (high/medium/low), and distinguish empirical findings from model-derived inferences.
- **FR-014**: System MUST generate structural predictions internally using ESMFold; no pre-computed structural data is required as input.

### Key Entities

- **Candidate Binder**: A designed protein sequence with associated metadata (design name, shorthand name, target DNA, design provenance).
- **DNA Target**: A specific DNA sequence that all candidates in an analysis batch are designed to bind.
- **Redundancy Cluster**: A group of candidates linked by sequence similarity, shared scaffold, or shared interface features.
- **DNA-Recognition Module**: A structurally defined region of a binder protein that is conserved across independent designs and is proposed to be responsible for sequence-specific DNA recognition.
- **Variable Region**: The portion of a binder protein outside the proposed module, serving scaffold-dependent structural roles.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Duplicate and near-duplicate candidates are reduced by at least 20% from the raw input set without losing any unique design families.
- **SC-002**: All retained candidates have a standardized name, assigned DNA-binding class, and confidence level.
- **SC-003**: Redundancy clusters are identified with clear classification of similarity origin for every grouped pair.
- **SC-004**: For DNA targets with >=10 non-redundant candidates, at least one candidate module region is proposed with structural definition and conservation evidence.
- **SC-005**: The modularity assessment includes at least 3 specific, actionable experimental or computational validation steps.
- **SC-006**: The final output consists of wiki pages (synthesis and entity types) following CLAUDE.md conventions, cross-linked and indexed, interpretable by a structural biologist without additional context.
- **SC-007**: No candidate is counted as "independent evidence" for convergence if it belongs to a near-duplicate or scaffold-variation cluster of another counted candidate.

## Clarifications

### Session 2026-04-16

- Q: Should the analysis require pre-existing structural metrics or operate from sequences only? → A: The workflow generates structural predictions internally using ESMFold for binder validation; no pre-computed structural data is required as input.
- Q: Which structure prediction tool for scoring generated binders? → A: ESMFold only (speed over accuracy, sufficient for design filtering).
- Q: Output format for analysis results? → A: Wiki pages following CLAUDE.md conventions (synthesis + entity pages, cross-linked, indexed).

## Assumptions

- Input data is primarily sourced from the wiki's RFD3 genome editing binders dataset and potentially additional RFD3 design runs provided by the user.
- Structural evaluation of candidate binders uses ESMFold for speed; no MSA or ColabFold/AF2 is required.
- DNA-binding class and interface prediction rely on ESMFold-predicted structures, sequence motif analysis, and positional conservation across designs.
- The analysis operates per-target — each DNA sequence is analyzed independently. Cross-target comparisons (e.g., do PNRP1 binders share modules with CAG binders?) are out of scope for the initial version but noted as a future extension.
- "Independence" of designs is assessed by design lineage (different generation batches) and sequence dissimilarity, not by guaranteed independence of the RFD3 sampling process.
- The user has domain expertise in structural biology and protein design; the report uses technical terminology appropriate for this audience.
