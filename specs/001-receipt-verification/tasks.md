# Tasks: Ingesta y Verificación de Comprobantes Bancarios (Feature 001)

**Input**: Design documents from `/specs/001-receipt-verification/plan.md` and `spec.md`  
**Status**: Ready for Implementation (`speckit-implement`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del entorno Python, dependencias de visión y estructura base

- [ ] T001 Inicializar `pyproject.toml` con dependencias base vía `uv` (`fastapi`, `uvicorn`, `sqlmodel`, `aiosqlite`, `pydantic-settings`, `opencv-python-headless`, `pyzbar`, `pytesseract`, `python-multipart`, `pytest`, `httpx`).
- [ ] T002 Crear la estructura de directorios en `src/` (`api/v1`, `core`, `domain`, `services/vision`, `services/extractors`) y `tests/` (`fixtures`, `unit`, `integration`).
- [ ] T003 [P] Configurar `ruff.toml` con reglas estrictas de linting y formateo para Python 3.12.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura de persistencia SQLite WAL y entidades transversales de dominio

- [ ] T004 Configurar `src/core/config.py` con `pydantic-settings` para variables de entorno (`DATABASE_URL`, `TOLERANCE_MINUTES`, `DEBUG`).
- [ ] T005 Configurar `src/core/database.py` con motor async SQLAlchemy/SQLModel y habilitación de `PRAGMA journal_mode=WAL;`.
- [ ] T006 Crear modelos de dominio SQLModel en `src/domain/models.py` (`Order`, `OrderItem`, `PaymentReceipt`, `InventoryItem`, `StockMovement`).
- [ ] T007 [P] Implementar excepciones de negocio en `src/core/exceptions.py` (`ReceiptDuplicateError`, `AmountMismatchError`, `ExpiredReceiptError`, `ExtractionFailedError`).
- [ ] T008 [P] Configurar `src/main.py` con middleware CORS, exception handlers y endpoint de salud `GET /health`.

**Checkpoint**: Base de datos, modelos y app base listos para pruebas unitarias.

---

## Phase 3: User Story 1 - Extracción Determinista Visual (Priority: P1) 🎯 MVP

**Goal**: Procesar imágenes de comprobantes y extraer con precisión banco, referencia, monto en COP y fecha.

### Tests para User Story 1 (TDD)
- [ ] T009 [P] [US1] Crear fixtures sintéticos de prueba en `tests/fixtures/receipts/` (`nequi_sample.png`, `daviplata_sample.png`, `bancolombia_qr.png`).
- [ ] T010 [P] [US1] Escribir tests unitarios en `tests/unit/test_extractors.py` que verifiquen el parsing de regex y extracción de campos por banco (deben fallar inicialmente).

### Implementación para User Story 1
- [ ] T011 [P] [US1] Implementar `src/services/vision/preprocessor.py` con OpenCV (escala de grises, corrección de rotación/deskew, binarización adaptativa Otsu).
- [ ] T012 [P] [US1] Implementar `src/services/vision/qr_decoder.py` usando `pyzbar` para extracción prioritaria de códigos QR (DIAN CUFE y cadenas EMVCo).
- [ ] T013 [P] [US1] Implementar `src/services/vision/ocr_engine.py` como wrapper determinista de `pytesseract` en español.
- [ ] T014 [US1] Implementar extractores especializados en `src/services/extractors/`:
  - `nequi.py` (anclas *¡Listo!*, *Enviaste*, referencia `M\d+`).
  - `daviplata.py` (anclas *Transacción exitosa*, *Aprobación*).
  - `bancolombia.py` (anclas *Comprobante No.*, *Transferencia exitosa*).
  - `dian_invoice.py` (decodificación de URL y CUFE).
- [ ] T015 [US1] Implementar `VisionExtractorService` en `src/services/vision_service.py` que orqueste: QR primero -> Fallback OCR -> Selector de extractor por banco.

**Checkpoint**: Extracción de datos financieros 100% funcional y verificada con tests unitarios.

---

## Phase 4: User Story 2 - Conciliación contra Órdenes de Venta (Priority: P1)

**Goal**: Validar el pago contra una orden específica (`order_id`) comprobando monto exacto y ventana temporal.

### Tests para User Story 2 (TDD)
- [ ] T016 [P] [US2] Escribir tests de integración en `tests/integration/test_order_reconciliation.py` validando coincidencia de monto y rechazo por monto disparejo.

### Implementación para User Story 2
- [ ] T017 [P] [US2] Crear endpoints de órdenes en `src/api/v1/orders.py` (`POST /api/v1/orders` para crear orden y `GET /api/v1/orders/{id}`).
- [ ] T018 [US2] Implementar `src/services/verification_service.py` para contrastar monto del comprobante vs total de la orden y fecha del comprobante vs creación de la orden.
- [ ] T019 [US2] Implementar endpoint `POST /api/v1/receipts/verify` en `src/api/v1/receipts.py` que reciba multipart (imagen + `order_id`) y retorne el veredicto de validación.

**Checkpoint**: Órdenes se crean y se marcan como `PAID` deterministamente al subir el comprobante correcto.

---

## Phase 5: User Story 3 - Deduplicación y Protección Antifraude (Priority: P2)

**Goal**: Bloquear intentos de doble uso de un mismo pantallazo o referencia bancaria con HTTP 409 Conflict.

### Tests para User Story 3 (TDD)
- [ ] T020 [P] [US3] Escribir tests en `tests/integration/test_antifraud_deduplication.py` intentando enviar el mismo comprobante para dos órdenes distintas.

### Implementación para User Story 3
- [ ] T021 [US3] Implementar cálculo de hash SHA-256 de la imagen cruda en `src/services/verification_service.py`.
- [ ] T022 [US3] Agregar verificación de existencia previa por `image_sha256` y por `(bank_platform, reference_number)` antes de procesar la orden.
- [ ] T023 [US3] Configurar respuesta HTTP 409 Conflict con payload estructurado indicando la orden original donde ya fue usado el comprobante.

**Checkpoint**: Blindaje antifraude 100% activo y probado.

---

## Phase 6: User Story 4 - Decremento Atómico de Inventario y Kardex (Priority: P2)

**Goal**: Descontar existencias de stock de forma atómica cuando una orden pase a estado `PAID`.

### Tests para User Story 4 (TDD)
- [ ] T024 [P] [US4] Escribir tests unitarios en `tests/unit/test_inventory_atomic.py` probando decremento de stock y rollback ante stock insuficiente.

### Implementación para User Story 4
- [ ] T025 [P] [US4] Implementar endpoints de inventario en `src/api/v1/inventory.py` (`POST /api/v1/inventory` para crear productos y `GET /api/v1/inventory/{sku}/history`).
- [ ] T026 [US4] Implementar `src/services/inventory_service.py` para decrementar stock y registrar registros `StockMovement` dentro de la transacción de la orden.
- [ ] T027 [US4] Integrar el servicio de inventario en el flujo de `verification_service.py` bajo un mismo bloque transaccional atómico.

**Checkpoint**: Venta, pago e inventario perfectamente sincronizados y auditables.

---

## Phase 7: Deployment & Containerization (OCI ARM64 + Coolify)

**Purpose**: Empaquetado en contenedor Docker multi-stage optimizado para la VM Ampere Altra

- [ ] T028 Crear `Dockerfile` optimizado con Debian Slim, `tesseract-ocr`, `tesseract-ocr-spa`, `libzbar0` y `uv`.
- [ ] T029 Crear `docker-compose.yml` con configuración de volumen persistente `/data` y etiquetas de Traefik para Coolify v4.
- [ ] T030 [P] Crear script de verificación y smoke-test `scripts/smoke_test.sh` para probar los endpoints en local y en el contenedor.
