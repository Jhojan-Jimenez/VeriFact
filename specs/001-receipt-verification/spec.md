# Feature Specification: Ingesta y Verificación de Comprobantes Bancarios con Conciliación de Órdenes e Inventario

**Feature Branch**: `001-receipt-verification`  
**Created**: 2026-10-24  
**Status**: Ready for Review (Draft)  
**Input**: Ingesta y verificación de comprobantes de pago bancarios (QR, Nequi, Daviplata, Bancolombia, Bre-B) con conciliación contra órdenes de venta y trazabilidad de inventario.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingesta de Comprobante y Extracción Determinista (Priority: P1)

Como cajero o servicio cliente de venta, quiero enviar la imagen de un comprobante de pago bancario colombiano (captura de pantalla o foto de recibo) para que el backend identifique automáticamente la entidad emisora (Nequi, Daviplata, Bancolombia, Bre-B o Factura DIAN) y extraiga con precisión el número de referencia, el monto pagado, la fecha/hora y el concepto.

**Why this priority**: Es la base del producto. Sin extracción confiable y determinista, no existe automatización ni verificación posible.

**Independent Test**: Se puede probar aislando el servicio de visión (`VisionExtractorService`) con un conjunto de fixtures de prueba de cada banco. La prueba valida que la respuesta contenga el diccionario con `bank`, `reference_number`, `amount_cop` y `timestamp`.

**Acceptance Scenarios**:
1. **Given** un pantallazo legítimo de Nequi con monto `$50.000` y referencia `M12345678`, **When** se envía al endpoint de procesamiento, **Then** el sistema retorna `bank: NEQUI`, `amount: 50000`, `reference: M12345678` y `status: EXTRACTED`.
2. **Given** una imagen que contiene un código QR de Facturación Electrónica DIAN, **When** el decodificador rápido lo procesa, **Then** el sistema extrae el CUFE y la URL de validación sin necesidad de ejecutar OCR pesado de texto.
3. **Given** una imagen corrupta, ilegible o sin datos financieros, **When** se procesa, **Then** el sistema responde con error estructurado `EXTRACTION_FAILED` y detalle del campo no detectado.

---

### User Story 2 - Conciliación contra Orden de Venta (Priority: P1)

Como comerciante o caja registradora, quiero asociar la carga del comprobante a un `order_id` o `order_number` específico para que el sistema compruebe automáticamente que el dinero pagado cubre la totalidad de la venta y que el comprobante fue emitido dentro de la ventana de tiempo de la orden.

**Why this priority**: Evita el error humano de cobrar de menos o dar por pagada una venta con un comprobante de otra transacción diferente.

**Independent Test**: Crear una orden en estado `PENDING` por `$75.000`. Enviar comprobante por `$75.000` y verificar que la orden pasa a `PAID`. Enviar otro comprobante por `$40.000` y verificar que es rechazado con `AMOUNT_MISMATCH`.

**Acceptance Scenarios**:
1. **Given** una orden `#ORD-100` con total `$80.000 COP` en estado `PENDING`, **When** se sube un comprobante válido por `$80.000 COP` cuya hora esté dentro de los 15 minutos posteriores a la orden, **Then** el backend marca la orden como `PAID` y registra la transacción bancaria asociada.
2. **Given** una orden `#ORD-100` por `$80.000 COP`, **When** el comprobante registra un monto de `$50.000 COP`, **Then** el sistema rechaza el pago con estado `AMOUNT_MISMATCH` y mantiene la orden como `PENDING`.
3. **Given** una orden que ya está en estado `PAID` o `CANCELLED`, **When** se intenta subir un nuevo comprobante, **Then** el sistema responde con `ORDER_ALREADY_SETTLED`.

---

### User Story 3 - Deduplicación Estricta y Prevención Antifraude (Priority: P2)

Como dueño de negocio, quiero que el sistema detecte y bloquee inmediatamente cualquier intento de "reciclaje" de comprobantes (utilizar el mismo pantallazo para pagar dos ventas distintas) o alteración digital.

**Why this priority**: El fraude más común en Colombia con Nequi y Daviplata consiste en reutilizar pantallazos viejos o mostrar capturas editadas.

