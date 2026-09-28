"""Deterministic mastery + learning-debt logic. No AI, no database, no third-party imports.

Terminology
-----------
edge  (prerequisite_id, concept_id)   prerequisite -> concept
weak  mastery below `moderate_debt` threshold (default 60%)
root cause  a weak concept none of whose prerequisites are weak
affected    every concept that directly/indirectly depends on a weak concept

The scoring is a transparent heuristic for the MVP, NOT a scientifically validated model.
"""
import heapq
from dataclasses import dataclass

from app.services.graph_utils import ancestors, build_adjacency, compute_depths, descendants


@dataclass(frozen=True)
class Thresholds:
    high_debt: float = 40.0
    moderate_debt: float = 60.0
    developing: float = 80.0
    min_questions_full_confidence: int = 3
    escalation_dependents: int = 3

    @classmethod
    def from_settings(cls, s) -> "Thresholds":
        return cls(
            high_debt=s.threshold_high_debt,
            moderate_debt=s.threshold_moderate_debt,
            developing=s.threshold_developing,
            min_questions_full_confidence=s.min_questions_for_full_confidence,
            escalation_dependents=s.escalation_dependents,
        )


# ------------------------------------------------------------------ mastery
def classify_mastery(pct: float, t: Thresholds) -> str:
    if pct < t.high_debt:
        return "HIGH_DEBT"
    if pct < t.moderate_debt:
        return "MODERATE_DEBT"
    if pct < t.developing:
        return "DEVELOPING"
    return "MASTERED"


def calculate_mastery(correct: int, total: int, t: Thresholds) -> dict:
    """mastery % = correct / total * 100.  confidence = min(1, total / min_questions_full_confidence)."""
    if total <= 0:
        raise ValueError("Cannot calculate mastery without at least one answered question.")
    if not 0 <= correct <= total:
        raise ValueError("correct must be between 0 and total.")
    pct = round(correct / total * 100, 1)
    confidence = round(min(1.0, total / max(1, t.min_questions_full_confidence)), 2)
    return {
        "correct_answers": correct,
        "total_questions": total,
        "mastery_percentage": pct,
        "confidence": confidence,
        "status": classify_mastery(pct, t),
    }


# ------------------------------------------------------------- learning debt
def detect_learning_debt(
    names: dict[int, str],
    edges: list[tuple[int, int]],
    mastery: dict[int, float],
    t: Thresholds,
) -> list[dict]:
    """Return one item per weak concept, most urgent first.

    Concepts without mastery data (never assessed) are ignored rather than assumed weak.
    """
    valid_edges = [(p, c) for p, c in edges if p in names and c in names]
    prereqs, dependents = build_adjacency(valid_edges)
    depths = compute_depths(names.keys(), valid_edges)
    weak = {cid for cid, m in mastery.items() if cid in names and m < t.moderate_debt}

    items = []
    for cid in weak:
        m = mastery[cid]
        affected = descendants(cid, dependents)
        weak_ancestors = ancestors(cid, prereqs) & weak
        severity = "high" if m < t.high_debt else "moderate"
        if severity == "moderate" and len(affected) >= t.escalation_dependents:
            severity = "high"  # a shaky foundation blocking many concepts is treated as high
        affected_sorted = sorted(affected, key=lambda a: (depths.get(a, 0), names[a]))
        items.append(
            {
                "concept_id": cid,
                "concept": names[cid],
                "mastery": round(m, 1),
                "severity": severity,
                "depth": depths.get(cid, 0),
                "is_root_cause": not weak_ancestors,
                "caused_by": [names[a] for a in sorted(weak_ancestors, key=lambda a: (depths.get(a, 0), names[a]))],
                "affected_concept_ids": [a for a in affected_sorted],
                "affected_concepts": [names[a] for a in affected_sorted],
                "priority_score": round((100 - m) * (1 + len(affected)), 1),
            }
        )
    items.sort(key=lambda i: (not i["is_root_cause"], -i["priority_score"], i["concept"]))
    return items


# ------------------------------------------------------------- learning path
def build_learning_path(
    names: dict[int, str],
    edges: list[tuple[int, int]],
    mastery: dict[int, float],
    t: Thresholds,
) -> list[dict]:
    """Order what the student should study.

    Included: weak concepts, plus their prerequisites that are not yet mastered.
    Order: a topological order of the whole graph (prerequisites always first); when several
    concepts are ready, foundational weak concepts that block the most weak concepts go first,
    then the lowest mastery, then name.
    """
    valid_edges = [(p, c) for p, c in edges if p in names and c in names]
    prereqs, dependents = build_adjacency(valid_edges)
    weak = {cid for cid, m in mastery.items() if cid in names and m < t.moderate_debt}

    included = set(weak)
    for cid in weak:
        for anc in ancestors(cid, prereqs):
            if anc in mastery and mastery[anc] < t.developing:
                included.add(anc)

    blocked_weak = {cid: len(descendants(cid, dependents) & weak) for cid in names}

    def key(cid: int):
        return (0 if cid in included else 1, -blocked_weak[cid], mastery.get(cid, 100.0), names[cid])

    indegree = {cid: len(prereqs.get(cid, ())) for cid in names}
    heap = [(key(c), c) for c, d in indegree.items() if d == 0]
    heapq.heapify(heap)
    order: list[int] = []
    while heap:
        _, cid = heapq.heappop(heap)
        order.append(cid)
        for dep in dependents.get(cid, ()):
            indegree[dep] -= 1
            if indegree[dep] == 0:
                heapq.heappush(heap, (key(dep), dep))
    order += [c for c in sorted(names, key=lambda c: names[c]) if c not in order]  # defensive (cycle)

    steps = []
    for cid in order:
        if cid not in included:
            continue
        m = mastery.get(cid)
        blocks = sorted(names[d] for d in descendants(cid, dependents) & weak)
        weak_anc = sorted(names[a] for a in ancestors(cid, prereqs) & weak)
        if cid in weak and not weak_anc:
            reason = "Foundational weak concept"
            reason += f" that other weak concepts depend on: {', '.join(blocks)}." if blocks else "."
        elif cid in weak:
            reason = f"Weak concept that builds on weak prerequisites: {', '.join(weak_anc)}."
        else:
            reason = "Prerequisite that is still developing; strengthen it before the concepts that rely on it."
        steps.append(
            {
                "order": len(steps) + 1,
                "concept_id": cid,
                "concept": names[cid],
                "mastery": m,
                "status": classify_mastery(m, t) if m is not None else None,
                "reason": reason,
                "unblocks": blocks,
            }
        )
    return steps
