# Implementation Plan: Dashboard Web para Verificación de Pagos y Auditoría (Feature 002)

**Branch**: `002-verification-dashboard` | **Date**: 2026-10-24 | **Spec**: [specs/002-verification-dashboard/spec.md](file:///home/claude/Workspace/Proyectos/VeriFact/specs/002-verification-dashboard/spec.md)

---

## Summary

Desarrollo e integración de un Dashboard Web interactivo servido nativamente por FastAPI:
1. Endpoints complementarios de API:
   - `GET /api/v1/receipts`: Historial de comprobantes con ordenamiento y filtros.
   - `GET /api/v1/orders`: Listado de órdenes con filtro por estado (`PENDING`, `PAID`).
   - `POST /api/v1/orders/quick`: Generación de órdenes rápidas para agilizar pruebas en caja.
2. Single Page Application (SPA) en `src/static/`:
   - Pestaña 1: Carga drag-and-drop de comprobantes, preview de imagen, vinculación a orden y tarjeta de resultado en tiempo real.
   - Pestaña 2: Tabla reactiva de auditoría de transacciones con búsqueda en vivo, badges por banco (Nequi, Daviplata, Bancolombia, Bre-B, DIAN) y filtros por estado.
3. Despliegue unificado: Cero contenedores adicionales, servido directamente en el mismo puerto `8000/5020` y dominio `https://verifact.jhojan.cloud`.

---

## Technical Context

- **Frontend Tech**: HTML5 semántico + Tailwind CSS (v3 CDN) + Lucide Icons + JavaScript Vanilla moderno (async/await, sin framework pesado).
- **Backend Tech**: FastAPI + `StaticFiles` + SQLAlchemy 2.0 / SQLModel.
- **Testing**: `pytest` con `AsyncClient` para los nuevos endpoints de listado y ruta estática.
- **Rendimiento**: Peso total < 100 KB, tiempo de carga < 150 ms en ARM64.

---

## Constitution Check

- [x] **Principio I (Determinista & Local):** La UI se ejecuta enteramente en el cliente y consume los endpoints deterministas locales.
- [x] **Principio II (Backend-First):** La UI consume los contratos REST formales de FastAPI.
- [x] **Principio III (TDD):** Tests de integración para `GET /api/v1/receipts` y `GET /api/v1/orders`.
- [x] **Principio V (Persistencia):** Los listados consultan eficientemente la base de datos SQLite WAL con índices.

---

## Project Structure

```text
VeriFact/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── orders.py             # Añadir GET /orders (list) y POST /orders/quick
│   │       └── receipts.py           # Añadir GET /receipts (list)
│   ├── static/
│   │   ├── index.html                # Single Page Application (Pestañas, Formularios, Tablas)
│   │   ├── app.js                    # Lógica interactiva de tabs, upload, preview, fetch y filtros
│   │   └── style.css                 # Estilos complementarios y animaciones
│   └── main.py                       # Montar static files en / y servir index.html
└── tests/
    └── integration/
        └── test_dashboard_api.py     # Tests para endpoints de listado y UI
```
