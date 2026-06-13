import pandas as pd

def calculate_kpi_metrics(valid_records, total_records):
    total_exceed = valid_records['status_exceed'].sum()
    pct_exceed = (total_exceed / len(valid_records) * 100) if len(valid_records) > 0 else 0.0
    
    # 1. Total Coliform Maks
    df_coliform = valid_records[valid_records['nama_parameter'].isin(['Total Coliform', 'Fecal Coliform'])]
    if len(df_coliform) > 0:
        max_coliform_idx = df_coliform['hasil_pengukuran'].idxmax()
        max_coliform_val = df_coliform.loc[max_coliform_idx, 'hasil_pengukuran']
        max_coliform_sungai = df_coliform.loc[max_coliform_idx, 'nama_sungai']
        
        if max_coliform_val >= 1000000:
            val_coliform_str = f"{max_coliform_val / 1000000:.1f} Jt"
        else:
            val_coliform_str = f"{max_coliform_val:,.0f}"
        desc_coliform_str = f"MPN/100ml - {max_coliform_sungai}"
    else:
        val_coliform_str = "N/A"
        desc_coliform_str = "Tidak ada data Coliform"

    # 2. DO Terendah Rata-rata
    df_do_kpi = valid_records[valid_records['nama_parameter'] == 'Do']
    if len(df_do_kpi) > 0:
        do_by_river = df_do_kpi.groupby('nama_sungai')['hasil_pengukuran'].mean()
        min_do_river = do_by_river.idxmin()
        min_do_val = do_by_river.min()
        val_do_str = f"{min_do_val:.2f}"
        desc_do_str = f"mg/L - {min_do_river} (Batas min: 4)"
    else:
        val_do_str = "N/A"
        desc_do_str = "Tidak ada data DO"
        
    return pct_exceed, total_exceed, val_coliform_str, desc_coliform_str, val_do_str, desc_do_str


def generate_alert_banner_html(valid_records, filter_sungai, pct_exceed):
    if len(valid_records) > 0:
        # Sungai terpolusi teratas
        if filter_sungai == "Semua Sungai":
            top_polluted_rivers = valid_records[valid_records['status_exceed'] == True].groupby('nama_sungai').size().nlargest(2).index.tolist()
            if len(top_polluted_rivers) >= 2:
                river_text = f"Sungai {top_polluted_rivers[0]} dan {top_polluted_rivers[1]}"
            elif len(top_polluted_rivers) == 1:
                river_text = f"Sungai {top_polluted_rivers[0]}"
            else:
                river_text = "Sungai-sungai utama"
        else:
            river_text = f"Sungai {filter_sungai}"

        # Parameter terpolusi teratas
        top_params = valid_records[valid_records['status_exceed'] == True].groupby('nama_parameter').size().nlargest(2).index.tolist()
        if len(top_params) >= 2:
            param_text = f"parameter {top_params[0]} dan {top_params[1]}"
        elif len(top_params) == 1:
            param_text = f"parameter {top_params[0]}"
        else:
            param_text = "beberapa parameter utama"
    else:
        river_text = "Wilayah pantau"
        param_text = "beberapa parameter"

    if pct_exceed > 30.0:
        return f"""
            <div class="alert-banner">
                <span style="font-size: 18px; font-weight: bold; color: #c53030;">🚨 DARURAT KUALITAS AIR:</span> 
                <b>{pct_exceed:.1f}%</b> sampel parameter air sungai terpantau melampaui batas ambang baku mutu nasional (PP No. 22/2021). 
                {river_text} terdeteksi memiliki kontaminasi {param_text} ekstrem yang memerlukan tindakan penegakan hukum dan restorasi ekologi segera.
            </div>
        """
    else:
        return f"""
            <div style="background-color: #f6ffed; border-left: 5px solid #52c41a; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <span style="font-size: 18px; font-weight: bold; color: #237804;">🟢 KONDISI AIR AMAN/SEDANG:</span> 
                Tingkat polusi berada di angka aman <b>{pct_exceed:.1f}%</b>. Pengukuran menunjukkan kondisi air sungai {filter_sungai if filter_sungai != 'Semua Sungai' else 'DKI Jakarta'} secara umum memenuhi baku mutu nasional untuk kriteria terfilter.
            </div>
        """


