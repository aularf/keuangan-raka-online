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

# --- CSS TEMA: PROFESSIONAL CLEAN (High Contrast) ---
st.markdown("""
    <style>
        /* BACKGROUND: Putih Abu Elegan */
        .stApp {
            background-color: #f8fafc;
            color: #0f172a; 
        }

        /* SIDEBAR: Biru Gelap Solid */
        [data-testid="stSidebar"] {
            background-color: #1e293b;
        }
        
        /* Teks di Sidebar jadi Putih/Terang */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {
            color: #f1f5f9 !important;
        }

        /* CARD METRIK: Putih Bersih + Shadow Lebih Tegas */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-left: 6px solid #2563eb;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }
        
        div[data-testid="stMetric"]:hover {
            box-shadow: 0 10px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
            transition: all 0.2s ease;
        }

        /* JUDUL ANGKA (Value) - Hitam Pekat */
        [data-testid="stMetricValue"] {
            font-size: 26px;
            font-weight: 800;
            color: #0f172a;
        }

        /* JUDUL LABEL (Keterangan) */
        [data-testid="stMetricLabel"] {
            font-size: 14px;
            color: #475569;
            font-weight: 600;
        }

        /* TOMBOL SIMPAN */
        .stButton > button {
            background-color: #3b82f6; /* Biru cerah */
            color: white;
            border: none;
            border-radius: 8px;
            height: 45px;
            width: 100%;
            font-weight: bold;
            letter-spacing: 0.5px;
        }
        .stButton > button:hover {
            background-color: #2563eb;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        }

        /* ALERT BOX BIAR KEREN */
        .stAlert {
            border-radius: 8px;
        }

        /* JUDUL HALAMAN */
        h1, h2, h3 {
            color: #0f172a !important;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 700;
        }
        
    </style>
""", unsafe_allow_html=True)

# --- 2. KONEKSI GOOGLE SHEETS (YANG SUDAH TERBUKTI SUKSES) ---
@st.cache_resource
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # CEK KONEKSI CLOUD (ST.SECRETS)
    if "gcp_service_account" in st.secrets:
        secrets_data = st.secrets["gcp_service_account"]
        # Logika: Kalau string di-decode, kalau dict langsung pakai
        if isinstance(secrets_data, str):
            creds_dict = json.loads(secrets_data)
        else:
            creds_dict = dict(secrets_data)

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    # CEK KONEKSI LOKAL (FILE JSON)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.load(open("credentials.json")), scope
        )
    
    client = gspread.authorize(creds)
    return client.open("MyMonetaryApp")

# --- MAIN LOGIC ---
try:
    sh = connect_to_sheet()
    ws_transaksi = sh.worksheet("Transaksi")
    ws_budget = sh.worksheet("Budget")
except Exception as e:
    st.error(f"❌ Koneksi Gagal: {e}")
    st.stop()

# --- OLAH DATA ---
data_transaksi = ws_transaksi.get_all_records()
df_transaksi = pd.DataFrame(data_transaksi)

if not df_transaksi.empty:
    df_transaksi['Nominal'] = pd.to_numeric(df_transaksi['Nominal'], errors='coerce').fillna(0)
    df_transaksi['Tanggal'] = pd.to_datetime(df_transaksi['Tanggal'], errors='coerce')

data_budget = ws_budget.get_all_records()
df_budget = pd.DataFrame(data_budget)
df_budget['Batas_Anggaran'] = pd.to_numeric(df_budget['Batas_Anggaran'], errors='coerce').fillna(0)

# --- SIDEBAR (DENGAN LOGO KEREN) ---
with st.sidebar:
    # Logo Dompet 3D
    st.image("https://cdn-icons-png.flaticon.com/512/9382/9382189.png", width=120)
    
    st.title("DOMPET RAKA")
    st.caption("Financial Command Center")
    st.markdown("---")
    
    with st.form(key='input_form', clear_on_submit=True):
        st.markdown("**📝 Input Transaksi Baru**")
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
        st.toast("Data Berhasil Disimpan!", icon="✅")
        st.rerun()

# --- DASHBOARD & HITUNGAN ---
now = datetime.now()
df_this_year = df_transaksi[df_transaksi['Tanggal'].dt.year == now.year] if not df_transaksi.empty else pd.DataFrame()

