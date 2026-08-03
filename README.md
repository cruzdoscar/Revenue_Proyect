# Optimización de Ingresos y Gestión del Riesgo de Cancelación en Hotelería

## 📈 Resumen Ejecutivo

Este proyecto desarrolla un marco de trabajo analítico para maximizar el RevPAR mediante la predicción del riesgo de cancelación y la optimización de las políticas de sobreventa (overbooking). Utilizando un dataset de 119,390 reservas (City y Resort Hotel), se identificó un costo de oportunidad de $X.XX MDD debido a habitaciones vacías por cancelación. El modelo predictivo implementado permite anticipar cancelaciones con un [Métrica de evaluación, ej. Recall del 88%], dándole al equipo de Revenue Management una ventana de acción de más de 30 días para la re-comercialización del inventario.

## 🎯 Objetivos del Proyecto

* **Cuantificar el impacto financiero** de las cancelaciones en el ADR y la ocupación general.
* **Diseñar un modelo predictivo** que asigne un score de riesgo de cancelación a cada reserva entrante en tiempo real.
* **Evaluar estadísticamente** la efectividad de las políticas de depósito actuales frente al volumen de venta.
* **Desplegar un Dashboard Operativo en Tableau** para el monitoreo de curvas de Pick-up y alertas de inventario.

## 🛠️ Stack Tecnológico

* **Procesamiento y EDA:** Python (Pandas, NumPy)
* **Visualización Estática y Análisis:** Matplotlib, Seaborn
* **Validación Estadística:** SciPy (Pruebas Chi-cuadrado para variables categóricas, T-Test para ADRs)
* **Machine Learning:** Scikit-Learn (Random Forest / XGBoost, optimizando Recall para evitar falsos negativos)
* **Business Intelligence:** Tableau Public

## 📊 Arquitectura del Análisis

### 1. Análisis del Comportamiento de Demanda (EDA)

* Análisis de la estacionalidad del ADR y tasas de ocupación por mes.
* Comportamiento del Lead Time: Identificación del "punto de no retorno" donde las cancelaciones se estabilizan.

### 2. Pruebas de Hipótesis (A/B Testing Framework)

* *Hipótesis:* Las reservas con políticas "Non-Refundable" presentan un ADR significativamente menor pero aseguran la ocupación. (Validado mediante pruebas estadísticas con un p-valor < 0.05).

### 3. Modelo de Machine Learning para Revenue Managers

* **Ingeniería de Características:** Creación de métricas de densidad de ocupación y desviaciones de tarifa promedio.
* **Enfoque de Negocio:** El modelo prioriza reducir los falsos negativos (reservas que el modelo dice que se quedarán, pero terminan cancelando), protegiendo el inventario del hotel.

## 🚀 Conclusiones y Recomendaciones para el Negocio

* [Aquí pondrás tu insight más fuerte, ej: "El 40% de las cancelaciones ocurren en el segmento de agencias online (OTA) cuando el lead time supera los 90 días. Se recomienda implementar depósitos automatizados a los 60 días de la llegada."]
* [Otro insight, ej: "El modelo predictivo permite habilitar una estrategia de sobreventa controlada del 5% en temporadas de alta ocupación sin riesgo de denegación de embarque."]

## 🔗 Enlaces de Interés

* [Ver Dashboard Interactivo en Tableau Public](URL_A_TU_TABLEAU)
* [Ver Notebook de Python con el Pipeline de Datos](URL_A_TU_NOTEBOOK)
