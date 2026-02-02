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

# --- CSS TEMA: MODERN GLASS UI (Ganteng Maksimal) ---
st.markdown("""
    <style>
        /* BACKGROUND GRADASI HALUS (Biar gak monoton) */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(to top, #dfe9f3 0%, white 100%);
        }

        /* SIDEBAR (Tetap Gelap biar kontras tegas buat input) */
        [data-testid="stSidebar"] {
            background-color: #1e293b;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }
        [data-testid="stSidebar"] * { color: #f1f5f9 !important; }

        /* KARTU KACA (Glassmorphism Effect) - Ini rahasianya! */
        div[data-testid="stMetric"], div[data-testid="stForm"], .big-button-container {
            background: rgba(255, 255, 255, 0.7); /* Putih transparan */
            backdrop-filter: blur(10px); /* Efek kaca buram */
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.5);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07); /* Bayangan lembut */
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 15px;
        }

        /* PERBAIKAN KONTRAS TEKS (Wajib Hitam/Gelap) */
        h1, h2, h3, p, div, span {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #1e293b; /* Warna Slate Dark - Pasti Kelihatan */
        }
        
        /* Judul Angka di Kartu */
        [data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: 800;
            color: #0f172a !important; /* Hitam Pekat */
        }
        [data-testid="stMetricLabel"] { font-weight: 600; color: #475569 !important; }

        /* TOMBOL-TOMBOL KEREN */
        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            font-weight: bold;
            height: 55px;
            font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.2s ease-in-out;
        }
        /* Tombol Primary (Biru) */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        /* Hover effect */
        div.stButton > button:hover {
             transform: translateY(-3px);
             box-shadow: 0 7px 14px rgba(0,0,0,0.2);
        }

    </style>
""", unsafe_allow_html=True)

# --- 2. MANAJEMEN NAVIGASI ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'
def navigate_to(page):
    st.session_state['page'] = page
    st.rerun()

# --- 3. KONEKSI DATABASE ---
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

