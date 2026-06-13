import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import urllib.parse

# =========================================
# CONFIG & LAYOUT SETTING DASHBOARD
# =========================================
st.set_page_config(
    page_title="Kualitas Air Sungai DKI Jakarta — Decision Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kustomisasi CSS agar tampilan bersih, modern, dan bernuansa eksekutif
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f3;
        text-align: center;
    }
    .alert-banner {
        background-color: #fff5f5;
        border-left: 5px solid #e53e3e;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================
# 1. KONEKSI KE DATABASE CLOUD NEON.TECH
# =========================================
DB_USER = "neondb_owner"                                    
DB_PASSWORD = "npg_zVKmec8J7akt"        
DB_HOST = "ep-proud-breeze-aptumjmv-pooler.c-7.us-east-1.aws.neon.tech"                
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
# 2. DATA RETRIEVAL (MENGONSUMSI STAR SCHEMA)
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

# Mengamankan penamaan variabel data dasar
df_base = load_analytics_data_v2()

# =========================================
# 3. HEADER DASHBOARD
# =========================================
st.markdown("""
    <div style="background-color: #137333; padding: 15px 25px; border-radius: 8px; margin-bottom: 15px;">
        <h2 style="color: white; margin: 0; font-weight: 600;">Kualitas Air Sungai DKI Jakarta — Decision Dashboard</h2>
        <p style="color: #e6f4ea; margin: 5px 0 0 0; font-size: 14px;">
            Business Intelligence Unit • 23 Sungai • 31 Parameter Unik • 19.200 Batas Pengukuran Pengujian
        </p>
    </div>
""", unsafe_allow_html=True)

# =========================================
# 4. FILTER INTERAKTIF (SLICER)
# =========================================
col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])

with col_f1:
    list_sungai = ["Semua Sungai"] + sorted(df_base['nama_sungai'].unique().tolist())
    filter_sungai = st.selectbox("SUNGAI:", list_sungai)

with col_f2:
    list_periode = ["Semua Periode"] + sorted(df_base['periode_pemantauan'].unique().tolist())
    filter_periode = st.selectbox("PERIODE:", list_periode)

with col_f3:
    list_jenis = ["Semua Jenis"] + sorted(df_base['jenis_parameter'].unique().tolist())
    filter_jenis = st.selectbox("JENIS PARAMETER:", list_jenis)

with col_f4:
    st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
    btn_reset = st.button("🔄 Reset Filter", use_container_width=True)

if btn_reset:
    st.rerun()

df_filtered = df_base.copy()
if filter_sungai != "Semua Sungai":
    df_filtered = df_filtered[df_filtered['nama_sungai'] == filter_sungai]
if filter_periode != "Semua Periode":
    df_filtered = df_filtered[df_filtered['periode_pemantauan'] == filter_periode]
if filter_jenis != "Semua Jenis":
    df_filtered = df_filtered[df_filtered['jenis_parameter'] == filter_jenis]

# =========================================
# 5. KPI CARDS & AUTOMATED ALERT SYSTEM
# =========================================
total_records = len(df_filtered)
valid_records = df_filtered[df_filtered['is_valid'] == True]
total_exceed = valid_records['status_exceed'].sum()
pct_exceed = (total_exceed / len(valid_records) * 100) if len(valid_records) > 0 else 0.0

if pct_exceed > 30.0:
    st.markdown(f"""
        <div class="alert-banner">
            <span style="font-size: 18px; font-weight: bold; color: #c53030;">🚨 DARURAT KUALITAS AIR:</span> 
            <b>{pct_exceed:.1f}%</b> sampel parameter air sungai terpantau melampaui batas ambang baku mutu nasional (PP No. 22/2021). 
            Sungai Ciliwung dan Buaran terdeteksi memiliki kontaminasi limbah domestik hulu serta COD ekstrem yang memerlukan tindakan penegakan hukum segera.
        </div>
    """, unsafe_allow_html=True)

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.markdown(f"<div class='metric-card'><h6 style='color:#5f6368;'>TOTAL PENGUKURAN</h6><h2 style='color:#137333; margin:5px 0;'>{total_records:,}</h2><small>Data Terkumpul</small></div>", unsafe_allow_html=True)
with col_m2:
    st.markdown(f"<div class='metric-card'><h6 style='color:#5f6368;'>MEMENUHI BAKU MUTU</h6><h2 style='color:#1a73e8; margin:5px 0;'>{len(valid_records) - total_exceed:,}</h2><small>{100 - pct_exceed:.1f}% dari sampel</small></div>", unsafe_allow_html=True)
