# Fase 0 — Definición y Supuestos del Proyecto

## 1. Contexto y dataset

Este proyecto de Revenue Management se construye sobre el dataset público **"Hotel Booking Demand"** (Kaggle), que contiene ~119,390 registros de reservas de dos hoteles en Portugal:

- **Resort Hotel** (hotel de playa/vacacional)
- **City Hotel** (hotel urbano/corporativo)

El dataset incluye 32 columnas por reserva: datos de estancia (`lead_time`, `stays_in_weekend_nights`, `stays_in_week_nights`), huéspedes (`adults`, `children`, `babies`), canal y segmento (`market_segment`, `distribution_channel`, `agent`, `company`), habitación (`reserved_room_type`, `assigned_room_type`), tarifa (`adr`), comportamiento histórico (`previous_cancellations`, `previous_bookings_not_canceled`, `booking_changes`), y estado final (`is_canceled`, `reservation_status`, `reservation_status_date`).

## 2. Limitación principal: no hay inventario real

El dataset **no incluye información de inventario** — no sabemos cuántas habitaciones de cada tipología existen físicamente en cada hotel, ni tarifas de rack oficiales por tipología. Esto es un problema crítico porque métricas estándar de Revenue Management como **RevPAR** (`Revenue / Available Rooms`) requieren un denominador de capacidad que este dataset no provee.

### Supuesto adoptado

Se simula la capacidad de cada hotel, por tipología de habitación, a partir del **máximo histórico de ocupación diaria observada** en los propios datos. La lógica: si en algún momento del histórico se ocuparon N habitaciones de un tipo en un mismo día, la capacidad real de ese hotel para esa tipología es *al menos* N.

## 3. Metodología de construcción del inventario simulado

### Paso 1 — Expansión a nivel noche-reserva

El dataset original tiene una fila por reserva, no por noche ocupada. Una reserva de 4 noches ocupa una habitación en 4 fechas distintas, no solo en `arrival_date`. Para conocer la ocupación real por día, cada reserva se expande en N filas (una por noche de estancia).

Reglas aplicadas en la expansión:

- Se excluyen reservas con `is_canceled == 1` — solo estancias que ocurrieron generan ocupación física real.
- Se usa `assigned_room_type` (la habitación realmente ocupada), no `reserved_room_type` (la solicitada). Esto es consistente con la columna de negocio `assigned_status` (Upgrade/Downgrade/Normal) ya calculada en `transform.py`.

### Paso 2 — Cálculo de capacidad base

Se agrupa la ocupación expandida por `hotel + room_type + fecha`, y se toma el **máximo histórico** de habitaciones ocupadas simultáneamente como capacidad candidata.

### Tabla de resultados (capacidad simulada final)

| Hotel | Room Type | Capacidad simulada |
| --- | --- | --- |
| City Hotel | A | 146 |
| City Hotel | B | 15 |
| City Hotel | C | **2** |
| City Hotel | D | 57 |
| City Hotel | E | 10 |
| City Hotel | F | 8 |
| City Hotel | G | 5 |
| City Hotel | K | 8 |
| Resort Hotel | A | 75 |
| Resort Hotel | B | **2** |
| Resort Hotel | C | 13 |
| Resort Hotel | D | 53 |
| Resort Hotel | E | 33 |
| Resort Hotel | F | 13 |
| Resort Hotel | G | 9 |
| Resort Hotel | H | 4 |
| Resort Hotel | I | 8 |

## 4. Limitaciones descubiertas de esta metodología

- **Tipologías de bajo volumen** (ej. `Resort Hotel - B`, con capacidad simulada de solo 2 habitaciones) Se marcan como válidas pero son de menor confianza.
- Es posible que la capacidad real podría ser más de lo esperado, si el hotel nunca llegó a venderse al 100% de esa tipología durante el periodo capturado en el dataset.
- El dataset no distingue entre "no vendido por falta de demanda" y "no vendido por no estar disponible" (ej. habitaciones en mantenimiento), lo cual no podemos corregir con la información disponible.

