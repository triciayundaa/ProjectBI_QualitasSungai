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

# Helper to render custom HTML without triggering markdown code-block rendering
def render_html(html_str):
    clean_lines = [line.strip() for line in html_str.split("\n")]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)

# Load custom CSS styles from app/style.css
try:
    with open("app/style.css", "r", encoding="utf-8") as f:
        render_html(f"<style>{f.read()}</style>")
except FileNotFoundError:
    st.warning("style.css tidak ditemukan. Silakan pastikan file berada di folder app/style.css.")

# Load logo as base64 for header inline display
try:
    with open("app/logo.png", "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{encoded_logo}" style="background-color: white; height: 36px; margin-right: 12px; vertical-align: middle; border-radius: 6px; border: 2px solid rgba(255,255,255,0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.15);">'
except Exception:
    logo_html = ""

# Load database base data
df_base = load_analytics_data_v2()

# =========================================
# HEADER DASHBOARD (Bleed to Edge)
# =========================================
header_html = f"""
<div style="background-color: #1044A5; padding: 20px 1.5rem; border-radius: 0; margin-left: -1.5rem; margin-right: -1.5rem; margin-top: -1.5rem; margin-bottom: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; justify-content: space-between; align-items: center; font-family: 'Plus Jakarta Sans', sans-serif;">
    <!-- Left Side -->
    <div style="display: flex; align-items: center;">
        {logo_html}
        <div>
            <div style="color: white; margin:  0 1px 0; font-weight: 700; font-size: 19px; line-height: 1.1; letter-spacing: -0.5px;">Kualitas Air Sungai DKI Jakarta — Decision Dashboard</div>
            <div style="color: #dbeafe; margin: 0; font-size: 9.5px; opacity: 0.85; font-weight: 500;">Business Intelligence Unit • 23 Sungai • 31 Parameter Unik • 19.200 Batas Pengukuran Pengujian</div>
        </div>
    </div>
    
</div>
"""
render_html(header_html)

# =========================================
# MAIN COLUMNS SPLIT: SIDEBAR & MAIN BODY
# =========================================
col_sidebar, col_main = st.columns([0.8, 4.2])

# Inisialisasi session state untuk filter jika belum ada
if 'filter_sungai_key' not in st.session_state:
    st.session_state['filter_sungai_key'] = "Semua Sungai"
if 'filter_periode_key' not in st.session_state:
    st.session_state['filter_periode_key'] = "Semua Periode"
if 'filter_jenis_key' not in st.session_state:
    st.session_state['filter_jenis_key'] = "Semua Jenis"

# Fungsi callback untuk reset filter secara aman
def reset_filters():
    st.session_state['filter_sungai_key'] = "Semua Sungai"
    st.session_state['filter_periode_key'] = "Semua Periode"
    st.session_state['filter_jenis_key'] = "Semua Jenis"

# -----------------------------------------
# LEFT COLUMN: SIDEBAR SLICER
# -----------------------------------------
with col_sidebar:
    # 1. Filter Data Card
    with st.container(border=True):
        render_html("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#1044A5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
            <span style="font-size: 11.5px; font-weight: 750; color: #1044A5; letter-spacing: 0.5px; text-transform: uppercase;">Filter Data</span>
        </div>
        """)
        
        list_sungai = ["Semua Sungai"] + sorted(df_base['nama_sungai'].unique().tolist())
        filter_sungai = st.selectbox("SUNGAI", list_sungai, key='filter_sungai_key')
        
        list_periode = ["Semua Periode"] + sorted(df_base['periode_pemantauan'].unique().tolist())
        filter_periode = st.selectbox("PERIODE", list_periode, key='filter_periode_key')
        
        list_jenis = ["Semua Jenis"] + sorted(df_base['jenis_parameter'].unique().tolist())
        filter_jenis = st.selectbox("JENIS PARAMETER", list_jenis, key='filter_jenis_key')
        
        st.button("↻ Reset Filter", on_click=reset_filters, use_container_width=True)
        

        
    # 3. Tentang Dashboard Card
    with st.container(border=True):
        render_html("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#1044A5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" x2="12" y1="17" y2="17"/></svg>
            <span style="font-size: 11.5px; font-weight: 750; color: #1044A5; letter-spacing: 0.5px; text-transform: uppercase;">Tentang Dashboard</span>
        </div>
        """)
        
        render_html("""
        <div style="font-size: 11px; color: #64748b; line-height: 1.45; text-align: justify; min-height: 140px;">
            Dashboard ini menyajikan pemantauan kualitas air sungai secara real-time berdasarkan hasil pengujian laboratorium dan ambang baku mutu nasional.
        </div>
        """)

# -----------------------------------------
# FILTER LOGIC FOR DATASET
# -----------------------------------------
df_filtered = df_base.copy()
if filter_sungai != "Semua Sungai":
    df_filtered = df_filtered[df_filtered['nama_sungai'] == filter_sungai]
if filter_periode != "Semua Periode":
    df_filtered = df_filtered[df_filtered['periode_pemantauan'] == filter_periode]
if filter_jenis != "Semua Jenis":
    df_filtered = df_filtered[df_filtered['jenis_parameter'] == filter_jenis]

total_records = len(df_filtered)
valid_records = df_filtered[df_filtered['is_valid'] == True]

# Melakukan kalkulasi metrik secara modular via metrics.py
pct_exceed, total_exceed, val_coliform_str, desc_coliform_str, val_do_str, desc_do_str = calculate_kpi_metrics(
    valid_records, total_records
)

# -----------------------------------------
# RIGHT COLUMN: MAIN CONTENT BODY
# -----------------------------------------
with col_main:
    # 1. WARNING BANNER
    alert_html = generate_alert_banner_html(valid_records, filter_sungai, pct_exceed)
    render_html(alert_html)
    
    # 2. KPI METRICS (6 COLUMNS)
    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
    
    # Calculate Sungai Kondisi Kritis
    unique_rivers = valid_records['nama_sungai'].unique()
    total_rivers = len(unique_rivers)
    kritis_rivers = 0
    if total_rivers > 0:
        for r in unique_rivers:
            r_df = valid_records[valid_records['nama_sungai'] == r]
            r_exceed = r_df['status_exceed'].sum()
            r_pct = (r_exceed / len(r_df)) * 100 if len(r_df) > 0 else 0.0
            if r_pct > 50.0:
                kritis_rivers += 1
        pct_kritis = (kritis_rivers / total_rivers) * 100
    else:
        pct_kritis = 0.0

    # Calculate BOD dynamically
    df_bod_kpi = valid_records[valid_records['nama_parameter'].str.lower() == 'bod']
    if len(df_bod_kpi) > 0:
        avg_bod = df_bod_kpi['hasil_pengukuran'].mean()
        val_bod_str = f"{avg_bod:.1f}" if not pd.isna(avg_bod) else "N/A"
        desc_bod_str = "Batas aman: 3 mg/L"
    else:
        val_bod_str = "N/A"
        desc_bod_str = "Batas aman: 3 mg/L"

    # SVG Icons
    svg_flask = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v6.5M14 2v6.5M14 2h-4M8.5 22h7M16 11l4.7 7.8c.7 1.2-.1 2.7-1.5 2.7H4.8c-1.4 0-2.2-1.5-1.5-2.7L8 11V8h8v3Z"/></svg>'
    svg_alert = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12" y1="16" y2="16"/></svg>'
    svg_shield = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 11 2 2 4-4"/></svg>'
    svg_beaker = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 3h16M4 3v17a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3M9 8h6M19 14h-4M9 14H4"/></svg>'
    svg_virus = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24M14.83 9.17l4.24-4.24M14.83 14.83l4.24 4.24M9.17 14.83l-4.24 4.24M8 12h8M12 8v8"/></svg>'
    svg_waves = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.6 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.6 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/></svg>'

    # Render KPI Cards in HTML
    with col_kpi1:
        render_html(f"""
        <div class="metric-card" style="border-bottom: 4px solid #2563eb;">
            <div style="background-color: #eff6ff; color: #2563eb; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {svg_flask}
            </div>
            <div style="display: flex; flex-direction: column;">
                <span style="color: #64748b; font-size: 7.5px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">Total Pengukuran Valid</span>
                <span style="color: #1e293b; font-size: 13.5px; font-weight: 800; line-height: 1.1; margin: 1px 0;">{len(valid_records)}</span>
                <span style="color: #94a3b8; font-size: 7.5px; line-height: 1.1;">Dari {len(df_base):,} total sampel</span>
            </div>
        </div>
        """)

    with col_kpi2:
        render_html(f"""
        <div class="metric-card" style="border-bottom: 4px solid #ef4444;">
            <div style="background-color: #fef2f2; color: #ef4444; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {svg_alert}
            </div>
            <div style="display: flex; flex-direction: column;">
                <span style="color: #64748b; font-size: 7.5px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">Melebihi Baku Mutu</span>
                <span style="color: #ef4444; font-size: 13.5px; font-weight: 800; line-height: 1.1; margin: 1px 0;">{total_exceed} ({pct_exceed:.1f}%)</span>
                <span style="color: #94a3b8; font-size: 7.5px; line-height: 1.1;">Tingkat polusi dari total sampel</span>
            </div>
        </div>
        """)

    with col_kpi3:
        render_html(f"""
        <div class="metric-card" style="border-bottom: 4px solid #f97316;">
            <div style="background-color: #fff7ed; color: #f97316; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {svg_beaker}
            </div>
            <div style="display: flex; flex-direction: column;">
                <span style="color: #64748b; font-size: 7.5px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">BOD Rata-rata</span>
                <span style="color: #f97316; font-size: 13.5px; font-weight: 800; line-height: 1.1; margin: 1px 0;">{val_bod_str}</span>
                <span style="color: #94a3b8; font-size: 7.5px; line-height: 1.1;">{desc_bod_str}</span>
            </div>
        </div>
        """)

    with col_kpi4:
        render_html(f"""
        <div class="metric-card" style="border-bottom: 4px solid #8b5cf6;">
            <div style="background-color: #f5f3ff; color: #8b5cf6; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {svg_virus}
            </div>
            <div style="display: flex; flex-direction: column;">
                <span style="color: #64748b; font-size: 7.5px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">Total Coliform Maks</span>
                <span style="color: #8b5cf6; font-size: 13.5px; font-weight: 800; line-height: 1.1; margin: 1px 0;">{val_coliform_str}</span>
                <span style="color: #94a3b8; font-size: 7.5px; line-height: 1.1; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 100px;">{desc_coliform_str}</span>
            </div>
        </div>
        """)

    with col_kpi5:
        render_html(f"""
        <div class="metric-card" style="border-bottom: 4px solid #14b8a6;">
            <div style="background-color: #f0fdfa; color: #14b8a6; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {svg_waves}
            </div>
            <div style="display: flex; flex-direction: column;">
                <span style="color: #64748b; font-size: 7.5px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">DO Rata-rata</span>
                <span style="color: #14b8a6; font-size: 13.5px; font-weight: 800; line-height: 1.1; margin: 1px 0;">{val_do_str}</span>
                <span style="color: #94a3b8; font-size: 7.5px; line-height: 1.1;">{desc_do_str}</span>
            </div>
        </div>
        """)



    # 3. ROW 3: VISUALIZATIONS LAYOUT (3 COLUMNS: MAP, MIDDLE, RIGHT)
    col_map_chart, col_mid_charts, col_right_charts = st.columns([1.1, 1, 1])

    # --- COLUMN 1: MAP ---
    with col_map_chart:
        with st.container(border=True):
            render_html("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #1e293b;">Peta Sebaran Geografis Kualitas Air Sungai</span>
            </div>
            """)
            render_html("""
                <div style="margin-top: 1px; border-top: 1px solid #f1f5f9; padding-top: 1px;">
                    <span style="font-size: 10px; font-weight: 700; color: #475569; display: block; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.3px;">Persentase Pelanggaran</span>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 8px; color: #64748b; margin-bottom: 15px;">
                        <div style="display: flex; align-items: center; gap: 4px;"><span style="background-color: #d93025; width: 8px; height: 8px; border-radius: 50%; display: inline-block;"></span> &gt; 75% (Sangat Tinggi)</div>
                        <div style="display: flex; align-items: center; gap: 4px;"><span style="background-color: #f97316; width: 8px; height: 8px; border-radius: 50%; display: inline-block;"></span> 50% - 75% (Tinggi)</div>
                        <div style="display: flex; align-items: center; gap: 4px;"><span style="background-color: #eab308; width: 8px; height: 8px; border-radius: 50%; display: inline-block;"></span> 25% - 50% (Sedang)</div>
                        <div style="display: flex; align-items: center; gap: 4px;"><span style="background-color: #10b981; width: 8px; height: 8px; border-radius: 50%; display: inline-block;"></span> &le; 25% (Rendah)</div>
                    </div>
                </div>
                """)
            
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
                    if pct > 75.0: return '#d93025' # Merah (Sangat Tinggi)
                    if pct > 50.0: return '#f97316' # Oranye (Tinggi)
                    if pct > 25.0: return '#eab308' # Kuning (Sedang)
                    return '#10b981' # Hijau (Rendah)

                df_map_points['color'] = df_map_points['% Pelanggaran'].apply(get_color)

                center_lat = df_map_points['latitude'].mean() if not pd.isna(df_map_points['latitude'].mean()) else -6.2088
                center_lon = df_map_points['longitude'].mean() if not pd.isna(df_map_points['longitude'].mean()) else 106.8456
                m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB positron")

                for _, row in df_map_points.iterrows():
                    popup_html = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 11px; width: 180px;">
                        <h5 style="margin: 0 0 5px 0; color: #1044A5; font-size: 12px; font-weight:700;">{row['nama_sungai']}</h5>
                        <b>Titik Sampel:</b> {row['id_titik_sampel']}<br>
                        <b>Total Pengukuran:</b> {row['total_sampel']}<br>
                        <b>Persentase Pelanggaran:</b> <span style="color: {row['color']}; font-weight: bold;">{row['% Pelanggaran']}%</span>
                    </div>
                    """
                    
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=8,
                        popup=folium.Popup(popup_html, max_width=220),
                        color=row['color'],
                        fill=True,
                        fill_color=row['color'],
                        fill_opacity=0.7,
                        weight=2
                    ).add_to(m)

                st_folium(m, height=565, use_container_width=True)
                
                # Render Legend under the Map inside the Card
                
            else:
                st.info("Tidak ada data koordinat geografis yang valid.")

    # --- COLUMN 2: MIDDLE STACKED CARDS ---
    with col_mid_charts:
        # Card 1: Jumlah Pelanggaran Baku Mutu per Sungai
        with st.container(border=True):
            render_html("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #1e293b;">Jumlah Pelanggaran Baku Mutu per Sungai</span>
            </div>
            """)
            
            df_rank = valid_records[valid_records['status_exceed'] == True].groupby('nama_sungai').size().reset_index(name='Jumlah Pelanggaran')
            df_rank = df_rank.sort_values(by='Jumlah Pelanggaran', ascending=True).tail(10)

            if len(df_rank) > 0:
                fig_rank = px.bar(
                    df_rank, x='Jumlah Pelanggaran', y='nama_sungai', orientation='h',
                    color='Jumlah Pelanggaran', color_continuous_scale=['#4db6ac', '#f89406', '#d93025'],
                    template='simple_white'
                )
                
                # 1. Tampilkan angka jumlah pelanggaran di ujung luar batang (menggantikan fungsi colorbar)
                fig_rank.update_traces(
                    text=df_rank['Jumlah Pelanggaran'], 
                    textposition='outside'
                )
                
                # 2. Kembalikan nama sungai di sumbu Y dan hapus judul "nama_sungai" yang bikin sempit
                fig_rank.update_yaxes(
                    showticklabels=True, 
                    title=None
                ) 

                # 3. Matikan colorbar raksasa di sebelah kanan agar grafik melebar penuh
                fig_rank.update_coloraxes(
                    showscale=False
                )

                fig_rank.update_layout(
                    height=230, 
                    # Beri margin kiri (l=120) agar nama sungai panjang seperti "Kalibaru Timur" tidak terpotong
                    margin=dict(l=120, r=40, t=10, b=0), 
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_rank, width='stretch')
            else:
                st.info("Tidak ada data pelanggaran untuk filter aktif.")


        # Card 2: Top 10 Parameter Paling Sering Melebihi Baku Mutu
        with st.container(border=True):
            render_html("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #1e293b;">Top 10 Parameter Paling Sering Melebihi Baku Mutu</span>
            </div>
            """)
            
            df_param_counts = valid_records[valid_records['status_exceed'] == True].groupby('nama_parameter').size().reset_index(name='Frekuensi')
        
            if len(df_param_counts) > 0:
                df_param_counts = df_param_counts.sort_values(by='Frekuensi', ascending=True).tail(10)
                fig_param = px.bar(df_param_counts, x='Frekuensi', y='nama_parameter', orientation='h', template='simple_white', text_auto=True)
                fig_param.update_traces(marker_color='#e74c3c')
                fig_param.update_layout(
                    height=315, 
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_param, width='stretch')
            else:
                st.info("Tidak ada data pelanggaran parameter.")

    # --- COLUMN 3: RIGHT STACKED CARDS ---
    with col_right_charts:
        # Card 1: Tren Pelanggaran per Periode
        with st.container(border=True):
            render_html("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #1e293b;">Tren Pelanggaran per Periode</span>
            </div>
            """)
            
            df_trend = valid_records[valid_records['status_exceed'] == True].groupby('periode_pemantauan').size().reset_index(name='Pelanggaran')
            
            if len(df_trend) > 0:
                fig_trend = px.line(df_trend, x='periode_pemantauan', y='Pelanggaran', markers=True, template='simple_white')
                fig_trend.update_traces(line_color='#d93025', line_width=4, marker=dict(size=10))
                fig_trend.update_layout(
                    height=230, 
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_trend, width='stretch')
            else:
                st.info("Tidak ada data tren pelanggaran.")
                
        # Card 2: Perbandingan BOD & COD Rata-rata per Sungai
        with st.container(border=True):
            render_html("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #1e293b;">Perbandingan BOD & COD Rata-rata per Sungai</span>
            </div>
            """)
            
            df_bod_cod = df_base[df_base['nama_parameter'].isin(['Bod', 'Cod'])].groupby(['nama_sungai', 'nama_parameter'])['hasil_pengukuran'].mean().reset_index()
            if filter_sungai != "Semua Sungai":
                df_bod_cod = df_bod_cod[df_bod_cod['nama_sungai'] == filter_sungai]
                
            if len(df_bod_cod) > 0:
                df_bod_cod_pivot = df_bod_cod.pivot(index='nama_sungai', columns='nama_parameter', values='hasil_pengukuran').reset_index()
                
                if 'Bod' not in df_bod_cod_pivot.columns:
                    df_bod_cod_pivot['Bod'] = 0.0
                if 'Cod' not in df_bod_cod_pivot.columns:
                    df_bod_cod_pivot['Cod'] = 0.0
                    
                if filter_sungai == "Semua Sungai":
                    df_bod_cod_pivot = df_bod_cod_pivot.sort_values(by='Bod', ascending=False).head(5)
                
                fig_bod_cod = go.Figure()
                fig_bod_cod.add_trace(go.Bar(
                    x=df_bod_cod_pivot['nama_sungai'], 
                    y=df_bod_cod_pivot['Bod'], 
                    name='BOD (mg/L)', 
                    marker_color='#10b981'
                ))
                fig_bod_cod.add_trace(go.Bar(
                    x=df_bod_cod_pivot['nama_sungai'], 
                    y=df_bod_cod_pivot['Cod'], 
                    name='COD (mg/L)', 
                    marker_color='#2563eb'
                ))
                fig_bod_cod.update_layout(
                    barmode='group', 
                    height=315, 
                    template='simple_white', 
                    margin=dict(l=0, r=0, t=5, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=9)
                    )
                )
                fig_bod_cod.update_xaxes(title_text="", showgrid=False, tickfont=dict(size=9))
                fig_bod_cod.update_yaxes(title_text="", showgrid=True, gridcolor='#f1f5f9', tickfont=dict(size=9))
                st.plotly_chart(fig_bod_cod, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Tidak ada data BOD/COD.")



# =========================================
# ROW 4: TABEL RINGKASAN PRIORITAS TINDAKAN (FULL-WIDTH)
# =========================================
with st.container(border=True):
    render_html("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1044A5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v18H3z"/><path d="M21 9H3M21 15H3M12 3v18"/></svg>
            <span style="font-size: 13px; font-weight: 750; color: #1e293b; text-transform: uppercase; letter-spacing: 0.3px;">Tabel Ringkasan Prioritas Tindakan Pengelolaan Sungai</span>
        </div>
        <span style="color: #94a3b8; font-size: 14px; cursor: pointer;">•••</span>
    </div>
    """)

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
        
        df_summary = df_summary.rename(columns={'% Pelanggaran': 'pct_pelanggaran'})
        df_summary['pct_pelanggaran'] = round((df_summary['Total_Pelanggaran'] / df_summary['Total_Sampel']) * 100, 1)
        df_summary['Status'] = df_summary['pct_pelanggaran'].apply(lambda x: "Kritis" if x > 38.0 else ("Tinggi" if x > 33.0 else "Sedang"))
        
        df_summary = df_summary.sort_values(by='pct_pelanggaran', ascending=False).head(8)
        df_summary['BOD_Avg'] = df_summary['BOD_Avg'].round(2)
        df_summary['COD_Avg'] = df_summary['COD_Avg'].round(2)
        df_summary['DO_Avg'] = df_summary['DO_Avg'].round(2)

        # Generate HTML Table
        table_rows = ""
        for i, row in enumerate(df_summary.itertuples(), 1):
            status = row.Status
            if status == "Kritis":
                status_badge = '<span style="background-color: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 10px;">Kritis</span>'
            elif status == "Tinggi":
                status_badge = '<span style="background-color: #fff7ed; color: #ea580c; border: 1px solid #ffedd5; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 10px;">Tinggi</span>'
            else:
                status_badge = '<span style="background-color: #f0fdf4; color: #16a34a; border: 1px solid #dcfce7; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 10px;">Sedang</span>'
            
            table_rows += f"""
            <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;">
                <td style="padding: 6px 8px; font-weight: 600; color: #64748b; font-size: 11.5px; text-align: center;">{i}</td>
                <td style="padding: 6px 8px; font-weight: 700; color: #1e293b; font-size: 11.5px;">{row.nama_sungai}</td>
                <td style="padding: 6px 8px; color: #475569; font-size: 11.5px;">{row.BOD_Avg:.2f}</td>
                <td style="padding: 6px 8px; color: #475569; font-size: 11.5px;">{row.COD_Avg:.2f}</td>
                <td style="padding: 6px 8px; color: #475569; font-size: 11.5px;">{row.DO_Avg:.2f}</td>
                <td style="padding: 6px 8px; font-weight: 700; color: #dc2626; font-size: 11.5px;">{row.pct_pelanggaran:.1f}%</td>
                <td style="padding: 6px 8px;">{status_badge}</td>
            </tr>
            """
        
        table_html = f"""
        <div style="overflow-x: auto; margin-top: 5px;">
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-family: inherit;">
                <thead>
                    <tr style="border-bottom: 2px solid #e2e8f0; background-color: #f8fafc;">
                        <th style="padding: 6px 8px; color: #475569; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; text-align: center; width: 40px;">No</th>
                        <th style="padding: 6px 8px; color: #475569; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Nama Sungai</th>
                        <th style="padding: 6px 8px; color: #475569; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">BOD Avg (mg/L)</th>
                        <th style="padding: 6px 8px; color: #475569; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">COD Avg (mg/L)</th>
                        <th style="padding: 6px 8px; color: #475569; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">DO Avg (mg/L)</th>
                        <th style="padding: 6px 8px; color: #475569; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">% Pelanggaran</th>
                        <th style="padding: 6px 8px; color: #475569; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
        render_html(table_html)
    else:
        st.info("Tidak ada data valid yang tersedia.")



# ========================================================
# ROW 5: AUTOMATED & DYNAMIC ACTIONABLE INSIGHTS
# ========================================================
render_html("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px; margin-top: 15px;">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1044A5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A5 5 0 0 0 8 8c0 1 .3 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6M10 22h4"/></svg>
    <span style="font-size: 13.5px; font-weight: 750; color: #1e293b; text-transform: uppercase; letter-spacing: 0.3px;">Actionable Insights — Rekomendasi Berbasis Data BI</span>
</div>
""")

# Mengambil data insight secara dinamis dari metrics.py
(insight_1_title, insight_1_desc, insight_1_badge, 
 insight_2_title, insight_2_desc, insight_2_badge, 
 insight_3_title, insight_3_desc, insight_3_badge, 
 border_do_color, badge_do_bg, badge_do_text, do_tag) = generate_insights_data(
     df_filtered, filter_sungai
 )

col_ins1, col_ins2, col_ins3 = st.columns(3)

with col_ins1:
    card_html_1 = f"""
    <div class="insight-card" style="border-left: 5px solid #ef4444;">
        <div>
            <p class="insight-tag">INSIGHT 01 • KRITIS</p>
            <div style="color: #ffffff; font-size: 13.5px; font-weight: 700; margin: 3px 0 8px 0; line-height:1.2;">{insight_1_title}</div>
            <p class="insight-desc">{insight_1_desc}</p>
        </div>
        <div class="insight-badge" style="background-color: #fef2f2; color: #dc2626;">{insight_1_badge}</div>
    </div>
    """
    render_html(card_html_1)

with col_ins2:
    card_html_2 = f"""
    <div class="insight-card" style="border-left: 5px solid #ef4444;">
        <div>
            <p class="insight-tag">INSIGHT 02 • KRITIS</p>
            <div style="color: #ffffff; font-size: 13.5px; font-weight: 700; margin: 3px 0 8px 0; line-height:1.2;">{insight_2_title}</div>
            <p class="insight-desc">{insight_2_desc}</p>
        </div>
        <div class="insight-badge" style="background-color: #fef2f2; color: #dc2626;">{insight_2_badge}</div>
    </div>
    """
    render_html(card_html_2)

with col_ins3:
    card_html_3 = f"""
    <div class="insight-card" style="border-left: 5px solid {border_do_color};">
        <div>
            <p class="insight-tag">INSIGHT 03 • {do_tag}</p>
            <div style="color: #ffffff; font-size: 13.5px; font-weight: 700; margin: 3px 0 8px 0; line-height:1.2;">{insight_3_title}</div>
            <p class="insight-desc">{insight_3_desc}</p>
        </div>
        <div class="insight-badge" style="background-color: {badge_do_bg}; color: {badge_do_text};">{insight_3_badge}</div>
    </div>
    """
    render_html(card_html_3)

# ========================================================
# FOOTER (Menempel bawah, Bleed to Edge)
# ========================================================
render_html("""
    <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px; border-top: 1px solid #cbd5e1; margin-top: 50px; margin-left: -1.5rem; margin-right: -1.5rem; margin-bottom: -1.5rem; background-color: #cbd5e1; border-radius: 0px; box-shadow: 0 -2px 10px rgba(0,0,0,0.02);">
        © 2026 Business Intelligence Unit — Dinas Lingkungan Hidup DKI Jakarta.<br>
        Dashboard Pemantauan Kualitas Air Sungai • Terkoneksi Real-Time dengan Cloud Data Warehouse Neon.tech.
    </div>
""")