def generate_insights_data(df_filtered, filter_sungai):
    df_valid_filtered = df_filtered[df_filtered['is_valid'] == True]

    # 1. Insight 01: Parameter Biologi (Coliform)
    df_bio_filtered = df_valid_filtered[df_valid_filtered['jenis_parameter'] == 'Biologi']
    total_bio = len(df_bio_filtered)
    langgar_bio = df_bio_filtered['status_exceed'].sum()
    pct_bio_real = round((langgar_bio / total_bio) * 100, 1) if total_bio > 0 else 0.0

    if filter_sungai == "Semua Sungai":
        insight_1_title = "Biologi: Seluruh Sungai Darurat Coliform"
        insight_1_desc = f"<b>{pct_bio_real}%</b> sampel parameter biologi di seluruh sungai terpantau melebihi baku mutu aman. Tingginya kontaminasi bakteri fecal merata di wilayah padat penduduk, memerlukan intervensi sanitasi komunal."
        insight_1_badge = "→ Sanitasi & IPAL Darurat"
    else:
        insight_1_title = f"Biologi: Kualitas Sanitasi di {filter_sungai}"
        if total_bio > 0:
            insight_1_desc = f"Di <b>Sungai {filter_sungai}</b>, sebesar <b>{pct_bio_real}%</b> parameter biologi (termasuk Coliform) melebihi batas aman. Ini mengindikasikan adanya buangan air limbah rumah tangga langsung di bantaran sungai ini."
        else:
            insight_1_desc = f"Tidak ada data parameter biologi terpantau untuk Sungai {filter_sungai} pada filter aktif saat ini."
        insight_1_badge = "→ Sanitasi Lokal"

    # 2. Insight 02: Parameter Kimia (BOD / COD)
    df_cod_filtered = df_valid_filtered[df_valid_filtered['nama_parameter'] == 'Cod']
    if len(df_cod_filtered) > 0:
        if filter_sungai != "Semua Sungai":
            val_cod = round(df_cod_filtered['hasil_pengukuran'].mean(), 1)
            kali_lipat_bm = round(val_cod / 25, 1)
            insight_2_title = f"Kimia: Rata-rata COD {filter_sungai}"
            insight_2_desc = f"Rata-rata kadar COD di <b>Sungai {filter_sungai}</b> adalah <b>{val_cod} mg/L</b> (atau <b>{kali_lipat_bm}x</b> dari batas baku mutu 25 mg/L). Kadar organik tinggi ini memicu penurunan kualitas ekosistem secara cepat."
            insight_2_badge = f"→ Audit Limbah {filter_sungai}"
        else:
            idx_max_cod = df_cod_filtered.groupby('nama_sungai')['hasil_pengukuran'].mean().idxmax()
            val_max_cod = round(df_cod_filtered.groupby('nama_sungai')['hasil_pengukuran'].mean().max(), 1)
            kali_lipat_bm = round(val_max_cod / 25, 1)
            insight_2_title = f"{idx_max_cod}: Polusi COD Tertinggi"
            insight_2_desc = f"Beban limbah organik di <b>Sungai {idx_max_cod}</b> terpantau paling ekstrem dibandingkan sungai lain, dengan rata-rata COD mencapai <b>{val_max_cod} mg/L</b> (<b>{kali_lipat_bm}x lipat</b> melampaui baku mutu)."
            insight_2_badge = "→ Audit & Penindakan Industri"
    else:
        insight_2_title = "Kimia: Analisis BOD/COD Organik"
        insight_2_desc = "Tidak ada pengukuran parameter COD dalam lingkup filter aktif saat ini. Secara umum, limbah industri non-domestik mendominasi pencemaran COD di sungai-sungai utama Jakarta."
        insight_2_badge = "→ Pengawasan Sumber Polusi"

    # 3. Insight 03: Parameter Oksigen Terlarut (DO)
    df_do_filtered = df_valid_filtered[df_valid_filtered['nama_parameter'] == 'Do']
    border_do_color = "#f97316"  # default orange
    badge_do_bg = "#fff7ed"
    badge_do_text = "#ea580c"
    do_tag = "TINGGI"

    if len(df_do_filtered) > 0:
        if filter_sungai != "Semua Sungai":
            val_do = round(df_do_filtered['hasil_pengukuran'].mean(), 2)
            insight_3_title = f"Ekologi: Kadar DO {filter_sungai}"
            if val_do < 4.0:
                insight_3_desc = f"Rata-rata DO di <b>Sungai {filter_sungai}</b> drop ke angka kritis <b>{val_do} mg/L</b> (di bawah ambang minimum minimal 4 mg/L). Kondisi anoksik ini berbahaya bagi kelangsungan biota air lokal."
                insight_3_badge = "→ Aerasi & Restorasi Ekologi"
                border_do_color = "#ef4444"  # red
                badge_do_bg = "#fef2f2"
                badge_do_text = "#dc2626"
                do_tag = "KRITIS"
            else:
                insight_3_desc = f"Rata-rata kadar DO di <b>Sungai {filter_sungai}</b> adalah <b>{val_do} mg/L</b> (memenuhi batas minimum 4 mg/L). Oksigen terlarut masih cukup baik untuk mendukung kehidupan akuatik."
                insight_3_badge = "→ Pemeliharaan Aliran Sungai"
                border_do_color = "#10b981"  # green
                badge_do_bg = "#ecfdf5"
                badge_do_text = "#059669"
                do_tag = "AMAN"
        else:
            idx_min_do = df_do_filtered.groupby('nama_sungai')['hasil_pengukuran'].mean().idxmin()
            val_min_do = round(df_do_filtered.groupby('nama_sungai')['hasil_pengukuran'].mean().min(), 2)
            insight_3_title = f"DO Kritis: Oksigen {idx_min_do}"
            insight_3_desc = f"Kadar DO rata-rata terendah ditemukan di <b>Sungai {idx_min_do}</b> dengan angka <b>{val_min_do} mg/L</b>. Hal ini menyebabkan daerah aliran sungai tersebut secara ekologis terancam mati."
            insight_3_badge = "→ Aerasi Sungai Utama"
            border_do_color = "#ef4444"  # red
            badge_do_bg = "#fef2f2"
            badge_do_text = "#dc2626"
            do_tag = "KRITIS"
    else:
        insight_3_title = "Ekologi: Oksigen Terlarut (DO)"
        insight_3_desc = "Tidak ada pengukuran parameter Oksigen Terlarut (DO) dalam filter aktif. Parameter DO sangat penting untuk mengukur kemampuan pemulihan ekosistem sungai."
        insight_3_badge = "→ Monitoring Rutin DO"

    return (insight_1_title, insight_1_desc, insight_1_badge, 
            insight_2_title, insight_2_desc, insight_2_badge, 
            insight_3_title, insight_3_desc, insight_3_badge, 
            border_do_color, badge_do_bg, badge_do_text, do_tag)
