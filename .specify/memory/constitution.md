# VeriFact Constitution

## Core Principles

### I. Deterministic-First & Local-Only Visual Pipeline
Every receipt, invoice, and payment voucher is processed locally using open-source, deterministic computer vision tools (OpenCV, pyzbar, Tesseract OCR). 
- **Zero External API Dependency:** No paid external LLM/Vision APIs in the core pipeline; completely offline-capable and cost-free.
- **Privacy & Security:** Sensitive financial data (account numbers, names, balances) remains strictly on-premise/local.
- **Pre-processing Standard:** Raw images must pass through standardized geometric correction, noise reduction, and adaptive binarization before OCR extraction.

### II. Backend-First API-Driven Architecture
The system core is exposed exclusively as a robust, decoupled REST API built with **Python 3.12+ and FastAPI**.
- Clean separation of concerns: `api` (routes/schemas), `services` (OCR, parsing, inventory), `domain` (business models), and `repositories` (persistence).
- Strict validation with **Pydantic v2** for all inputs and outputs.
- Comprehensive OpenAPI / Swagger documentation out-of-the-box for consumption by web, mobile apps, POS terminals, or WhatsApp bots.

### III. Test-Driven & Fixture-Verified Extraction (TDD Mandatory)
Parser logic and receipt extraction cannot be merged without golden test cases.
- Synthetic and anonymized image fixtures for each supported Colombian banking slip: **Nequi**, **Daviplata**, **QR Bancolombia**, **Bre-B / Transfiya**, and **Facturación Electrónica DIAN**.
- Each slip parser must achieve 100% extraction accuracy on reference numbers, monetary amounts, and timestamps for known test fixtures.
- Test suites must run fast via `pytest` without requiring external network connectivity.

### IV. Idempotency & Anti-Fraud Verification
To prevent fraudulent double-spending or altered receipts:
- **Deduplication:** Every incoming transaction must register a perceptual or cryptographic hash (SHA-256) of the image and an index on `(bank_platform, transaction_reference)`.
- Duplicate attempts must be rejected with deterministic HTTP 409 Conflict and an audit alert.
- **Validation Rules:** Extracted dates must fall within acceptable sliding windows; monetary values must strictly parse as Colombian Pesos (COP integers or precise decimals).

### V. Decoupled Persistence with SQLite WAL (Postgres-Ready)
- Initial database engine is **SQLite with Write-Ahead Logging (WAL)** enabled for zero-config, low latency, and concurrent read capabilities.
- Repository pattern using **SQLAlchemy 2.0 / SQLModel** ensuring zero vendor lock-in, enabling drop-in migration to PostgreSQL 16 by changing only the connection DSN.

---

## Technical Constraints & Standards

1. **Runtime:** Python 3.12+ managed with `uv`.
2. **Web Framework:** FastAPI with async handlers and Pydantic v2 models.
3. **Vision & OCR Stack:**
   - `opencv-python-headless` for image transformations (deskew, thresholding, ROI cropping).
   - `pyzbar` for rapid 2D/QR code decoding.
   - `pytesseract` with Spanish language training data (`spa.traineddata`).
4. **Parser Taxonomy:**
   - Separate extractor strategies under `services/extractors/` for `nequi.py`, `daviplata.py`, `bancolombia_qr.py`, `bre_b.py`, and `dian_qr.py`.
5. **Inventory Traceability:**
   - Transactions must support linking to inventory line items (SKU, description, unit price, quantity) to maintain an audit trail of stock decrements.

---

## Development Workflow & Quality Gates

1. **Format & Quality:** `ruff check` and `ruff format` mandatory on all codebase changes.
2. **Type Safety:** Strict type hints across all function signatures and domain models.
3. **Spec Alignment:** Every new feature must trace back to a corresponding `spec.md` under the `.specify/` or `specs/` directory before coding.

---

## Governance

- This Constitution is the authoritative operational baseline for the VeriFact repository.
- Changes to core architecture, supported banks, or storage backends require an explicit amendment to this document.
- In case of ambiguity during implementation, priority is given to **Data Integrity > Local Determinism > Processing Speed > Feature Breadth**.

**Version**: 1.0.0 | **Ratified**: 2026-10-24 | **Last Amended**: 2026-10-24
