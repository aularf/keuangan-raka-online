import streamlit as st
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timedelta # Tambah timedelta buat WIB
import calendar
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dompet Raka", page_icon="💳", layout="wide")

# --- CSS TEMA: TOSCA UNIFIED (LIGHT MODE FORCED) ---
st.markdown("""
    <style>
        /* PAKSA MODE TERANG (Light Mode Override) */
        :root {
            --primary-color: #0d9488;
            --background-color: #f0fdfa;
            --secondary-background-color: #ffffff;
            --text-color: #0f172a;
            --font: "Helvetica Neue", sans-serif;
        }

        /* GLOBAL TEXT COLOR - HITAM PEKAT */
        html, body, [class*="css"], [class*="st-"], h1, h2, h3, p, span, div, label {
            color: #0f172a !important; 
            font-family: 'Helvetica', sans-serif;
        }

        /* BACKGROUND UTAMA: Gradasi Tosca Muda */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #ccfbf1 0%, #ffffff 100%);
        }

        /* SIDEBAR: Putih Bersih */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #99f6e4;
        }
        
        /* HEADER BOX */
        .header-box {
            background: linear-gradient(90deg, #0f766e 0%, #14b8a6 100%);
            padding: 30px;
            border-radius: 15px;
            color: white !important;
            text-align: center;
            box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3);
            margin-bottom: 25px;
        }
        .header-box h1 { color: white !important; margin: 0; font-size: 2.5rem; }
        .header-box p { color: #f0fdfa !important; font-size: 1.1rem; }

        /* PERBAIKAN INPUT FIELD (BIAR GAK HITAM) */
        /* Kotak Input */
        .stTextInput input, .stNumberInput input, .stDateInput input {
            background-color: #ffffff !important; /* Latar Putih */
            color: #0f172a !important; /* Teks Hitam */
            border: 1px solid #0d9488 !important; /* Garis Tosca */
            border-radius: 8px;
        }
        /* Dropdown (Selectbox) */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #0d9488 !important;
            border-radius: 8px;
        }
        /* Pilihan di dalam Dropdown */
        li[role="option"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }

        /* KARTU MENU & METRIK */
        div[data-testid="stMetric"], div[data-testid="stForm"], .menu-card {
            background-color: #ffffff !important;
            border: 1px solid #ccfbf1;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(13, 148, 136, 0.1);
            padding: 20px;
        }

        /* TEXT METRIC */
        [data-testid="stMetricValue"] {
            color: #0d9488 !important; /* Angka Tosca */
            font-size: 28px;
            font-weight: 800;
        }

        /* TOMBOL UTAMA */
        div.stButton > button {
            background: linear-gradient(90deg, #0d9488 0%, #14b8a6 100%);
            color: white !important;
            border: none;
            height: 50px;
            border-radius: 10px;
            font-weight: bold;
        }
        div.stButton > button:hover {
            opacity: 0.9;
            color: white !important;
            transform: translateY(-2px);
        }
        
        /* Tombol Sekunder (Menu) */
        div.stButton > button[key*="btn_"] {
            background: white;
            color: #0d9488 !important;
            border: 2px solid #0d9488;
        }

        /* TABEL */
        [data-testid="stDataFrame"] {
            border: 1px solid #ccfbf1;
            border-radius: 10px;
            background-color: white;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. NAVIGASI ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'
def navigate_to(page):
    st.session_state['page'] = page
    st.rerun()

# --- 3. KONEKSI ---
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

# --- 4. DATA & WAKTU (WIB) ---
data_transaksi = ws_transaksi.get_all_records()
df_transaksi = pd.DataFrame(data_transaksi)
if not df_transaksi.empty:
    df_transaksi['Nominal'] = pd.to_numeric(df_transaksi['Nominal'], errors='coerce').fillna(0)
    df_transaksi['Tanggal'] = pd.to_datetime(df_transaksi['Tanggal'], errors='coerce')

data_budget = ws_budget.get_all_records()
df_budget = pd.DataFrame(data_budget)
df_budget['Batas_Anggaran'] = pd.to_numeric(df_budget['Batas_Anggaran'], errors='coerce').fillna(0)

# SETTING WAKTU WIB (UTC + 7)
wib_now = datetime.utcnow() + timedelta(hours=7)
df_this_year = df_transaksi[df_transaksi['Tanggal'].dt.year == wib_now.year] if not df_transaksi.empty else pd.DataFrame()

# --- HALAMAN 1: HOME ---
def show_home():
    jam = wib_now.hour # Pakai Jam WIB
    if 5 <= jam < 11: greeting, icon = "Selamat Pagi", "☀️"
    elif 11 <= jam < 15: greeting, icon = "Selamat Siang", "🌤️"
    elif 15 <= jam < 18: greeting, icon = "Selamat Sore", "🌇"
    else: greeting, icon = "Selamat Malam", "🌙"

    # Header
    st.markdown(f"""
        <div class="header-box">
            <h1>{greeting}, Raka! {icon}</h1>
            <p>Aplikasi siap! Sekarang jam {wib_now.strftime('%H:%M')} WIB</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center;'>🚀 Menu Utama</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("📝 **CATAT & PANTAU**")
        if st.button("Buka Dashboard", key="btn_dash", use_container_width=True): navigate_to('dashboard')
    with col2:
        st.success("📜 **LIHAT DATA LAMA**")
        if st.button("Lihat Riwayat", key="btn_hist", use_container_width=True): navigate_to('history')

# --- HALAMAN 2: DASHBOARD ---
def show_dashboard():
    # SIDEBAR SERASI
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/9382/9382189.png", width=80)
        st.markdown("### Input Transaksi")
        with st.form(key='input_form', clear_on_submit=True):
            tgl_input = st.date_input("Tanggal", wib_now)
            tipe_input = st.selectbox("Tipe", ["Pengeluaran", "Pemasukan"])
            list_kategori = df_budget['Kategori'].tolist() if not df_budget.empty else ["Umum"]
            kategori_input = st.selectbox("Kategori", list_kategori)
            nominal_input = st.number_input("Nominal (Rp)", min_value=0, step=1000)
            ket_input = st.text_input("Catatan")
            st.markdown("---")
            submit_button = st.form_submit_button(label='Simpan Data')

        if submit_button:
            row_data = [str(tgl_input), tipe_input, kategori_input, nominal_input, ket_input]
            ws_transaksi.append_row(row_data)
            st.toast("Data Tersimpan!", icon="✅")
            st.rerun()
        
        st.write("")
        if st.button("⬅️ Kembali ke Home"): navigate_to('home')

    # KONTEN UTAMA
    st.markdown("## 📊 Monitoring Keuangan")
    st.caption(f"Update per {wib_now.strftime('%d %B %Y')}")
    
    total_masuk = df_this_year[df_this_year['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_this_year.empty else 0
    total_keluar = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_this_year.empty else 0
    sisa_uang = total_masuk - total_keluar
    
    # STATUS BOX
    if total_masuk > 0:
        ratio = total_keluar / total_masuk
        if sisa_uang < 0: st.error("🚨 **DARURAT!** Saldo Minus!")
        elif ratio > 0.8: st.warning("⚠️ **BOROS!** Pengeluaran > 80%")
        else: st.success("✅ **SEHAT!** Keuangan Aman.")
    else:
        st.info("ℹ️ Belum ada pemasukan bulan ini.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Sisa Saldo", f"Rp {sisa_uang:,.0f}", delta="Cashflow")
    c2.metric("Pemasukan", f"Rp {total_masuk:,.0f}")
    c3.metric("Pengeluaran", f"Rp {total_keluar:,.0f}", delta="-Terpakai", delta_color="inverse")

    st.markdown("---")

    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("🍩 Porsi Jajan")
        df_out = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']
        if not df_out.empty:
            # FIX TEXT CHART HITAM
            fig = px.pie(df_out, values='Nominal', names='Kategori', hole=0.6, color_discrete_sequence=px.colors.qualitative.Prism)
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=300, paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="black", size=14)) # PAKSA HITAM
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Kosong.")

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
        colors = ['#0d9488' if p < 85 else '#ef4444' for p in df_mon['Persen']]
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Terpakai'], orientation='h', name='Terpakai', marker_color=colors, 
            text=df_mon['Persen'].apply(lambda x: f"{x:.1f}%"), textposition='auto', textfont=dict(color="white")))
        
        # FIX TEXT CHART HITAM
        fig_bar.update_layout(barmode='overlay', showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=350, 
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="black", size=12), xaxis=dict(gridcolor='#e2e8f0'))
        st.plotly_chart(fig_bar, use_container_width=True)
    
    if st.button("🔄 Refresh Data"): st.rerun()

# --- HALAMAN 3: RIWAYAT ---
def show_history():
    st.markdown("## 📜 Riwayat Transaksi")
    if st.button("⬅️ Kembali ke Home"): navigate_to('home')
    st.markdown("---")
    
    if not df_transaksi.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1: filter_kat = st.multiselect("Filter Kategori", options=df_transaksi['Kategori'].unique())
        with col_f2: filter_tipe = st.selectbox("Filter Tipe", ["Semua", "Pengeluaran", "Pemasukan"])
        
        df_show = df_transaksi.copy()
        if filter_kat: df_show = df_show[df_show['Kategori'].isin(filter_kat)]
        if filter_tipe != "Semua": df_show = df_show[df_show['Tipe'] == filter_tipe]
        
        st.dataframe(df_show.sort_values(by='Tanggal', ascending=False), use_container_width=True, hide_index=True,
             column_config={"Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"), 
                            "Nominal": st.column_config.NumberColumn("Nominal", format="Rp %d")})
    else: st.info("Belum ada data.")

# --- ROUTER ---
if st.session_state['page'] == 'home': show_home()
elif st.session_state['page'] == 'dashboard': show_dashboard()
elif st.session_state['page'] == 'history': show_history()