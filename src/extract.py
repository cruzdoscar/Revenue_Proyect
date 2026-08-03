import pandas as pd
from sqlalchemy import create_engine
import os

def extract_from_sqlite(db_path: str = os.path.join("data", "hotel_data.db"))  -> pd.DataFrame:
    """
    Conecta a la base de datos SQLite y extrae los datos de la tabla 'raw_bookings'.

    Args:
        db_path (str): Ruta al archivo de la base de datos SQLite.

    Returns:
        pd.DataFrame: DataFrame que contiene los datos extraídos.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"❌ Error: No se encontró el archivo de base de datos en {db_path}. Asegúrate de que la base de datos exista.")
    
    print(f"⏳ Conectando a la base de datos en {db_path}...")

    # Crear la conexión a la base de datos SQLite
    engine = create_engine(f'sqlite:///{db_path}')

    # Consulta SQL para extraer los datos de la tabla 'raw_bookings'
    query = "SELECT * FROM raw_bookings"

    print("⏳ Ejecutando la consulta SQL para extraer los datos...")

    # Leer los datos de la tabla especificada en un DataFrame
    df = pd.read_sql_query(query, con=engine)

    print(f"✅ Extracción exitosa. Filas extraídas: {df.shape[0]}, Columnas: {df.shape[1]}")
    
    return df

if __name__ == "__main__":
    # Prueba de la función de extracción
    df_test = extract_from_sqlite()
    print(df_test.head())