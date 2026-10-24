# Tasks: Dashboard Web para Verificación de Pagos y Auditoría (Feature 002)

**Input**: Design documents from `/specs/002-verification-dashboard/plan.md` and `spec.md`  
**Status**: Completed (`speckit-implement`)

---

## Phase 1: Backend Endpoints for Dashboard

**Purpose**: Habilitar los endpoints necesarios para alimentar el selector de órdenes y la tabla de auditoría

- [x] T001 Implementar endpoint `GET /api/v1/receipts` en `src/api/v1/receipts.py` con ordenamiento descendente y filtro opcional por `status`.
- [x] T002 Implementar endpoint `GET /api/v1/orders` en `src/api/v1/orders.py` con filtro opcional `status=PENDING`.
- [x] T003 Implementar endpoint `POST /api/v1/orders/quick` en `src/api/v1/orders.py` para generación exprés de órdenes.
- [x] T004 Escribir tests de integración en `tests/integration/test_dashboard_endpoints.py` validando los nuevos endpoints.

---

## Phase 2: Frontend SPA Setup & Static Serving

**Purpose**: Crear la estructura de archivos estáticos y montar el middleware en FastAPI

- [x] T005 [P] Crear directorio `src/static/` con `index.html`, `app.js` y `style.css`.
- [x] T006 [P] Configurar en `src/main.py` el montaje de `StaticFiles` y la ruta raíz `GET /` que sirva `index.html`.
- [x] T007 [P] Maquetar el layout principal con Tailwind CSS (Header con logo VeriFact, indicador de salud del backend y barra de navegación de 2 pestañas: "Verificar Pago" y "Historial de Transacciones").

---

## Phase 3: User Story 1 - Pestaña de Verificación & Drag & Drop (Priority: P1) 🎯 MVP

**Goal**: Permitir cargar comprobantes, asociarlos a una orden y recibir veredicto visual inmediato.

- [x] T008 [US1] Implementar selector dinámico de órdenes pendientes que cargue automáticamente de `GET /api/v1/orders?status=PENDING` con modal para "Crear Orden Rápida".
- [x] T009 [US1] Implementar zona de drop interactiva con soporte para arrastrar o hacer clic, previsualización de imagen (JPEG/PNG) y botón de remover.
- [x] T010 [US1] Implementar función async `submitVerification()` que envíe `FormData` a `POST /api/v1/receipts/verify` con spinner de carga durante el OCR.
- [x] T011 [US1] Renderizar tarjeta de resultado con veredicto en tiempo real:
  - Éxito (Badge verde `VERIFIED`, banco, referencia, monto formateado COP, fecha).
  - Error (Alerta roja con badge `REJECTED`, `409 DUPLICATE` o `AMOUNT_MISMATCH` con detalle del fallo).

---

## Phase 4: User Story 2 - Pestaña de Historial de Transacciones y Auditoría (Priority: P1)

**Goal**: Visualizar y filtrar todas las transacciones procesadas.

- [x] T012 [US2] Implementar función async `loadTransactions()` que consulte `GET /api/v1/receipts` y renderice las filas de la tabla.
- [x] T013 [US2] Implementar badges temáticos por banco (Nequi púrpura, Daviplata rojo, Bancolombia amarillo, Bre-B verde, DIAN azul) y badges por estado (`VERIFIED`, `REJECTED`, `DUPLICATE`).
- [x] T014 [US2] Implementar filtros de estado en cliente (`Todos`, `Verificados`, `Rechazados`) y barra de búsqueda reactiva por referencia bancaria o ID de orden.
- [x] T015 [US2] Implementar modal de detalle forense para inspeccionar el hash SHA-256 de la imagen y el texto crudo extraído por OCR.

---

## Phase 5: Verification, Tests & Deployment

- [x] T016 Ejecutar suite de pruebas completa con `pytest` y formateo con `ruff check`.
- [x] T017 Compilar y actualizar el despliegue en la VM de producción (`~/verifact`) y verificar la interfaz en vivo.
