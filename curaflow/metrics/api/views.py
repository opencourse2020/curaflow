"""
metrics/api/views.py

DRF chart data endpoints — JSON only; no HTML rendering.

Why DRF here and not in other sections of the codebase?
  - Analytics charts need to re-fetch data when the user changes date ranges
    — a full-page reload for each filter change would be unacceptable UX on a
    data-heavy dashboard.
  - All other CuraFlow pages are server-rendered and never require in-page
    JSON responses, so DRF is intentionally scoped to these six endpoints only.

Auth/permission design:
  - IsAuthenticated is always required (enforced by OrgAPIPermission).
  - OrgAPIPermission also validates that `request.user` belongs to an
    organisation, mirroring the OrganizationRequiredMixin used in class-based
    views. This is the API equivalent of that mixin.

All views delegate 100% of their computation to metrics.services so the
views stay thin and the service functions remain independently testable.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from curaflow.metrics.services import (
    get_adherence_trend,
    get_completion_rate_by_category,
    get_dropout_risk_trend,
    get_outcome_trend_by_metric,
    get_service_utilisation,
)

from .serializers import (
    CategoryCompletionSerializer,
    ServiceUtilisationSerializer,
    WeeklyRateSerializer,
)


class OrgAPIPermission(IsAuthenticated):
    """
    Extends IsAuthenticated to require an active organisation.
    Resolves the organisation from the user's Profile FK so the
    endpoint is equivalent in security to OrganizationRequiredMixin.
    """

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        org = _resolve_org(request.user)
        if org is None:
            return False
        request._org = org  # cache for the view
        return True


def _resolve_org(user):
    """Return the Organization for a user via their Admin or Member profile."""
    for attr in ("admin", "member"):
        profile = getattr(user, attr, None)
        if profile and getattr(profile, "organization", None):
            return profile.organization
    return None


class _BaseChartView(APIView):
    """
    Shared base for chart endpoints.

    Parses the `weeks` query param (default 12, max 52) so every
    endpoint supports the same date-range control without repeating
    the validation.
    """

    permission_classes = [OrgAPIPermission]

    def _org(self):
        return self.request._org

    def _weeks(self):
        try:
            w = int(self.request.query_params.get("weeks", 12))
            return max(1, min(w, 52))
        except (ValueError, TypeError):
            return 12


class AdherenceTrendView(_BaseChartView):
    """GET /metrics/api/adherence-trend/?weeks=12"""

    def get(self, request):
        data = get_adherence_trend(self._org(), weeks=self._weeks())
        return Response({"results": data})


class CompletionRateByCategoryView(_BaseChartView):
    """GET /metrics/api/completion-by-category/"""

    def get(self, request):
        data = get_completion_rate_by_category(self._org())
        serializer = CategoryCompletionSerializer(data, many=True)
        return Response({"results": serializer.data})


class ServiceUtilisationView(_BaseChartView):
    """GET /metrics/api/service-utilisation/?limit=10"""

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 10))
            limit = max(1, min(limit, 30))
        except (ValueError, TypeError):
            limit = 10
        data = get_service_utilisation(self._org(), limit=limit)
        serializer = ServiceUtilisationSerializer(data, many=True)
        return Response({"results": serializer.data})


class DropoutRiskTrendView(_BaseChartView):
    """GET /metrics/api/dropout-risk/?weeks=12"""

    def get(self, request):
        data = get_dropout_risk_trend(self._org(), weeks=self._weeks())
        return Response({"results": data})


class OutcomeTrendView(_BaseChartView):
    """
    GET /metrics/api/outcome-trend/?metric=<code>&weeks=12

    `metric` is a MetricType.code value (e.g. "pain_level", "mobility_score").
    Returns an empty list with a 200 if the metric code is unknown —
    this is intentional so the chart gracefully shows an empty state
    rather than a 404 that the frontend must handle differently.
    """

    def get(self, request):
        metric_code = request.query_params.get("metric", "")
        if not metric_code:
            return Response({"results": [], "error": "metric param required."}, status=400)
        data = get_outcome_trend_by_metric(self._org(), metric_code, weeks=self._weeks())
        return Response({"results": data})
