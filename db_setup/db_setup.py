import pandas as pd
from sqlalchemy import create_engine
import os

# --- CONFIGURACIÓN DE RUTAS ---
# Ruta del archivo CSV crudo de kaggle
RAW_CSV_PATH = os.path.join("data", "raw", "hotel_bookings.csv")

# Ruta donde se creará la base de datos SQLite
DB_PATH = os.path.join("data", "hotel_data.db")

def setup_database():
    """
    Lee el archivo CSV crudo y lo carga en una base de datos SQLite
    para simular un entorno de producción con base de datos SQL.
    """
    if not os.path.exists(RAW_CSV_PATH):
        print(f"❌ Error: No se encontró el archivo {RAW_CSV_PATH}")
        print("Asegúrate de colocar el archivo 'hotel_bookings.csv' en la carpeta 'data/raw/'")
        return
    
    print("⏳ Cargando datos desde el CSV a la base de datos SQLite...")

    # PASO 1: Leer el archivo CSV crudo
    df_raw = pd.read_csv(RAW_CSV_PATH)

    # PASO 2: Crear la conexión a la base de datos SQLite con SQLAlchemy
    # 'sqlite:///data/hotel_bookings.db' define la ubicación del archivo DB
    engine = create_engine(f'sqlite:///{DB_PATH}')

    # PASO 3: Guardar el DataFrame en la tabla SQL 'raw_bookings'
    # if_exists='replace' asegura que si la tabla ya existe, se reemplazará
    df_raw.to_sql('raw_bookings', con=engine, if_exists='replace', index=False)

    print(f"✅ Base de datos creada exitosamente en {DB_PATH}")
    print(f"📊 Registros insertados en la tabla 'raw_bookings': {len(df_raw)}")

if __name__ == "__main__":
    setup_database()