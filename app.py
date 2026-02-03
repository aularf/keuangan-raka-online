import streamlit as st
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go
import time

# --- 1. KONFIGURASI & LOGIKA BISNIS ---
st.set_page_config(page_title="Dompet Raka", page_icon="💳", layout="wide")

# [PENTING] ATUR PERSENTASE ALOKASI GAJI DISINI
# Total harus 1.0 (100%). Sesuaikan nama kategori persis dengan yang ada di Google Sheet kamu.
CONFIG_PERSENTASE_BUDGET = {
    "Makan": 0.20,            # 20%
    "Rokok": 0.10,            # 10%
    "Transport": 0.10,        # 10%
    "Kebutuhan Kos": 0.10,    # 10%
    "Hiburan": 0.10,          # 10%
    "Tabungan": 0.20,         # 20%
    "Dana Darurat": 0.10,     # 10%
    "Sedekah": 0.05,          # 5%
    "Lainnya": 0.05           # 5%
}
# Kategori yang masuk perhitungan "Jatah Harian"
KATEGORI_HARIAN = ["Makan", "Rokok"]

# --- CSS TEMA: ADAPTIVE (BUNGLON) ---
st.markdown("""
    <style>
        .header-box {
            background: linear-gradient(90deg, #0f766e 0%, #14b8a6 100%);
            padding: 30px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3);
            margin-bottom: 25px;
        }
        .header-box h1 { color: white !important; margin: 0; font-size: 2.5rem; }
        .header-box p { color: #f0fdfa !important; font-size: 1.1rem; }

        div[data-testid="stMetric"], div[data-testid="stForm"], .menu-card, .big-button-container {
            background-color: var(--secondary-background-color);
            border: 1px solid var(--primary-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        h1, h2, h3, h4, p, li, .stMarkdown { color: var(--text-color) !important; }
        [data-testid="stMetricValue"] { color: #14b8a6 !important; font-size: 28px; font-weight: 800; }
        [data-testid="stMetricLabel"] { color: var(--text-color) !important; opacity: 0.8; font-size: 14px; font-weight: 600; }

        div.stButton > button {
            background: linear-gradient(90deg, #0d9488 0%, #14b8a6 100%);
            color: white !important;
            border: none;
            height: 50px;
            border-radius: 10px;
            font-weight: bold;
        }
        
        div.stButton > button[key*="btn_"] {
            background: transparent;
            color: var(--text-color) !important;
            border: 2px solid #0d9488;
        }
        [data-testid="stDataFrame"] { border: 1px solid #14b8a6; border-radius: 10px; }
        [data-testid="stSidebar"] { border-right: 1px solid #14b8a6; }
    </style>
""", unsafe_allow_html=True)

# --- 2. NAVIGASI ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'
def navigate_to(page):
    st.session_state['page'] = page
    st.rerun()

# --- 3. KONEKSI & FUNGSI BANTUAN ---
@st.cache_resource
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        secrets_data = st.secrets["gcp_service_account"]
        if isinstance(secrets_data, str): creds_dict = json.loads(secrets_data)
        else: creds_dict = dict(secrets_data)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.load(open("credentials.json")), scope)
    client = gspread.authorize(creds)
    return client.open("MyMonetaryApp")

# Fungsi Menentukan Periode Gaji (Tgl 20 - 19)
def get_payroll_period(current_date):
    if current_date.day >= 20:
        start_date = date(current_date.year, current_date.month, 20)
        # End date bulan depan tgl 19
        next_month = current_date.replace(day=28) + timedelta(days=4)
        end_date = date(next_month.year, next_month.month, 19)
    else:
        # Start date bulan lalu tgl 20
        last_month = current_date.replace(day=1) - timedelta(days=1)
        start_date = date(last_month.year, last_month.month, 20)
        end_date = date(current_date.year, current_date.month, 19)
    return start_date, end_date

# Fungsi Update Budget Otomatis di Sheet
def update_budget_allocation(worksheet, total_gaji):
    all_records = worksheet.get_all_records()
    df_temp = pd.DataFrame(all_records)
    
    updates = []
    # Loop persentase config
    for kategori, persentase in CONFIG_PERSENTASE_BUDGET.items():
        nominal_baru = int(total_gaji * persentase)
        
        # Cari baris mana kategori ini berada (row index mulai dari 2 di gspread karena header row 1)
        try:
            # Cari cell yang berisi nama kategori
            cell = worksheet.find(kategori)
            if cell:
                # Update kolom Batas_Anggaran (misal kolom B/2, sesuaikan dengan sheet kamu)
                # Asumsi urutan kolom: Kategori, Tipe_Budget, Batas_Anggaran
                worksheet.update_cell(cell.row, 3, nominal_baru) 
        except:
            pass # Kalau kategori ga ketemu di sheet, skip aja

