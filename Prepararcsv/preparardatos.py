import pandas as pd


ARCHIVO_ENTRADA = "../data/buildings.csv"   
ARCHIVO_SALIDA  = "../data/buildings.csv"   

ZONAS = {
    "Z1_Providencia":     {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600},
    "Z2_LasCondes":       {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550},
    "Z3_Maipu":           {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740},
    "Z4_SantiagoCentro":  {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630},
    "Z5_Pudahuel":        {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760},
}

print("Leyendo CSV original...")
df = pd.read_csv(ARCHIVO_ENTRADA)

print(f"Columnas encontradas: {list(df.columns)}")
print(f"Total filas originales: {len(df):,}")

columnas_necesarias = ['latitude', 'longitude', 'area_in_meters', 'confidence']
df = df[columnas_necesarias]
filtros = []
for nombre, z in ZONAS.items():
    mask = (
        (df['latitude']  >= z['lat_min']) & (df['latitude']  <= z['lat_max']) &
        (df['longitude'] >= z['lon_min']) & (df['longitude'] <= z['lon_max'])
    )
    zona_df = df[mask].copy()
    print(f"  {nombre}: {len(zona_df):,} edificios")
    filtros.append(zona_df)

df_filtrado = pd.concat(filtros).drop_duplicates().reset_index(drop=True)

print(f"\nTotal después de filtrar: {len(df_filtrado):,} edificios")
print(f"Columnas finales: {list(df_filtrado.columns)}")


df_filtrado.to_csv(ARCHIVO_SALIDA, index=False)