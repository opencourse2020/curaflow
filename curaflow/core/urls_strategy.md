# CuraFlow URL Organization Strategy

## Principles
We use a **domain-first, modular routing strategy**. The root `urls.py` should be as clean as possible, delegating to the `urls.py` in individual Django applications.

## Path Structure
The path structure should reflect the core business entities grouped sensibly, prioritizing the multi-tenant SaaS layout. We avoid exposing the 'organization' directly in the URL (like `/org/{id}/...`) because standard staff only ever exist within one organization at a time (scoped via the authenticated User).

### Root `urls.py` Example:
```python
urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Account & Auth
    path("accounts/", include("allauth.urls")),
    
    # Application Domains
    path("", include("core.urls", namespace="core")),
    path("customers/", include("customers.urls", namespace="customers")),
    path("programs/", include("programs.urls", namespace="programs")),
    path("services/", include("services.urls", namespace="services")),
    path("tracking/", include("tracking.urls", namespace="tracking")),
    
    # API Endpoints (if DRF introduced later)
    # path("api/v1/", include("curaflow.api_urls")),
]
```

## Nested Routing vs Flat Routing
For deeply associated entities (e.g., a Program belonging to a Customer), use flat routes representing the workflow, rather than excessively deep nested routes.

**Bad (Too Deep):** 
`/customers/<id>/programs/<prog_id>/sessions/<sess_id>/`

**Good (Flat and Action-Oriented):**
`/customers/<id>/` (Customer Profile)
`/programs/<prog_id>/` (Program Details — checks permissions securely via CBV mixins)
`/tracking/sessions/<sess_id>/` (Session view)

## Namespacing
Always use the `namespace` argument when including `.urls` from child applications. This enables reverse URL resolution like `reverse('customers:detail', kwargs={'pk': customer.pk})`, keeping URL configurations cleanly separated and avoiding collisions.