try:
    sh = connect_to_sheet()
    ws_transaksi = sh.worksheet("Transaksi")
    ws_budget = sh.worksheet("Budget")
except Exception as e:
    st.error(f"❌ Koneksi Error: {e}")
    st.stop()

# --- 4. LOAD DATA ---
data_transaksi = ws_transaksi.get_all_records()
df_transaksi = pd.DataFrame(data_transaksi)
if not df_transaksi.empty:
    df_transaksi['Nominal'] = pd.to_numeric(df_transaksi['Nominal'], errors='coerce').fillna(0)
    df_transaksi['Tanggal'] = pd.to_datetime(df_transaksi['Tanggal'], errors='coerce').dt.date

data_budget = ws_budget.get_all_records()
df_budget = pd.DataFrame(data_budget)
df_budget['Batas_Anggaran'] = pd.to_numeric(df_budget['Batas_Anggaran'], errors='coerce').fillna(0)

# SETTING WAKTU WIB (UTC + 7) & PERIODE GAJI
wib_now = datetime.utcnow() + timedelta(hours=7)
today_date = wib_now.date()
start_periode, end_periode = get_payroll_period(today_date)

# Filter Data Sesuai Periode Gaji (20 - 19)
if not df_transaksi.empty:
    df_periode = df_transaksi[
        (df_transaksi['Tanggal'] >= start_periode) & 
        (df_transaksi['Tanggal'] <= end_periode)
    ]
else:
    df_periode = pd.DataFrame()

