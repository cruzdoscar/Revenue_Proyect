# Fase 0 — Definición y Supuestos del Proyecto

## Contexto y dataset

Este proyecto de Revenue Management se construye sobre el dataset público **"Hotel Booking Demand"** (Kaggle), que contiene ~119,390 registros de reservas de dos hoteles en Portugal:

- **Resort Hotel** (hotel de playa/vacacional)
- **City Hotel** (hotel urbano/corporativo)

El dataset incluye 32 columnas por reserva: datos de estancia (`lead_time`, `stays_in_weekend_nights`, `stays_in_week_nights`), huéspedes (`adults`, `children`, `babies`), canal y segmento (`market_segment`, `distribution_channel`, `agent`, `company`), habitación (`reserved_room_type`, `assigned_room_type`), tarifa (`adr`), comportamiento histórico (`previous_cancellations`, `previous_bookings_not_canceled`, `booking_changes`), y estado final (`is_canceled`, `reservation_status`, `reservation_status_date`).

## 1. Supuesto de Inventario

El dataset **no incluye información de inventario** — no sabemos cuántas habitaciones de cada tipología existen físicamente en cada hotel, ni tarifas de rack oficiales por tipología. Esto es un problema crítico porque métricas estándar de Revenue Management como **RevPAR** (`Revenue / Available Rooms`) requieren un denominador de capacidad que este dataset no provee.

### Supuesto adoptado

La capacidad de cada hotel es simulada por tipología de habitación, a partir del **máximo histórico de ocupación diaria observada** en los propios datos. La lógica: si en algún momento del histórico se ocuparon N habitaciones de un tipo en un mismo día, la capacidad real de ese hotel para esa tipología es *al menos* N.

### Metodología de construcción del inventario simulado

#### Paso 1 — Expansión a nivel noche-reserva

El dataset original tiene una fila por reserva, no por noche ocupada. Una reserva de 4 noches ocupa una habitación en 4 fechas distintas, no solo en `arrival_date`. Para conocer la ocupación real por día, cada reserva se expande en N filas (una por noche de estancia).

Reglas aplicadas en la expansión:

- Se excluyen reservas con `is_canceled == 1` — solo estancias que ocurrieron generan ocupación física real.
- Se usa `assigned_room_type` (la habitación realmente ocupada), no `reserved_room_type` (la solicitada). Esto es consistente con la columna de negocio `assigned_status` (Upgrade/Downgrade/Normal) ya calculada en `transform.py`.

#### Paso 2 — Cálculo de capacidad base

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

> **Nota:** Es posible que la capacidad real podría ser más de lo esperado, si el hotel nunca llegó a venderse al 100% de esa tipología durante el periodo capturado en el dataset. Además, el dataset no distingue entre "no vendido por falta de demanda" y "no vendido por no estar disponible" (ej. habitaciones en mantenimiento), lo cual no podemos corregir con la información disponible.

Esta capacidad simulada se integra a la base de datos `\data\hotel_data.db` como tabla de referencia, disponible para las Fases 2 (EDA), 3 (pruebas de hipótesis) y 4 (dashboards).

---

## 2. Supuesto CPoR Ajustado por BAR y ADR Real

- **BAR (Best Available Rate):** es la tarifa pública más alta/estándar sin restricciones que el hotel ofrece para una tipología, en un momento dado. Sacarlo como `.max()` del adr histórico por tipología es un proxy razonable; asume que el precio más alto pagado por esa tipología refleja aproximadamente su tarifa "de lista", sin descuentos de grupo, agencia o temporada baja.

- **CPOR (Cost Per Occupied Room):** es el costo operativo de tener una habitación ocupada (limpieza, amenities, desgaste, servicios), no un precio de venta.

El dataset no tiene ningún dato de costos operativos. No hay forma de "calcular" el CPoR desde los datos, el calculo de esta métrica, por si misma, es suficiente para crear otro proyecto; sin embargo, Lo que vamos a construir es un supuesto explícito y documentado, igual que hicimos con el inventario.

### Metodología propuesta (estándar de industria hotelera)

