import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from database import load_analytics_data_v2
from metrics import calculate_kpi_metrics, generate_alert_banner_html, generate_insights_data
import base64

# =========================================
# CONFIG & LAYOUT SETTING DASHBOARD
# =========================================
st.set_page_config(
    page_title="Kualitas Air Sungai DKI Jakarta — Decision Dashboard",
    page_icon="app/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS styles from app/style.css
try:
    with open("app/style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("style.css tidak ditemukan. Silakan pastikan file berada di folder app/style.css.")

# Load logo as base64 for header inline display
try:
    with open("app/logo.png", "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{encoded_logo}" style="background-color: white;height: 50px; margin-right: 18px; vertical-align: middle; border-radius: 8px; border: 2px solid rgba(255,255,255,0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.15);">'
except Exception:
    logo_html = ""

# Mengamankan penamaan variabel data dasar
df_base = load_analytics_data_v2()

# =========================================
# 3. HEADER DASHBOARD (Bleed to Edge)
# =========================================
header_html = f'<div style="background-color: #2563eb; padding: 20px 25px; border-radius: 0; margin-left: -5rem; margin-right: -5rem; margin-top: -1.5rem; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: flex; align-items: center;">{logo_html}<div><div style="color: white; margin: 0 0 4px 0; font-weight: 600; font-size: 26px; line-height: 1.2;">Kualitas Air Sungai DKI Jakarta — Decision Dashboard</div><div style="color: #dbeafe; margin: 0; font-size: 14px; line-height: 1.2;">Business Intelligence Unit • 23 Sungai • 31 Parameter Unik • 19.200 Batas Pengukuran Pengujian</div></div></div>'
st.markdown(header_html, unsafe_allow_html=True)

# =========================================
# 4. FILTER INTERAKTIF (SLICER)
# =========================================
col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])

# Inisialisasi session state untuk filter jika belum ada
if 'filter_sungai_key' not in st.session_state:
    st.session_state['filter_sungai_key'] = "Semua Sungai"
if 'filter_periode_key' not in st.session_state:
    st.session_state['filter_periode_key'] = "Semua Periode"
if 'filter_jenis_key' not in st.session_state:
    st.session_state['filter_jenis_key'] = "Semua Jenis"

# Fungsi callback untuk reset filter secara aman sebelum widget dirender kembali
def reset_filters():
    st.session_state['filter_sungai_key'] = "Semua Sungai"
    st.session_state['filter_periode_key'] = "Semua Periode"
    st.session_state['filter_jenis_key'] = "Semua Jenis"

with col_f1:
    list_sungai = ["Semua Sungai"] + sorted(df_base['nama_sungai'].unique().tolist())
    filter_sungai = st.selectbox("SUNGAI:", list_sungai, key='filter_sungai_key')

with col_f2:
    list_periode = ["Semua Periode"] + sorted(df_base['periode_pemantauan'].unique().tolist())
    filter_periode = st.selectbox("PERIODE:", list_periode, key='filter_periode_key')

with col_f3:
    list_jenis = ["Semua Jenis"] + sorted(df_base['jenis_parameter'].unique().tolist())
    filter_jenis = st.selectbox("JENIS PARAMETER:", list_jenis, key='filter_jenis_key')

with col_f4:
    st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("Reset Filter", on_click=reset_filters, use_container_width=True)

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

# Melakukan kalkulasi metrik secara modular via metrics.py
pct_exceed, total_exceed, val_coliform_str, desc_coliform_str, val_do_str, desc_do_str = calculate_kpi_metrics(
    valid_records, total_records
)

# Render Alert Banner secara dinamis
alert_html = generate_alert_banner_html(valid_records, filter_sungai, pct_exceed)
st.markdown(alert_html, unsafe_allow_html=True)

# Render KPI Cards dengan CSS Baru
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>TOTAL PENGUKURAN</div>
        <div class='metric-value' style='color:#1e293b;'>{total_records:,}</div>
        <div class='metric-desc'>Data Terkumpul</div>
    </div>
    """, unsafe_allow_html=True)
with col_m2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>MEMENUHI BAKU MUTU</div>
        <div class='metric-value' style='color:#137333;'>{len(valid_records) - total_exceed:,}</div>
        <div class='metric-desc'>{100 - pct_exceed:.1f}% dari sampel</div>
    </div>
    """, unsafe_allow_html=True)
