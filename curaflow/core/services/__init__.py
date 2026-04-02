"""
Service Layer Pattern for CuraFlow.

All complex business logic should reside in service layers rather than in Views or Models.
A service function:
    1. Usually acts on behalf of an Organization and/or User.
    2. Performs business validations.
    3. Executes database transactions, updates, or creations.
    4. Is highly testable in isolation.

Structure:
    core/services/__init__.py
    customers/services.py
    programs/services.py
    ...
"""

import logging

logger = logging.getLogger(__name__)


class ServiceException(Exception):
    """
    Base exception for business logic errors. 
    Services should raise this or subclasses of this when business rules are violated,
    allowing the Presentation layer (Views) to handle it cleanly (e.g., as form errors).
    """
    pass


def get_object_for_organization(model_class, organization, prefetch=None, select=None, **kwargs):
    """
    Safely retrieves a single object ensuring it belongs to the given organization.
    Supports prefetching and select_related directly to avoid N+1 issues.
    
    Args:
        model_class: The Django model to query.
        organization: The Organization instance to scope to.
        prefetch: Iterable of prefetch_related lookups.
        select: Iterable of select_related lookups.
        kwargs: Additional filter parameters.
        
    Raises:
        model_class.DoesNotExist if not found.
    """
    qs = model_class.objects.filter(organization=organization)
    
    if select:
        qs = qs.select_related(*select)
    if prefetch:
        qs = qs.prefetch_related(*prefetch)
        
    return qs.get(**kwargs)
