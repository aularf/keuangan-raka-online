import streamlit as st
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date
import calendar
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dompet Raka", page_icon="💎", layout="wide")

# --- CSS TEMA: APP-LIKE EXPERIENCE ---
st.markdown("""
    <style>
        /* Base Style */
        .stApp { background-color: #f8fafc; color: #0f172a; }
        
        /* Tombol Menu Besar di Home */
        .big-button {
            width: 100%;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* Styling Sidebar & Header */
        [data-testid="stSidebar"] { background-color: #1e293b; }
        [data-testid="stSidebar"] * { color: #f1f5f9 !important; }
        h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #0f172a; }
        
        /* Card Metrik */
        div[data-testid="stMetric"] {
            background-color: white; border-left: 5px solid #3b82f6;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 10px;
            padding: 10px;
        }

        /* Navigasi Button Custom */
        div.stButton > button {
            width: 100%;
            border-radius: 10px;
            font-weight: bold;
            height: 50px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. MANAJEMEN NAVIGASI (SESSION STATE) ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

def navigate_to(page):
    st.session_state['page'] = page
    st.rerun()

# --- 3. KONEKSI DATABASE ---
@st.cache_resource
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        secrets_data = st.secrets["gcp_service_account"]
        if isinstance(secrets_data, str):
            creds_dict = json.loads(secrets_data)
        else:
            creds_dict = dict(secrets_data)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.load(open("credentials.json")), scope
        )
    client = gspread.authorize(creds)
    return client.open("MyMonetaryApp")

try:
    sh = connect_to_sheet()
    ws_transaksi = sh.worksheet("Transaksi")
    ws_budget = sh.worksheet("Budget")
except Exception as e:
    st.error(f"❌ Koneksi Error: {e}")
    st.stop()

# --- 4. PREPARE DATA ---
data_transaksi = ws_transaksi.get_all_records()
df_transaksi = pd.DataFrame(data_transaksi)
if not df_transaksi.empty:
    df_transaksi['Nominal'] = pd.to_numeric(df_transaksi['Nominal'], errors='coerce').fillna(0)
    df_transaksi['Tanggal'] = pd.to_datetime(df_transaksi['Tanggal'], errors='coerce')

data_budget = ws_budget.get_all_records()
df_budget = pd.DataFrame(data_budget)
df_budget['Batas_Anggaran'] = pd.to_numeric(df_budget['Batas_Anggaran'], errors='coerce').fillna(0)

now = datetime.now()
df_this_year = df_transaksi[df_transaksi['Tanggal'].dt.year == now.year] if not df_transaksi.empty else pd.DataFrame()

# --- HALAMAN 1: HOME (SELAMAT DATANG) ---
def show_home():
    # Sapaan Waktu
    jam = datetime.now().hour
    if 5 <= jam < 12: greeting = "Selamat Pagi"
    elif 12 <= jam < 15: greeting = "Selamat Siang"
    elif 15 <= jam < 18: greeting = "Selamat Sore"
    else: greeting = "Selamat Malam"

    col_space1, col_center, col_space2 = st.columns([1, 2, 1])
    with col_center:
        st.markdown(f"<h1 style='text-align: center; margin-bottom:0;'>{greeting}, Raka! 👋</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #64748b; font-weight: 400;'>Bagaimana keuanganmu hari ini?</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Menu Pilihan
        st.write("")
        st.write("")
        
        # Tombol A: Input & Dashboard
        btn_dashboard = st.button("📝 INPUT & MONITORING\n(Catat Transaksi & Cek Grafik)", type="primary", use_container_width=True)
        if btn_dashboard:
            navigate_to('dashboard')
            
        st.write("")
        
        # Tombol B: Riwayat
        btn_history = st.button("📜 LIHAT RIWAYAT\n(Daftar Semua Transaksi)", type="secondary", use_container_width=True)
        if btn_history:
            navigate_to('history')

        st.markdown("---")
        st.caption("Dompet Raka v3.0 • Financial Command Center")

# --- HALAMAN 2: DASHBOARD (INPUT & ANALISA) ---
def show_dashboard():
    # --- SIDEBAR INPUT ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/9382/9382189.png", width=100)
        st.title("Input Transaksi")
        with st.form(key='input_form', clear_on_submit=True):
            tgl_input = st.date_input("Tanggal", date.today())
            tipe_input = st.selectbox("Tipe", ["Pengeluaran", "Pemasukan"])
            list_kategori = df_budget['Kategori'].tolist() if not df_budget.empty else ["Umum"]
            kategori_input = st.selectbox("Kategori", list_kategori)
            nominal_input = st.number_input("Nominal (Rp)", min_value=0, step=1000)
            ket_input = st.text_input("Catatan")
            submit_button = st.form_submit_button(label='💾 SIMPAN DATA')

        if submit_button:
            row_data = [str(tgl_input), tipe_input, kategori_input, nominal_input, ket_input]
            ws_transaksi.append_row(row_data)
            st.toast("Data Berhasil Masuk! Dashboard diperbarui.", icon="✅")
            st.rerun()
            
        st.markdown("---")
        if st.button("🏠 KEMBALI KE HOME"):
            navigate_to('home')

    # --- MAIN CONTENT ---
    st.title("📊 Monitoring Keuangan Real-Time")
    
    # Hitung Data
    total_masuk = df_this_year[df_this_year['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_this_year.empty else 0
    total_keluar = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_this_year.empty else 0
    sisa_uang = total_masuk - total_keluar
    
    # Logika Kesehatan Keuangan (Komentar Otomatis)
    if total_masuk > 0:
        ratio = total_keluar / total_masuk
        if sisa_uang < 0:
            kondisi = "🚨 **DARURAT!** Besar pasak daripada tiang. Kamu minus!"
            warna_kondisi = "error"
        elif ratio > 0.8:
            kondisi = "⚠️ **HATI-HATI!** Pengeluaranmu sudah 80% dari pemasukan. Rem sedikit ya!"
            warna_kondisi = "warning"
        elif ratio > 0.5:
            kondisi = "✅ **AMAN.** Pengeluaran masih wajar, tapi tetap pantau terus."
            warna_kondisi = "success"
        else:
            kondisi = "🌿 **SEHAT BANGET!** Kamu hemat banget, tabungan aman."
            warna_kondisi = "success"
    else:
        kondisi = "😐 Belum ada pemasukan yang tercatat."
        warna_kondisi = "info"

    # Tampilkan Pesan Kondisi
    if warna_kondisi == "error": st.error(kondisi)
    elif warna_kondisi == "warning": st.warning(kondisi)
    elif warna_kondisi == "success": st.success(kondisi)
    else: st.info(kondisi)

    # Metric Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Sisa Uang (Cashflow)", f"Rp {sisa_uang:,.0f}", delta="Saldo Saat Ini")
    c2.metric("Total Pemasukan", f"Rp {total_masuk:,.0f}")
    c3.metric("Total Pengeluaran", f"Rp {total_keluar:,.0f}", delta="-Terpakai", delta_color="inverse")

    st.markdown("---")
    
    # Grafik
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("🍩 Porsi Jajan")
        df_out = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']
        if not df_out.empty:
            fig = px.pie(df_out, values='Nominal', names='Kategori', hole=0.5, color_discrete_sequence=px.colors.qualitative.Vivid)
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data pengeluaran.")

    with c_right:
        st.subheader("📉 Budget vs Realisasi")
        df_mon = df_budget.copy()
        if not df_this_year.empty:
            used = df_this_year[df_this_year['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum()
            df_mon['Terpakai'] = df_mon['Kategori'].map(used).fillna(0)
        else:
            df_mon['Terpakai'] = 0
        df_mon['Persen'] = (df_mon['Terpakai'] / df_mon['Batas_Anggaran']).fillna(0) * 100
        
        # Bar Chart Logic
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Batas_Anggaran'], orientation='h', name='Batas', marker_color='#e2e8f0'))
        colors = ['#2563eb' if p < 85 else '#ef4444' for p in df_mon['Persen']]
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Terpakai'], orientation='h', name='Terpakai', marker_color=colors))
        fig_bar.update_layout(barmode='overlay', showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=300)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.write("")
    if st.button("🔄 Buat Laporan Baru / Reset Tampilan", use_container_width=True):
        st.rerun()

# --- HALAMAN 3: RIWAYAT ---
def show_history():
    st.title("📜 Riwayat Transaksi")
    if st.button("⬅️ KEMBALI KE MENU UTAMA"):
        navigate_to('home')
    
    st.markdown("---")
    
    if not df_transaksi.empty:
        # Filter Sederhana
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_kat = st.multiselect("Filter Kategori", options=df_transaksi['Kategori'].unique())
        with col_f2:
            filter_tipe = st.selectbox("Filter Tipe", ["Semua", "Pengeluaran", "Pemasukan"])
            
        df_show = df_transaksi.copy()
        if filter_kat:
            df_show = df_show[df_show['Kategori'].isin(filter_kat)]
        if filter_tipe != "Semua":
            df_show = df_show[df_show['Tipe'] == filter_tipe]
            
        st.dataframe(
            df_show.sort_values(by='Tanggal', ascending=False),
            use_container_width=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "Nominal": st.column_config.NumberColumn("Nominal", format="Rp %d")
            }
        )
    else:
        st.info("Belum ada data sama sekali.")

# --- MAIN ROUTER ---
if st.session_state['page'] == 'home':
    show_home()
elif st.session_state['page'] == 'dashboard':
    show_dashboard()
elif st.session_state['page'] == 'history':
    show_history()