with col_m3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>MELEBIHI BAKU MUTU</div>
        <div class='metric-value' style='color:#d93025;'>{total_exceed:,}</div>
        <div class='metric-desc' style='color:#d93025; font-weight:bold;'>{pct_exceed:.1f}% Tingkat Polusi</div>
    </div>
    """, unsafe_allow_html=True)
with col_m4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>TOTAL COLIFORM MAKS</div>
        <div class='metric-value' style='color:#1255cc;'>{val_coliform_str}</div>
        <div class='metric-desc'>{desc_coliform_str}</div>
    </div>
    """, unsafe_allow_html=True)
with col_m5:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>DO TERENDAH RATA-RATA</div>
        <div class='metric-value' style='color:#e67e22;'>{val_do_str}</div>
        <div class='metric-desc'>{desc_do_str}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================
# 6. ROW 1: PETA (KIRI 50%) & RANKING PELANGGARAN (KANAN 50%)
# =========================================
col_map, col_chart_rank = st.columns([1, 1])

with col_map:
    with st.container(border=True):
        st.subheader("Peta Sebaran Geografis Kualitas Air Sungai")
        df_map = df_filtered.dropna(subset=['latitude', 'longitude'])
        if len(df_map) > 0:
            df_map_points = df_map.groupby(['id_titik_sampel', 'nama_sungai']).agg(
                latitude=('latitude', 'first'),
                longitude=('longitude', 'first'),
                total_sampel=('status_exceed', 'count'),
                total_pelanggaran=('status_exceed', 'sum')
            ).reset_index()

            df_map_points['% Pelanggaran'] = (df_map_points['total_pelanggaran'] / df_map_points['total_sampel'] * 100).round(1)

            def get_color(pct):
                if pct > 38.0: return '#d93025' # Merah (Sangat Kritis)
                if pct > 33.0: return '#f89406' # Oranye (Kritis)
                if pct > 20.0: return '#f1c40f' # Kuning (Waspada)
                return '#137333' # Hijau (Aman)

            df_map_points['color'] = df_map_points['% Pelanggaran'].apply(get_color)

            center_lat = df_map_points['latitude'].mean() if not pd.isna(df_map_points['latitude'].mean()) else -6.2088
            center_lon = df_map_points['longitude'].mean() if not pd.isna(df_map_points['longitude'].mean()) else 106.8456
            m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB positron")

            for _, row in df_map_points.iterrows():
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; font-size: 12px; width: 200px;">
                    <h5 style="margin: 0 0 5px 0; color: #137333;">{row['nama_sungai']}</h5>
                    <b>Titik Sampel:</b> {row['id_titik_sampel']}<br>
                    <b>Total Pengukuran:</b> {row['total_sampel']}<br>
                    <b>Rasio Pelanggaran:</b> <span style="color: {row['color']}; font-weight: bold;">{row['% Pelanggaran']}%</span>
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=8,
                    popup=folium.Popup(popup_html, max_width=250),
                    color=row['color'],
                    fill=True,
                    fill_color=row['color'],
                    fill_opacity=0.7,
                    weight=2
                ).add_to(m)

            st_folium(m, height=450, use_container_width=True)
        else:
            st.info("Tidak ada data koordinat geografis yang valid untuk filter saat ini.")

with col_chart_rank:
    with st.container(border=True):
        st.subheader("Jumlah Pelanggaran Baku Mutu per Sungai")
        df_rank = valid_records[valid_records['status_exceed'] == True].groupby('nama_sungai').size().reset_index(name='Jumlah Pelanggaran')
        df_rank = df_rank.sort_values(by='Jumlah Pelanggaran', ascending=True).tail(12)
        
        fig_rank = px.bar(
            df_rank, x='Jumlah Pelanggaran', y='nama_sungai', orientation='h',
            color='Jumlah Pelanggaran', color_continuous_scale=['#4db6ac', '#f89406', '#d93025'],
            template='simple_white'
        )
        fig_rank.update_layout(
            height=450, 
            margin=dict(l=0, r=0, t=10, b=0), 
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_rank, width='stretch')

