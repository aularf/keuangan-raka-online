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

# --- CSS TEMA: NEOBRUTALISM / HIGH CONTRAST MODERN (Gaya Inspirasi Baru) ---
st.markdown("""
    <style>
        /* BACKGROUND UTAMA: Warna Krem/Off-White Terang yang Bersih */
        [data-testid="stAppViewContainer"] {
            background-color: #F3F4F6;
            color: #000000; /* Teks Default HITAM PEKAT */
        }

        /* SIDEBAR: Hitam Solid biar kontras */
        [data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 3px solid #000000;
        }
        [data-testid="stSidebar"] * { color: #FFFFFF !important; } /* Teks Sidebar PUTIH */

        /* KARTU DATA & CONTAINER: Gaya "Pop-Out" dengan Border Tebal & Bayangan Keras */
        div[data-testid="stMetric"], div[data-testid="stForm"], .big-button-container, .stAlert {
            background-color: #FFFFFF !important; /* Latar Putih Bersih */
            border: 3px solid #000000 !important; /* Garis Tepi Hitam Tebal */
            box-shadow: 6px 6px 0px #000000 !important; /* Bayangan Keras (Hard Shadow) */
            border-radius: 12px !important;
            padding: 20px !important;
            color: #000000 !important; /* Pastikan Teks di dalamnya Hitam */
            margin-bottom: 20px;
        }

        /* PERBAIKAN TIPOGRAFI (Semua harus tegas dan jelas) */
        h1, h2, h3, h4, p, div, span, label {
            font-family: 'Inter', sans-serif !important;
            color: #000000 !important; /* Paksa jadi Hitam */
            font-weight: 700 !important; /* Agak tebal biar jelas */
        }
        
        /* Judul Angka di Kartu (Metric) */
        [data-testid="stMetricValue"] {
            font-size: 32px !important;
            font-weight: 900 !important; /* Sangat tebal */
        }
        [data-testid="stMetricLabel"] { font-size: 16px !important; font-weight: 700 !important;}

        /* TOMBOL-TOMBOL GAYA KERAS */
        div.stButton > button {
            width: 100%;
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 3px solid #000000 !important;
            box-shadow: 4px 4px 0px #000000 !important; /* Bayangan Keras */
            border-radius: 10px !important;
            font-weight: 900 !important;
            height: 55px;
            font-size: 18px !important;
            transition: all 0.1s ease-in-out;
        }

        /* Efek Hover Tombol (Bergeser & Berubah Warna Cerah) */
        div.stButton > button:hover {
             transform: translate(-2px, -2px); /* Geser ke atas kiri */
             box-shadow: 6px 6px 0px #000000 !important; /* Bayangan membesar */
             background-color: #FFD700 !important; /* Warna Kuning Emas Cerah saat disorot */
        }
        
        /* Tombol Primary (Simpan Data) dikasih warna beda */
        div.stButton > button[kind="primary"] {
            background-color: #A7F3D0 !important; /* Hijau Mint Cerah */
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #34D399 !important; /* Hijau lebih gelap saat hover */
        }

        /* Perbaikan Ikon di Tombol Menu Home */
        .home-menu-icon {
            font-size: 40px;
            margin-bottom: 10px;
            display: block;
            text-align: center;
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
        st.markdown(f"<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0;'>{greeting}, Raka! 👋</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; font-weight: 600; margin-top: 10px;'>Siap pantau cuan hari ini?</h3>", unsafe_allow_html=True)
        st.markdown("---", unsafe_allow_html=True)
        
        # Container Tombol Menu (Gaya Pop-Out)
        st.markdown('<div class="big-button-container" style="background-color: #DBEAFE !important;">', unsafe_allow_html=True) # Kasih warna biru muda dikit
        st.markdown("<h3 style='text-align: center;'>🎯 PILIH MENU</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            # Ikon dipisah biar rapi
            st.markdown('<span class="home-menu-icon">📝</span>', unsafe_allow_html=True)
            if st.button("INPUT & DASHBOARD", help="Catat transaksi dan lihat analisa grafik"): navigate_to('dashboard')
        with c2:
            st.markdown('<span class="home-menu-icon">📜</span>', unsafe_allow_html=True)
            if st.button("RIWAYAT LENGKAP", help="Lihat semua daftar transaksi"): navigate_to('history')
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
            # Tombol Primary (Hijau Mint)
            submit_button = st.form_submit_button(label='💾 SIMPAN DATA', type="primary")

        if submit_button:
            row_data = [str(tgl_input), tipe_input, kategori_input, nominal_input, ket_input]
            ws_transaksi.append_row(row_data)
            st.toast("DATA MASUK! MANTAP! 🚀", icon="✅")
            st.rerun()
        
        st.write("")
        if st.button("🏠 KEMBALI KE HOME"): navigate_to('home')

    st.title("📊 Monitoring Real-Time")
    st.markdown("---")
    
    total_masuk = df_this_year[df_this_year['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_this_year.empty else 0
    total_keluar = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_this_year.empty else 0
    sisa_uang = total_masuk - total_keluar
    
    # Komentar Otomatis (Dalam Box Kuning Cerah)
    st.markdown('<div class="big-button-container" style="background-color: #FEF9C3 !important; text-align: center;">', unsafe_allow_html=True)
    st.markdown("### 📢 STATUS KEUANGAN")
    if total_masuk > 0:
        ratio = total_keluar / total_masuk
        if sisa_uang < 0: st.markdown("### 🚨 DARURAT! MINUS! REM BLONG!")
        elif ratio > 0.8: st.markdown("### ⚠️ HATI-HATI! Udah boros nih.")
        elif ratio > 0.5: st.markdown("### ✅ AMAN. Masih terkendali.")
        else: st.markdown("### 🌿 SEHAT BANGET! Tabungan aman jaya.")
    else: st.markdown("### 😐 Belum ada pemasukan.")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Sisa Uang (Cashflow)", f"Rp {sisa_uang:,.0f}", delta="Saldo")
    c2.metric("Total Pemasukan", f"Rp {total_masuk:,.0f}")
    c3.metric("Total Pengeluaran", f"Rp {total_keluar:,.0f}", delta="-Terpakai", delta_color="inverse")

    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("🍩 Porsi Jajan")
        df_out = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']
        if not df_out.empty:
            # Warna chart yang lebih tegas (Bold)
            fig = px.pie(df_out, values='Nominal', names='Kategori', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
            # Paksa teks chart jadi HITAM dan tebal
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#000000", size=14, family="Inter Black"))
            fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
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
        # Bar Background (Abu gelap tegas)
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Batas_Anggaran'], orientation='h', name='Batas', marker_color='#9CA3AF', marker_line_width=2, marker_line_color='black'))
        colors = ['#3b82f6' if p < 85 else '#ef4444' for p in df_mon['Persen']]
        # Bar Terpakai dengan border hitam
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Terpakai'], orientation='h', name='Terpakai', marker_color=colors, text=df_mon['Persen'].apply(lambda x: f"{x:.1f}%"), textposition='auto', marker_line_width=2, marker_line_color='black'))
        
        # Paksa semua teks dan grid chart jadi HITAM TEGAS
        fig_bar.update_layout(barmode='overlay', showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#000000", size=13, family="Inter Bold"), xaxis=dict(gridcolor='#000000', gridwidth=1), yaxis=dict(gridcolor='#000000'))
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    if st.button("🔄 REFRESH DATA", use_container_width=True): st.rerun()

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
        
        # Tabel dengan border tegas
        st.markdown('<style> [data-testid="stDataFrame"] { border: 3px solid black !important; border-radius: 10px; } </style>', unsafe_allow_html=True)
        st.dataframe(df_show.sort_values(by='Tanggal', ascending=False), use_container_width=True, column_config={"Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"), "Nominal": st.column_config.NumberColumn("Nominal", format="Rp %d")})
    else: st.info("Belum ada data sama sekali.")

# --- MAIN ROUTER ---
if st.session_state['page'] == 'home': show_home()
elif st.session_state['page'] == 'dashboard': show_dashboard()
elif st.session_state['page'] == 'history': show_history()