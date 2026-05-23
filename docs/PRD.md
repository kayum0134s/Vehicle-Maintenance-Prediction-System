# Product Requirements Document (PRD)

## Vehicle Maintenance Prediction System (VMPS)

---

| Field            | Details                                     |
|------------------|---------------------------------------------|
| **Document ID**  | VMPS-PRD-001                                |
| **Version**      | 1.0.0                                       |
| **Status**       | Final                                       |
| **Created**      | 2026-05-15                                  |
| **Author**       | Sameer                                      |
| **Product Name** | Vehicle Maintenance Prediction System (VMPS)|

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Objectives](#3-goals--objectives)
4. [Target Users](#4-target-users)
5. [User Stories](#5-user-stories)
6. [Feature Requirements](#6-feature-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [User Interface Requirements](#8-user-interface-requirements)
9. [Out of Scope](#9-out-of-scope)
10. [Success Metrics](#10-success-metrics)
11. [Timeline & Milestones](#11-timeline--milestones)

---

## 1. Executive Summary

The **Vehicle Maintenance Prediction System (VMPS)** is an AI-powered web platform that enables vehicle fleet operators and individual car owners to proactively manage vehicle health and maintenance schedules. By inputting live or historical sensor telemetry (engine temperature, oil quality, tire pressure, battery health, brake condition, and fuel efficiency), VMPS applies a multi-model machine learning ensemble to generate a real-time **Health Score**, **Risk Classification**, **Failure Component Detection**, and **Actionable Maintenance Recommendations** — all presented through a premium cybernetic glassmorphism dashboard.

The product's core value proposition is the shift from **reactive maintenance** (fixing what has already broken) to **predictive maintenance** (acting before a failure occurs), reducing repair costs by up to 40% and preventing vehicle downtime.

---

## 2. Problem Statement

### Current Pain Points

| Pain Point | Impact |
|---|---|
| Unscheduled vehicle breakdowns | High towing/repair costs, lost productivity |
| Manual inspection-based maintenance | Inconsistent, human-error prone |
| No consolidated health visibility across a fleet | Missed early warning signs |
| Reactive-only service culture | 40–60% higher lifetime repair costs |
| No digital record of maintenance history | Difficulty tracking degradation trends |

Fleet operators and private owners lack an affordable, intelligent, and unified tool to monitor multiple vehicles and be alerted to impending failures before they become expensive emergencies.

---

## 3. Goals & Objectives

### Primary Goals

- **G1 — Predictive Intelligence**: Provide ML-driven failure probability, health scoring, and urgency classification for any vehicle.
- **G2 — Unified Dashboard**: Offer a single-pane view of fleet-wide health, risk distribution, and active alerts.
- **G3 — Actionable Recommendations**: Translate AI predictions into concrete, costed maintenance actions.
- **G4 — Historical Trends**: Surface 12-month rolling health trends for each vehicle via interactive charts.
- **G5 — Report Generation**: Allow users to export per-vehicle diagnostic reports as downloadable PDFs.

### Secondary Goals

- Provide a built-in AI chatbot for quick maintenance Q&A.
- Enable secure multi-user access through registered accounts.
- Offer an intuitive vehicle registration and editing workflow.

---

## 4. Target Users

### Primary: Fleet Manager
- Manages 4–50 vehicles (commercial transport, logistics, rental)
- Needs consolidated risk overview and alerting
- Values cost savings and downtime reduction

### Secondary: Individual Vehicle Owner
- Owns 1–3 vehicles (personal/family)
- Wants simple, non-technical health summary
- Motivated by preventing expensive repairs

### Tertiary: Automotive Service Technician
- Uses VMPS to pre-assess vehicles before physical inspection
- Needs detailed component-level breakdown and cost estimates

---

## 5. User Stories

| ID | As a… | I want to… | So that… |
|----|--------|------------|----------|
| US-01 | Fleet manager | Register and log in securely | My vehicle data is private |
| US-02 | Fleet manager | Add multiple vehicles with telemetry data | I can track all assets in one place |
| US-03 | Fleet manager | See a dashboard overview of fleet health | I can prioritize which vehicles need attention |
| US-04 | Vehicle owner | Run an AI health analysis on my car | I know what maintenance is needed |
| US-05 | Vehicle owner | Receive urgency-rated alerts | I know how quickly I need to act |
| US-06 | Fleet manager | View historical health trend charts | I can see if a vehicle is degrading over time |
| US-07 | Vehicle owner | Download a PDF maintenance report | I have documentation for my service centre |
| US-08 | Technician | See which specific component is at risk | I know where to focus my physical inspection |
| US-09 | Any user | Ask the chatbot maintenance questions | I get quick guidance without leaving the app |
| US-10 | Fleet manager | Delete vehicles no longer in service | My fleet list stays accurate |

---

## 6. Feature Requirements

### F1 — Authentication Module

| ID | Requirement | Priority |
|----|-------------|----------|
| F1.1 | User registration with username, email, and password | Must Have |
| F1.2 | Secure login with session management | Must Have |
| F1.3 | Password hashing using Werkzeug (PBKDF2/SHA-256) | Must Have |
| F1.4 | Logout with full session clearance | Must Have |
| F1.5 | Redirect unauthenticated users to login page | Must Have |

---

### F2 — Vehicle Management

| ID | Requirement | Priority |
|----|-------------|----------|
| F2.1 | Add vehicle with: number, model, manufacturer, mileage, engine temp, oil quality, tire pressure, brake condition, battery health, fuel efficiency, service history, last service date | Must Have |
| F2.2 | Edit vehicle telemetry fields | Must Have |
| F2.3 | Delete vehicle (cascading removal of predictions and alerts) | Must Have |
| F2.4 | List all vehicles belonging to authenticated user | Must Have |
| F2.5 | Vehicle cards showing latest health score and risk badge | Must Have |

---

### F3 — ML Prediction Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| F3.1 | Compute overall Vehicle Health Score (0–100) | Must Have |
| F3.2 | Classify maintenance requirement (YES / NO) | Must Have |
| F3.3 | Assign Risk Level: LOW / MEDIUM / HIGH / CRITICAL | Must Have |
| F3.4 | Assign Service Urgency: LOW / MEDIUM / HIGH / CRITICAL | Must Have |
| F3.5 | Identify the primary at-risk component (Engine, Brakes, Battery, Tires, Oil) | Must Have |
| F3.6 | Generate costed, prioritised maintenance recommendations | Must Have |
| F3.7 | Compute estimated total repair cost (USD) | Must Have |
| F3.8 | Report prediction model confidence/accuracy (%) | Must Have |
| F3.9 | Auto-trigger prediction when a vehicle is added | Must Have |
| F3.10 | Allow re-analysis of existing vehicles on demand | Should Have |

---

### F4 — Dashboard & Analytics

| ID | Requirement | Priority |
|----|-------------|----------|
| F4.1 | KPI tiles: Total Vehicles, Average Fleet Health, Critical Alerts, Healthy Vehicles | Must Have |
| F4.2 | 12-month rolling health trend line chart (Chart.js) | Must Have |
| F4.3 | Risk distribution doughnut chart (LOW / MEDIUM / HIGH / CRITICAL) | Must Have |
| F4.4 | Per-vehicle health gauges (animated radial) | Must Have |
| F4.5 | Real-time alert feed with severity badges | Must Have |
| F4.6 | Alert dismissal (mark as read) | Should Have |

---

### F5 — PDF Report Export

| ID | Requirement | Priority |
|----|-------------|----------|
| F5.1 | Generate per-vehicle diagnostic PDF using ReportLab | Must Have |
| F5.2 | PDF includes: vehicle info table, prediction results, recommendations | Must Have |
| F5.3 | Report auto-downloads with filename `VMPS_Report_<VehicleNumber>.pdf` | Must Have |

---

### F6 — AI Chatbot

| ID | Requirement | Priority |
|----|-------------|----------|
| F6.1 | Keyword-matching chatbot for maintenance queries | Should Have |
| F6.2 | Topics: oil, brakes, battery, tires, engine, fuel, service schedules, costs, emergencies | Should Have |
| F6.3 | Response includes timestamp | Should Have |

---

### F7 — Demo Data Seeding

| ID | Requirement | Priority |
|----|-------------|----------|
| F7.1 | Pre-seed 1 demo user (`admin@vmps.ai`) on first launch | Must Have |
| F7.2 | Pre-seed 4 representative vehicles (Tesla, BMW, Ford, Honda) with varied health profiles | Must Have |
| F7.3 | Auto-generate predictions and alerts for seeded vehicles | Must Have |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Dashboard loads within 2 seconds on local host; ML prediction completes < 500 ms |
| **Security** | Passwords stored as hashed values (never plain text); session-based auth with CSRF-safe cookies |
| **Scalability** | SQLite suitable for ≤ 500 vehicles; designed for easy migration to PostgreSQL |
| **Availability** | Runs reliably on Python 3.10+ / Flask dev server; production deployment via Gunicorn supported |
| **Maintainability** | Modular Flask Blueprint architecture; models, routes, and templates separated |
| **Usability** | Responsive design; all critical actions accessible within 2 clicks |
| **Cross-browser** | Tested on Chrome 120+, Firefox 120+, Edge 120+ |
| **Accessibility** | Semantic HTML5 elements, descriptive alt texts, keyboard navigable |

---

## 8. User Interface Requirements

| Requirement | Detail |
|-------------|--------|
| **Design Language** | Cybernetic glassmorphism — dark background (`#0a0f1e`), frosted-glass cards, neon accent colours (`#00d4ff`, `#8b5cf6`) |
| **Typography** | Primary: Orbitron (headings); Secondary: Rajdhani (body) — loaded via Google Fonts |
| **Animations** | Particle canvas background, glitch text effects, pulsing holographic borders |
| **Charts** | Chart.js — Line (health trend), Doughnut (risk distribution), custom gauge components |
| **Responsive** | Full desktop (1280px+); gracefully degrades on tablet; not optimised for mobile |
| **Login Page** | Full-screen holographic login; form validation; auto-redirect if session active |
| **Dashboard** | Split layout: left panel (vehicle form + vehicle list), right panel (analytics + alerts + chatbot) |

---

## 9. Out of Scope

The following features are explicitly **not** in v1.0:

- Real-time OBD-II hardware sensor integration
- Push notifications (email / SMS)
- Mobile native application (iOS / Android)
- Multi-tenant organisation management
- Payment processing for service bookings
- Live GPS vehicle tracking
- Integration with third-party repair shop APIs
- Role-based access control (Admin vs. Read-only)

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| ML Health Score accuracy (vs. rule-based ground truth) | ≥ 90% |
| Time to generate prediction | < 500 ms |
| Time to generate PDF report | < 3 seconds |
| Dashboard load time | < 2 seconds |
| User can complete: register → add vehicle → get prediction | < 3 minutes |
| Zero unhandled server errors during demo walkthrough | 100% |

---

## 11. Timeline & Milestones

| Phase | Milestone | Status |
|-------|-----------|--------|
| 1 | Core ML engine (training, prediction pipeline) | ✅ Complete |
| 2 | Flask REST API with all CRUD routes | ✅ Complete |
| 3 | SQLAlchemy data models (User, Vehicle, Prediction, Alert) | ✅ Complete |
| 4 | Authentication (register/login/logout) | ✅ Complete |
| 5 | Glassmorphism dashboard frontend | ✅ Complete |
| 6 | Chart.js analytics integration | ✅ Complete |
| 7 | PDF report generation (ReportLab) | ✅ Complete |
| 8 | AI chatbot module | ✅ Complete |
| 9 | Demo data seeding | ✅ Complete |
| 10 | Documentation (PRD + TRD) | ✅ Complete |

---

*End of Product Requirements Document*
