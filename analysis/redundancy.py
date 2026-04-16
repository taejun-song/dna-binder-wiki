"""Step 5: Redundancy clustering and origin classification."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from analysis.normalize import CandidateBinder

NEAR_DUPLICATE_THRESHOLD = 0.90


@dataclass
class RedundancyCluster:
    cluster_id: str
    target_dna: str
    members: list[str] = field(default_factory=list)
    representative: str = ""
    similarity_type: str = "singleton"
    max_seq_identity: float = 0.0
    max_tm_score: float | None = None


def cluster_candidates(
    candidates: list[CandidateBinder],
    seq_identity_matrix: np.ndarray,
    threshold: float = NEAR_DUPLICATE_THRESHOLD,
) -> list[RedundancyCluster]:
    n = len(candidates)
    assigned = [False] * n
    clusters: list[RedundancyCluster] = []
    cluster_counter = 0

    for i in range(n):
        if assigned[i]:
            continue
        members_idx = [i]
        assigned[i] = True
        for j in range(i + 1, n):
            if assigned[j]:
                continue
            if candidates[i].target_dna != candidates[j].target_dna:
                continue
            if seq_identity_matrix[i, j] >= threshold:
                members_idx.append(j)
                assigned[j] = True

        target_short = candidates[i].target_dna[:8]
        cluster_counter += 1
        cluster_id = f"{target_short}_C{cluster_counter:02d}"
        member_names = [candidates[idx].shorthand_name for idx in members_idx]

        best_idx = members_idx[0]
        if candidates[best_idx].plddt_global is not None:
            for idx in members_idx[1:]:
                if (candidates[idx].plddt_global or 0) > (candidates[best_idx].plddt_global or 0):
                    best_idx = idx
        representative = candidates[best_idx].shorthand_name

        max_identity = 0.0
        for a in range(len(members_idx)):
            for b in range(a + 1, len(members_idx)):
                val = seq_identity_matrix[members_idx[a], members_idx[b]]
                if val > max_identity:
                    max_identity = val

        if len(members_idx) == 1:
            sim_type = "singleton"
        elif any(candidates[idx].is_specblock for idx in members_idx):
            sim_type = "scaffold-variation"
        elif max_identity >= threshold:
            sim_type = "near-duplicate"
        else:
            sim_type = "near-duplicate"

        cluster = RedundancyCluster(
            cluster_id=cluster_id,
            target_dna=candidates[i].target_dna,
            members=member_names,
            representative=representative,
            similarity_type=sim_type,
            max_seq_identity=max_identity,
        )
        clusters.append(cluster)

        for idx in members_idx:
            candidates[idx].cluster_id = cluster_id
            candidates[idx].cluster_role = "representative" if candidates[idx].shorthand_name == representative else "member"

    return clusters