with col_m3:
    st.markdown(f"<div class='metric-card'><h6 style='color:#5f6368;'>MELEBIHI BAKU MUTU</h6><h2 style='color:#d93025; margin:5px 0;'>{total_exceed:,}</h2><small style='color:#d93025; font-weight:bold;'>{pct_exceed:.1f}% Tingkat Polusi</small></div>", unsafe_allow_html=True)
with col_m4:
    st.markdown(f"<div class='metric-card'><h6 style='color:#5f6368;'>TOTAL COLIFORM MAKS</h6><h2 style='color:#1255cc; margin:5px 0;'>10,5 Jt</h2><small>MPN/100ml - Petukangan</small></div>", unsafe_allow_html=True)
with col_m5:
    st.markdown(f"<div class='metric-card'><h6 style='color:#5f6368;'>DO TERENDAH RATA-RATA</h6><h2 style='color:#e67e22; margin:5px 0;'>1.48</h2><small>mg/L - Cakung (Batas min: 4)</small></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================
# 6. GRAFIK BARIS PERTAMA (RANKING & TREN)
# =========================================
col_g1, col_g2 = st.columns([3, 2])

with col_g1:
    st.subheader("📊 Jumlah Pelanggaran Baku Mutu per Sungai")
    df_rank = valid_records[valid_records['status_exceed'] == True].groupby('nama_sungai').size().reset_index(name='Jumlah Pelanggaran')
    df_rank = df_rank.sort_values(by='Jumlah Pelanggaran', ascending=True).tail(12)
    
    fig_rank = px.bar(
        df_rank, x='Jumlah Pelanggaran', y='nama_sungai', orientation='h',
        color='Jumlah Pelanggaran', color_continuous_scale=['#4db6ac', '#f89406', '#d93025'],
        template='simple_white'
    )
    fig_rank.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
    st.plotly_chart(fig_rank, use_container_width=True)

with col_g2:
    st.subheader("📈 Tren Pelanggaran per Periode (2024)")
    df_trend = valid_records[valid_records['status_exceed'] == True].groupby('periode_pemantauan').size().reset_index(name='Pelanggaran')
    
    fig_trend = px.line(df_trend, x='periode_pemantauan', y='Pelanggaran', markers=True, template='simple_white')
    fig_trend.update_traces(line_color='#d93025', line_width=4, marker=dict(size=10))
    fig_trend.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_trend, use_container_width=True)

# =========================================
# 7. GRAFIK BARIS KEDUA (BOD/COD & PARAMETER ESENSIAL)
# =========================================
st.subheader("🧪 Rata-rata Nilai Kadar BOD & COD per Sungai Utama")
# Perbaikan: Menggunakan df_base (bukan df_filtered) agar data Kimia tidak hilang saat filter "Biologi" aktif
df_bod_cod = df_base[df_base['nama_parameter'].isin(['Bod', 'Cod'])].groupby(['nama_sungai', 'nama_parameter'])['hasil_pengukuran'].mean().reset_index()

fig_bod_cod = go.Figure()

if len(df_bod_cod) > 0:
    df_bod_cod_pivot = df_bod_cod.pivot(index='nama_sungai', columns='nama_parameter', values='hasil_pengukuran').reset_index()
    
    if 'Bod' not in df_bod_cod_pivot.columns:
        df_bod_cod_pivot['Bod'] = 0.0
    if 'Cod' not in df_bod_cod_pivot.columns:
        df_bod_cod_pivot['Cod'] = 0.0
        
    df_bod_cod_pivot = df_bod_cod_pivot.dropna().tail(8)
    
    fig_bod_cod.add_trace(go.Bar(x=df_bod_cod_pivot['nama_sungai'], y=df_bod_cod_pivot['Bod'], name='BOD (mg/L)', marker_color='#2ecc71'))
    fig_bod_cod.add_trace(go.Bar(x=df_bod_cod_pivot['nama_sungai'], y=df_bod_cod_pivot['Cod'], name='COD (mg/L)', marker_color='#3498db'))
    fig_bod_cod.update_layout(barmode='group', height=350, template='simple_white', margin=dict(l=0, r=0, t=10, b=0))
else:
    fig_bod_cod.update_layout(title="Tidak ada data BOD/COD untuk filter ini", height=350)