# --- HALAMAN 1: HOME ---
def show_home():
    jam = wib_now.hour
    if 5 <= jam < 11: greeting, icon = "Selamat Pagi", "☀️"
    elif 11 <= jam < 15: greeting, icon = "Selamat Siang", "🌤️"
    elif 15 <= jam < 18: greeting, icon = "Selamat Sore", "🌇"
    else: greeting, icon = "Selamat Malam", "🌙"

    st.markdown(f"""
        <div class="header-box">
            <h1>{greeting}, Raka! {icon}</h1>
            <p>Periode: {start_periode.strftime('%d %b')} - {end_periode.strftime('%d %b %Y')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("📝 **CATAT & PANTAU**")
        if st.button("Buka Dashboard", key="btn_dash", use_container_width=True): navigate_to('dashboard')
    with col2:
        st.success("📜 **EVALUASI**")
        if st.button("Lihat & Download Riwayat", key="btn_hist", use_container_width=True): navigate_to('history')

# --- HALAMAN 2: DASHBOARD ---
def show_dashboard():
    # SIDEBAR
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/9382/9382189.png", width=80)
        st.markdown("### Input Transaksi")
        with st.form(key='input_form', clear_on_submit=True):
            tgl_input = st.date_input("Tanggal", today_date)
            tipe_input = st.selectbox("Tipe", ["Pengeluaran", "Pemasukan"])
            list_kategori = df_budget['Kategori'].tolist() if not df_budget.empty else ["Umum"]
            kategori_input = st.selectbox("Kategori", list_kategori)
            nominal_input = st.number_input("Nominal (Rp)", min_value=0, step=1000)
            ket_input = st.text_input("Catatan")
            st.markdown("---")
            submit_button = st.form_submit_button(label='Simpan Data')

        if submit_button:
            # 1. Simpan Transaksi
            row_data = [str(tgl_input), tipe_input, kategori_input, nominal_input, ket_input]
            ws_transaksi.append_row(row_data)
            
            # 2. Cek Otomatisasi Gaji
            if tipe_input == "Pemasukan" and "Gaji" in kategori_input:
                with st.spinner("🤖 Mendeteksi Gaji... Mengatur Ulang Anggaran Otomatis..."):
                    update_budget_allocation(ws_budget, nominal_input)
                    st.success(f"✅ Anggaran berhasil di-reset otomatis sesuai persentase Gaji Rp {nominal_input:,}!")
                    time.sleep(2)
            
            st.toast("Data Tersimpan!", icon="✅")
            st.rerun()
        
        st.write("")
        if st.button("⬅️ Kembali ke Home"): navigate_to('home')

    # KONTEN UTAMA
    st.markdown(f"## 📊 Dashboard Periode Ini")
    st.caption(f"Rentang: {start_periode.strftime('%d %b')} - {end_periode.strftime('%d %b')}")
    
    total_masuk = df_periode[df_periode['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_periode.empty else 0
    total_keluar = df_periode[df_periode['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_periode.empty else 0
    sisa_uang = total_masuk - total_keluar
    
    # 1. SALDO HARIAN PINTAR (Makan & Rokok)
    st.markdown("### 🔥 Jatah Harian (Makan & Rokok)")
    # Hitung Budget Khusus Harian
    budget_harian_total = df_budget[df_budget['Kategori'].isin(KATEGORI_HARIAN)]['Batas_Anggaran'].sum()
    # Hitung Terpakai Khusus Harian di Periode Ini
    terpakai_harian = 0
    if not df_periode.empty:
        terpakai_harian = df_periode[
            (df_periode['Tipe'] == 'Pengeluaran') & 
            (df_periode['Kategori'].isin(KATEGORI_HARIAN))
        ]['Nominal'].sum()
    
    sisa_budget_harian = budget_harian_total - terpakai_harian
    # Hitung sisa hari sampai tgl 20 bulan depan (atau tgl 19)
    sisa_hari = (end_periode - today_date).days + 1
    jatah_per_hari = sisa_budget_harian / sisa_hari if sisa_hari > 0 else 0

    col_h1, col_h2 = st.columns(2)
    col_h1.metric("Boleh Jajan Hari Ini", f"Rp {jatah_per_hari:,.0f}", delta=f"Sisa {sisa_hari} hari")
    col_h2.metric("Sisa Budget Harian", f"Rp {sisa_budget_harian:,.0f}", delta="-Terpakai")

    st.markdown("---")

    # 2. METRIK UTAMA
    c1, c2, c3 = st.columns(3)
    c1.metric("Sisa Saldo Total", f"Rp {sisa_uang:,.0f}", delta="Cashflow")
    c2.metric("Pemasukan", f"Rp {total_masuk:,.0f}")
    c3.metric("Pengeluaran", f"Rp {total_keluar:,.0f}", delta="-Terpakai", delta_color="inverse")

    # 3. MONITORING DETAIL PER KATEGORI
    st.markdown("### 📋 Status Anggaran Per Kategori")
    df_mon = df_budget.copy()
    if not df_periode.empty:
        used = df_periode[df_periode['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum()
        df_mon['Terpakai'] = df_mon['Kategori'].map(used).fillna(0)
    else:
        df_mon['Terpakai'] = 0
    
    df_mon['Sisa'] = df_mon['Batas_Anggaran'] - df_mon['Terpakai']
    df_mon['Persen'] = (df_mon['Terpakai'] / df_mon['Batas_Anggaran']) * 100
    df_mon['Persen'] = df_mon['Persen'].fillna(0)

    # Indikator Status
    def get_status(row):
        if row['Sisa'] < 0: return "🚨 OVER!"
        elif row['Persen'] > 80: return "⚠️ Hati-hati"
        else: return "✅ Aman"
    
    df_mon['Status'] = df_mon.apply(get_status, axis=1)

    # Tampilkan Tabel
    st.dataframe(
        df_mon[['Kategori', 'Batas_Anggaran', 'Terpakai', 'Sisa', 'Persen', 'Status']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Batas_Anggaran": st.column_config.NumberColumn("Budget", format="Rp %d"),
            "Terpakai": st.column_config.NumberColumn("Real Time", format="Rp %d"),
            "Sisa": st.column_config.NumberColumn("Sisa", format="Rp %d"),
            "Persen": st.column_config.ProgressColumn("Persentase", format="%.1f%%", min_value=0, max_value=100),
        }
    )

    if st.button("🔄 Refresh Data"): st.rerun()

# --- HALAMAN 3: RIWAYAT & EVALUASI ---
def show_history():
    st.markdown("## 📜 Evaluasi & Riwayat")
    if st.button("⬅️ Kembali ke Home"): navigate_to('home')
    st.markdown("---")
    
    if not df_transaksi.empty:
        # Filter Tampilan
        col_f1, col_f2 = st.columns(2)
        with col_f1: 
            filter_kat = st.multiselect("Filter Kategori", options=df_transaksi['Kategori'].unique())
        with col_f2: 
            filter_tipe = st.selectbox("Filter Tipe", ["Semua", "Pengeluaran", "Pemasukan"])
        
        df_show = df_transaksi.copy()
        if filter_kat: df_show = df_show[df_show['Kategori'].isin(filter_kat)]
        if filter_tipe != "Semua": df_show = df_show[df_show['Tipe'] == filter_tipe]
        
        # Download Button
        csv = df_show.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv,
            file_name=f'Laporan_Keuangan_Raka_{today_date}.csv',
            mime='text/csv',
        )

        st.dataframe(
            df_show.sort_values(by='Tanggal', ascending=False), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"), 
                "Nominal": st.column_config.NumberColumn("Nominal", format="Rp %d")
            }
        )
    else: st.info("Belum ada data.")

# --- ROUTER ---
if st.session_state['page'] == 'home': show_home()
elif st.session_state['page'] == 'dashboard': show_dashboard()
elif st.session_state['page'] == 'history': show_history()