**Independent Test**: Subir exitosamente un comprobante con referencia `M998877`. Intentar subir el mismo comprobante (o uno con la misma referencia bancaria) para una orden distinta. Verificar rechazo con código `409 Conflict` y alerta de fraude.

**Acceptance Scenarios**:
1. **Given** un comprobante con número de referencia `REF-889911` ya aprobado previamente, **When** un usuario intenta usarlo para pagar la orden `#ORD-200`, **Then** el sistema rechaza la solicitud con código HTTP 409 y razón `DUPLICATE_TRANSACTION_REFERENCE`.
2. **Given** un archivo de imagen con el mismo hash SHA-256 ya registrado en el histórico, **When** se sube nuevamente, **Then** el sistema lo bloquea con `DUPLICATE_IMAGE_PAYLOAD`.
3. **Given** un comprobante cuya fecha/hora extraída tenga más de 30 minutos de desfase respecto a la creación de la orden, **When** se valida, **Then** se marca como `EXPIRED_RECEIPT_TIMESTAMP` requiriendo confirmación manual.

---

### User Story 4 - Trazabilidad y Decremento Automático de Inventario (Priority: P2)

Como administrador de inventarios, quiero que cada vez que una orden sea verificada y pagada satisfactoriamente, el stock de cada producto incluido en la orden se descuente de inmediato en una transacción atómica y quede registrado en el kardex/histórico de movimientos.

**Why this priority**: Garantiza que el stock refleje en tiempo real las ventas efectivamente cobradas y no pedidos ficticios o no pagados.

**Independent Test**: Crear un producto con stock de 10 unidades. Generar orden por 3 unidades. Aprobar el pago y verificar que el stock disminuye exactamente a 7, registrándose un `StockMovement` con referencia al `order_id`.

**Acceptance Scenarios**:
1. **Given** una orden pagada con 2 unidades del SKU `CAMISA-L`, **When** la transacción de pago se completa, **Then** el inventario del SKU se decrementa en 2 y se genera un registro en `stock_movements`.
2. **Given** una orden cuyo pago se intenta conciliar pero algún ítem no tiene stock suficiente, **When** se ejecuta la validación, **Then** la operación revierte atómicamente (`rollback`) y la orden se marca con `INSUFFICIENT_STOCK`.

---

## Edge Cases

- **Imágenes rotadas o inclinadas:** El preprocesador de OpenCV debe detectar la orientación del texto o código QR y aplicar corrección de inclinación (`deskew`) antes de OCR.
- **Capturas en modo oscuro (Dark Mode de Nequi/Bancolombia):** El binarizador debe soportar inversión de contraste (texto claro sobre fondo oscuro).
- **Formatos con separadores de miles y decimales:** En Colombia se usa `$50.000,00` o `$50.000`. El parser monetario debe normalizar comas y puntos a enteros limpios en COP.
- **Imágenes de comprobantes falsos con fuentes alteradas:** Si los patrones de anclaje (posicionamiento de logos y palabras clave como "¡Listo!", "Comprobante", "Transferencia exitosa") no coinciden con las geometrías esperadas, catalogar como `UNRECOGNIZED_TEMPLATE`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El endpoint `POST /api/v1/receipts/verify` debe aceptar cargas multipart con un archivo de imagen (`image/jpeg`, `image/png`, `image/webp`) y el identificador `order_id`.
- **FR-002**: El módulo de visión debe intentar primero la lectura de códigos QR (`pyzbar`) antes de ejecutar el OCR completo para maximizar velocidad en facturas DIAN o códigos de pago interoperables.
- **FR-003**: El motor OCR (`pytesseract` con español) debe pasar las imágenes por filtros de normalización: escala de grises, aumento de contraste, reducción de ruido gaussiano y binarización adaptativa Otsu.
- **FR-004**: Deben existir extractores dedicados y aislados para las siguientes plataformas bancarias:
  - `NequiExtractor` (busca anclas: *¡Listo!*, *Enviaste*, *Referencia*, formato `M\d{7,9}`).
  - `DaviplataExtractor` (busca anclas: *Transacción exitosa*, *Número de aprobación*, *Monto*).
  - `BancolombiaExtractor` (busca anclas: *Transferencia exitosa*, *Comprobante No.*, formato numérico).
  - `BreBExtractor` (busca identificador Bre-B / Llaves y código de trazabilidad del Banco de la República).
