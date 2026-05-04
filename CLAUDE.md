# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

A Streamlit web app for Chilean companies that:
1. Accepts PDF quotations as input
2. Extracts structured data (products, prices, vendor info, totals) via regex
3. Generates formal Purchase Order (Orden de Compra) PDFs using ReportLab

The UI is in Spanish; prices use Chilean format (dots for thousands, e.g. `1.234.567`).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app (opens at http://localhost:8501)
streamlit run app.py
```

No test suite exists. Validate by running the app and uploading a real quotation PDF.

## Architecture

**Data flow:** PDF upload → text extraction → regex parsing → user review → PDF generation → browser download

**Two main files:**

- `app.py` — Streamlit UI. Handles file upload, PDF preview (via PyMuPDF/fitz), company selector, OC number input, and persists the last used OC number to `datos_oc.json`.
- `extract_pdf_data.py` — All logic: `extract_text_from_pdf()` reads text with PyPDF2; `extract_all_data()` orchestrates multiple regex extractors for vendor info, product lines, and totals; `crear_orden_compra_pdf()` builds the output PDF with ReportLab including logo (`imagenes/logo.png`) and signature (`imagenes/firma.png`).

**Persistence:** `datos_oc.json` stores the last generated OC number between sessions.

**Hardcoded data:**
- Two buying companies (selectable in UI): *VICTOR HUGO ALMONACID ULLOA* and *INGENIERIA Y CONSTRUCCION ALMONACID LIMITADA*
- Quotation source assumed to be EASY RETAIL S.A.

## Key Implementation Notes

- Product extraction uses `extract_productos_mejorado()` with multiple fallback regex patterns — when extraction fails, add/adjust patterns there first.
- Images (logo, firma) are optional; the code checks for existence before embedding.
- The dev container (`.devcontainer/devcontainer.json`) targets Python 3.11 and auto-installs requirements on startup.
