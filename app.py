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

# --- CSS TEMA: SOFT MOBILE APP UI (Mirip Referensi Biru Kamu) ---
st.markdown("""
    <style>
        /* BACKGROUND: Abu-abu muda bersih (Biar kartu putihnya "pop-up") */
        [data-testid="stAppViewContainer"] {
            background-color: #F1F5F9;
            font-family: 'Helvetica', sans-serif;
        }

        /* HEADER SIDEBAR: Biru Tosca Gelap */
        [data-testid="stSidebar"] {
            background-color: #0F172A;
        }
        [data-testid="stSidebar"] * { color: #F8FAFC !important; }

        /* KARTU PUTIH (Card Style) */
        div[data-testid="stMetric"], div.stButton, div[data-testid="stForm"] {
            background-color: #FFFFFF;
            border-radius: 20px; /* Sudut Bulat Banget */
            padding: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02); /* Bayangan Halus */
            border: 1px solid #E2E8F0;
        }

        /* METRIC VALUE (Angka Duit) */
        [data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: 800;
            color: #0EA5E9; /* Warna Biru Laut */
        }
        [data-testid="stMetricLabel"] { font-size: 14px; font-weight: 600; color: #64748B; }

        /* TOMBOL UTAMA (Gaya Tombol Ungu di Referensi) */
        div.stButton > button {
            background: linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%); /* Gradasi Ungu */
            color: white;
            border: none;
            border-radius: 15px;
            height: 50px;
            font-weight: bold;
            box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
            width: 100%;
            transition: transform 0.2s;
        }
        div.stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 15px rgba(99, 102, 241, 0.5);
            color: white;
        }

        /* TOMBOL SEKUNDER (Outline) */
        div.stButton > button[kind="secondary"] {
            background: white;
            color: #6366F1;
            border: 2px solid #6366F1;
        }

        /* CUSTOM HEADER BOX (Biru di atas) */
        .header-box {
            background: linear-gradient(90deg, #0EA5E9 0%, #2563EB 100%);
            padding: 30px;
            border-radius: 20px;
            color: white;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(14, 165, 233, 0.3);
        }
        .header-box h1 { color: white !important; margin: 0; font-size: 2.5rem; }
        .header-box p { color: #E0F2FE !important; font-size: 1.1rem; }

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

    # Header Biru Besar (Pakai HTML biasa biar aman dari zoom)
    st.markdown(f"""
        <div class="header-box">
            <h1>{greeting}, Raka! {icon}</h1>
            <p>Siap mengatur cuan biar makin sultan?</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Menu Pilihan (Pakai Native Columns biar Responsif)
    st.write("### 🚀 Pilih Menu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Kartu Putih Menu 1
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>📝</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center;'>Input & Dashboard</h4>", unsafe_allow_html=True)
            st.write("Catat transaksi baru dan lihat grafik analisa keuanganmu.")
            if st.button("Buka Dashboard", key="btn_dash", use_container_width=True):
                navigate_to('dashboard')

    with col2:
        # Kartu Putih Menu 2
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>📜</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center;'>Riwayat Lengkap</h4>", unsafe_allow_html=True)
            st.write("Cek daftar semua pemasukan dan pengeluaran yang lalu.")
            if st.button("Lihat Riwayat", key="btn_hist", use_container_width=True):
                navigate_to('history')

# --- HALAMAN 2: DASHBOARD ---
def show_dashboard():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/9382/9382189.png", width=80)
        st.title("Input Baru")
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

    # Header Dashboard
    st.title("📊 Monitoring Keuangan")
    st.caption("Update Real-time dari Google Sheets")
    
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

    # 3 Kolom Metrik
    c1, c2, c3 = st.columns(3)
    c1.metric("Sisa Saldo", f"Rp {sisa_uang:,.0f}", delta="Cashflow")
    c2.metric("Pemasukan", f"Rp {total_masuk:,.0f}")
    c3.metric("Pengeluaran", f"Rp {total_keluar:,.0f}", delta="-Terpakai", delta_color="inverse")

    st.markdown("---")

    # Grafik
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("🍩 Porsi Jajan")
        df_out = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']
        if not df_out.empty:
            fig = px.pie(df_out, values='Nominal', names='Kategori', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=300, paper_bgcolor="rgba(0,0,0,0)")
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
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Batas_Anggaran'], orientation='h', name='Batas', marker_color='#E2E8F0'))
        colors = ['#6366F1' if p < 85 else '#EF4444' for p in df_mon['Persen']]
        fig_bar.add_trace(go.Bar(y=df_mon['Kategori'], x=df_mon['Terpakai'], orientation='h', name='Terpakai', marker_color=colors, text=df_mon['Persen'].apply(lambda x: f"{x:.1f}%"), textposition='auto'))
        fig_bar.update_layout(barmode='overlay', showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    if st.button("🔄 Refresh"): st.rerun()

# --- HALAMAN 3: RIWAYAT ---
def show_history():
    st.title("📜 Riwayat Transaksi")
    if st.button("⬅️ Kembali ke Home"): navigate_to('home')
    st.markdown("---")
    
    if not df_transaksi.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1: filter_kat = st.multiselect("Filter Kategori", options=df_transaksi['Kategori'].unique())
        with col_f2: filter_tipe = st.selectbox("Filter Tipe", ["Semua", "Pengeluaran", "Pemasukan"])
        
        df_show = df_transaksi.copy()
        if filter_kat: df_show = df_show[df_show['Kategori'].isin(filter_kat)]
        if filter_tipe != "Semua": df_show = df_show[df_show['Tipe'] == filter_tipe]
        
        st.dataframe(df_show.sort_values(by='Tanggal', ascending=False), use_container_width=True, hide_index=True)
    else: st.info("Belum ada data.")

# --- ROUTER ---
if st.session_state['page'] == 'home': show_home()
elif st.session_state['page'] == 'dashboard': show_dashboard()
elif st.session_state['page'] == 'history': show_history()