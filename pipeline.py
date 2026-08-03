import time
from src.extract import extract_from_sqlite
from src.transform import transform_data
from src.load import load_to_sqlite

def run_pipeline() -> None: # EXPLCIAME QUE HACE EL '->' PORQUE ANTES PONIAMOS UN 'pd.DataFrame' Y AHORA UN 'None' PERO NO SE QUE HAGA EXACTAMENTE
    """
    Orquestador principal del Pipeline ETL de Revenue Management.
    Ejecuta en secuencia la Extracción, Transfromación y Carga de datos,
    midiendo el timepo total de ejecución.
    """

    start_time = time.time()

    print("=" * 60)
    print("🚀 INICIANDO PIPELINE ETL DE REVENUE MANAGEMENT")
    print("=" * 60)

    try:
        print("\n1️⃣    [FASE DE EXTRACCIÓN]\n")
        df_raw = extract_from_sqlite()
        print(f"   └─ Registros extraídos exitosamente: {len(df_raw):,}\n")

        # FASE 2: TRANSFORMACIÓN
        print("2️⃣    [FASE DE TRANSFORMACIÓN]\n")
        df_transformed = transform_data(df_raw)
        print(f"   └─ Registros listos tras transformación: {len(df_transformed):,}\n")

        # FASE 3: CARGA
        print("3️⃣    [FASE DE CARGA]\n")
        load_to_sqlite(
            df=df_transformed, 
            db_path="data/hotel_data.db", 
            table_name="clean_bookings", 
            if_exists_strategy="replace"
        )

        # RESUMEN Y TIEMPOS
        elapsed_time = time.time() - start_time
        print("=" * 60)
        print(f"🎉 PIPELINE COMPLETADO CON ÉXITO EN {elapsed_time:.2f} SEGUNDOS")
        print("=" * 60)

    except Exception as e:
        print("\n" + "!" * 60)
        print(f"❌ EL PIPELINE HA FALLADO DEBIDO A UN ERROR: {e}")
        print("!" * 60)
        raise e

if __name__ == "__main__":
    run_pipeline()