st.markdown("<br>", unsafe_allow_html=True)

# =========================================
# 7. ROW 2: TREN (KIRI 50%) & TOP 10 PARAMETERS (KANAN 50%)
# =========================================
col_trend, col_param = st.columns([1, 1])

with col_trend:
    with st.container(border=True):
        st.subheader("Tren Pelanggaran per Periode")
        df_trend = valid_records[valid_records['status_exceed'] == True].groupby('periode_pemantauan').size().reset_index(name='Pelanggaran')
        
        fig_trend = px.line(df_trend, x='periode_pemantauan', y='Pelanggaran', markers=True, template='simple_white')
        fig_trend.update_traces(line_color='#d93025', line_width=4, marker=dict(size=10))
        fig_trend.update_layout(
            height=330, 
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_trend, width='stretch')

with col_param:
    with st.container(border=True):
        st.subheader("Top 10 Parameter Paling Sering Melebihi Baku Mutu")
        df_param_counts = valid_records[valid_records['status_exceed'] == True].groupby('nama_parameter').size().reset_index(name='Frekuensi')
        
        if len(df_param_counts) > 0:
            df_param_counts = df_param_counts.sort_values(by='Frekuensi', ascending=True).tail(10)
            fig_param = px.bar(df_param_counts, x='Frekuensi', y='nama_parameter', orientation='h', template='simple_white', text_auto=True)
            fig_param.update_traces(marker_color='#e74c3c')
            fig_param.update_layout(
                height=330, 
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_param, width='stretch')
        else:
            st.info("Tidak ada data pelanggaran parameter.")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================
# 8. ROW 3: BOD/COD (FULL-WIDTH)
# =========================================
with st.container(border=True):
    st.subheader("Rata-rata Nilai Kadar BOD & COD per Sungai Utama")
    df_bod_cod = df_base[df_base['nama_parameter'].isin(['Bod', 'Cod'])].groupby(['nama_sungai', 'nama_parameter'])['hasil_pengukuran'].mean().reset_index()

    fig_bod_cod = go.Figure()

    if len(df_bod_cod) > 0:
        df_bod_cod_pivot = df_bod_cod.pivot(index='nama_sungai', columns='nama_parameter', values='hasil_pengukuran').reset_index()
        
        if 'Bod' not in df_bod_cod_pivot.columns:
            df_bod_cod_pivot['Bod'] = 0.0
        if 'Cod' not in df_bod_cod_pivot.columns:
            df_bod_cod_pivot['Cod'] = 0.0
            
        df_bod_cod_pivot = df_bod_cod_pivot.dropna().tail(12) # Tampilkan 12 sungai teratas agar lega
        
        fig_bod_cod.add_trace(go.Bar(x=df_bod_cod_pivot['nama_sungai'], y=df_bod_cod_pivot['Bod'], name='BOD (mg/L)', marker_color='#2ecc71'))
        fig_bod_cod.add_trace(go.Bar(x=df_bod_cod_pivot['nama_sungai'], y=df_bod_cod_pivot['Cod'], name='COD (mg/L)', marker_color='#3498db'))
        fig_bod_cod.update_layout(
            barmode='group', 
            height=360, 
            template='simple_white', 
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bod_cod, width='stretch')
    else:
        st.info("Tidak ada data BOD/COD untuk filter ini.")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================