total_masuk = df_this_year[df_this_year['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_this_year.empty else 0
total_keluar = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_this_year.empty else 0
sisa_uang = total_masuk - total_keluar

total_budget_harian = df_budget[df_budget['Tipe_Budget'] == 'Harian']['Batas_Anggaran'].sum()
terpakai_harian = 0
if not df_this_year.empty:
    items_harian = df_budget[df_budget['Tipe_Budget'] == 'Harian']['Kategori'].tolist()
    terpakai_harian = df_this_year[
        (df_this_year['Tipe'] == 'Pengeluaran') & 
        (df_this_year['Kategori'].isin(items_harian)) &
        (df_this_year['Tanggal'].dt.month == now.month)
    ]['Nominal'].sum()

sisa_hari = max(1, calendar.monthrange(now.year, now.month)[1] - now.day + 1)
jatah_per_hari = max(0, (total_budget_harian - terpakai_harian) / sisa_hari)

# --- TAMPILAN HEADER ---
jam = datetime.now().hour
sapaan = "Selamat Pagi" if 5 <= jam < 12 else "Selamat Siang" if 12 <= jam < 18 else "Selamat Malam"

st.header(f"{sapaan}, Raka! 👋")
st.markdown("Berikut laporan keuangan kamu hari ini.")

# ROW 1: KARTU METRIK
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Saldo Bersih", f"{sisa_uang:,.0f}", delta="Cashflow")
col2.metric("📥 Total Pemasukan", f"{total_masuk:,.0f}", delta="YTD")
col3.metric("💸 Total Pengeluaran", f"{total_keluar:,.0f}", delta="-Terpakai", delta_color="inverse")
col4.metric("🔥 Jatah Jajan/Hari", f"{jatah_per_hari:,.0f}", delta=f"Sisa {sisa_hari} hari")

st.markdown("---")

# SIAPKAN DATA MONITORING (Untuk Grafik & Tabel)
df_monitor = df_budget.copy()
if not df_this_year.empty:
    pengeluaran_per_kat = df_this_year[df_this_year['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum()
    df_monitor['Terpakai'] = df_monitor['Kategori'].map(pengeluaran_per_kat).fillna(0)
else:
    df_monitor['Terpakai'] = 0

df_monitor['Sisa'] = df_monitor['Batas_Anggaran'] - df_monitor['Terpakai']
df_monitor['Persen'] = (df_monitor['Terpakai'] / df_monitor['Batas_Anggaran']).fillna(0) * 100

# FITUR: ALERT / PERINGATAN ⚠️
over_budget = df_monitor[df_monitor['Sisa'] < 0]
if not over_budget.empty:
    kategori_jebol = ", ".join(over_budget['Kategori'].tolist())
    st.error(f"🚨 PERHATIAN! Kategori ini sudah Over Budget (Minus): **{kategori_jebol}**. Rem sedikit ya!")
else:
    st.success("👍 Aman! Semua pengeluaran masih di bawah anggaran.")

# ROW 2: GRAFIK
col_grafik_kiri, col_grafik_kanan = st.columns([1, 2])

with col_grafik_kiri:
    st.subheader("🍩 Porsi Pengeluaran")
    df_pie = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']
    if not df_pie.empty:
        # Pie Chart dengan Warna Vivid & Teks Hitam
        fig_pie = px.pie(df_pie, values='Nominal', names='Kategori', hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Prism) # Warna Prism biar tegas
        fig_pie.update_layout(
            showlegend=False, 
            margin=dict(t=30, b=0, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#000000", size=14) 
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Belum ada data.")

with col_grafik_kanan:
    st.subheader("📊 Realisasi vs Budget")
    
    fig_bar = go.Figure()
    # Bar Background
    fig_bar.add_trace(go.Bar(
        y=df_monitor['Kategori'], x=df_monitor['Batas_Anggaran'],
        name='Batas Budget', orientation='h',
        marker=dict(color='#cbd5e1', line=dict(width=0))
    ))
    
    # Warna Bar Dinamis (Biru = Aman, Merah = Bahaya)
    colors = ['#2563eb' if p < 85 else '#ef4444' for p in df_monitor['Persen']]
    
    fig_bar.add_trace(go.Bar(
        y=df_monitor['Kategori'], x=df_monitor['Terpakai'],
        name='Terpakai', orientation='h',
        text=df_monitor['Persen'].apply(lambda x: f"{x:.1f}%"),
        textposition='auto',
        textfont=dict(color='white'), 
        marker=dict(color=colors) 
    ))
    
    fig_bar.update_layout(
        barmode='overlay', 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#000000", size=12), 
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(showgrid=True, gridcolor='#94a3b8'),
        yaxis=dict(showgrid=False),
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ROW 3: TABEL DETAIL & RIWAYAT (YANG HILANG KEMARIN)
st.markdown("### 📋 Detail Angka")
with st.container(border=True): 
    st.dataframe(
        df_monitor[['Kategori', 'Batas_Anggaran', 'Terpakai', 'Sisa', 'Persen']],
        column_config={
            "Batas_Anggaran": st.column_config.NumberColumn("Jatah Awal", format="Rp %d"),
            "Terpakai": st.column_config.NumberColumn("Terpakai", format="Rp %d"),
            "Sisa": st.column_config.NumberColumn("Sisa Dana", format="Rp %d"),
            "Persen": st.column_config.ProgressColumn("Status", format="%.1f%%", min_value=0, max_value=100),
        },
        use_container_width=True,
        hide_index=True
    )

# FITUR: LIHAT RIWAYAT TRANSAKSI 📜
st.markdown("---")
with st.expander("📜 Lihat Riwayat Transaksi Terakhir (Klik Disini)"):
    if not df_transaksi.empty:
        # Tampilkan data terbaru paling atas
        st.dataframe(
            df_transaksi.sort_values(by="Tanggal", ascending=False),
            use_container_width=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "Nominal": st.column_config.NumberColumn("Nominal", format="Rp %d")
            }
        )
    else:
        st.info("Belum ada transaksi.")