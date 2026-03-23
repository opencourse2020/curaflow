
# CuraFlow Design System

Defines the UI standards for the CuraFlow frontend.

Goal: create a premium, calm, professional SaaS interface suitable for healthcare and wellness providers.

## Core Principles

Clarity over decoration.  
Interfaces must prioritize readability and usability.

Calm visual tone appropriate for health technology.

Operational UX that supports monitoring and decision making.

## Color System

Primary: #0f766e  
Primary Soft: #ccfbf1  
Accent: #14b8a6

Neutral colors:

Background: #f8fafc  
Surface: #ffffff  
Border: #e2e8f0  
Text: #0f172a  
Muted Text: #64748b

Feedback colors:

Success: #16a34a  
Warning: #f59e0b  
Error: #ef4444  
Info: #3b82f6

## Typography

Font stack:

Inter  
system-ui  
Segoe UI  
Roboto

Hierarchy:

H1 – Page title (~28–32px)  
H2 – Section title (~20–24px)  
H3 – Card title (~16–18px)  
Body text (~14–16px)

## Spacing System

Use an 8px grid.

Allowed spacing values:
4px  
8px  
16px  
24px  
32px  
48px  
64px

Example:
Card padding: 24px

## Layout Structure

Sidebar (left)  
Header (top)  
Main content area

Sidebar navigation:
Dashboard  
Customers  
Programs  
Services  
Tracking  
Analytics  
Settings

## Cards

Primary layout unit.

Style:
background: white  
border-radius: 10–12px  
padding: 24px  
border: 1px solid #e2e8f0

Use subtle shadows.

## Buttons

Primary button:
background: primary color  
text: white  
border-radius: 8px  
padding: 8px 16px

Secondary button:
neutral background with border.

Ghost button:
minimal styling for subtle actions.

## Badges

Used for status:
Active  
Paused  
Completed  
Risk  
Low Adherence

Style:
small, rounded, soft background.

## Tables

Used for operational data:
- customer lists
- sessions
- services

Tables should support search, filters, sorting.

## Forms

Forms should be clear and grouped logically.

Each field includes:
- label
- input
- optional hint
- validation message

## Alerts

Types:
Info  
Warning  
Error  
Success

Alerts include:
icon, title, description, optional action.

## Charts

Charts appear inside card containers.

Examples:
adherence trends  
session completion  
program outcomes

## Icons

Use minimal icon styles similar to:
Heroicons or Feather.

## Responsiveness

Rules:
- sidebar collapses on mobile
- cards stack vertically
- tables scroll horizontally

## Page Structure

Page Title  
Page Description

Section  
  Card  
  Card

Section  
  Table or Chart

## Design Checklist

Ensure:
- spacing follows 8px grid
- cards consistent
- colors match palette
- typography hierarchy respected
- UI feels calm and professional
