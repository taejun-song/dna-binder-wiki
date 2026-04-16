# Data Model: Modular DNA-Binding Protein Discovery

**Date**: 2026-04-16 | **Plan**: [plan.md](plan.md)

## Entities

### CandidateBinder

Represents a single RFD3-designed protein sequence with all associated metadata accumulated through the pipeline.

| Field | Type | Description |
|-------|------|-------------|
| design_name | string | Original full pipeline identifier |
| shorthand_name | string | Standardized short name (e.g., `PNRP1_design21`) |
| sequence | string | Amino acid sequence (single-letter code) |
| target_dna | string | DNA target sequence this binder is designed for |
| length | int | Sequence length (derived) |
| is_specblock | bool | Whether this is a re-scaffolded variant |
| parent_design | string (nullable) | Shorthand name of parent design if specblock variant |
| pdb_path | string (nullable) | Path to ESMFold-predicted PDB file |
| plddt_global | float (nullable) | Global average pLDDT from ESMFold |
| plddt_per_residue | list[float] (nullable) | Per-residue pLDDT array |
| passes_quality | bool | Whether candidate passed quality gate |
| binding_class | string (nullable) | Predicted DNA-binding class (HTH, zinc-finger, novel, etc.) |
| candidate_contacts | list[int] (nullable) | Residue indices predicted to contact DNA |
| cluster_id | string (nullable) | Redundancy cluster assignment |
| cluster_role | string (nullable) | Role in cluster: representative / member |
| module_region | tuple[int,int] (nullable) | Start/end residue indices of proposed module |
| confidence | string (nullable) | Overall confidence: high / medium / low |

**Identity rule**: unique by `sequence` (exact string match for dedup)
**Lifecycle**: raw → normalized → predicted → filtered → clustered → module-annotated

### DNATarget

Represents a specific DNA sequence that groups candidates for analysis.

| Field | Type | Description |
|-------|------|-------------|
| sequence | string | The DNA target sequence |
| shorthand | string | Human-readable name (e.g., PNRP1, CAG, HSTELO) |
| candidate_count | int | Total candidates before dedup |
| unique_count | int | Candidates after dedup |
| filtered_count | int | Candidates passing quality gate |
| cluster_count | int | Number of redundancy clusters |
| independent_count | int | Number of truly independent designs |

**Identity rule**: unique by `sequence`

### RedundancyCluster

Groups related candidates by similarity or shared provenance.

| Field | Type | Description |
|-------|------|-------------|
| cluster_id | string | Unique identifier (e.g., `PNRP1_C01`) |
| target_dna | string | DNA target sequence |
| members | list[string] | Shorthand names of member candidates |
| representative | string | Shorthand name of representative candidate |
| similarity_type | string | duplication / near-duplicate / scaffold-variation / convergent |
| max_seq_identity | float | Highest pairwise sequence identity within cluster |
| max_tm_score | float (nullable) | Highest pairwise TM-score within cluster |

### DNARecognitionModule

A structurally defined region proposed as a reusable DNA-recognition element.

| Field | Type | Description |
|-------|------|-------------|
| module_id | string | Unique identifier (e.g., `PNRP1_MOD01`) |
| target_dna | string | DNA target this module recognizes |
| residue_range | string | Typical residue range in aligned coordinates |
| length | int | Module length in residues |
| conserved_residues | list[string] | Key conserved positions (e.g., R32, K45, R51) |
| structural_description | string | Fold description (e.g., "three-helix HTH bundle") |
| conservation_score | float | Mean per-position conservation score |
| structural_rmsd | float (nullable) | Mean pairwise RMSD of module region across designs |
| plddt_mean | float | Mean pLDDT across module region across designs |
| occurrences | int | Number of independent designs containing this module |
| scaffold_ids | list[string] | Cluster representatives containing this module |
| confidence | string | high / medium / low |

## Relationships

```
DNATarget 1──* CandidateBinder
DNATarget 1──* RedundancyCluster
DNATarget 1──* DNARecognitionModule
RedundancyCluster 1──* CandidateBinder
DNARecognitionModule *──* CandidateBinder (via module_region annotation)
```

## State Transitions

### CandidateBinder Lifecycle

```
raw → [normalize] → normalized → [predict] → predicted → [filter] → filtered/rejected
filtered → [cluster] → clustered → [analyze_interface] → interface-annotated
interface-annotated → [identify_modules] → module-annotated
```

### Pipeline Stages

```
Stage 1: Normalize    — dedup, standardize names
Stage 2: Predict      — ESMFold structure prediction
Stage 3: Filter       — pLDDT quality gate
Stage 4: Similarity   — pairwise sequence + structural comparison
Stage 5: Cluster      — redundancy grouping + classification
Stage 6: Interface    — DNA-contact residue prediction
Stage 7: Modules      — conserved region identification
Stage 8: Assess       — modularity + transferability evaluation
Stage 9: Output       — generate wiki pages
```