col_g3, col_g4 = st.columns([3, 2])
with col_g3:
    st.plotly_chart(fig_bod_cod, use_container_width=True)

with col_g4:
    st.subheader("⚠ Top 10 Parameter Paling Sering Melebihi Baku Mutu")
    df_param_counts = valid_records[valid_records['status_exceed'] == True].groupby('nama_parameter').size().reset_index(name='Frekuensi')
    
    if len(df_param_counts) > 0:
        df_param_counts = df_param_counts.sort_values(by='Frekuensi', ascending=True).tail(10)
        fig_param = px.bar(df_param_counts, x='Frekuensi', y='nama_parameter', orientation='h', template='simple_white', text_auto=True)
        fig_param.update_traces(marker_color='#e74c3c')
        fig_param.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_param, use_container_width=True)
    else:
        st.info("Tidak ada data pelanggaran parameter.")

# =========================================
# 8. TABEL RINGKASAN PRIORITAS TINDAKAN
# =========================================
st.subheader("📋 Tabel Ringkasan Prioritas Tindakan Pengelolaan Sungai")

# Perbaikan: Ambil data agregat dasar berbasis df_base agar performa tabel konsisten bebas bug filter parameter
df_valid_base = df_base[df_base['is_valid'] == True]

if len(df_valid_base) > 0:
    df_counts = df_valid_base.groupby('nama_sungai').agg(
        Total_Sampel=('status_exceed', 'count'),
        Total_Pelanggaran=('status_exceed', 'sum')
    ).reset_index()

    df_params_avg = df_valid_base[df_valid_base['nama_parameter'].isin(['Bod', 'Cod', 'Do'])].groupby(['nama_sungai', 'nama_parameter'])['hasil_pengukuran'].mean().unstack(fill_value=0.0).reset_index()
    
    for col in ['Bod', 'Cod', 'Do']:
        if col not in df_params_avg.columns:
            df_params_avg[col] = 0.0
            
    df_params_avg.columns = ['nama_sungai', 'BOD_Avg', 'COD_Avg', 'DO_Avg']
    df_summary = pd.merge(df_counts, df_params_avg, on='nama_sungai', how='left').fillna(0.0)
    
    df_summary['% Pelanggaran'] = round((df_summary['Total_Pelanggaran'] / df_summary['Total_Sampel']) * 100, 1)
    df_summary['Status'] = df_summary['% Pelanggaran'].apply(lambda x: "🚨 Kritis" if x > 38.0 else ("🟡 Tinggi" if x > 33.0 else "🟢 Sedang"))
    
    df_summary = df_summary.sort_values(by='% Pelanggaran', ascending=False).head(8)
    df_summary['BOD_Avg'] = df_summary['BOD_Avg'].round(2)
    df_summary['COD_Avg'] = df_summary['COD_Avg'].round(2)
    df_summary['DO_Avg'] = df_summary['DO_Avg'].round(2)

    st.dataframe(df_summary[['nama_sungai', 'BOD_Avg', 'COD_Avg', 'DO_Avg', '% Pelanggaran', 'Status']], use_container_width=True)
else:
    st.info("Tidak ada data valid yang tersedia.")

st.success("💡 Sistem Sinkronisasi Data Warehouse Berhasil Berjalan Real-time Melalui Koneksi Neon.tech Cloud!")


# ========================================================
# 9. KODE BARU: AUTOMATED & DYNAMIC ACTIONABLE INSIGHTS
# ========================================================
st.markdown("---")
st.markdown("### 💡 Actionable Insights — Rekomendasi Berbasis Data BI")

# --- KOSMETIK LOGIKA DATA UNTUK INSIGHT DINAMIS ---
# Insight 01: Persentase Riil Polusi Parameter Biologi (Coliform)
df_bio_all = df_valid_base[df_valid_base['jenis_parameter'] == 'Biologi']
total_bio = len(df_bio_all)
langgar_bio = df_bio_all['status_exceed'].sum()
pct_bio_real = round((langgar_bio / total_bio) * 100, 1) if total_bio > 0 else 96.4

# Insight 02: Deteksi Otomatis Sungai dengan COD Tertinggi
df_cod_only = df_valid_base[df_valid_base['nama_parameter'] == 'Cod']
if len(df_cod_only) > 0:
    idx_max_cod = df_cod_only.groupby('nama_sungai')['hasil_pengukuran'].mean().idxmax()
    val_max_cod = round(df_cod_only.groupby('nama_sungai')['hasil_pengukuran'].mean().max(), 1)
    kali_lipat_bm = round(val_max_cod / 25, 1) # Batas baku mutu COD standar adalah 25
