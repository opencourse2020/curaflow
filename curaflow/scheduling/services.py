"""
scheduling/services.py

Business-logic helpers for the Tracking section.

All functions are pure Python — no Django request objects.
They accept and return model instances and plain dicts so they can be
called from views, management commands, and Celery tasks alike.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from .models import AdherenceSnapshot, Appointment, ExecutionAlert, SessionExecution

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Adherence
# ---------------------------------------------------------------------------


def compute_live_adherence(program):
    """
    Calculate real-time adherence figures from SessionExecution records
    without relying on a pre-existing AdherenceSnapshot.

    Returns a dict:
        {
            "planned":    int,
            "completed":  int,
            "missed":     int,
            "cancelled":  int,
            "rate":       Decimal,   # 0–100
            "target":     Decimal,   # program.adherence_target
            "on_track":   bool,
        }
    """
    agg = SessionExecution.objects.filter(program=program).aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=SessionExecution.Status.COMPLETED)),
        partial=Count("id", filter=Q(status=SessionExecution.Status.PARTIAL)),
        missed=Count("id", filter=Q(status=SessionExecution.Status.MISSED)),
        cancelled=Count("id", filter=Q(status=SessionExecution.Status.CANCELLED)),
    )

    planned = agg["total"]
    completed = agg["completed"] + agg["partial"]  # partial counts toward adherence
    missed = agg["missed"]
    cancelled = agg["cancelled"]

    rate = (
        Decimal(completed / planned * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if planned > 0
        else Decimal("0.00")
    )

    return {
        "planned": planned,
        "completed": completed,
        "missed": missed,
        "cancelled": cancelled,
        "rate": rate,
        "target": program.adherence_target,
        "on_track": rate >= program.adherence_target,
    }


def get_latest_adherence_snapshot(program):
    """
    Return the most recent AdherenceSnapshot for a program, or None.
    Avoids an extra query if the caller already prefetched snapshots
    by passing them in via a kwarg pattern.
    """
    return (
        AdherenceSnapshot.objects.filter(program=program)
        .order_by("-snapshot_date")
        .first()
    )


def take_adherence_snapshot(program):
    """
    Compute current adherence and persist it as an AdherenceSnapshot
    for today.  Idempotent — updates if a snapshot for today exists.

    Returns the saved AdherenceSnapshot.
    """
    data = compute_live_adherence(program)
    today = date.today()

    snapshot, created = AdherenceSnapshot.objects.update_or_create(
        customer=program.customer,
        program=program,
        snapshot_date=today,
        defaults={
            "planned_sessions": data["planned"],
            "completed_sessions": data["completed"],
            "missed_sessions": data["missed"],
            "cancelled_sessions": data["cancelled"],
            "adherence_rate": data["rate"],
        },
    )
    action = "Created" if created else "Updated"
    logger.info(
        "%s adherence snapshot for program %s on %s (rate=%s%%)",
        action, program.pk, today, data["rate"],
    )
    return snapshot


# ---------------------------------------------------------------------------
# Alert aggregation
# ---------------------------------------------------------------------------


def get_open_alerts_for_program(program):
    """
    Return all OPEN ExecutionAlerts for a program, ordered by severity
    (high first) then creation time.

    Severity is stored as a free-text CharField; we sort it by a fixed
    priority map so 'high' always floats to the top.
    """
    SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}

    alerts = list(
        ExecutionAlert.objects.filter(
            program=program,
            status=ExecutionAlert.Status.OPEN,
        )
        .select_related("customer", "appointment__service", "assigned_to__user")
        .order_by("created_at")
    )
    alerts.sort(key=lambda a: (SEVERITY_ORDER.get(a.severity.lower(), 3), a.created_at))
    return alerts


def aggregate_alert_counts(program):
    """
    Return a summary dict of alert counts grouped by status.
    Useful for the tracking page header badges.
    """
    agg = ExecutionAlert.objects.filter(program=program).aggregate(
        open=Count("id", filter=Q(status=ExecutionAlert.Status.OPEN)),
        acknowledged=Count("id", filter=Q(status=ExecutionAlert.Status.ACKNOWLEDGED)),
        resolved=Count("id", filter=Q(status=ExecutionAlert.Status.RESOLVED)),
    )
    return agg


# ---------------------------------------------------------------------------
# Appointment / session helpers
# ---------------------------------------------------------------------------


def get_upcoming_appointments(program, days_ahead=14):
    """
    Return scheduled/confirmed appointments for the next `days_ahead` days.
    """
    now = timezone.now()
    cutoff = now + timedelta(days=days_ahead)
    return (
        Appointment.objects.filter(
            program=program,
            status__in=[
                Appointment.Status.SCHEDULED,
                Appointment.Status.CONFIRMED,
            ],
            scheduled_start__range=(now, cutoff),
        )
        .select_related("service", "staff__user", "location")
        .order_by("scheduled_start")
    )


def get_recent_session_executions(program, limit=10):
    """
    Return the most recent SessionExecution records for a program.
    """
    return (
        SessionExecution.objects.filter(program=program)
        .select_related("service", "staff__user", "program_item__service")
        .order_by("-execution_date")[:limit]
    )


def mark_appointment_status(*, appointment, new_status, actor_user):
    """
    Change an appointment's status and log the action.

    Does NOT create a SessionExecution — that is a separate step done
    by SessionExecutionUpdateView so the two concerns stay separate.
    """
    old_status = appointment.status
    with transaction.atomic():
        appointment.status = new_status
        appointment.save(update_fields=["status", "updated_at"])

    logger.info(
        "Appointment %s status changed %s → %s by user %s",
        appointment.pk, old_status, new_status, actor_user.pk,
    )
    return appointment


def get_program_status_summary(program):
    """
    Build a concise status summary dict for the tracking page header.

    Returns:
        {
            "total_appointments":   int,
            "completed_count":      int,
            "missed_count":         int,
            "upcoming_count":       int,
            "completion_pct":       int,   # 0-100
        }
    """
    agg = Appointment.objects.filter(program=program).aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=Appointment.Status.COMPLETED)),
        missed=Count("id", filter=Q(status=Appointment.Status.MISSED)),
        upcoming=Count(
            "id",
            filter=Q(status__in=[
                Appointment.Status.SCHEDULED,
                Appointment.Status.CONFIRMED,
            ]),
        ),
    )
    total = agg["total"] or 0
    completed = agg["completed"] or 0
    return {
        "total_appointments": total,
        "completed_count": completed,
        "missed_count": agg["missed"] or 0,
        "upcoming_count": agg["upcoming"] or 0,
        "completion_pct": int(completed / total * 100) if total else 0,
    }
