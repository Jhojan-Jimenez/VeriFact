# Implementation Plan: Ingesta y Verificación de Comprobantes Bancarios (Feature 001)

**Branch**: `001-receipt-verification` | **Date**: 2026-10-24 | **Spec**: [specs/001-receipt-verification/spec.md](file:///home/claude/Workspace/Proyectos/VeriFact/specs/001-receipt-verification/spec.md)

---

## Summary

Implementación del núcleo de verificación determinista de pagos y trazabilidad de inventario:
1. Servicio de ingestión multipart para imágenes y PDFs de comprobantes de pago.
2. Pipeline de visión computacional local (`pyzbar` para códigos QR + preprocesamiento OpenCV + `pytesseract` con español).
3. Extractores especializados por entidad financiera (Nequi, Daviplata, Bancolombia, Bre-B, DIAN).
4. Verificación antifraude: deduplicación estricta por hash SHA-256 e índice único de referencia bancaria.
5. Conciliación contra orden de venta y decremento atómico de inventario en SQLite con modo WAL.
6. Especificación de contenedor Docker optimizado para arquitectura ARM64 (Oracle Cloud) desplegable vía Coolify v4 con proxy inverso Traefik.

---

## Technical Context

- **Lenguaje & Runtime**: Python 3.12+ (gestionado con `uv`).
- **Framework Web**: FastAPI 0.115+ con validación estricta en **Pydantic v2**.
- **Servidor ASGI**: Uvicorn con `uvloop` y `httptools`.
- **Motor de Visión & OCR**:
  - `opencv-python-headless`: Preprocesamiento morfológico (deskew, escalado, binarización Otsu).
  - `pyzbar`: Decodificación directa y de alto rendimiento de códigos QR matriciales.
  - `pytesseract` (Tesseract 5.x) con diccionario de idioma español (`tesseract-ocr-spa`).
- **Persistencia**: SQLite con **Write-Ahead Logging (WAL)** y aislamiento serializable vía SQLAlchemy 2.0 / SQLModel. Migrable a PostgreSQL 16 sin cambios de código.
- **Testing**: `pytest`, `pytest-asyncio`, `httpx` (para TestClient asíncrono) y fixtures de imágenes bancarias sintéticas.
- **Plataforma de Despliegue**:
  - **Servidor Destino**: Oracle Cloud Always On VM (`150.136.63.103`).
  - **Arquitectura de CPU**: ARM64 (Ampere Altra 4 OCPUs, 24 GB RAM).
  - **Orquestador**: Coolify v4 + Traefik Reverse Proxy + Let's Encrypt TLS automático.

---

## 📊 Estimación y Presupuesto de Recursos en la VM (ARM64)

### Estado Actual de la VM (Octubre 2026)
* **Memoria Total:** 23 GiB
* **Memoria en Uso Actual:** 5.0 GiB (Vocero CRM, Actual Budget, n8n, TalentMatch, Vaultwarden, etc.)
* **Memoria Disponible:** **~18 GiB**
* **Disco Libre:** **~13 GB** en `/dev/sda1`

### Huella de Recursos Proyectada para VeriFact:

| Componente | Estado Idle (Reposo) | Pico de Carga (5 comprobantes simultáneos) | Límite Recomendado en Coolify |
| :--- | :--- | :--- | :--- |
| **RAM del Contenedor** | **~85 MB - 110 MB** | **~250 MB - 350 MB** | `mem_limit: 512m` (Reserva: `128m`) |
| **Uso de CPU** | `< 0.2%` (1 worker Uvicorn) | Ráfaga de `40% - 60%` de 1 OCPU durante OCR (~400ms) | `cpus: 1.0` (o sin límite estricto) |
| **Almacenamiento Docker** | **~320 MB** (Imagen Debian Slim con Tesseract + OpenCV) | Variable según retención de imágenes | Volumen montado `/data/verifact.db` |
| **Almacenamiento BD** | `< 1 MB` inicial | ~25 MB por cada 10,000 transacciones completas | Mínimo impacto |

> [!NOTE]
> La huella de **VeriFact** es sumamente ligera (~1.5% de la RAM disponible en tu VM de 24 GB). No afectará en absoluto el rendimiento de n8n, Vocero CRM ni Actual Budget.

---

## Constitution Check

*GATE: Todas las decisiones respetan la Constitución v1.0.0:*
- [x] **Principio I (Determinista & Local):** Se usan `opencv-python-headless`, `pyzbar` y `pytesseract`. Cero consumo de APIs externas pagadas.
- [x] **Principio II (Backend-First):** API REST con FastAPI y Pydantic v2.
- [x] **Principio III (TDD Obligatorio):** Fixtures anonimizados para Nequi, Daviplata, Bancolombia, Bre-B y DIAN en `tests/fixtures/`.
- [x] **Principio IV (Antifraude & Deduplicación):** Hash SHA-256 de imagen + índice único en `(bank_platform, reference_number)`.
- [x] **Principio V (Persistencia Desacoplada):** SQLite WAL con SQLAlchemy 2.0 / SQLModel.

---

## Project Structure

```text
VeriFact/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py             # Enrutador principal v1
│   │   │   ├── receipts.py           # POST /receipts/verify, GET /receipts/{id}
│   │   │   ├── orders.py             # POST /orders, GET /orders/{id}
│   │   │   └── inventory.py          # GET /inventory, POST /inventory, GET /inventory/{sku}/history
│   │   └── schemas/
│   │       ├── receipt.py            # Schemas Pydantic (ReceiptVerificationRequest, ReceiptResponse)
│   │       ├── order.py              # Schemas de órdenes e ítems
│   │       └── inventory.py          # Schemas de stock y kardex
│   ├── core/
│   │   ├── config.py                 # Settings vía Pydantic Settings (.env)
│   │   ├── database.py               # Motor SQLAlchemy / SQLite WAL connection pool
│   │   └── exceptions.py             # Excepciones de dominio (AmountMismatch, DuplicateReceipt, etc.)
│   ├── domain/
│   │   └── models.py                 # Entidades SQLModel (Order, OrderItem, PaymentReceipt, InventoryItem, StockMovement)
│   ├── services/
│   │   ├── vision/
│   │   │   ├── preprocessor.py       # Normalización, deskew, escala y binarización Otsu
│   │   │   ├── qr_decoder.py         # Decodificación pyzbar (DIAN, EMVCo)
│   │   │   └── ocr_engine.py         # Motor pytesseract en español
│   │   ├── extractors/
│   │   │   ├── base.py               # Interfaz abstracta BaseReceiptExtractor
│   │   │   ├── nequi.py              # Extractor Nequi (M-XXXX, ¡Listo!, Enviaste)
│   │   │   ├── daviplata.py          # Extractor Daviplata (Aprobación, Monto)
│   │   │   ├── bancolombia.py        # Extractor Bancolombia QR / Transferencia
│   │   │   ├── bre_b.py              # Extractor Bre-B / Transfiya
│   │   │   └── dian_invoice.py       # Extractor Factura Electrónica QR (CUFE)
│   │   ├── verification_service.py   # Lógica central: Hash -> OCR -> Match Orden -> Antifraude
│   │   └── inventory_service.py      # Transacción atómica de stock y registro en Kardex
│   └── main.py                       # Fábrica de la aplicación FastAPI y middleware CORS
├── tests/
│   ├── conftest.py                   # Sesiones de test SQLite in-memory y cliente async
│   ├── fixtures/
│   │   ├── receipts/                 # Imágenes sintéticas y anonimizadas de prueba
│   │   │   ├── nequi_valid.png
│   │   │   ├── bancolombia_valid.png
│   │   │   ├── daviplata_valid.png
│   │   │   └── dian_qr_valid.png
│   ├── unit/
│   │   ├── test_extractors.py        # Tests de regex y extracción por banco
│   │   ├── test_preprocessor.py      # Tests de binarización y deskew
│   │   └── test_inventory.py         # Tests de decremento atómico
│   └── integration/
│       ├── test_receipt_verification_api.py # Test de punta a punta del endpoint
│       └── test_antifraud_deduplication.py  # Test de rechazo 409 por duplicados
├── Dockerfile                        # Multi-stage ARM64 compatible con Tesseract + OpenCV
├── docker-compose.yml                # Configuración local y para Coolify
└── pyproject.toml                    # Dependencias gestionadas con uv
```

---

## 🚢 Estrategia de Despliegue en la VM (Coolify v4 + Docker)

### 1. `Dockerfile` Multi-Stage Optimizado para ARM64:
```dockerfile
FROM python:3.12-slim-bookworm AS base

# Dependencias de sistema de bajo peso
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libzbar0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia de dependencias con uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV DATABASE_URL="sqlite+aiosqlite:////data/verifact.db"

VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Integración con Traefik y Coolify:
* **Subdominio sugerido:** `https://verifact.jhojan.cloud` (o `https://api.verifact.jhojan.cloud`).
* **Volumen persistente:** `verifact_data:/data` para preservar la base de datos SQLite WAL.
* **Healthcheck:** `GET /health` responde `{"status": "healthy", "version": "0.1.0"}`.
