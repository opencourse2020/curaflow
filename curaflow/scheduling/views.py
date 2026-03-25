import logging
from datetime import datetime, timezone

from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, UpdateView, View

from curaflow.core.mixins import OrganizationRequiredMixin
from curaflow.programs.models import Program

from .forms import AlertAcknowledgeForm, AppointmentStatusForm, SessionExecutionForm
from .models import Appointment, ExecutionAlert, SessionExecution
from .services import (
    aggregate_alert_counts,
    compute_live_adherence,
    get_latest_adherence_snapshot,
    get_open_alerts_for_program,
    get_program_status_summary,
    get_recent_session_executions,
    get_upcoming_appointments,
)

logger = logging.getLogger(__name__)


class TrackingOverviewView(OrganizationRequiredMixin, DetailView):
    """
    Main tracking dashboard for a specific Program.

    Assembles full context for the tracking template:
      - adherence summary (live + latest snapshot)
      - appointment status summary
      - upcoming appointments
      - recent session executions
      - open alerts (severity-sorted)
      - alert counts for badge display

    Uses the service layer for all derived data so the view stays thin.
    """

    model = Program
    template_name = "tracking.html"
    context_object_name = "program"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "customer__profile",
                "approved_by__user",
            )
            .prefetch_related(
                Prefetch(
                    "items",
                    to_attr="program_items",
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        program = self.object
        customer = program.customer

        # ── Adherence ──────────────────────────────────────────────────────
        context["adherence"] = compute_live_adherence(program)
        context["latest_snapshot"] = get_latest_adherence_snapshot(program)

        # ── Appointment summary ─────────────────────────────────────────────
        context["status_summary"] = get_program_status_summary(program)

        # ── Upcoming appointments (next 14 days) ────────────────────────────
        context["upcoming_appointments"] = get_upcoming_appointments(program, days_ahead=14)

        # ── Recent session executions ────────────────────────────────────────
        context["recent_executions"] = get_recent_session_executions(program, limit=10)

        # ── Alerts ──────────────────────────────────────────────────────────
        context["open_alerts"] = get_open_alerts_for_program(program)
        context["alert_counts"] = aggregate_alert_counts(program)

        # ── Customer snapshot (for summary panel) ────────────────────────────
        context["customer"] = customer
        context["customer_profile"] = getattr(customer, "profile", None)

        # Alert counts as convenience booleans for the template
        context["has_alerts"] = context["alert_counts"].get("open", 0) > 0

        context["page_title"] = f"Tracking — {program.name}"
        return context


class AppointmentUpdateView(OrganizationRequiredMixin, UpdateView):
    """
    Updates an Appointment's status and notes.

    The appointment is fetched via its program which is already org-scoped,
    ensuring a user cannot update appointments from another tenant.
    Redirects back to the tracking overview on success.
    """

    model = Appointment
    form_class = AppointmentStatusForm
    template_name = "appointment_update.html"

    def get_queryset(self):
        # Explicitly scope: appointment must belong to a program in this org
        return Appointment.objects.filter(
            organization=self.organization
        ).select_related("service", "customer", "program")

    def form_valid(self, form):
        appointment = form.save()
        messages.success(
            self.request,
            f"Appointment updated to {appointment.get_status_display()}.",
        )
        program_pk = appointment.program_id
        if program_pk:
            return redirect(reverse("scheduling:tracking", kwargs={"pk": program_pk}))
        return redirect(reverse("core:dashboard"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Appointment"
        return context


class SessionExecutionUpdateView(OrganizationRequiredMixin, View):
    """
    GET  → renders the session execution form for a given Appointment.
    POST → creates or updates the linked SessionExecution and marks the
           Appointment as COMPLETED if the customer attended.

    An Appointment has a OneToOne `execution` relation. We use
    get_or_create so re-submitting is safe.
    """

    template_name = "session_execution.html"

    def _get_appointment(self):
        return get_object_or_404(
            Appointment,
            pk=self.kwargs["pk"],
            organization=self.organization,
        )

    def get(self, request, *args, **kwargs):
        from django.shortcuts import render

        appointment = self._get_appointment()
        existing = getattr(appointment, "execution", None)
        form = SessionExecutionForm(instance=existing)
        return render(request, self.template_name, self._ctx(appointment, form))

    def post(self, request, *args, **kwargs):
        from django.shortcuts import render

        appointment = self._get_appointment()
        existing = getattr(appointment, "execution", None)
        form = SessionExecutionForm(request.POST, instance=existing)

        if form.is_valid():
            with transaction.atomic():
                execution = form.save(commit=False)
                execution.appointment = appointment
                execution.program = appointment.program
                execution.program_item = appointment.program_item
                execution.customer = appointment.customer
                execution.service = appointment.service
                execution.staff = appointment.staff
                execution.execution_date = (
                    appointment.scheduled_start.date()
                    if appointment.scheduled_start
                    else datetime.now(tz=timezone.utc).date()
                )

                # Resolve staff admin profile
                try:
                    execution.staff = request.user.admin
                except Exception:
                    pass

                execution.save()

                # Mirror the appointment status if attended
                new_appt_status = (
                    Appointment.Status.COMPLETED
                    if form.cleaned_data.get("customer_attended")
                    else Appointment.Status.MISSED
                )
                appointment.status = new_appt_status
                appointment.save(update_fields=["status", "updated_at"])

            messages.success(request, "Session outcome recorded.")
            program_pk = appointment.program_id
            if program_pk:
                return redirect(
                    reverse("scheduling:tracking", kwargs={"pk": program_pk})
                )
        return render(request, self.template_name, self._ctx(appointment, form))

    def _ctx(self, appointment, form):
        return {
            "appointment": appointment,
            "form": form,
            "page_title": f"Record Session — {appointment.service}",
        }


class AlertAcknowledgeView(OrganizationRequiredMixin, View):
    """
    POST-only view to acknowledge, resolve, or dismiss an ExecutionAlert.
    Redirects back to the tracking overview for the alert's program.
    """

    def post(self, request, *args, **kwargs):
        alert = get_object_or_404(
            ExecutionAlert,
            pk=self.kwargs["pk"],
            organization=self.organization,
        )
        form = AlertAcknowledgeForm(request.POST, instance=alert)
        if form.is_valid():
            alert = form.save(commit=False)
            if alert.status == ExecutionAlert.Status.RESOLVED:
                alert.resolved_at = datetime.now(tz=timezone.utc)
            # Assign to reviewing staff if available
            try:
                alert.assigned_to = request.user.admin
            except Exception:
                pass
            alert.save(update_fields=["status", "resolved_at", "assigned_to", "updated_at"])
            messages.success(
                request,
                f"Alert "{alert.title}" marked as {alert.get_status_display()}.",
            )
        else:
            messages.error(request, "Invalid alert status.")

        program_pk = alert.program_id
        if program_pk:
            return redirect(
                reverse("scheduling:tracking", kwargs={"pk": program_pk})
            )
        return redirect(reverse("core:dashboard"))
