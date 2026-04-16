# Tasks: Modular DNA-Binding Protein Discovery

**Input**: Design documents from `/specs/001-dna-binder-modularity/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec — test tasks omitted.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Python package structure

- [ ] T001 Create project directory structure: analysis/, tests/, tests/fixtures/, scripts/ per plan.md
- [ ] T002 Create analysis/__init__.py and analysis/utils.py with shared helpers (sequence I/O, CSV parsing, FASTA reading)
- [ ] T003 [P] Create scripts/run_analysis.py CLI entry point with argparse (--input, --target, --all-targets, --output-dir flags)
- [ ] T004 [P] Create requirements.txt with dependencies: torch, esm, biopython, numpy, pandas, tmtools, freesasa
- [ ] T005 [P] Create tests/fixtures/sample_candidates.csv with 10 representative rows from the genome editing binders dataset (3 PNRP1, 2 CAG, 2 duplicates, 1 specblock pair, 2 other targets)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and ESMFold prediction pipeline that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement CandidateBinder dataclass in analysis/normalize.py with all fields from data-model.md
- [ ] T007 Implement DNATarget dataclass in analysis/normalize.py with fields from data-model.md
- [ ] T008 Implement CSV loading and name normalization in analysis/normalize.py: parse design_name to extract target shorthand, detect specblock variants, standardize short names, dedup by exact sequence match
- [ ] T009 Implement ESMFold structure prediction in analysis/predict.py: load model, predict structure for a single sequence, return PDB string and per-residue pLDDT array, save PDB to output directory
- [ ] T010 Implement batch prediction wrapper in analysis/predict.py: iterate over candidate list, skip already-predicted sequences, compute global average pLDDT
- [ ] T011 Implement quality gate in analysis/quality.py: filter by global pLDDT > 70, flag anomalous sequence composition, log rejection reasons

**Checkpoint**: Foundation ready — can load CSV, normalize candidates, predict structures, and filter by quality

---

## Phase 3: User Story 1 — Curate High-Confidence Binder Set (Priority: P1) MVP

**Goal**: Given a raw CSV of RFD3 candidates, produce a cleaned, deduplicated, quality-filtered set with standardized names and ESMFold structures.

**Independent Test**: Run pipeline on sample_candidates.csv and verify output contains only unique, quality-passing designs with standardized names and PDB files.

### Implementation for User Story 1

- [ ] T012 [US1] Implement pipeline stage 1 in analysis/pipeline.py: wire normalize → predict → filter stages, accept CSV path and target DNA as input, return filtered CandidateBinder list
- [ ] T013 [US1] Implement diversity check in analysis/quality.py: verify filtered set contains representatives from multiple generation batches (parsed from design_name), warn if all from single batch
- [ ] T014 [US1] Implement summary statistics output in analysis/pipeline.py: total candidates, unique after dedup, passing quality gate, generation batch distribution
- [ ] T015 [US1] End-to-end validation: run stage 1 on PNRP1 target (38 candidates) from raw/data/RFD3 binders for Genome Editing Assay -BakerLab.csv, verify dedup count and pLDDT filtering

**Checkpoint**: User Story 1 complete — clean, quality-filtered candidate set with ESMFold structures

---

## Phase 4: User Story 2 — Detect Redundancy and Convergent Design (Priority: P2)

**Goal**: Group candidates by similarity, classify redundancy origin, determine how many truly independent designs exist.

**Independent Test**: Given the filtered PNRP1 set from US1, verify that near-duplicates are clustered, specblock variants are linked to parents, and each cluster has an origin classification.

### Implementation for User Story 2

- [ ] T016 [P] [US2] Implement pairwise sequence identity computation in analysis/similarity.py: global alignment using BioPython pairwise2, return NxN identity matrix
- [ ] T017 [P] [US2] Implement structural similarity computation in analysis/similarity.py: TM-score between ESMFold PDBs using tmtools, return NxN TM-score matrix
- [ ] T018 [US2] Implement RedundancyCluster dataclass and clustering logic in analysis/redundancy.py: group by >90% seq identity (near-duplicate), TM-score >0.7 with <90% seq identity (scaffold-variation), specblock detection from design names
- [ ] T019 [US2] Implement similarity origin classification in analysis/redundancy.py: label each cluster as duplication / near-duplicate / scaffold-variation / convergent per thresholds from research.md
- [ ] T020 [US2] Implement representative selection in analysis/redundancy.py: pick highest-pLDDT member as cluster representative
- [ ] T021 [US2] Wire redundancy analysis into analysis/pipeline.py as stage 2: takes filtered candidates, returns clustered candidates with independent_count per target
- [ ] T022 [US2] Validation: run redundancy analysis on PNRP1 candidates, verify specblock pairs are correctly grouped and independent design count < total candidate count

**Checkpoint**: User Story 2 complete — redundancy clusters identified with origin classification

---

## Phase 5: User Story 3 — Identify Modular DNA-Recognition Elements (Priority: P2)

**Goal**: Find conserved structural/sequence regions across independent designs that may constitute a reusable DNA-recognition module.

**Independent Test**: Given non-redundant PNRP1 representatives, verify that conserved regions are identified with structural definition and residue-level characterization.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement DNA-contact residue prediction in analysis/interface.py: compute SASA per residue from PDB using FreeSASA, identify surface-exposed Arg/Lys clusters (>=3 within 10A)
- [ ] T024 [P] [US3] Implement DNA-binding class prediction in analysis/interface.py: scan for HTH motif signatures (helix-turn-helix pattern in secondary structure from ESMFold pLDDT + backbone geometry), zinc finger CxxC/HxxH patterns, flag novel folds
- [ ] T025 [US3] Implement multiple sequence alignment of cluster representatives in analysis/modules.py: align using BioPython ClustalW or MUSCLE wrapper, compute per-position conservation score (% identity)
- [ ] T026 [US3] Implement structural superposition of cluster representatives in analysis/modules.py: pairwise TM-align of module candidate regions, compute mean RMSD
- [ ] T027 [US3] Implement DNARecognitionModule identification in analysis/modules.py: intersect sequence-conserved (>60% identity) + structurally-conserved (RMSD <2.0A) regions, require >=15 contiguous residues, require presence in >=3 independent designs
- [ ] T028 [US3] Implement module/variable-region partitioning in analysis/modules.py: for each candidate, label residues as module or variable based on identified module boundaries
- [ ] T029 [US3] Wire module identification into analysis/pipeline.py as stage 3: takes clustered candidates, returns module-annotated candidates with DNARecognitionModule objects
- [ ] T030 [US3] Validation: run module identification on PNRP1 representatives, verify at least one module region is proposed (if convergence exists) or "no convergence" is correctly reported

**Checkpoint**: User Story 3 complete — modules identified with structural definition and conservation evidence

---

## Phase 6: User Story 4 — Assess Modularity and Programmability (Priority: P3)

**Goal**: Evaluate whether identified modules are genuinely transferable and propose validation experiments.

**Independent Test**: Given identified PNRP1 modules, verify transferability criteria are evaluated and experimental recommendations are generated.

### Implementation for User Story 4

- [ ] T031 [US4] Implement modularity scoring in analysis/modularity.py: count independent scaffolds containing module, compute structural RMSD of module region across scaffolds, assess sequence signature preservation
- [ ] T032 [US4] Implement programmability assessment in analysis/modularity.py: classify module residues as base-reading (conserved Arg/Lys/Asn/Gln in predicted contact positions) vs scaffold-anchoring (hydrophobic core residues)
- [ ] T033 [US4] Implement experimental recommendation generator in analysis/modularity.py: produce list of >=3 specific validation steps (module transplantation, variable-region swap, contact-residue mutagenesis, redesign for related DNA sequence)
- [ ] T034 [US4] Wire modularity assessment into analysis/pipeline.py as stage 4: takes module-annotated candidates, returns full assessment with confidence levels

**Checkpoint**: User Story 4 complete — modularity assessed with actionable recommendations

---

## Phase 7: Wiki Output Generation

**Purpose**: Produce wiki pages following CLAUDE.md conventions

- [ ] T035 [P] Implement wiki page templates in analysis/wiki_output.py: synthesis page template (frontmatter, summary paragraph, sections), entity page template for modules
- [ ] T036 Implement per-target synthesis page generator in analysis/wiki_output.py: generate syntheses/[target]-binder-analysis.md with curated candidate set, redundancy clusters, conserved features, module proposals, modularity assessment, recommendations
- [ ] T037 Implement module entity page generator in analysis/wiki_output.py: generate entities/[module-id].md for each high-confidence module with structural description, conservation evidence, transferability assessment
- [ ] T038 Implement index update helper in analysis/wiki_output.py: generate updated entries for index.md (new pages in appropriate sections)
- [ ] T039 Implement log entry helper in analysis/wiki_output.py: generate log.md append block listing all created/updated pages
- [ ] T040 Wire wiki output into analysis/pipeline.py as final stage: generate all wiki pages, print summary of pages created

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and cleanup

- [ ] T041 [P] Run full pipeline on all 9 DNA targets from the dataset, verify wiki pages are generated for targets with sufficient candidates
- [ ] T042 [P] Verify generated wiki pages pass frontmatter validation (all required fields present, correct types, dates)
- [ ] T043 Review and clean up analysis/ code: remove dead code, ensure consistent error handling
- [ ] T044 Update quickstart.md with any changes discovered during implementation
- [ ] T045 Run quickstart.md validation: follow setup instructions from scratch, confirm pipeline runs successfully

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — can start first
- **US2 (Phase 4)**: Depends on US1 (needs filtered candidates as input)
- **US3 (Phase 5)**: Depends on US2 (needs redundancy clusters and representatives)
- **US4 (Phase 6)**: Depends on US3 (needs identified modules)
- **Wiki Output (Phase 7)**: Depends on US4 (needs all analysis results)
- **Polish (Phase 8)**: Depends on Wiki Output

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational — no other story dependencies
- **User Story 2 (P2)**: After US1 — needs filtered candidate set
- **User Story 3 (P2)**: After US2 — needs redundancy clusters and representatives
- **User Story 4 (P3)**: After US3 — needs identified modules

Note: This is a sequential pipeline — each stage consumes the output of the previous stage. Parallelism exists within phases (marked [P]) but not across user stories.

### Within Each User Story

- Models/dataclasses before logic
- Core computation before integration
- Integration (wiring into pipeline.py) last

### Parallel Opportunities

- T003, T004, T005 can run in parallel (Setup phase)
- T016, T017 can run in parallel (sequence and structural similarity are independent computations)
- T023, T024 can run in parallel (SASA analysis and motif scanning are independent)
- T035 can run in parallel with T031–T034 (template code independent of assessment logic)
- T041, T042 can run in parallel (different validation concerns)

---

## Parallel Example: User Story 2

```
# Launch both similarity computations together:
Task: T016 "Implement pairwise sequence identity in analysis/similarity.py"
Task: T017 "Implement structural similarity (TM-score) in analysis/similarity.py"

# Then sequential:
Task: T018 "Implement clustering logic in analysis/redundancy.py" (needs T016 + T017)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (ESMFold prediction pipeline)
3. Complete Phase 3: User Story 1 (normalize + predict + filter)
4. **STOP and VALIDATE**: Run on PNRP1 target, verify clean candidate set with PDB files
5. This alone delivers value: curated, quality-scored binder dataset

### Incremental Delivery

1. Setup + Foundational → ESMFold prediction infrastructure ready
2. Add US1 → Curated binder set with structures (MVP)
3. Add US2 → Redundancy analysis reveals independent design count
4. Add US3 → Module identification tests the core hypothesis
5. Add US4 → Programmability assessment with experimental recommendations
6. Add Wiki Output → Findings persisted as wiki pages
7. Each stage adds analytical depth without breaking previous stages

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This pipeline is inherently sequential (each stage feeds the next), so cross-story parallelism is limited
- ESMFold prediction (T009-T010) is the computational bottleneck — run on GPU if available
- Commit after each task or logical group
