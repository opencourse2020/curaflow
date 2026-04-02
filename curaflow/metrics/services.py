"""
metrics/services.py

All heavy aggregation logic for the analytics page.

Query design principles applied here:
  - Use .values() + .annotate() for grouped aggregates → single SQL query per metric.
  - Use TruncWeek/TruncMonth from django.db.models.functions for time-series bucketing.
  - All functions accept `organization` as the first argument so org scoping
    is explicit and cannot be accidentally omitted.
  - Functions return plain Python dicts / lists so they are trivially
    serialisable by DRF or renderable by Django templates.
"""

import logging
from datetime import date, timedelta

from django.db.models import Avg, Count, F, FloatField, Q, Sum
from django.db.models.functions import TruncWeek, TruncMonth

from curaflow.programs.models import Program
from curaflow.scheduling.models import (
    AdherenceSnapshot,
    Appointment,
    ExecutionAlert,
    SessionExecution,
)
from curaflow.services.models import Service

logger = logging.getLogger(__name__)

_DEFAULT_WEEKS = 12


# ---------------------------------------------------------------------------
# KPI cards  (served at page load via the server-rendered shell)
# ---------------------------------------------------------------------------


def get_kpi_summary(organization):
    """
    Returns the four headline KPIs shown in the stat-card strip.
    Single annotated query per model — no N+1.
    """
    programs_agg = Program.objects.filter(organization=organization).aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Program.Status.ACTIVE)),
    )

    sessions_agg = SessionExecution.objects.filter(
        program__organization=organization
    ).aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=SessionExecution.Status.COMPLETED)),
    )

    open_alerts = ExecutionAlert.objects.filter(
        organization=organization, status=ExecutionAlert.Status.OPEN
    ).count()

    avg_adherence = (
        AdherenceSnapshot.objects.filter(program__organization=organization)
        .aggregate(avg=Avg("adherence_rate"))["avg"]
        or 0
    )

    completion_rate = (
        round(sessions_agg["completed"] / sessions_agg["total"] * 100, 1)
        if sessions_agg["total"]
        else 0
    )

    return {
        "active_programs": programs_agg["active"],
        "total_programs": programs_agg["total"],
        "completion_rate": completion_rate,
        "avg_adherence": round(float(avg_adherence), 1),
        "open_alerts": open_alerts,
        "total_sessions": sessions_agg["total"],
    }


# ---------------------------------------------------------------------------
# Adherence trend  (chart endpoint)
# ---------------------------------------------------------------------------


def get_adherence_trend(organization, weeks=_DEFAULT_WEEKS):
    """
    Weekly average adherence rate across all active programs.

    Returns a list of {"week": "YYYY-MM-DD", "avg_rate": float} dicts
    ordered oldest → newest for chart rendering.
    """
    since = date.today() - timedelta(weeks=weeks)

    rows = (
        AdherenceSnapshot.objects.filter(
            program__organization=organization,
            snapshot_date__gte=since,
        )
        .annotate(week=TruncWeek("snapshot_date"))
        .values("week")
        .annotate(avg_rate=Avg("adherence_rate"))
        .order_by("week")
    )

    return [
        {"week": row["week"].strftime("%Y-%m-%d"), "avg_rate": round(float(row["avg_rate"]), 1)}
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Completion rate by service category  (chart endpoint)
# ---------------------------------------------------------------------------


def get_completion_rate_by_category(organization):
    """
    Completion rate per service category.

    Returns:
        [{"category": str, "total": int, "completed": int, "rate": float}]
    """
    rows = (
        SessionExecution.objects.filter(program__organization=organization)
        .values(category=F("service__category__name"))
        .annotate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=SessionExecution.Status.COMPLETED)),
        )
        .order_by("-total")
    )

    result = []
    for row in rows:
        cat = row["category"] or "Uncategorised"
        total = row["total"]
        completed = row["completed"]
        result.append(
            {
                "category": cat,
                "total": total,
                "completed": completed,
                "rate": round(completed / total * 100, 1) if total else 0,
            }
        )
    return result


# ---------------------------------------------------------------------------
# Service utilisation  (chart endpoint)
# ---------------------------------------------------------------------------


def get_service_utilisation(organization, limit=10):
    """
    Top services by number of planned sessions.

    Returns:
        [{"service": str, "sessions": int, "completed": int}]
    """
    rows = (
        SessionExecution.objects.filter(program__organization=organization)
        .values(service=F("service__name"))
        .annotate(
            sessions=Count("id"),
            completed=Count("id", filter=Q(status=SessionExecution.Status.COMPLETED)),
        )
        .order_by("-sessions")[:limit]
    )

    return [
        {
            "service": row["service"],
            "sessions": row["sessions"],
            "completed": row["completed"],
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Drop-off indicators  (chart endpoint)
# ---------------------------------------------------------------------------


def get_dropout_risk_trend(organization, weeks=_DEFAULT_WEEKS):
    """
    Weekly average dropout risk score from AdherenceSnapshot.

    Returns:
        [{"week": "YYYY-MM-DD", "avg_dropout_risk": float}]
    """
    since = date.today() - timedelta(weeks=weeks)

    rows = (
        AdherenceSnapshot.objects.filter(
            program__organization=organization,
            snapshot_date__gte=since,
            dropout_risk_score__isnull=False,
        )
        .annotate(week=TruncWeek("snapshot_date"))
        .values("week")
        .annotate(avg_dropout_risk=Avg("dropout_risk_score"))
        .order_by("week")
    )

    return [
        {
            "week": row["week"].strftime("%Y-%m-%d"),
            "avg_dropout_risk": round(float(row["avg_dropout_risk"]), 1),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Customer outcome trends  (chart endpoint)
# ---------------------------------------------------------------------------


def get_outcome_trend_by_metric(organization, metric_code, weeks=_DEFAULT_WEEKS):
    """
    Weekly average value for a specific MetricType (identified by `code`).

    Returns:
        [{"week": "YYYY-MM-DD", "avg_value": float}]
    """
    from curaflow.metrics.models import CustomerMetricRecord

    since = date.today() - timedelta(weeks=weeks)

    rows = (
        CustomerMetricRecord.objects.filter(
            metric_type__organization=organization,
            metric_type__code=metric_code,
            recorded_at__date__gte=since,
            value_number__isnull=False,
        )
        .annotate(week=TruncWeek("recorded_at"))
        .values("week")
        .annotate(avg_value=Avg("value_number"))
        .order_by("week")
    )

    return [
        {
            "week": row["week"].strftime("%Y-%m-%d"),
            "avg_value": round(float(row["avg_value"]), 2),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Alert summary by type  (served at page load)
# ---------------------------------------------------------------------------


def get_alert_breakdown(organization):
    """
    Alert counts grouped by alert_type for the org.

    Returns:
        [{"alert_type": str, "label": str, "open": int, "total": int}]
    """
    rows = (
        ExecutionAlert.objects.filter(organization=organization)
        .values("alert_type")
        .annotate(
            total=Count("id"),
            open=Count("id", filter=Q(status=ExecutionAlert.Status.OPEN)),
        )
        .order_by("-total")
    )

    type_labels = dict(ExecutionAlert.AlertType.choices)
    return [
        {
            "alert_type": row["alert_type"],
            "label": type_labels.get(row["alert_type"], row["alert_type"]),
            "open": row["open"],
            "total": row["total"],
        }
        for row in rows
    ]
