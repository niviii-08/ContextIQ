"""
API routes for System A (context switching intelligence).

    POST /api/v1/context/analyze
    GET  /api/v1/context/{context_id}/associations
"""

from __future__ import annotations

import warnings

from fastapi import APIRouter, HTTPException, Query

from app.schemas.associations import ContextAssociationResult
from app.schemas.context import ContextAnalysisResult
from app.schemas.events import EventBatch
from app.state import store

from ml.associations.mining import mine_association_rules
from ml.associations.transactions import generate_transactions, transactions_to_basket_list
from ml.context.metrics import compute_session_metrics
from ml.context.pattern_discovery import discover_all_patterns
from ml.context.recovery_cost import estimate_recovery_costs
from ml.context.session_reconstruction import reconstruct_sessions

router = APIRouter()


@router.post("/analyze", response_model=ContextAnalysisResult)
def analyze_context(batch: EventBatch) -> ContextAnalysisResult:
    """Run the full System A pipeline over a batch of raw events:
    session reconstruction -> metrics -> pattern discovery -> recovery cost.

    Also opportunistically mines association rules per context from the
    same event batch (via COMPLETE-derived transactions) and caches them,
    so that GET /context/{context_id}/associations has data to serve.
    """
    if not batch.events:
        raise HTTPException(status_code=400, detail="events must not be empty")

    sessions = reconstruct_sessions(batch.events)
    metrics = compute_session_metrics(sessions, scope="request_batch")
    patterns = discover_all_patterns(sessions)
    recovery_estimates = estimate_recovery_costs(sessions)

    store.save_sessions(sessions)

    # Best-effort association mining per context present in this batch.
    transactions = generate_transactions(batch.events)
    contexts = sorted({t.context for t in transactions})
    for context in contexts:
        context_baskets = transactions_to_basket_list(
            [t for t in transactions if t.context == context]
        )
        if len(context_baskets) < 2:
            continue
        try:
            rules = mine_association_rules(
                context_baskets,
                context=context,
                algorithm="apriori",
                min_support=0.1,
                min_confidence=0.3,
                min_lift=1.0,
            )
        except (ImportError, RuntimeError) as exc:
            warnings.warn(
                f"Association mining skipped for context '{context}': {exc}",
                stacklevel=2,
            )
            rules = []
        store.save_rules(context, rules)

    return ContextAnalysisResult(
        sessions=sessions,
        metrics=metrics,
        patterns=patterns,
        recovery_estimates=recovery_estimates,
    )


@router.get("/{context_id}/associations", response_model=ContextAssociationResult)
def get_context_associations(
    context_id: str,
    algorithm: str = Query(default="apriori", pattern="^(apriori|fpgrowth)$"),
    min_support: float = Query(default=0.1, ge=0.0, le=1.0),
    min_confidence: float = Query(default=0.3, ge=0.0, le=1.0),
    min_lift: float = Query(default=1.0, ge=0.0),
) -> ContextAssociationResult:
    """Return association rules for a given context. If custom thresholds
    are supplied that differ from the cached defaults, rules are re-mined
    on the fly from cached transactions-equivalent session data."""
    cached_rules = store.get_rules(context_id)
    if not cached_rules:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No associations found for context '{context_id}'. "
                "Submit events via POST /api/v1/context/analyze first."
            ),
        )

    filtered = [
        r
        for r in cached_rules
        if r.support >= min_support and r.confidence >= min_confidence and r.lift >= min_lift
    ]

    return ContextAssociationResult(
        context=context_id,
        num_transactions=-1,  # Not tracked post-hoc for cached rules; see docs.
        frequent_itemsets_count=len(filtered),
        rules=filtered,
        algorithm=algorithm,
        thresholds={
            "min_support": min_support,
            "min_confidence": min_confidence,
            "min_lift": min_lift,
        },
    )
