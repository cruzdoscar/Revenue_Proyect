import pandas as pd
import numpy as np

def clean_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza la imputación de valores nulos y optimiza el tipo de datos.
    """
    df = df.copy()

    # Contar nulos iniciales para reporte
    nulls_before = df.isnull().sum().sum()

    # 1. Imputación de valores nulos
    # Rellenamos los valores nulos de 'adr' con la mediana del grupo definido por 'hotel' y 'customer_type'
    df['adr'] = df.groupby(['hotel', 'customer_type'], observed= False)['adr'].transform(lambda x: x.fillna(x.median()))

    # Imputación genérica por tipo de dato
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].fillna(0)
        else:
            df[column] = df[column].fillna('Unknown')

    nulls_after = df.isnull().sum().sum()

    print(f"    ├─ Valores nulos imputados: {nulls_before - nulls_after} (Nulos restantes: {nulls_after})")

    # 2. Conversión de tipos de dato
    # Conversion de fechas
    df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'])

    # Convertimos variables catégoricas repetitivas para reducir consumo de memoria
    cat_cols = [
    'hotel', 'arrival_date_year', 'arrival_date_month', 'meal',
    'market_segment', 'distribution_channel', 'deposit_type', 'customer_type', 
    'reservation_status'
    ]

    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype('category')

    # Casteo explícito a entero para columnas numéricas discretas (excepto 'adr' y fechas)
    converted_to_int = 0
    for col in df.columns:
        if col != 'adr' and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(int)
            converted_to_int += 1

    return df

def remove_system_duplicates(df: pd.DataFrame, threshold_pct: float = 5.0, auto_approve: bool = False) -> pd.DataFrame:
    """
    Filtra únicamente los registros duplicados que corresponden a un bug de sistema:
    - Canal Directo ('Direct')
    - Sin Agente/Empresa (agent==0, company==0)
    - Cliente de tipo 'Transient'
    - Frecuencia de repetición >= 3

    Incluye una regla de seguridad que solicita confirmación interactiva si el porcentaje
    de duplicados supera el umbral definido (por defecto 5%).
    """

    df = df.copy()

    # Columnas que definirán la 'huella digital' de una reserva
    subset_cols = [col for col in df.columns if col not in ['reservation_status', 'reservation_status_date']]

    # Identificamos filas completamente idénticas
    dup_mask = df.duplicated(subset=subset_cols, keep=False)

    # Regla de negocio para aislar fallos del sistema
    system_bug_mask = (
        dup_mask &
        (df['distribution_channel'] == 'Direct') &
        (df['market_segment'] == 'Direct') &
        (df['agent'] == 0) &
        (df['company'] == 0) &
        (df['customer_type'] == 'Transient')
    )

    # Contamos las repeticiones exactas bajo el criterio de bug
    bug_counts = df[system_bug_mask].groupby(subset_cols, observed=True).size()
    bug_fingerprints = set(bug_counts[bug_counts >= 3].index)

    # Filtramos descartando los duplicados verdaderos del bug (dejando solo la primera reserva)
    def is_bug_duplicate(row):
        fingerprint = tuple(row[col] for col in subset_cols)
        return fingerprint in bug_fingerprints

    # Marcamos y eliminamos únicamente el excedente de duplicados del sistema
    duplicates_to_remove = df[system_bug_mask].duplicated(subset=subset_cols, keep='first') & df[system_bug_mask].apply(is_bug_duplicate, axis=1)

    cant_duplicados = duplicates_to_remove.sum()
    total_registros = len(df)
    porcentaje_error_sistema = (cant_duplicados / total_registros) * 100

    print(f"    ├─ Duplicados de bug de sistema detectados: {cant_duplicados} ({porcentaje_error_sistema:.2f}% sobre el total de {total_registros:,} registros)")

    # Validación de umbral de seguridad
    proceder_eliminacion = True

    if porcentaje_error_sistema > threshold_pct and not auto_approve:
        print(f"    ⚠️ ALERTA: El volumen de duplicados ({porcentaje_error_sistema:.2f}%) supera el umbral de seguridad de {threshold_pct}%.")
        
        # Bucle de interacción en la terminal
        while True:
            respuesta = input("    ❓ ¿Desea continuar y eliminar estos registros duplicados? (S/N): ").strip().upper()
            if respuesta in ['S', 'Y', 'SI', 'YES']:
                proceder_eliminacion = True
                break
            elif respuesta in ['N', 'NO']:
                proceder_eliminacion = False
                print("    ⛔ Eliminación cancelada por el usuario. Se conservan todos los registros originales.")
                break
            else:
                print("    ⚠️ Opción inválida. Responda 'S' para Sí o 'N' para No.")

    # Aplicamos la eliminación según la decisión
    if proceder_eliminacion and cant_duplicados > 0:
        clean_df = df.drop(index=duplicates_to_remove[duplicates_to_remove].index)
        print(f"    ├─ Duplicados eliminados exitosamente")
        print(f"    └─ Registros restantes tras deduplicación: {len(clean_df):,}")
        return clean_df
    else:
        print(f"    └─ Registros conservados tras deduplicación: {len(df):,}")

    return clean_df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables avanzadas para análisis de Revenue Management
    """
    df = df.copy()

    # Total de noches y huspedes
    df['total_nights'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
    df['total_guests'] = df['adults'] + df['children'] + df['babies']

    # Metricas de upsell
    # Validamos si el tipo de habitacion reservada es el mismo tipo de habitacion asignada
    df['roomtype_match'] = df['reserved_room_type'] == df['assigned_room_type']

    # Etiquetamos Upgrade/Downgrade
    def get_roomtype_status(row):
        reserved = str(row['reserved_room_type'])
        assigned = str(row['assigned_room_type'])
        if row['roomtype_match']:
            return 'Normal'
        elif reserved < assigned:
            return 'Upgrade'
        elif reserved > assigned:
            return 'Downgrade'

    df['assigned_status'] = df.apply(get_roomtype_status, axis=1).astype('category')

    # Metricas financieras
    df['potencial_revenue'] = df['adr'] * df['total_nights']
    df['adr_per_guest'] = np.where(df['total_guests'] > 0, df['adr'] / df['total_guests'], 0)

    # Ratios de reservas
    df['lead_stay_ratio'] = np.where(df['total_nights'] > 0, df['lead_time'] / df['total_nights'], df['lead_time'])

    # Calculamos el total historico de reservas por huesped para la creacion de 'cancellation_ratio'
    total_reservations = df['previous_cancellations'] + df['previous_bookings_not_canceled']
    # Calculamos el ratio. Si el cliente no tiene historial previo (es su primera vez), su ratio es 0.
    df['cancellation_ratio'] = np.where(total_reservations > 0, df['previous_cancellations'] / total_reservations, 0)

    # Clasificacion de sesgo de estancia
    def get_stay_bias(row):
        wknd = row['stays_in_weekend_nights']
        wk = row['stays_in_week_nights']
        if wknd > 0 and wk == 0:
            return 'Pure Weekend'
        elif wknd > wk:
            return 'Weekend Heavy'
        elif wk > 0 and wknd == 0:
            return 'Pure Week'
        elif wk > wknd:
            return 'Weekday Heavy'
        elif wknd > 0 and wk > 0:
            return 'Mixed Stay'
        return 'Day use'

    df['stay_duration_bias'] = df.apply(get_stay_bias, axis=1).astype('category')

    # Creación del índice de modificaciones por noche 'changes_per_night'
    # Lógica: Si las noches son mayores a 0, dividimos los cambios entre las noches. Si es 0, dejamos los cambios base.
    df['changes_per_night'] = np.where(df['total_nights'] > 0, df['booking_changes'] / df['total_nights'], df['booking_changes'])

    # ==========================================
    # ESTACIONALIDAD DINÁMICA POR TIPO DE HOTEL
    # ==========================================
    orden_meses = ['January', 'February', 'March', 'April', 'May', 'June', 
               'July', 'August', 'September', 'October', 'November', 'December']

    # Convertimos temporalmente a str para agrupar sin problemas por categorías
    df_temp = df.copy()
    df_temp['hotel_str'] = df_temp['hotel'].astype(str)
    df_temp['month_str'] = df_temp['arrival_date_month'].astype(str)

    # RESORT HOTEL
    # Filtramos el dataset para quedarnos SOLO con el hotel de playa
    df_resort = df_temp[df_temp['hotel_str'] == 'Resort Hotel']
    diagnostico_resort = df_resort.groupby('month_str', observed=False).agg(total_reservas=('adr', 'count'), precio_promedio=('adr', 'mean'))
    resort_ordenado = diagnostico_resort.reindex(orden_meses).reset_index()
    resort_ordenado['ingreso_proxy'] = (resort_ordenado['total_reservas'] * resort_ordenado['precio_promedio'])
    resort_ordenado['seasonality'] = pd.qcut(resort_ordenado['ingreso_proxy'], q=3, labels=['Low', 'Medium', 'High'])
    resort_ordenado['hotel'] = 'Resort Hotel'

    # CITY HOTEL
    # Filtramos el dataset para quedarnos SOLO con el hotel de ciudad
    df_city = df_temp[df_temp['hotel_str'] == 'City Hotel']
    diagnostico_city = df_city.groupby('month_str', observed=False).agg(total_reservas=('adr', 'count'), precio_promedio=('adr', 'mean'))
    city_ordenado = diagnostico_city.reindex(orden_meses).reset_index()
    city_ordenado['ingreso_proxy'] = (city_ordenado['total_reservas'] * city_ordenado['precio_promedio'])
    city_ordenado['seasonality'] = pd.qcut(city_ordenado['ingreso_proxy'], q=3, labels=['Low', 'Medium', 'High'])
    city_ordenado['hotel'] = 'City Hotel'

    # CRUCE DE INFORMACION
    resort_ordenado = resort_ordenado.rename(columns={'month_str': 'arrival_date_month'})
    city_ordenado = city_ordenado.rename(columns={'month_str': 'arrival_date_month'})
    ref_cols = ['hotel', 'arrival_date_month', 'seasonality']
    df_seasson = pd.concat([resort_ordenado[ref_cols], city_ordenado[ref_cols]], ignore_index=True)

    # Convertimos llaves a string para asegurar el merge
    df['hotel_str'] = df['hotel'].astype(str)
    df['month_str'] = df['arrival_date_month'].astype(str)

    df = pd.merge(df, df_seasson, left_on=['hotel_str', 'month_str'], right_on=['hotel', 'arrival_date_month'], suffixes=('', '_ref'), how='left')

    # Limpiamos las columnas auxiliares creadas para el merge
    df = df.drop(columns=['hotel_str', 'month_str', 'hotel_ref', 'arrival_date_month_ref'], errors='ignore')

    print(f"    ├─ Variables para análisis y ML generadas")
    print(f"    └─ Estacionalidad agrupada correctamente para Resort y City Hotel.")

    return df

def transform_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Función principal que orquesta todas las fases de transformación.
    """
    print("🧹 Iniciando proceso de transformación...")

    print("  └─ Clean Missing & Types...")
    df_clean = clean_missing_data(df_raw)

    print("  └─ Deduplicating System Bugs...")
    df_dedup = remove_system_duplicates(df_clean, threshold_pct=5, auto_approve=False)

    print("  └─ Feature Engineering (Revenue Metrics)...")
    df_transformed = engineer_features(df_dedup)

    print(f"✅ Transformación completada. Dimensión final: {df_transformed.shape}")
    return df_transformed

if __name__ == "__main__":
    # Prueba de la etapa de transformación integrando con extract
    from extract import extract_from_sqlite

    df_raw = extract_from_sqlite()
    df_clean = transform_data(df_raw)
    print("\nResumen de columnas generadas:")
    print(df_clean[['total_nights', 'total_guests', 'roomtype_match', 'assigned_status', 'potencial_revenue', 'adr_per_guest', 'lead_stay_ratio', 'cancellation_ratio', 'stay_duration_bias', 'changes_per_night', 'seasonality']].sample(5))