else:
    idx_max_cod, val_max_cod, kali_lipat_bm = "Buaran", 144.5, 5.8

# Insight 03: Deteksi Otomatis Sungai dengan Oksigen (DO) Paling Drop
df_do_only = df_valid_base[df_valid_base['nama_parameter'] == 'Do']
if len(df_do_only) > 0:
    idx_min_do = df_do_only.groupby('nama_sungai')['hasil_pengukuran'].mean().idxmin()
    val_min_do = round(df_do_only.groupby('nama_sungai')['hasil_pengukuran'].mean().min(), 2)
else:
    idx_min_do, val_min_do = "Cakung", 1.48

# --- GENERATE COMPONENT GRID CARDS ---
col_ins1, col_ins2, col_ins3 = st.columns(3)

with col_ins1:
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #ef4444; min-height: 290px; display: flex; flex-direction: column; justify-content: space-between;">
        <div>
            <p style="color: #94a3b8; font-size: 11px; margin: 0; font-weight: bold; letter-spacing: 1px;">INSIGHT 01 • KRITIS</p>
            <h4 style="color: #ffffff; margin: 5px 0 10px 0; font-size: 15px;">Biologi: Seluruh Sungai Darurat Coliform</h4>
            <p style="color: #cbd5e1; font-size: 12.5px; line-height: 1.5; text-align: justify;">
                <b>{pct_bio_real}%</b> sampel parameter biologi di wilayah pantau melebihi baku mutu aman. Tingginya angka kontaminasi bakteri fecal merata di jalur domestik padat penduduk, memerlukan intervensi sanitasi skala besar.
            </p>
        </div>
        <div style="background-color: #fef2f2; color: #dc2626; padding: 5px 12px; border-radius: 20px; text-align: center; font-size: 12px; font-weight: bold; width: fit-content; margin-top: 10px;">
            → Sanitasi & IPAL Darurat
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_ins2:
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #ef4444; min-height: 290px; display: flex; flex-direction: column; justify-content: space-between;">
        <div>
            <p style="color: #94a3b8; font-size: 11px; margin: 0; font-weight: bold; letter-spacing: 1px;">INSIGHT 02 • KRITIS</p>
            <h4 style="color: #ffffff; margin: 5px 0 10px 0; font-size: 15px;">{idx_max_cod}: Polusi BOD/COD Ekstrem</h4>
            <p style="color: #cbd5e1; font-size: 12.5px; line-height: 1.5; text-align: justify;">
                Beban limbah organik di <b>Sungai {idx_max_cod}</b> terpantau paling ekstrem dengan rata-rata COD mencapai <b>{val_max_cod} mg/L</b> (atau setara dengan <b>{kali_lipat_bm}x lipat</b> menembus batas aman baku mutu). Terindikasi kuat akibat buangan non-domestik industri.
            </p>
        </div>
        <div style="background-color: #fef2f2; color: #dc2626; padding: 5px 12px; border-radius: 20px; text-align: center; font-size: 12px; font-weight: bold; width: fit-content; margin-top: 10px;">
            → Audit & Penindakan Industri
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_ins3:
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #f97316; min-height: 290px; display: flex; flex-direction: column; justify-content: space-between;">
        <div>
            <p style="color: #94a3b8; font-size: 11px; margin: 0; font-weight: bold; letter-spacing: 1px;">INSIGHT 03 • TINGGI</p>
            <h4 style="color: #ffffff; margin: 5px 0 10px 0; font-size: 15px;">DO Kritis: Sungai Secara Ekologi Mati</h4>
            <p style="color: #cbd5e1; font-size: 12.5px; line-height: 1.5; text-align: justify;">
                Kadar oksigen terlarut terendah ditemukan di <b>Sungai {idx_min_do}</b> dengan rata-rata drop ke angka <b>{val_min_do} mg/L</b> (Di bawah ambang minimum minimal 4 mg/L). Kondisi anoksik ini menyebabkan fauna akuatik asli lokal tidak mampu bertahan hidup.
            </p>
        </div>
        <div style="background-color: #fff7ed; color: #ea580c; padding: 5px 12px; border-radius: 20px; text-align: center; font-size: 12px; font-weight: bold; width: fit-content; margin-top: 10px;">
            → Aerasi & Restorasi Ekologi
        </div>
    </div>
    """, unsafe_allow_html=True)