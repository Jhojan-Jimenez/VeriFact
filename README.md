# VeriFact 🧾🔍

> **Verificación y Trazabilidad Inteligente de Facturas y Pagos de Banca Colombiana**  
> Proyecto desarrollado bajo la metodología **Spec-Driven Development (SDD)** con **GitHub Spec Kit** y **Antigravity CLI**.

---

## 🎯 Propósito del Proyecto

Captura, extracción y validación determinista de comprobantes de pago y facturas en Colombia:
- **Lectura Multimodal & OCR:** Comprobantes de Nequi, Daviplata, QR Bancolombia, transferencias Bre-B y Facturación Electrónica DIAN.
- **Verificación de Pagos:** Validación de montos, números de comprobante/referencia, fechas y remitentes para prevenir fraude por comprobantes editados.
- **Trazabilidad & Conciliación:** Registro estructurado de ítems vendidos por transacción.
- **Análisis de Inventarios:** Pipeline de datos para control de stock y proyecciones de venta basadas en transacciones verificadas.

---

## 🏗️ Metodología: Spec-Driven Development (SDD)

Este proyecto está gobernado por **Spec Kit (`github/spec-kit`)** integrado con las habilidades (`skills`) de **Antigravity**:

```
VeriFact/
├── .agents/skills/          # Habilidades SDD para Antigravity CLI/IDE
│   ├── speckit-constitution # Gobernanza y principios innegociables
│   ├── speckit-specify      # Redacción de la especificación funcional
│   ├── speckit-clarify      # Refinamiento y de-risking de ambigüedades
│   ├── speckit-checklist    # Checklist de calidad de requerimientos
│   ├── speckit-plan         # Plan de arquitectura y diseño técnico
│   ├── speckit-tasks        # Desglose de tareas atómicas y verificables
│   ├── speckit-analyze      # Verificación de consistencia cruzada
│   ├── speckit-implement    # Implementación progresiva con tests
│   └── speckit-converge     # Auditoría de completitud y deuda técnica
├── .specify/                # Templates, memoria viva y scripts de workflow
│   ├── memory/
│   │   └── constitution.md  # Constitución técnica del proyecto
│   └── templates/           # Plantillas estándar de spec, plan y tasks
```

---

## 🚀 Flujo de Trabajo en Antigravity CLI

1. **Constitución:** `/speckit-constitution` para formalizar las reglas del stack técnico y seguridad.
2. **Especificar Feature:** `/speckit-specify "Captura de comprobante Nequi vía OCR y verificación de referencia"`
3. **Refinar:** `/speckit-clarify` para resolver casos de esquina (imágenes borrosas, marcas de agua, fraude).
4. **Planificar:** `/speckit-plan` para definir modelos de datos, endpoints y pipelines.
5. **Tareas:** `/speckit-tasks` para generar `tasks.md`.
6. **Implementar:** `/speckit-implement` para ejecutar tarea por tarea con TDD.
