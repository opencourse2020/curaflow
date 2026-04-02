"""
programs/services.py

Business logic for the Program Builder workflow.

Keeping these functions here rather than in views.py means they can be
called from management commands, tests, and (eventually) API views
without duplicating the creation logic.
"""

import logging
from decimal import Decimal

from django.db import transaction

from curaflow.profiles.models import Admin

from .models import Program, ProgramCase, ProgramItem

logger = logging.getLogger(__name__)


def create_program(*, organization, customer, name, created_by_user, **program_kwargs):
    """
    Create a Program and its owning ProgramCase atomically.

    Returns the saved Program instance.

    Parameters
    ----------
    organization : Organization
        The tenant. Stamped on both ProgramCase and Program.
    customer : Customer
        Must already belong to `organization` — caller is responsible
        for validating this (the view ensures it via org-scoped form).
    name : str
        Human-readable program name.
    created_by_user : User
        The authenticated user triggering the creation.
        We resolve their Admin profile for the `created_by` FK; if no
        Admin profile exists we store NULL rather than raising.
    **program_kwargs
        Any remaining Program field values
        (objective_summary, duration_weeks, start_date, etc.).
    """
    admin_profile = _resolve_admin(created_by_user)

    with transaction.atomic():
        case = ProgramCase.objects.create(
            organization=organization,
            customer=customer,
            created_by=admin_profile,
            source=ProgramCase.Source.MANUAL,
            case_status=ProgramCase.CaseStatus.DRAFT,
        )

        program = Program.objects.create(
            organization=organization,
            customer=customer,
            program_case=case,
            name=name,
            status=Program.Status.DRAFT,
            **program_kwargs,
        )

    logger.info(
        "Program %s created for customer %s in org %s by user %s",
        program.pk,
        customer.pk,
        organization.pk,
        created_by_user.pk,
    )
    return program


def add_program_items(*, program, formset):
    """
    Persist a valid ProgramItemFormSet for the given program.

    Stamps `program=` on each form instance before saving (the inline
    formset already does this via the parent FK, but being explicit
    avoids surprises if the formset is ever reused).

    Returns a list of saved ProgramItem instances.
    """
    if not formset.is_valid():
        raise ValueError("Cannot save an invalid formset.")

    saved = []
    with transaction.atomic():
        items = formset.save(commit=False)
        for idx, item in enumerate(items):
            item.program = program
            if not item.order_index:
                item.order_index = idx
            item.save()
            saved.append(item)

        # Handle deleted items (can_delete=True on the formset)
        for obj in formset.deleted_objects:
            obj.delete()

    return saved


def calculate_program_price(program):
    """
    Derive a rough total price from ProgramItems by summing
    service.base_price × planned_sessions_count for each item.

    Returns a Decimal. Stores the result on program.total_price if
    it differs from the current value.
    """
    total = Decimal("0.00")
    items = program.items.select_related("service").filter(
        status__in=[ProgramItem.Status.PLANNED, ProgramItem.Status.ACTIVE]
    )
    for item in items:
        if item.service.base_price:
            total += item.service.base_price * item.planned_sessions_count

    if program.total_price != total:
        program.total_price = total
        program.save(update_fields=["total_price", "updated_at"])

    return total


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _resolve_admin(user):
    """Return the Admin profile for a User, or None."""
    try:
        return user.admin
    except Exception:
        return None