- **FR-005**: El sistema debe computar el hash SHA-256 del binario de la imagen y verificar unicidad en la tabla `payment_receipts`.
- **FR-006**: La validación de la orden debe contrastar:
  1. Que `order.status == 'PENDING'`.
  2. Que `abs(extracted_amount - order.total_amount) == 0`.
  3. Que `receipt_timestamp >= (order.created_at - 10 min)` y `<= (order.created_at + 30 min)`.
- **FR-007**: El decremento de stock y la confirmación de la orden deben ejecutarse dentro de una misma transacción de base de datos (`BEGIN TRANSACTION ... COMMIT`).
- **FR-008**: Se debe exponer un endpoint `GET /api/v1/orders/{order_id}` para consultar el estado de la orden, el comprobante vinculado y el desglose de productos.
- **FR-009**: Se debe exponer un endpoint `GET /api/v1/inventory/{sku}/history` para auditar la trazabilidad de ventas asociadas a comprobantes.

---

### Key Entities

- **Order**:
  - `id`: UUID (Primary Key)
  - `order_number`: String (ej. `ORD-2026-0001`, Unique)
  - `total_amount`: Integer (Monto en COP)
  - `status`: Enum (`PENDING`, `PAID`, `CANCELLED`, `REJECTED`)
  - `created_at`: Datetime
  - `updated_at`: Datetime

- **OrderItem**:
  - `id`: UUID
  - `order_id`: UUID (Foreign Key a Order)
  - `sku`: String (Foreign Key a InventoryItem)
  - `quantity`: Integer
  - `unit_price`: Integer

- **PaymentReceipt**:
  - `id`: UUID
  - `order_id`: UUID (Foreign Key opcional / nullable)
  - `bank_platform`: Enum (`NEQUI`, `DAVIPLATA`, `BANCOLOMBIA`, `BRE_B`, `DIAN_INVOICE`, `UNKNOWN`)
  - `reference_number`: String (Unique index junto a bank_platform)
  - `extracted_amount`: Integer (COP)
  - `receipt_timestamp`: Datetime
  - `image_sha256`: String (Unique index)
  - `verification_status`: Enum (`VERIFIED`, `REJECTED`, `DUPLICATE`, `FLAGGED_FRAUD`, `UNCONFIRMED`)
  - `raw_extracted_text`: Text
  - `failure_reason`: String (Nullable)
  - `created_at`: Datetime

- **InventoryItem**:
  - `sku`: String (Primary Key)
  - `name`: String
  - `unit_price`: Integer (COP)
  - `stock`: Integer
  - `is_active`: Boolean

- **StockMovement**:
  - `id`: UUID
  - `sku`: String (Foreign Key)
  - `order_id`: UUID (Foreign Key)
  - `quantity`: Integer (negativo para decrementos de venta)
  - `movement_type`: Enum (`SALE_DEDUCTION`, `RETURN`, `ADJUSTMENT`)
  - `timestamp`: Datetime

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tiempo de respuesta de procesamiento y validación completo inferior a **1.5 segundos** por comprobante en entorno local sin GPU.
- **SC-002**: Tasa de detección de comprobantes duplicados del **100%** (por hash o número de referencia).
- **SC-003**: Cero inconsistencias o condiciones de carrera en inventario bajo concurrencia (garantizado por transacciones atómicas SQLite WAL).
- **SC-004**: Precisión de extracción de monto y número de referencia superior al **95%** en fixtures de comprobantes nítidos de Nequi, Bancolombia y Daviplata.

---

## Assumptions

- Las transacciones monetarias se manejan como números enteros de Pesos Colombianos (COP), sin centavos.
- Las capturas son legibles por ojo humano y contienen al menos el bloque del monto y el número de referencia.
- La aplicación se ejecuta en servidores locales o contenedores Linux con soporte para binarios `tesseract-ocr` y `libzbar0`.
