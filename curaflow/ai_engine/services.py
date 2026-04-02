"""
ai_engine/services.py

Service layer for AI recommendation orchestration.

Design intent
─────────────
These functions are the single integration point between Django views and the
underlying AI pipeline (currently a stub, future LangGraph graph).

Rules:
  1. All public functions are pure Python — no HTTP, no Django request objects.
  2. They operate on model instances and dicts of serialisable data.
  3. They raise ServiceException (from core.services) on logical failures.
  4. Each function has a clear, documented contract so the LangGraph swap is
     a one-file change with no ripple to views or forms.
"""

import logging
from datetime import datetime, timezone

from django.db import transaction

from curaflow.core.services import ServiceException

from .models import (
    RecommendationDecision,
    RecommendationInputSnapshot,
    RecommendationRun,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Input snapshot helpers
# ---------------------------------------------------------------------------


def build_input_snapshot(*, run, customer):
    """
    Collect and persist the structured input that the AI engine will consume.

    Called before triggering a generation run so there is always a complete
    audit record of what data was used, regardless of whether the AI step
    succeeds.

    Parameters
    ----------
    run : RecommendationRun
        The parent run record (must already be saved).
    customer : Customer
        Fully loaded customer instance (caller should prefetch profile,
        goals, conditions, injuries).

    Returns
    -------
    RecommendationInputSnapshot
    """
    profile = getattr(customer, "profile", None)

    snapshot_data = {
        "customer_profile_json": _serialize_customer_profile(customer, profile),
        "goals_json": _serialize_goals(customer),
        "conditions_json": _serialize_conditions(customer),
        "injuries_json": _serialize_injuries(customer),
        "services_catalog_json": _serialize_services(run.organization),
        "constraints_json": {},
        "metadata_json": {
            "snapshot_taken_at": datetime.now(tz=timezone.utc).isoformat(),
            "customer_id": customer.pk,
            "organization_id": run.organization_id,
        },
    }

    snapshot, _ = RecommendationInputSnapshot.objects.update_or_create(
        recommendation_run=run,
        defaults=snapshot_data,
    )
    return snapshot


def _serialize_customer_profile(customer, profile):
    data = {
        "id": customer.pk,
        "name": str(customer),
        "gender": customer.gender,
        "date_of_birth": str(customer.date_of_birth) if customer.date_of_birth else None,
    }
    if profile:
        data.update(
            {
                "height_cm": float(profile.height_cm) if profile.height_cm else None,
                "weight_kg": float(profile.weight_kg) if profile.weight_kg else None,
                "bmi": float(profile.bmi) if profile.bmi else None,
                "activity_level": profile.activity_level,
                "risk_level": profile.risk_level,
                "dietary_preference": profile.dietary_preference,
                "goals_summary": profile.goals_summary,
            }
        )
    return data


def _serialize_goals(customer):
    return [
        {
            "goal": str(cg.goal),
            "category": cg.goal.category,
            "priority": cg.priority,
            "target_date": str(cg.target_date) if cg.target_date else None,
        }
        for cg in getattr(customer, "prefetched_goals", customer.goals.select_related("goal").all())
    ]


def _serialize_conditions(customer):
    return [
        {
            "condition": str(cmc.medical_condition),
            "category": cmc.medical_condition.category,
            "severity": cmc.severity,
            "status": cmc.status,
            "requires_restriction": cmc.requires_program_restriction,
            "is_high_risk": cmc.medical_condition.is_high_risk,
        }
        for cmc in getattr(
            customer,
            "prefetched_conditions",
            customer.medical_conditions.filter(status="active").select_related("medical_condition"),
        )
    ]


def _serialize_injuries(customer):
    return [
        {
            "injury": str(ci.injury),
            "body_area": ci.injury.body_area,
            "side": ci.side,
            "severity": ci.severity,
            "status": ci.status,
        }
        for ci in customer.injuries.filter(status__in=["active", "recovering"]).select_related("injury")
    ]


def _serialize_services(organization):
    from curaflow.services.models import Service

    return [
        {
            "id": svc.pk,
            "name": svc.name,
            "code": svc.code,
            "category": str(svc.category) if svc.category else None,
            "duration_minutes": svc.duration_minutes,
            "intensity_level": svc.intensity_level,
            "delivery_mode": svc.delivery_mode,
            "base_price": float(svc.base_price) if svc.base_price else None,
            "requires_medical_clearance": svc.requires_medical_clearance,
        }
        for svc in Service.objects.filter(organization=organization, is_active=True)
        .select_related("category")
        .order_by("name")
    ]


# ---------------------------------------------------------------------------
# Generation stub
# ---------------------------------------------------------------------------


def trigger_recommendation_run(*, run):
    """
    Entry point for AI recommendation generation.

    Current state: sets run.status = NEEDS_REVIEW and marks it ready for
    manual review (no AI inference yet).

    Future state: this function will:
        1. Call the LangGraph graph entry-point with the input snapshot.
        2. Parse the returned RecommendationOption list.
        3. Persist options + items via persist_recommendation_options().
        4. Fetch and persist EvidenceSources from the graph output.
        5. Set run.status = COMPLETED or FAILED.

    Parameters
    ----------
    run : RecommendationRun — must be in PENDING status.

    Returns
    -------
    RecommendationRun with updated status.

    Raises
    ------
    ServiceException if the run is not in a triggerable state.
    """
    if run.status not in (RecommendationRun.Status.PENDING,):
        raise ServiceException(
            f"Cannot trigger a run in '{run.status}' status. "
            "Only PENDING runs can be triggered."
        )

    with transaction.atomic():
        run.status = RecommendationRun.Status.NEEDS_REVIEW
        run.started_at = datetime.now(tz=timezone.utc)
        run.completed_at = datetime.now(tz=timezone.utc)
        run.save(update_fields=["status", "started_at", "completed_at", "updated_at"])

    logger.info(
        "RecommendationRun %s set to NEEDS_REVIEW (stub). "
        "LangGraph integration not yet connected.",
        run.pk,
    )
    return run


# ---------------------------------------------------------------------------
# Decision recording
# ---------------------------------------------------------------------------


def record_decision(*, run, decision_value, selected_option=None,
                    reviewed_by_admin=None, review_notes="", final_program=None):
    """
    Persist a clinician's decision on a completed recommendation run.

    Idempotent — calling with the same run a second time updates the
    existing RecommendationDecision rather than creating a duplicate.

    Parameters
    ----------
    run : RecommendationRun
    decision_value : str — one of RecommendationDecision.Decision values
    selected_option : RecommendationOption | None
    reviewed_by_admin : Admin | None
    review_notes : str
    final_program : Program | None — the program created from this decision

    Returns
    -------
    RecommendationDecision (created or updated)
    """
    allowed_decisions = [d.value for d in RecommendationDecision.Decision]
    if decision_value not in allowed_decisions:
        raise ServiceException(
            f"'{decision_value}' is not a valid decision. "
            f"Choose from: {allowed_decisions}"
        )

    with transaction.atomic():
        decision, _ = RecommendationDecision.objects.update_or_create(
            recommendation_run=run,
            defaults={
                "decision": decision_value,
                "selected_option": selected_option,
                "reviewed_by": reviewed_by_admin,
                "review_notes": review_notes,
                "final_program": final_program,
            },
        )

    logger.info(
        "Decision '%s' recorded on RecommendationRun %s by Admin %s",
        decision_value,
        run.pk,
        getattr(reviewed_by_admin, "pk", None),
    )
    return decision


# ---------------------------------------------------------------------------
# Convenience: initiate a new run record
# ---------------------------------------------------------------------------


def initiate_run(*, organization, customer, program_case, triggered_by_user):
    """
    Create a new RecommendationRun in PENDING status.

    This is the very first step — called before build_input_snapshot()
    and trigger_recommendation_run().  Raises ServiceException if the
    customer does not belong to the organization.
    """
    if customer.organization_id != organization.pk:
        raise ServiceException("Customer does not belong to this organization.")

    run = RecommendationRun.objects.create(
        organization=organization,
        customer=customer,
        program_case=program_case,
        triggered_by=triggered_by_user,
        status=RecommendationRun.Status.PENDING,
    )
    logger.info("RecommendationRun %s initiated for customer %s", run.pk, customer.pk)
    return run
