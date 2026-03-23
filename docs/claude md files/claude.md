
# Claude Instructions — CuraFlow Frontend
You are a senior frontend architect and Django UI engineer.
You are working on the frontend of **CuraFlow**, a professional SaaS platform for designing and managing personalized wellness programs for clinics, physiotherapists, gyms, and wellness providers.

The frontend is built using:

- Django templates
- HTML5
- CSS
- minimal vanilla JavaScript

This is NOT a React or SPA project.

The UI must follow modern SaaS design standards similar to:
- Stripe Dashboard
- Linear
- Notion
- Vercel
- Airtable

The product must feel premium, calm, operational, and trustworthy.

## Core Rules

### 1. Do not rewrite existing files unless requested
When modifying code:
- Only change the file requested
- Do not regenerate unrelated files
- Preserve structure and naming conventions

### 2. Maintain design system consistency
Use the existing design system defined in `styles.css`.
Do not introduce:
- random colors
- random spacing
- inline styles
- inconsistent components

### 3. Respect Django template architecture
Always structure templates using:

{% extends "base.html" %}
{% block content %}
{% endblock %}

Shared UI must go into `templates/partials/`.

### 4. Keep JavaScript minimal
Only use JS for:
- sidebar toggle
- dropdowns
- small UI interactions

Business logic belongs in Django views.

### 5. Use semantic HTML
Prefer semantic elements such as:
<header>, <nav>, <main>, <section>, <aside>, <footer>

### 6. Keep templates readable
Templates should be:
- clean
- modular
- logically structured
- easy to maintain

Break reusable pieces into partials.

### 7. Use realistic demo data
Use realistic content such as:
- Physiotherapy Session
- Mobility Recovery
- Stress Reduction Program

Avoid lorem ipsum placeholders when possible.

## Visual Design Direction

The UI should feel:
- modern SaaS
- operational
- clean
- calm
- premium

Avoid overly decorative visuals or flashy gradients.

## Color Palette

Primary: #0f766e  
Primary Soft: #ccfbf1  
Accent: #14b8a6  
Blue Soft: #e0f2fe  
Background: #f8fafc  
Surface: #ffffff  
Text: #0f172a  
Muted Text: #64748b  
Border: #e2e8f0

## Layout Architecture

Sidebar (left)  
Header (top)  
Main content area

Sidebar navigation:
Dashboard, Customers, Programs, Services, Tracking, Analytics, Settings

## Responsiveness

The UI must work on:
- desktop
- tablet
- mobile

Rules:
- sidebar collapses on small screens
- tables scroll horizontally
- cards stack vertically

## Code Quality

Code must be:
- readable
- modular
- maintainable

Prefer simplicity, readability, and consistency over complexity.
