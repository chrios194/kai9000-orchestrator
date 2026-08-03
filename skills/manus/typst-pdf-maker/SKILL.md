---
name: typst-pdf-maker
description: Generate professional PDF documents with Typst. For reports, papers, resumes, mathematical typesetting, and precise layouts.
---

# Typst PDF Maker

## Overview
Профессиональная PDF-генерация через Typst. 30+ шаблонов (resumes, reports, papers, invoices).

## Workflow
1. `plan_document.py` — create deterministic build plan from manifest
2. `prepare_document.py` — prepare Typst project from assets
3. `generate_pdf.py` — compile Typst to PDF
4. `verify_pdf.py` — deterministic PDF checks
5. `render_review.py` — render pages for visual review

## Routing Catalog
`references/routing-catalog.json` — 30+ templates with hard/soft signals, conflict groups.
Categories: resumes, scientific papers, invoices, presentations, reports, letters.
