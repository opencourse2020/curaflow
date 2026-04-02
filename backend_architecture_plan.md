# CuraFlow Backend Architecture Plan

## Core Philosophy
1. **Thin Views, Fat Services:** Keep the business logic out of the views and templates. All complex operations should happen in the service layer (`app_name/services/`).
2. **Organization-Scoped by Default:** CuraFlow is a multi-tenant B2B application. By default, all queries and creations must be tightly scoped to the tenant (Organization).
3. **Class-Based Views (CBVs):** Built-in generic CBVs should be the primary building blocks for all server-rendered UI.
4. **DRF Sparingly:** We should only introduce Django Rest Framework for external integrations or where complex client-side interactivity dictates a real API. For 90% of the SaaS, standard view rendering + HTMX (if needed) is preferred.

## Directory Structure Strategy
We organize the project into highly cohesive Django apps reflecting business domains:

```text
curaflow/
├── core/                # Core abstractions, mixins, global base models, utils
│   ├── mixins.py        # Organization and role checking CBV mixins
│   ├── services/        # Service layer base classes and helpers
│   └── models.py        # Organization, Base models
├── profiles/            # User authentication, staff profiles, roles
├── customers/           # End clients, their baseline data, notes
├── programs/            # Program builder, assigned programs to customers
├── services/            # The catalog of offerings (Physio, Nutrition, etc.)
├── tracking/            # Execution, sessions, adherence data
└── metrics/             # Aggregation and analytics calculation (KPIs)
```

## The Service Layer (`/services/`)
Instead of putting business logic in Django signals or `save()` overrides, keep it in explicit service functions.

- `create_customer(organization, data, user)`
- `assign_program_to_customer(customer, program_template, start_date)`
- `calculate_adherence(customer, date_range)`

This makes the business logic easy to unit test and reusable in API views, admin commands, or standard views.

## Query Performance
Always use `.select_related()` for foreign keys and `.prefetch_related()` for reverse relations and many-to-many fields to dodge the N+1 problem. The `OrganizationMixin` sets a baseline, but complex views MUST explicitly optimize queries.
