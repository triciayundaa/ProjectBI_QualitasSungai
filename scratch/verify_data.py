import pandas as pd
import urllib.parse
from sqlalchemy import create_engine

# Database settings matching app/database.py
DB_USER = "neondb_owner"                                    
DB_PASSWORD = "npg_zVKmec8J7akt"        
DB_HOST = "ep-proud-breeze-aptumjmv-pooler.c-7.us-east-1.aws.neon.tech"                
DB_NAME = "neondb"                                         

parsed_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{parsed_password}@{DB_HOST}/{DB_NAME}?sslmode=require"

engine = create_engine(DATABASE_URL)

print("Connecting to database...")
query = """
    SELECT 
        f.id_pengukuran,
        s.nama_sungai,
        s.id_titik_sampel,
        s.latitude,
        s.longitude,
        p.nama_parameter,
        p.jenis_parameter,
        p.baku_mutu_min,
        p.baku_mutu_max,
        w.periode_pemantauan,
        w.tahun_data,
        w.label_periode,
        st.label_status,
        f.hasil_pengukuran,
        f.status_exceed,
        f.rasio_terhadap_bm,
        f.is_valid
    FROM fact_pengukuran f
    JOIN dim_sungai s ON f.id_sungai = s.id_sungai
    JOIN dim_parameter p ON f.id_parameter = p.id_parameter
    JOIN dim_waktu w ON f.id_waktu = w.id_waktu
    JOIN dim_status st ON f.id_status = st.id_status
"""
with engine.connect() as conn:
    df = pd.read_sql(query, conn)

print(f"Total rows in df: {len(df)}")
df_valid = df[df['is_valid'] == True]
print(f"Total valid rows in df: {len(df_valid)}")

total_exceed = df_valid['status_exceed'].sum()
pct_exceed = (total_exceed / len(df_valid) * 100) if len(df_valid) > 0 else 0.0
print(f"Total exceed: {total_exceed} ({pct_exceed:.2f}%)")

# 1. Total Coliform Maks
df_coliform = df_valid[df_valid['nama_parameter'].isin(['Total Coliform', 'Fecal Coliform'])]
if len(df_coliform) > 0:
    max_coliform_idx = df_coliform['hasil_pengukuran'].idxmax()
    max_coliform_val = df_coliform.loc[max_coliform_idx, 'hasil_pengukuran']
    max_coliform_sungai = df_coliform.loc[max_coliform_idx, 'nama_sungai']
    print(f"Max Coliform: {max_coliform_val} MPN/100ml at {max_coliform_sungai}")
else:
    print("No Coliform data")

# 2. DO Terendah Rata-rata
df_do = df_valid[df_valid['nama_parameter'] == 'Do']
if len(df_do) > 0:
    do_by_river = df_do.groupby('nama_sungai')['hasil_pengukuran'].mean()
    min_do_river = do_by_river.idxmin()
    min_do_val = do_by_river.min()
    print(f"Min DO River: {min_do_river} with mean DO: {min_do_val:.4f} mg/L")
else:
    print("No DO data")

# 3. Ranking Pelanggaran per Sungai
print("\n--- Top 10 Sungai Pelanggaran Terbanyak ---")
df_rank = df_valid[df_valid['status_exceed'] == True].groupby('nama_sungai').size().sort_values(ascending=False).head(10)
print(df_rank)

# 4. Tren Pelanggaran per Periode
print("\n--- Tren Pelanggaran per Periode ---")
df_trend = df_valid[df_valid['status_exceed'] == True].groupby('periode_pemantauan').size()
print(df_trend)

# 5. Top 10 Parameter Paling Sering Melanggar
print("\n--- Top 10 Parameter Melanggar ---")
df_param = df_valid[df_valid['status_exceed'] == True].groupby('nama_parameter').size().sort_values(ascending=False).head(10)
print(df_param)

# 6. Rata-rata COD
df_cod = df_valid[df_valid['nama_parameter'] == 'Cod']
if len(df_cod) > 0:
    cod_by_river = df_cod.groupby('nama_sungai')['hasil_pengukuran'].mean().sort_values(ascending=False)
    print("\n--- Top 5 Sungai Rata-rata COD Tertinggi ---")
    print(cod_by_river.head(5))

# 7. Priority Table (Top 8 by % Pelanggaran)
df_counts = df_valid.groupby('nama_sungai').agg(
    Total_Sampel=('status_exceed', 'count'),
    Total_Pelanggaran=('status_exceed', 'sum')
).reset_index()
df_counts['pct_pelanggaran'] = (df_counts['Total_Pelanggaran'] / df_counts['Total_Sampel'] * 100).round(1)
print("\n--- Tabel Prioritas (Top 8 % Pelanggaran) ---")
print(df_counts.sort_values(by='pct_pelanggaran', ascending=False).head(8))

# 8. Insight 1: Parameter Biologi
df_bio = df_valid[df_valid['jenis_parameter'] == 'Biologi']
total_bio = len(df_bio)
langgar_bio = df_bio['status_exceed'].sum()
pct_bio = (langgar_bio / total_bio * 100) if total_bio > 0 else 0.0
print(f"\nInsight 1: Bio exceed pct: {pct_bio:.2f}% (from {total_bio} samples, {langgar_bio} violations)")