El CPoR (costo variable por habitación ocupada: limpieza, amenities, lavandería, desayuno, consumo energético, desgaste) no escala linealmente con el precio de venta. Una suite no cuesta operativamente 3 veces más que una habitación estándar solo porque se vende 3 veces más cara, el costo de servicio crece mucho menos que el precio. Por eso el estándar de la industria es modelar el CPoR como un % del ADR que decrece a medida que sube la categoría:

| Categoría (por ranking de BAR) | CPoR como % del ADR promedio |
| --- | --- |
| Premium | ~18% |
| Superior | ~22% |
| Standard | ~27% |
| Economy | ~33% |

- Uso el **ADR promedio real** (no el BAR) como base del cálculo: el BAR es un techo teórico que rara vez se cobra, el costo operativo debe estimarse sobre la tarifa que realmente se cobra en promedio, que es un proxy más realista del nivel de servicio que efectivamente se entrega noche a noche.

Clasifiqué cada tipología en un cuartil de categoría según su ranking de BAR dentro de su propio hotel (Premium = BAR más alto, Economy = BAR más bajo). Recordando que el dataset no tiene ningún nombre real de tipología (solo letras A-K), así que estos nombres son un supuesto narrativo propio.

### Tabla de resultados (CPoR simulado final)

## 1. City Hotel (Inventario Total: 252 habitaciones)

| room_type | capacidad_simulada | BAR Max (€) | ADR Promedio Ref (€) | CPoR Estimado (€) | Categoría | Tipo de Habitación |
| --- | --- | --- | --- | --- | --- | --- |
| **A** | 146 | 300.00 | 97.29 | **26.27 €** | Standard | Habitación Doble Estándar |
| **B** | 15 | 263.55 | 93.72 | **30.93 €** | Economy | Habitación Económica interior (sin vista) |
| **C** | 2 | 213.00 | 99.83 | **32.94 €** | Economy | Habitación de Hospitalidad |
| **D** | 57 | 375.50 | 115.87 | **25.49 €** | Superior | Habitación Superior estándar corporativa |
| **E** | 10 | 451.50 | 138.56 | **24.94 €** | Premium | Suite Deluxe con vista a la ciudad |
| **F** | 8 | 349.63 | 171.04 | **37.63 €** | Superior | Habitación Deluxe con terraza / esquina |
| **G** | 5 | 510.00 | 176.85 | **31.83 €** | Premium | Suite Ejecutiva / Business Suite |
| **K** | 8 | 283.23 | 52.77 | **14.25 €** | Standard | Habitación individual / accesible |

## 2. Resort Hotel (Inventario Total: 226 habitaciones)

| room_type | capacidad_simulada | BAR Max (€) | ADR Promedio Ref (€) | CPoR Estimado (€) | Categoría | Tipo de Habitación |
| --- | --- | --- | --- | --- | --- | --- |
| **A** | 75 | 337.00 | 80.08 | **21.62 €** | Standard | Habitación Estándar |
| **B** | 2 | 276.00 | 102.29 | **33.76 €** | Economy | Habitación de Hospitalidad |
| **C** | 13 | 508.00 | 107.08 | **19.27 €** | Premium | Suite Ocean Front |
| **D** | 53 | 350.75 | 81.24 | **17.87 €** | Superior | Habitación Doble Garden View |
| **E** | 33 | 349.67 | 100.95 | **27.26 €** | Standard | Habitación Doble Estándar |
| **F** | 13 | 368.10 | 117.31 | **25.81 €** | Superior | Habitación Superior con terraza |
| **G** | 9 | 426.25 | 149.09 | **26.84 €** | Premium | Suite Ocean View |
| **H** | 4 | 402.00 | 157.96 | **55.30 €** | 35% | Suite Presidencial |
| **I** | 8 | 310.20 | 40.11 | **13.24 €** | Economy | Habitación Individual |

> **Nota:** El CPoR aquí calculado es un supuesto basado en ratios estándar de industria (18-33% del ADR según categoría), no un dato observado.

Estas metricas simuladas se integran a la base de datos `\data\hotel_data.db` como tabla de referencia, disponible para las Fases 2 (EDA), 3 (pruebas de hipótesis) y 4 (dashboards).

---