# 9. ROW 4: TABEL RINGKASAN PRIORITAS TINDAKAN (FULL-WIDTH)
# =========================================
with st.container(border=True):
    st.subheader("Tabel Ringkasan Prioritas Tindakan Pengelolaan Sungai")

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
        df_summary['Status'] = df_summary['% Pelanggaran'].apply(lambda x: "Kritis" if x > 38.0 else ("Tinggi" if x > 33.0 else "Sedang"))
        
        df_summary = df_summary.sort_values(by='% Pelanggaran', ascending=False).head(8)
        df_summary['BOD_Avg'] = df_summary['BOD_Avg'].round(2)
        df_summary['COD_Avg'] = df_summary['COD_Avg'].round(2)
        df_summary['DO_Avg'] = df_summary['DO_Avg'].round(2)

        st.dataframe(df_summary[['nama_sungai', 'BOD_Avg', 'COD_Avg', 'DO_Avg', '% Pelanggaran', 'Status']], width='stretch')
    else:
        st.info("Tidak ada data valid yang tersedia.")

st.success("Sistem Sinkronisasi Data Warehouse Berhasil Berjalan Real-time Melalui Koneksi Neon.tech Cloud!")


# ========================================================
# 10. ROW 5: AUTOMATED & DYNAMIC ACTIONABLE INSIGHTS
# ========================================================
st.markdown("---")
st.markdown("### Actionable Insights — Rekomendasi Berbasis Data BI")

# Mengambil data insight secara dinamis dari metrics.py
(insight_1_title, insight_1_desc, insight_1_badge, 
 insight_2_title, insight_2_desc, insight_2_badge, 
 insight_3_title, insight_3_desc, insight_3_badge, 
 border_do_color, badge_do_bg, badge_do_text, do_tag) = generate_insights_data(
     df_filtered, filter_sungai
)

col_ins1, col_ins2, col_ins3 = st.columns(3)

with col_ins1:
    card_html_1 = f'<div class="insight-card" style="border-left: 5px solid #ef4444;"><div><p class="insight-tag">INSIGHT 01 • KRITIS</p><div class="insight-title" style="color: #ffffff; font-size: 16px; font-weight: 600; margin: 5px 0 10px 0;">{insight_1_title}</div><p class="insight-desc">{insight_1_desc}</p></div><div class="insight-badge" style="background-color: #fef2f2; color: #dc2626;">{insight_1_badge}</div></div>'
    st.markdown(card_html_1, unsafe_allow_html=True)

with col_ins2:
    card_html_2 = f'<div class="insight-card" style="border-left: 5px solid #ef4444;"><div><p class="insight-tag">INSIGHT 02 • KRITIS</p><div class="insight-title" style="color: #ffffff; font-size: 16px; font-weight: 600; margin: 5px 0 10px 0;">{insight_2_title}</div><p class="insight-desc">{insight_2_desc}</p></div><div class="insight-badge" style="background-color: #fef2f2; color: #dc2626;">{insight_2_badge}</div></div>'
    st.markdown(card_html_2, unsafe_allow_html=True)

with col_ins3:
    card_html_3 = f'<div class="insight-card" style="border-left: 5px solid {border_do_color};"><div><p class="insight-tag">INSIGHT 03 • {do_tag}</p><div class="insight-title" style="color: #ffffff; font-size: 16px; font-weight: 600; margin: 5px 0 10px 0;">{insight_3_title}</div><p class="insight-desc">{insight_3_desc}</p></div><div class="insight-badge" style="background-color: {badge_do_bg}; color: {badge_do_text};">{insight_3_badge}</div></div>'
    st.markdown(card_html_3, unsafe_allow_html=True)

# ========================================================
# 11. FOOTER (Menempel bawah, Bleed to Edge)
# ========================================================
st.markdown("""
    <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12.5px; border-top: 1px solid #cbd5e1; margin-top: 50px; margin-left: -5rem; margin-right: -5rem; margin-bottom: 0rem; background-color: #cbd5e1; border-radius: 0px; box-shadow: 0 -2px 10px rgba(0,0,0,0.02);">
        © 2026 Business Intelligence Unit — Dinas Lingkungan Hidup DKI Jakarta.<br>
        Dashboard Pemantauan Kualitas Air Sungai • Terkoneksi Real-Time dengan Cloud Data Warehouse Neon.tech.
    </div>
""", unsafe_allow_html=True)