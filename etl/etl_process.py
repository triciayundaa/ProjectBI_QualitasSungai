import os
import re
import pandas as pd
import numpy as np
import urllib.parse
from sqlalchemy import create_engine, text

def clean_coordinate(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    
    try:
        return float(val_str)
    except ValueError:
        pass
    
    pattern = r'(-?\d+(?:\.\d+)?)[^\d\.\-]+(\d+(?:\.\d+)?)[^\d\.\-]+(\d+(?:\.\d+)?)[^\d\.\-]*\s*([SNEWsnew]?)'
    match = re.search(pattern, val_str)
    if match:
        deg = float(match.group(1))
        minute = float(match.group(2))
        sec = float(match.group(3))
        direction = match.group(4).upper()
        
        is_negative = False
        if deg < 0:
            is_negative = True
            deg = abs(deg)
            
        decimal = deg + (minute / 60.0) + (sec / 3600.0)
        if is_negative:
            decimal = -decimal
            
        if direction in ['S', 'W'] and decimal > 0:
            decimal = -decimal
        elif direction in ['N', 'E'] and decimal < 0:
            decimal = abs(decimal)
            
        return round(decimal, 7)
    
    return None

print("=========================================")
print("     PROSES ETL DATA KUALITAS AIR        ")
print("=========================================")

# =========================================
# 1. KONFIGURASI DATABASE CLOUD (NEON.TECH)
# =========================================
DB_USER = "neondb_owner"                                    
DB_PASSWORD = "npg_zLeYAr0RQu6X"        
DB_HOST = "ep-polished-frost-aivnaxzq-pooler.c-4.us-east-1.aws.neon.tech"                
DB_NAME = "neondb"                                         

parsed_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{parsed_password}@{DB_HOST}/{DB_NAME}?sslmode=require"

try:
    engine = create_engine(DATABASE_URL)
    print("[SUCCESS] Koneksi database siap!")
except Exception as e:
    print(f"[ERROR] Gagal membuat engine database: {e}")
    exit()

# =========================================
# 2. EXTRACT: Membaca Dataset CSV
# =========================================
csv_path = os.path.join("dataset", "Filedata Data Kualitas Air Sungai.csv")
print(f"\n[INFO] 1. Extract: Membaca file {csv_path}...")

if not os.path.exists(csv_path):
    print(f"[ERROR] File dataset tidak ditemukan di: {csv_path}")
    exit()

df_raw = pd.read_csv(csv_path)
print(f"[SUCCESS] Berhasil membaca {len(df_raw)} baris data mentah.")

# =========================================
# 3. TRANSFORM: Pembersihan & Normalisasi Data
# =========================================
print("\n[INFO] 2. Transform: Melakukan pembersihan data...")
df_clean = df_raw.copy()

df_clean['nama_sungai'] = df_clean['nama_sungai'].str.strip().str.title()
df_clean['parameter'] = df_clean['parameter'].str.strip()
df_clean['parameter'] = df_clean['parameter'].apply(lambda x: 'pH' if x.upper() == 'PH' else x.title())
df_clean['jenis_parameter'] = df_clean['jenis_parameter'].str.strip().str.title()

df_clean['periode_pemantauan'] = df_clean['periode_pemantauan'].astype(str).str.strip()
df_clean['periode_pemantauan'] = df_clean['periode_pemantauan'].apply(
    lambda x: f"Periode {x}" if x in ['1', '2', '3', '4'] else x
)

df_clean['latitude'] = df_clean['latitude'].apply(clean_coordinate)
df_clean['longitude'] = df_clean['longitude'].apply(clean_coordinate)

df_clean['is_valid'] = True
df_clean.loc[df_clean['hasil_pengukuran'] <= 0, 'is_valid'] = False

def extract_baku_mutu(row):
    param = row['parameter']
    val = str(row['baku_mutu']).strip()
    if param == 'pH':
        return 6.0, 9.0
    if val == '-' or val.upper() == 'NIHIL' or val == '':
        return None, None
    try:
        return None, float(val.replace(',', '.'))
    except:
        return None, None

bm_limits = df_clean.apply(extract_baku_mutu, axis=1)
df_clean['baku_mutu_min'] = [x[0] for x in bm_limits]
df_clean['baku_mutu_max'] = [x[1] for x in bm_limits]

def hitung_status_exceed(row):
    hasil = row['hasil_pengukuran']
    p_name = row['parameter']
    b_min = row['baku_mutu_min']
    b_max = row['baku_mutu_max']
    if p_name == 'pH':
        return True if (hasil < b_min or hasil > b_max) else False
    if b_max is not None:
        return True if hasil > b_max else False
    return False

df_clean['status_exceed'] = df_clean.apply(hitung_status_exceed, axis=1)

def hitung_rasio(row):
    hasil = row['hasil_pengukuran']
    b_max = row['baku_mutu_max']
    if b_max and b_max > 0:
        return round(hasil / b_max, 4)
    return 0.0

df_clean['rasio_terhadap_bm'] = df_clean.apply(hitung_rasio, axis=1)
print("[SUCCESS] Transformasi dan kalkulasi KPI selesai.")

# =========================================
# 4. LOAD: Memasukkan Data ke Skema Bintang Cloud
# =========================================
print("\n[INFO] 3. Load: Memasukkan data ke tabel dimensi & fakta di Neon.tech...")

sql_file_path = os.path.join("database", "create_tables.sql")
if not os.path.exists(sql_file_path):
    print(f"[ERROR] File SQL '{sql_file_path}' tidak ditemukan.")
    exit()

try:
    with engine.begin() as conn:
        print("-> Membuat / Mereset skema database dengan menjalankan create_tables.sql...")
        conn.execute(text("DROP TABLE IF EXISTS fact_pengukuran, dim_sungai, dim_parameter, dim_waktu, dim_status CASCADE;"))
        
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
        
        statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]
        for statement in statements:
            conn.execute(text(statement))
            
        print("[SUCCESS] Struktur tabel berhasil diinisialisasi.")
        
        print("-> Mengisi Dim_Sungai...")
        sungai_data = df_clean[['nama_sungai', 'titik_sampel', 'latitude', 'longitude']].drop_duplicates()
        sungai_data.columns = ['nama_sungai', 'id_titik_sampel', 'latitude', 'longitude']
        sungai_data['wilayah_admin'] = 'DKI Jakarta'
        sungai_data.to_sql('dim_sungai', con=conn, if_exists='append', index=False)
        
        print("-> Mengisi Dim_Parameter...")
        param_data = df_clean[['parameter', 'jenis_parameter', 'baku_mutu_min', 'baku_mutu_max']].drop_duplicates()
        param_data.columns = ['nama_parameter', 'jenis_parameter', 'baku_mutu_min', 'baku_mutu_max']
        param_data['satuan'] = 'mg/L'
        param_data['keterangan'] = 'Normalisasi otomatis via ETL'
        param_data.to_sql('dim_parameter', con=conn, if_exists='append', index=False)
        
        print("-> Mengisi Dim_Waktu...")
        waktu_data = df_clean[['periode_pemantauan', 'periode_data']].drop_duplicates()
        waktu_data.columns = ['periode_pemantauan', 'tahun_data']
        waktu_data['urutan_periode'] = waktu_data['periode_pemantauan'].str.extract(r'(\d+)').astype(int)
        waktu_data['label_periode'] = waktu_data['tahun_data'].astype(str) + " - " + waktu_data['periode_pemantauan']
        waktu_data.to_sql('dim_waktu', con=conn, if_exists='append', index=False)
        
        print("-> Mengisi Dim_Status...")
        conn.execute(text("TRUNCATE TABLE dim_status CASCADE;"))
        status_rows = [
            {'id_status': 1, 'kode_status': 'AMAN', 'label_status': 'Aman', 'warna_indikator': 'hijau', 'deskripsi': 'Memenuhi baku mutu'},
            {'id_status': 2, 'kode_status': 'WASPADA', 'label_status': 'Waspada', 'warna_indikator': 'kuning', 'deskripsi': 'Sedikit melebihi batas'},
            {'id_status': 3, 'kode_status': 'KRITIS', 'label_status': 'Kritis', 'warna_indikator': 'oranye', 'deskripsi': 'Pencemaran sedang ekosistem terganggu'},
            {'id_status': 4, 'kode_status': 'SANGAT_KRITIS', 'label_status': 'Sangat Kritis', 'warna_indikator': 'merah', 'deskripsi': 'Pencemaran berat darurat komunal'}
        ]
        pd.DataFrame(status_rows).to_sql('dim_status', con=conn, if_exists='append', index=False)
        
        print("-> Memetakan ID dan Mengisi Fact_Pengukuran...")
        
        # Mengambil data ID resmi untuk pencocokan ID
        db_sungai = pd.read_sql("SELECT id_sungai, id_titik_sampel, nama_sungai FROM dim_sungai", con=conn)
        db_param = pd.read_sql("SELECT id_parameter, nama_parameter FROM dim_parameter", con=conn)
        db_waktu = pd.read_sql("SELECT id_waktu, periode_pemantauan, tahun_data FROM dim_waktu", con=conn)
        
        # Proses merge data fakta dengan id tabel dimensi secara aman
        df_fact = df_clean.merge(db_sungai, left_on='titik_sampel', right_on='id_titik_sampel', how='left')
        
        # Penanganan jika id_sungai kosong, gunakan nama sungai sebagai fallback
        if df_fact['id_sungai'].isna().sum() > 0:
            db_fallback = db_sungai[['id_sungai', 'nama_sungai']].drop_duplicates()
            df_fact['id_sungai'] = df_fact['id_sungai'].fillna(df_fact['nama_sungai_x'].map(db_fallback.set_index('nama_sungai')['id_sungai']))
            
        df_fact = df_fact.merge(db_param, left_on='parameter', right_on='nama_parameter', how='left')
        df_fact = df_fact.merge(db_waktu, left_on=['periode_pemantauan', 'periode_data'], right_on=['periode_pemantauan', 'tahun_data'], how='left')
        
        # Mengamankan nilai ID dari nilai kosong/null
        df_fact['id_sungai'] = df_fact['id_sungai'].fillna(1).astype(int)
        df_fact['id_parameter'] = df_fact['id_parameter'].fillna(1).astype(int)
        df_fact['id_waktu'] = df_fact['id_waktu'].fillna(1).astype(int)

        def tentukan_status_id(row):
            if not row['status_exceed']:
                return 1
            rasio = row['rasio_terhadap_bm']
            if rasio <= 1.5: return 2
            if rasio <= 3.0: return 3
            return 4

        df_fact['id_status'] = df_fact.apply(tentukan_status_id, axis=1)
        
        fact_upload = df_fact[[
            'id_sungai', 'id_parameter', 'id_waktu', 'id_status', 
            'hasil_pengukuran', 'status_exceed', 'rasio_terhadap_bm', 'is_valid'
        ]]
        
        fact_upload.to_sql('fact_pengukuran', con=conn, if_exists='append', index=False)
        print(f"[SUCCESS] Berhasil mengunggah {len(fact_upload)} baris data fakta ke Neon.tech cloud!")
except Exception as e:
    print(f"[ERROR] Gagal memproses ETL dan memuat data ke database: {e}")
    exit()

print("\n=========================================")
print("      PROSES ETL BERHASIL SELESAI        ")
print("=========================================")