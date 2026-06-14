import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse

# =========================================
# KONEKSI KE DATABASE CLOUD NEON.TECH
# =========================================
DB_USER = "neondb_owner"                                    
DB_PASSWORD = "npg_zLeYAr0RQu6X"        
DB_HOST = "ep-polished-frost-aivnaxzq-pooler.c-4.us-east-1.aws.neon.tech"                
DB_NAME = "neondb"                                         

parsed_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{parsed_password}@{DB_HOST}/{DB_NAME}?sslmode=require"

@st.cache_resource
def get_db_engine():
    return create_engine(DATABASE_URL)

try:
    engine = get_db_engine()
except Exception as e:
    st.error(f"Gagal terhubung ke Cloud Data Warehouse: {e}")
    st.stop()

# =========================================
# DATA RETRIEVAL (MENGONSUMSI STAR SCHEMA)
# =========================================
@st.cache_data(ttl=600)
def load_analytics_data_v2():
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
    df = pd.read_sql(query, engine)
    return df