## 5. Impacto en métricas de fases posteriores

| Métrica | Afectada por el supuesto | Nivel de confianza |
| --- | --- | --- |
| RevPAR | Sí (depende directamente de capacidad simulada) | Relativo — válido para comparar tendencias internas, no como benchmark absoluto |
| ADR | No | Alto — viene directo del dato original |
| % Ocupación | Sí | Relativo, mismo caso que RevPAR |
| Tasa de cancelación | No | Alto |
| Segmentación de clientes | No | Alto |

## 6. Próximos pasos

Esta capacidad simulada se integra a la base de datos `\data\hotel_data.db` como tabla de referencia (`hotel + room_type → capacidad_simulada`), disponible para las Fases 2 (EDA), 3 (pruebas de hipótesis) y 4 (dashboards).

## Supuestos de Inventario y CPoR (Cost per Occupied Room)

Para el cálculo del ARPAR (Adjusted RevPAR) mediante la fórmula:

$$\text{ARPAR} = \frac{\text{Ingresos Totales} - (\text{CPoR} \times \text{Habitaciones Ocupadas})}{\text{Habitaciones Totales Disponibles}}$$

Se establecen los siguientes supuestos de costos operativos por habitación ocupada (CPoR) según el tipo de hotel y la tipología de la habitación (asumiendo una escala donde A es la tipología base/estándar y las letras posteriores implican mayor espacio, mejores amenidades o servicios superiores):

### 1. City Hotel (Total Habitaciones: 252)

*Características operativas:* Mayor rotación, menor costo de áreas comunes por habitación, enfoque ejecutivo.

| room_type | capacidad_simulada | CPoR Estimado (Base €) | Justificación de Supuesto |
| :--- | :---: | :---: | :--- |
| **A** | 146 | **18.00 €** | Habitación estándar individual/doble. Costo base de lavandería, amenities estándar y limpieza rápida. |
| **B** | 15 | **22.00 €** | Habitación Twin/Superior con ligera variación en amenidades. |
| **C** | 3 | **35.00 €** | Habitaciones especiales / triples con mayor desgaste y rotación de blanco. |
| **D** | 57 | **20.00 €** | Habitación doble ejecutiva. |
| **E** | 10 | **45.00 €** | Junior Suite. Incluye kit de amenidades premium, cafetera, albornoces y mayor tiempo de limpieza. |
| **F** | 8 | **55.00 €** | Suite ejecutiva. |
| **G** | 5 | **70.00 €** | Suite de Lujo / Penthouse. |
| **K** | 8 | **25.00 €** | Tipología especial / Familiar adaptada. |

---

### 2. Resort Hotel (Total Habitaciones: 226)

*Características operativas:* Estancias más largas, costos de mantenimiento de áreas recreativas prorrateados, amenidades vacacionales más robustas.

| room_type | capacidad_simulada | CPoR Estimado (Base €) | Justificación de Supuesto |
| :--- | :---: | :---: | :--- |
| **A** | 75 | **22.00 €** | Standard Resort Room. Limpieza estándar y amenidades básicas de playa/piscina. |
| **B** | 2 | **28.00 €** | Habitaciones con vista o características mejoradas. |
| **C** | 13 | **32.00 €** | Habitaciones superiores con detalles vacacionales. |
| **D** | 53 | **25.00 €** | Doble estándar ampliada. |
| **E** | 33 | **40.00 €** | Bungalow / Habitaciones familiares (mayor desgaste de blancos y limpieza profunda). |
| **F** | 13 | **50.00 €** | Habitaciones con privilegios o acceso directos a zonas húmedas/piscina. |
| **G** | 9 | **65.00 €** | Suite familiar / con terraza privada. |
| **H** | 4 | **85.00 €** | Villa / Suite de lujo con servicio personalizado. |
| **I** | 8 | **95.00 €** | Máxima categoría (Presidential Villa / Master Suite). |
