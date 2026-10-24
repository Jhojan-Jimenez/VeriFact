# Feature Specification: Interfaz Web para Verificación de Pagos y Auditoría de Transacciones (Feature 002)

**Feature Branch**: `002-verification-dashboard`  
**Created**: 2026-10-24  
**Status**: Ready for Review (Draft)  
**Input**: Frontend web interactivo para subir comprobantes de pago bancarios, reconciliación en tiempo real y panel/tabla de transacciones con filtros de verificación.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Carga y Verificación Interactiva de Comprobantes (Priority: P1) 🎯 MVP

Como cajero, comerciante o auditor, quiero una interfaz visual donde pueda seleccionar una orden pendiente y cargar la imagen de un comprobante de pago (drag & drop o selector de archivos) para recibir en tiempo real el veredicto de validación (Banco, Monto, Referencia y Estado) sin usar herramientas como Postman o cURL.

**Why this priority**: Es la interfaz operativa primaria. Permite a cualquier usuario validar transacciones en punto de venta de manera inmediata y sin fricción.

**Independent Test**:
Abrir la pestaña de carga, seleccionar una orden pendiente de la lista desplegable, arrastrar un comprobante válido y verificar que la tarjeta de resultado muestre badge verde `VERIFICADO`, el monto en COP y la referencia bancaria.

**Acceptance Scenarios**:
1. **Given** una orden `#ORD-101` pendiente por `$50.000 COP`, **When** el usuario selecciona la orden, adjunta el comprobante de Nequi correspondiente y hace clic en "Verificar Pago", **Then** el sistema muestra un indicador de carga durante el OCR y luego despliega la tarjeta de éxito con estado `VERIFIED`, monto y referencia.
2. **Given** una orden `#ORD-101` por `$50.000 COP`, **When** se adjunta un comprobante por un valor diferente (ej: `$30.000 COP`), **Then** la interfaz muestra una alerta roja con el mensaje de error `AMOUNT_MISMATCH` indicando monto esperado vs recibido.
3. **Given** un comprobante que ya fue verificado previamente, **When** el usuario intenta subirlo nuevamente, **Then** la interfaz muestra alerta de advertencia `409 DUPLICATE_RECEIPT` con el ID de la transacción original.

---

### User Story 2 - Tablero y Registro de Auditoría de Transacciones (Priority: P1)

Como dueño de negocio o supervisor contable, quiero una segunda pestaña con una tabla en tiempo real de todas las transacciones procesadas para auditar qué pagos fueron aprobados, cuáles fueron rechazados por fraude o error y a qué orden corresponden.

**Why this priority**: Brinda trazabilidad y control financiero histórico, permitiendo conciliar ingresos contra el banco.

**Independent Test**:
Navegar a la pestaña "Transacciones", verificar que aparezca la tabla con columnas (Fecha, Banco, Referencia, Orden, Monto, Estado), probar el filtro por estado (`Todos`, `Verificados`, `Rechazados`) y el buscador por número de referencia.

**Acceptance Scenarios**:
1. **Given** un historial con 10 comprobantes (7 verificados y 3 rechazados), **When** el usuario selecciona el filtro "Verificados", **Then** la tabla muestra únicamente los 7 registros con badges verdes.
2. **Given** la tabla de transacciones, **When** el usuario escribe una referencia bancaria (ej: `M84729103`) en la barra de búsqueda, **Then** la tabla filtra instantáneamente la fila correspondiente.
3. **Given** cualquier fila de transacción en la tabla, **When** el usuario hace clic en "Ver Detalle", **Then** se despliega un modal con la información forense del comprobante (hash SHA-256, texto crudo extraído y motivo de fallo si aplica).

---

### User Story 3 - Creación Rápida de Órdenes desde la UI (Priority: P2)

Como vendedor en caja, quiero poder generar una orden rápida directamente desde la interfaz (indicando número de orden y valor total) si no viene precargada de un sistema externo, para poder asociar de inmediato el comprobante que me entrega el cliente.

**Why this priority**: Agiliza la adopción en comercios que no tienen un ERP o POS integrado y necesitan verificar ventas manuales al instante.

**Independent Test**:
Hacer clic en "Nueva Orden Rápida", ingresar número `ORD-EXPRESS-1` y valor `$65.000`, verificar que se cree en estado `PENDING` y quede seleccionada automáticamente para cargar el comprobante.

---

## Edge Cases

- **Carga de archivos no soportados:** Si el usuario arrastra un archivo que no es imagen (`.exe`, `.txt`), la interfaz debe validar la extensión en el cliente y mostrar un mensaje de error antes de enviar la petición.
- **Pérdida de conectividad:** Si el backend no responde, la UI debe mostrar un toast o banner de error de red sin congelar la pantalla.
- **Imágenes pesadas (> 10MB):** La UI debe advertir al usuario si la imagen excede el límite recomendado.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El backend debe exponer un endpoint `GET /api/v1/receipts` con soporte para listado de comprobantes ordenados por fecha descendente.
- **FR-002**: El backend debe exponer un endpoint `GET /api/v1/orders` con soporte para listar órdenes en estado `PENDING` para alimentar el selector de la UI.
- **FR-003**: La interfaz de usuario debe estar integrada y servida directamente por la aplicación FastAPI en la raíz `/` (o `/dashboard`) mediante archivos estáticos optimizados.
- **FR-004**: La interfaz debe implementar un sistema de dos pestañas:
  - `Tab 1: Verificar Pago`: Selector de orden, área drag-and-drop con previsualización de imagen, botón de acción y card de resultados con métricas bancarias.
  - `Tab 2: Historial de Transacciones`: Tabla reactiva con columnas (Fecha/Hora, Banco con badges temáticos, Referencia, Orden, Monto COP formateado con separadores de miles, Estado y Acciones).
- **FR-005**: La interfaz debe incluir buscador por texto en tiempo real y filtros de estado (`Todos`, `Verificados`, `Rechazados`, `Duplicados`).
- **FR-006**: La UI debe contar con diseño moderno, paleta de colores profesional (Dark Mode nativo con acentos esmeralda/azul fintech) y ser 100% responsive para teléfonos móviles y computadores de escritorio.

---

## Success Criteria *(mandatory)*

- **SC-001**: Tiempo de carga inicial de la interfaz inferior a **200 ms** (cero bundle pesado, assets servidos con compresión Gzip).
- **SC-002**: Feedback visual inmediato (<100 ms) al soltar una imagen en la zona de drop.
- **SC-003**: Compatibilidad total móvil para que un comerciante pueda abrir la web desde su celular, tomar foto al comprobante y verificarlo al instante.
