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

---

## Supuestos de Inventario y CPoR Ajustados por BAR y ADR Real

Para el cálculo financiero del **ARPAR** (*Adjusted RevPAR*):

$$\text{ARPAR} = \frac{\text{Ingresos Totales} - (\text{CPoR} \times \text{Habitaciones Ocupadas})}{\text{Habitaciones Totales Disponibles}}$$

Se actualizan los costos operativos por habitación ocupada (**CPoR**) vinculándolos al comportamiento del ADR real observado en las reservas históricas:

### 1. City Hotel (Inventario Total: 252 habitaciones)

| room_type | capacidad_simulada | BAR Máx (€) | ADR Promedio Ref. (€) | CPoR Estimado (€) | % aprox. del ADR | Justificación Operativa |
| --- | --- | --- | --- | --- | --- | --- |
| **A** | 146 | 300.00 | 97.29 | **19.50 €** | 20% | Tipología base. Costo estándar de lavandería y limpieza rápida. |
| **B** | 15 | 263.55 | 93.72 | **18.70 €** | 20% | Similar a la estándar con rotación eficiente. |
| **C** | 3 | 213.00 | 99.83 | **22.00 €** | 22% | Configuración especial con mayor desgaste de blancos. |
| **D** | 57 | 375.50 | 115.87 | **25.00 €** | 21% | Habitación ejecutiva/doble superior. |
| **E** | 10 | 451.50 | 138.56 | **34.60 €** | 25% | Junior Suite. Incluye amenidades de categoría superior y mayor metraje. |
| **F** | 8 | 349.63 | 171.04 | **44.50 €** | 26% | Suite ejecutiva de alta tarifa; mayor consumo de suministros. |
| **G** | 5 | 510.00 | 176.85 | **53.00 €** | 30% | Suite de Lujo. Requiere detalles de bienvenida y limpieza especializada. |
| **K** | 8 | 283.23 | 52.77 | **13.20 €** | 25% | Tipología especial con menor costo operativo unitario. |

---

### 2. Resort Hotel (Inventario Total: 226 habitaciones)

| room_type | capacidad_simulada | BAR Máx (€) | ADR Promedio Ref. (€) | CPoR Estimado (€) | % aprox. del ADR | Justificación Operativa |
| --- | --- | --- | --- | --- | --- | --- |
| **A** | 75 | 337.00 | 80.08 | **18.40 €** | 23% | Resort Standard. Incluye amenidades recreativas básicas. |
| **B** | 2 | 276.00 | 102.29 | **25.50 €** | 25% | Habitaciones con vistas o mejor ubicación. |
| **C** | 13 | 508.00 | 107.08 | **26.80 €** | 25% | Habitaciones superiores de度假 (vacacionales). |
| **D** | 53 | 350.75 | 81.24 | **18.70 €** | 23% | Doble estándar ampliada de alta rotación. |
| **E** | 33 | 349.67 | 100.95 | **27.30 €** | 27% | Bungalow / Familiar (desgaste y limpieza más robusta). |
| **F** | 13 | 368.10 | 117.31 | **35.20 €** | 30% | Habitaciones con privilegios o accesos directos. |
| **G** | 9 | 426.25 | 149.09 | **44.70 €** | 30% | Suite familiar con terraza. |
| **H** | 4 | 402.00 | 157.96 | **55.30 €** | 35% | Villa / Suite de lujo con servicio personalizado. |
| **I** | 8 | 310.20 | 40.11 | **12.00 €** | 30% | Tipología con tarifa económica o bloqueada, menor costo asociado. |

---
