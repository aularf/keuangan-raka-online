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
st.set_page_config(page_title="Dompet Raka", page_icon="💳", layout="wide")

# --- CSS TEMA: TOSCA CLEAN (High Contrast) ---
st.markdown("""
    <style>
        /* GLOBAL FONT & COLOR */
        html, body, [class*="css"] {
            font-family: 'Helvetica', 'Arial', sans-serif;
            color: #1e293b; /* Teks Utama: Hitam Slate Gelap (Pasti Kebaca) */
        }

        /* BACKGROUND UTAMA: Gradasi Tosca Muda ke Putih */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #ccfbf1 0%, #ffffff 100%); /* Teal-100 to White */
        }

        /* SIDEBAR: Putih Bersih dengan Aksen Tosca (Biar serasi) */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #99f6e4; /* Garis Tosca Tipis */
        }
        
        /* Teks di Sidebar PASTI HITAM */
        [data-testid="stSidebar"] * {
            color: #0f172a !important; /* Hitam Pekat */
        }
        
        /* Input Field di Sidebar */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #f0fdfa; /* Tosca Paling Muda */
            color: #0f172a;
            border: 1px solid #14b8a6; /* Border Tosca */
        }

        /* HEADER BOX (Sapaan) */
        .header-box {
            background: linear-gradient(90deg, #0d9488 0%, #14b8a6 100%); /* Tosca Gelap ke Terang */
            padding: 25px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3);
            margin-bottom: 25px;
        }
        .header-box h1 { color: white !important; margin: 0; font-size: 2.5rem; }
        .header-box p { color: #f0fdfa !important; font-size: 1.1rem; margin-top: 5px; }

        /* KARTU MENU & DATA (Putih Bersih + Shadow Tosca Tipis) */
        div[data-testid="stMetric"], div.stButton > button, div[data-testid="stForm"] {
            background-color: #ffffff;
            border-radius: 12px;
            border: 1px solid #ccfbf1;
            box-shadow: 0 4px 6px rgba(13, 148, 136, 0.1);
            color: #1e293b;
        }

        /* JUDUL ANGKA (METRIC) */
        [data-testid="stMetricValue"] {
            font-size: 26px;
            font-weight: 800;
            color: #0d9488; /* Tosca Tua */
        }
        [data-testid="stMetricLabel"] { font-size: 14px; font-weight: 600; color: #64748b; }

        /* TOMBOL UTAMA (Tosca Gradient) */
        div.stButton > button {
            background: linear-gradient(90deg, #0d9488 0%, #14b8a6 100%);
            color: white !important; /* Teks Tombol PUTIH TEGAS */
            border: none;
            border-radius: 10px;
            height: 50px;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(20, 184, 166, 0.4);
            color: white !important;
        }
        
        /* Tombol Sekunder/Menu (Putih Border Tosca) */
        div.stButton > button[key*="btn_dash"], div.stButton > button[key*="btn_hist"] {
            background: #ffffff;
            color: #0d9488 !important; /* Teks Tosca */
            border: 2px solid #0d9488;
        }
        div.stButton > button[key*="btn_dash"]:hover, div.stButton > button[key*="btn_hist"]:hover {
            background: #f0fdfa;
        }

        /* ALERT BOXES */
        .stAlert { background-color: #ffffff; border: 1px solid #e2e8f0; }

        /* Perbaikan Tabel */
        [data-testid="stDataFrame"] { border: 1px solid #ccfbf1; border-radius: 10px; }

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
    if 5 <= jam < 12: greeting, icon = "Selamat Pagi", "☀️"
    elif 12 <= jam < 15: greeting, icon = "Selamat Siang", "🌤️"
    elif 15 <= jam < 18: greeting, icon = "Selamat Sore", "🌇"
    else: greeting, icon = "Selamat Malam", "🌙"

    # Header Tosca (HTML)
    st.markdown(f"""
        <div class="header-box">
            <h1>{greeting}, Raka! {icon}</h1>
            <p>Siap pantau cuan hari ini?</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center; color: #0f172a;'>🚀 Pilih Menu Aplikasi</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>📝</h1>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: #0d9488;'>Input & Dashboard</h4>", unsafe_allow_html=True)
            if st.button("Buka Dashboard", key="btn_dash", use_container_width=True):
                navigate_to('dashboard')

    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>📜</h1>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: #0d9488;'>Riwayat Lengkap</h4>", unsafe_allow_html=True)
            if st.button("Lihat Riwayat", key="btn_hist", use_container_width=True):
                navigate_to('history')

# --- HALAMAN 2: DASHBOARD ---
def show_dashboard():
    # SIDEBAR: Sekarang Putih & Tosca (Serasi)
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/9382/9382189.png", width=80)
        st.markdown("<h2 style='color: #0d9488;'>Input Transaksi</h2>", unsafe_allow_html=True)
        
        with st.form(key='input_form', clear_on_submit=True):
            tgl_input = st.date_input("Tanggal", date.today())
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

    # Main Content
    st.markdown("<h1 style='color: #0d9488;'>📊 Monitoring Keuangan</h1>", unsafe_allow_html=True)
    st.caption("Update Real-time • Tema Tosca")
    
    total_masuk = df_this_year[df_this_year['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_this_year.empty else 0
    total_keluar = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_this_year.empty else 0
    sisa_uang = total_masuk - total_keluar
    
    # Status Keuangan
    if total_masuk > 0:
        ratio = total_keluar / total_masuk
        if sisa_uang < 0: 
            st.error("🚨 **DARURAT!** Saldo Minus! Stop jajan dulu!")
        elif ratio > 0.8: 
            st.warning("⚠️ **Warning!** Pengeluaran > 80%. Rem dikit!")
        else: 
            st.success("✅ **Aman Terkendali.** Keuanganmu sehat.")
    else:
        st.info("ℹ️ Belum ada data pemasukan.")

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
            # CHART: Paksa Text Hitam biar kelihatan di background terang
            fig = px.pie(df_out, values='Nominal', names='Kategori', hole=0.6, color_discrete_sequence=px.colors.qualitative.Prism)
            fig.update_layout(
                showlegend=False, 
                margin=dict(t=0,b=0,l=0,r=0), 
                height=300, 
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=13) # TEKS HITAM
            )
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
        # Bar Background (Abu Tosca Muda)
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Batas_Anggaran'], orientation='h', name='Batas', marker_color='#cbd5e1'))
        
        # Bar Terpakai (Tosca vs Merah)
        colors = ['#0d9488' if p < 85 else '#ef4444' for p in df_mon['Persen']]
        fig_bar.add_trace(go.Bar(
            y=df_mon['Kategori'], x=df_mon['Terpakai'], orientation='h', name='Terpakai', 
            marker_color=colors, 
            text=df_mon['Persen'].apply(lambda x: f"{x:.1f}%"), 
            textposition='auto',
            textfont=dict(color="white") # Text di dalam bar Putih
        ))
        
        fig_bar.update_layout(
            barmode='overlay', 
            showlegend=False, 
            margin=dict(t=0,b=0,l=0,r=0), 
            height=350, 
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1e293b", size=12), # Label Sumbu HITAM
            xaxis=dict(gridcolor='#e2e8f0'),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    if st.button("🔄 Refresh Data"): st.rerun()

# --- HALAMAN 3: RIWAYAT ---
def show_history():
    st.markdown("<h1 style='color: #0d9488;'>📜 Riwayat Transaksi</h1>", unsafe_allow_html=True)
    if st.button("⬅️ Kembali ke Home"): navigate_to('home')
    st.markdown("---")
    
    if not df_transaksi.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1: filter_kat = st.multiselect("Filter Kategori", options=df_transaksi['Kategori'].unique())
        with col_f2: filter_tipe = st.selectbox("Filter Tipe", ["Semua", "Pengeluaran", "Pemasukan"])
        
        df_show = df_transaksi.copy()
        if filter_kat: df_show = df_show[df_show['Kategori'].isin(filter_kat)]
        if filter_tipe != "Semua": df_show = df_show[df_show['Tipe'] == filter_tipe]
        
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