# --- HALAMAN 1: HOME ---
def show_home():
    jam = datetime.now().hour
    if 5 <= jam < 12: greeting = "Selamat Pagi"
    elif 12 <= jam < 15: greeting = "Selamat Siang"
    elif 15 <= jam < 18: greeting = "Selamat Sore"
    else: greeting = "Selamat Malam"

    # Layout Tengah
    col_sp1, col_main, col_sp2 = st.columns([1, 6, 1])
    with col_main:
        st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{greeting}, Raka! 👋</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #475569; font-weight: 400;'>Mau cek kondisi dompet atau catat jajan nih?</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Container Kaca untuk Tombol Menu
        st.markdown('<div class="big-button-container">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            # Pakai emoji besar biar interaktif
            st.markdown("<h1 style='text-align: center;'>📝</h1>", unsafe_allow_html=True)
            if st.button("INPUT & DASHBOARD\n(Catat & Analisa)", type="primary"): navigate_to('dashboard')
        with c2:
            st.markdown("<h1 style='text-align: center;'>📜</h1>", unsafe_allow_html=True)
            if st.button("RIWAYAT TRANSAKSI\n(Lihat Semua Data)"): navigate_to('history')
        st.markdown('</div>', unsafe_allow_html=True)

# --- HALAMAN 2: DASHBOARD ---
def show_dashboard():
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
            st.markdown("---")
            submit_button = st.form_submit_button(label='💾 SIMPAN DATA', type="primary")

        if submit_button:
            row_data = [str(tgl_input), tipe_input, kategori_input, nominal_input, ket_input]
            ws_transaksi.append_row(row_data)
            st.toast("Data Berhasil Masuk! Dashboard diperbarui.", icon="✅")
            st.rerun()
        
        st.write("")
        if st.button("🏠 KEMBALI KE HOME"): navigate_to('home')

    st.title("📊 Monitoring Keuangan Real-Time")
    
    total_masuk = df_this_year[df_this_year['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_this_year.empty else 0
    total_keluar = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_this_year.empty else 0
    sisa_uang = total_masuk - total_keluar
    
    # Komentar Otomatis (Dalam Box Kaca)
    st.markdown('<div class="big-button-container" style="padding: 15px; text-align: center;">', unsafe_allow_html=True)
    if total_masuk > 0:
        ratio = total_keluar / total_masuk
        if sisa_uang < 0: st.error("🚨 **DARURAT!** Besar pasak daripada tiang. Kamu minus!")
        elif ratio > 0.8: st.warning("⚠️ **HATI-HATI!** Pengeluaranmu sudah 80% dari pemasukan.")
        elif ratio > 0.5: st.success("✅ **AMAN.** Pengeluaran masih wajar, pantau terus.")
        else: st.success("🌿 **SEHAT BANGET!** Kamu hemat banget, tabungan aman.")
    else: st.info("😐 Belum ada pemasukan yang tercatat tahun ini.")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Sisa Uang (Cashflow)", f"Rp {sisa_uang:,.0f}", delta="Saldo Saat Ini")
    c2.metric("Total Pemasukan", f"Rp {total_masuk:,.0f}")
    c3.metric("Total Pengeluaran", f"Rp {total_keluar:,.0f}", delta="-Terpakai", delta_color="inverse")

    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("🍩 Porsi Jajan")
        df_out = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']
        if not df_out.empty:
            fig = px.pie(df_out, values='Nominal', names='Kategori', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
            # Pastikan teks di chart HITAM
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#1e293b"))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Belum ada data pengeluaran.")

    with c_right:
        st.subheader("📉 Budget vs Realisasi")
        df_mon = df_budget.copy()
        if not df_this_year.empty:
            used = df_this_year[df_this_year['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum()
            df_mon['Terpakai'] = df_mon['Kategori'].map(used).fillna(0)
        else: df_mon['Terpakai'] = 0
        df_mon['Persen'] = (df_mon['Terpakai'] / df_mon['Batas_Anggaran']).fillna(0) * 100
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Batas_Anggaran'], orientation='h', name='Batas', marker_color='#cbd5e1'))
        colors = ['#3b82f6' if p < 85 else '#ef4444' for p in df_mon['Persen']]
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Terpakai'], orientation='h', name='Terpakai', marker_color=colors, text=df_mon['Persen'].apply(lambda x: f"{x:.1f}%"), textposition='auto'))
        # Pastikan teks dan grid chart HITAM/GELAP
        fig_bar.update_layout(barmode='overlay', showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#1e293b"), xaxis=dict(gridcolor='#94a3b8'))
        st.plotly_chart(fig_bar, use_container_width=True)
    
    if st.button("🔄 Refresh Data / Buat Laporan Baru", use_container_width=True): st.rerun()

# --- HALAMAN 3: RIWAYAT ---
def show_history():
    st.title("📜 Riwayat Transaksi")
    if st.button("⬅️ KEMBALI KE MENU UTAMA"): navigate_to('home')
    st.markdown("---")
    if not df_transaksi.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1: filter_kat = st.multiselect("Filter Kategori", options=df_transaksi['Kategori'].unique())
        with col_f2: filter_tipe = st.selectbox("Filter Tipe", ["Semua", "Pengeluaran", "Pemasukan"])
        df_show = df_transaksi.copy()
        if filter_kat: df_show = df_show[df_show['Kategori'].isin(filter_kat)]
        if filter_tipe != "Semua": df_show = df_show[df_show['Tipe'] == filter_tipe]
        st.dataframe(df_show.sort_values(by='Tanggal', ascending=False), use_container_width=True, column_config={"Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"), "Nominal": st.column_config.NumberColumn("Nominal", format="Rp %d")})
    else: st.info("Belum ada data sama sekali.")

# --- MAIN ROUTER ---
if st.session_state['page'] == 'home': show_home()
elif st.session_state['page'] == 'dashboard': show_dashboard()
elif st.session_state['page'] == 'history': show_history()