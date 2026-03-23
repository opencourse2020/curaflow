
# Frontend Rules — CuraFlow

This document defines the architectural and coding rules for the CuraFlow frontend.
Claude must follow these rules when generating or modifying UI code.

CuraFlow is a **professional SaaS platform** used by clinics, physiotherapists, gyms, and wellness providers.
The frontend must be **clean, modular, maintainable, and consistent**.

Technology stack:
- Django templates
- HTML5
- CSS
- minimal vanilla JavaScript

No frontend frameworks (React, Vue, Angular) should be introduced.

------------------------------------------------------------

# 1. File Structure Rules

Templates must follow a clear Django structure.

templates/
    base.html
    dashboard.html
    customers.html
    services.html
    programs.html
    settings.html
    partials/
        sidebar.html
        header.html
        stat_card.html
        alert_card.html
        service_card.html
        progress_widget.html
        timeline_block.html
        table_toolbar.html

static/
    css/
        styles.css
    js/
        app.js

Rules:
- Shared UI elements belong in `partials/`
- Do not duplicate UI across templates
- Pages must extend `base.html`

------------------------------------------------------------

# 2. Template Structure Rules

Every page template must follow this structure:

{% extends "base.html" %}

{% block content %}
    Page content here
{% endblock %}

Rules:
- Do not create full HTML documents for each page
- Only `base.html` should include `<html>`, `<head>`, and `<body>`
- Pages should only define content blocks

------------------------------------------------------------

# 3. Component Reuse Rules

Reusable UI must be implemented as template partials.

Example:

{% include "partials/stat_card.html" %}

Do NOT copy and paste card structures across pages.

Common reusable components include:

- stat cards
- alert cards
- tables
- service cards
- progress widgets
- toolbars

------------------------------------------------------------

# 4. CSS Rules

All styling must live in:

static/css/styles.css

Rules:
- No inline styles
- No `<style>` blocks inside templates
- Use reusable CSS classes

CSS must follow:

- clear section comments
- logical grouping
- consistent naming

Example sections:

Base styles  
Layout  
Sidebar  
Header  
Cards  
Buttons  
Forms  
Tables  
Utilities

------------------------------------------------------------

# 5. Class Naming Conventions

Use predictable class names.

Examples:

.card
.card-header
.card-body
.card-title

.table
.table-row
.table-cell

.btn
.btn-primary
.btn-secondary

.alert
.alert-warning
.alert-error

Avoid cryptic names like:

.x1
.box2
.a-card

------------------------------------------------------------

# 6. Layout Rules

All pages follow the same structure:

Sidebar (left)  
Header (top)  
Main content

Main layout container:

.app-layout
.sidebar
.header
.main-content

Consistency across pages is mandatory.

------------------------------------------------------------

# 7. Spacing Rules

Spacing must follow the **8px system**.

Allowed spacing values:

4px
8px
16px
24px
32px
48px
64px

Do not invent arbitrary spacing values.

------------------------------------------------------------

# 8. JavaScript Rules

JavaScript should be minimal.

Allowed uses:

- sidebar toggle
- dropdown menus
- dismissible alerts
- small UI interactions

Rules:

- JS must live in `static/js/app.js`
- No inline JS inside templates
- Avoid complex client-side logic

Business logic belongs in Django views.

------------------------------------------------------------

# 9. Table Rules

Tables should support operational workflows.

Tables must include:

- readable headers
- hover state
- row actions
- spacing between rows

Optional features:

- search
- filtering
- sorting

Tables must remain readable even with many rows.

------------------------------------------------------------

# 10. Forms Rules

Forms must be structured clearly.

Each input must include:

Label  
Input  
Optional help text  
Error message

Example layout:

.form-group
    label
    input
    small hint text

Avoid dense form layouts.

------------------------------------------------------------

# 11. Page Composition Rules

Each page should follow a clear structure:

Page title  
Page description

Section
    Card
    Card

Section
    Table or chart

Avoid long pages without visual grouping.

------------------------------------------------------------

# 12. Responsiveness Rules

The UI must work on:

Desktop  
Tablet  
Mobile

Responsive rules:

- Sidebar collapses on small screens
- Cards stack vertically
- Tables scroll horizontally
- Forms become single-column

------------------------------------------------------------

# 13. Avoid These Common Mistakes

Do not:

- duplicate UI code
- use inline styles
- introduce random colors
- create inconsistent spacing
- add unnecessary JavaScript libraries
- generate overly complex HTML structures

------------------------------------------------------------

# 14. Code Quality Checklist

Before generating code verify:

- templates extend base.html
- partials are reused properly
- CSS follows naming conventions
- layout matches the design system
- UI elements remain consistent

------------------------------------------------------------

# 15. General Philosophy

The CuraFlow frontend should feel like a **premium SaaS dashboard**.

Design priorities:

clarity  
consistency  
simplicity  
maintainability

If unsure, choose the simpler solution.
