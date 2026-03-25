from django.views.generic import TemplateView

from curaflow.core.mixins import OrganizationRequiredMixin

from .services import get_alert_breakdown, get_kpi_summary


class AnalyticsDashboardView(OrganizationRequiredMixin, TemplateView):
    """
    Server-rendered shell for the analytics page.

    Loads:
      - KPI summary cards (4 metrics, computed server-side at page load)
      - Alert breakdown table (small enough to render inline)

    Chart data is intentionally NOT loaded here. Each chart is wired to a
    dedicated DRF endpoint under /metrics/api/ that accepts a `weeks`
    query param. This means:
      1. The page shell renders instantly without waiting for heavy aggregations.
      2. Charts can independently reload when the user changes date ranges
         without a full page reload.
      3. The DRF endpoints are cacheable at the HTTP layer if needed.
    """

    template_name = "analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.organization

        context["kpis"] = get_kpi_summary(org)
        context["alert_breakdown"] = get_alert_breakdown(org)

        # Expose API endpoint roots so the template JS can construct URLs
        # without hardcoding paths.
        context["api_base"] = "/metrics/api/"

        context["page_title"] = "Analytics"
        return context
