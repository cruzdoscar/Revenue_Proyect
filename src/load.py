import pandas as pd
import sqlite3
from pathlib import Path

def load_to_sqlite(df: pd.DataFrame, table_name: str, if_exists_strategy: str, db_path: str = "../data/hotel_data.db") -> None:
    """
    Carga el DataFrame trasnformado a una tabla estructurada.
    
    Parámetros:
        ------------
        df: pd.DataFrame
            DataFrame a cargar.
    
        table_name : str
            Nombre de la tabla destino donde se guardarán los datos. Obligatorio,
            ya que cada llamada debe declarar explícitamente a qué tabla escribe.
    
        if_exists_strategy : str
            Estrategia si la tabla ya existe: 'replace' (sobreescribir) o 'append' (anexar).
            
        db_path : str
            Ruta del archivo con la base de datos.
        """

    print("💾 Iniciando proceso de carga de datos...")

    # 1. Aseguramos la existencia del directorio de destino
    path_obj = Path(db_path)
    # path_obj.parent obtiene la carpteta contenedora (e. "data/")
    # mkdir crea el directorio si no existe: exist_ok evita errores si ya existía
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 2. Establecemos conexión con SQLite
        print(f"    ├─ Conectando a la base de datos en '{db_path}'...")
        conn = sqlite3.connect(db_path)

        # 3. Carga optimizada por lotes (chunksize)
        rows_to_load = len(df)
        print(f"    ├─ Insertando {rows_to_load:,} registros en la tabla '{table_name}' (Estrategia: {if_exists_strategy})...")

        df.to_sql(
            name=table_name,
            con=conn,
            if_exists=if_exists_strategy,
            index=False,
            chunksize=5000 # Inyectamos en bloques de 5,000 filas para mayor eficiencia
        )

        # 4. Validacion posterior a la carga mediante consulta SQL
        # El 'cursor' actúa como el canal para ejecutar comandos y leer resultados de la BD
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        # cursor.fetchone() devuelve una tupla con la primera fila del resultado; [0] toma la cuenta
        inserted_count = cursor.fetchone()[0]
        # Cerramos la conexión para liberar el archivo .db
        conn.close()

        print(f"    └─ Verificación de carga exitosa: {inserted_count:,} filas en la tabla '{table_name}'.")
        print("✅ Proceso de carga completado con éxito.\n")

    except Exception as e:
        print(f"❌ Error durante el proceso de carga a la base de datos: {e}")
        raise e

if __name__ == '__main__':
    # Prueba unitaria del módulo de Carga (Usando el Pipeline previo)
    from extract import extract_from_sqlite
    from transform import transform_data

    print("--- PRUEBA UNITARIA MÓDULO LOAD ---")
    df_raw = extract_from_sqlite()
    df_transformed = transform_data(df_raw)

    # Ejecutamos la carga
    load_to_sqlite(df_transformed)