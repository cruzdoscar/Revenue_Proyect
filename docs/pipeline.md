# 📌 Simulando una Base de Datos

El flujo para simular la extracción desde una base de datos consistirá en 3 pasos principales:

1. **Paso 1: Poblado inicial de la Base de Datos (Seed Script):**
Crearemos un script auxiliar que tome un archivo CSV y cargue esos datos dentro de una base de datos local SQLite (`hotel_data.db`) en una tabla llamada `raw_bookings`. Esto simula que los datos ya residen en la base de datos del sistema PMS (Property Management System) del hotel.
2. **Paso 2: Módulo de Extracción (`src/extract.py`):**
Escribiremos la lógica para conectarnos a `hotel_data.db` mediante `SQLAlchemy` y extraer los datos realizando una consulta SQL (`SELECT`).
3. **Paso 3: Integración:**
El módulo de extracción devolverá un *DataFrame* de Pandas con los datos crudos extraídos de SQL, listo para pasar a la fase de transformación (`src/transform.py`).

---

## 🛠️ 1. Script de Inicialización: `db_setup.py`

Vamos a crear el primer componente: el script para **crear la base de datos SQLite a partir de un CSV**

## 📥 2. Módulo de Extracción: `src/extract.py`

Ahora crearemos el módulo que formará parte de nuestro pipeline para extraer los datos mediante SQL. Archivo `extract.py`

## 🛠️ 3. Módulo de Transformación `src/transform.py`

En este módulo tomaremos el DataFrame de datos crudos extraído por `extract.py` y le aplicaremos todas las reglas de negocio y transformaciones que validamos previamente en el notebook.

Para mantener el código modular, mantenible y profesional, estructuraremos `transform.py` con **funciones independientes para cada etapa** y una función principal que orquestará la transformación.

### Diagrama del Flujo de Transformación `src/load.py`

```text
Entrada (df_raw)
       │
       ├── 1. clean_missing_data()      --> Imputación de nulos y tipos de datos
       ├── 2. remove_system_duplicates() --> Filtrado de duplicados por reglas de negocio
       └── 3. engineer_features()       --> Métricas de Revenue Management & Estacionalidad
       │
Salida (df_transformed)

```

## 4. Módulo de carga `src/load.py`

El objetivo de src/load.py es tomar el DataFrame limpio y transformado (df_transformed) y almacenarlo de forma persistente. En un entorno de Revenue Management, esta fase garantiza que los datos procesados estén listos para ser consumidos por dashboards (Power BI/Tableau) o modelos predictivos.

### ¿Qué hará load.py?

- Se conectará a la base de datos de destino (SQLite en data/hotel_data.db o una tabla limpia dedicada como hotel_reservations_cleaned).

- Utilizará el parámetro chunksize para insertar los datos de manera optimizada sin saturar la memoria RAM.

- Permitirá definir la estrategia de carga (replace para sobrescribir la tabla limpia o append para agregar nuevos datos).

- Confirmará en terminal cuántas filas y columnas se insertaron exitosamente en la base de datos final.

## 5. El Orquestador Principal `pipeline.py`

El archivo `pipeline.py` actuará como el punto de entrada unificado de todo el sistema. En lugar de ejecutar los scripts por separado (`extract.py`, `transform.py` y `load.py`), este orquestador se encargará de coordinar el flujo completo secuencialmente:

- **Extracción:** Llama a `extract_from_sqlite()` para traer los datos crudos desde la fuente.

- **Transformación:** Pasa los datos crudos a `transform_data()` para realizar la limpieza, deduplicación con control de seguridad y la generación de métricas de Revenue Management.

- **Carga:** Envía el DataFrame transformado a `load_to_sqlite()` para guardarlo en la base de datos de producción (`clean_bookings`).

- **Manejo de Errores y Tiempos:** Mide el tiempo total de ejecución y captura cualquier fallo en el proceso para reportarlo de forma clara en la consola.
