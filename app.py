import streamlit as st
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date
import calendar
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dompet Raka", page_icon="💎", layout="wide")

# --- CSS TEMA: CLEAN & MODERN ---
st.markdown("""
    <style>
        .stApp { background-color: #f8fafc; color: #0f172a; }
        [data-testid="stSidebar"] { background-color: #1e293b; }
        [data-testid="stSidebar"] * { color: #f1f5f9 !important; }
        div[data-testid="stMetric"] {
            background-color: white; border-left: 5px solid #3b82f6;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 8px;
        }
        [data-testid="stMetricValue"] { font-size: 24px; font-weight: 800; color: #0f172a; }
        .stButton > button { background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; }
        h1, h2, h3 { color: #0f172a !important; font-family: 'Segoe UI', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI KONEKSI SAKTI (ANTI ERROR) ---
@st.cache_resource
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Cek Apakah Jalan di Cloud (Secrets)
    if "gcp_service_account" in st.secrets:
        secret_value = st.secrets["gcp_service_account"]
        
        # Logika Pintar: Cek apakah dia Dictionary (TOML) atau String (JSON)
        if isinstance(secret_value, dict):
            # Jika formatnya sudah benar (TOML Table), langsung pakai!
            creds_dict = secret_value
        else:
            # Jika formatnya String (JSON yang dipaste), kita coba perbaiki manual
            try:
                creds_dict = json.loads(secret_value, strict=False)
            except json.JSONDecodeError:
                # Jurus perbaikan karakter enter (\n) yang sering error
                fixed_string = secret_value.replace('\n', '\\n')
                creds_dict = json.loads(fixed_string, strict=False)
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    # 2. Cek Apakah Jalan di Laptop (File JSON)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    
    client = gspread.authorize(creds)
    return client.open("MyMonetaryApp")

# --- MAIN APP LOGIC ---
try:
    sh = connect_to_sheet()
    ws_transaksi = sh.worksheet("Transaksi")
    ws_budget = sh.worksheet("Budget")
except Exception as e:
    st.error(f"❌ Gagal koneksi! Pesan Error: {e}")
    st.info("Tips: Cek format Secrets di Streamlit Cloud. Pastikan copy-paste JSON dengan benar.")
    st.stop() # BERHENTI DISINI KALAU ERROR, BIAR GAK CRASH KE BAWAH

# --- OLAH DATA ---
data_transaksi = ws_transaksi.get_all_records()
df_transaksi = pd.DataFrame(data_transaksi)

if not df_transaksi.empty:
    df_transaksi['Nominal'] = pd.to_numeric(df_transaksi['Nominal'], errors='coerce').fillna(0)
    df_transaksi['Tanggal'] = pd.to_datetime(df_transaksi['Tanggal'], errors='coerce')

data_budget = ws_budget.get_all_records()
df_budget = pd.DataFrame(data_budget)
df_budget['Batas_Anggaran'] = pd.to_numeric(df_budget['Batas_Anggaran'], errors='coerce').fillna(0)

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.title("DOMPET RAKA 💎")
    st.markdown("---")
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
        st.toast("✅ Data Tersimpan!", icon="🚀")
        st.rerun()

# --- DASHBOARD ---
now = datetime.now()
df_this_year = df_transaksi[df_transaksi['Tanggal'].dt.year == now.year] if not df_transaksi.empty else pd.DataFrame()

total_masuk = df_this_year[df_this_year['Tipe'] == 'Pemasukan']['Nominal'].sum() if not df_this_year.empty else 0
total_keluar = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']['Nominal'].sum() if not df_this_year.empty else 0
sisa_uang = total_masuk - total_keluar

# Hitung Jatah Harian
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

# TAMPILAN UTAMA
st.title(f"Selamat {'Pagi' if 5<=now.hour<12 else 'Siang' if 12<=now.hour<18 else 'Malam'}, Raka! 👋")

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Saldo Bersih", f"{sisa_uang:,.0f}")
c2.metric("📥 Pemasukan", f"{total_masuk:,.0f}")
c3.metric("💸 Pengeluaran", f"{total_keluar:,.0f}")
c4.metric("🔥 Jatah Jajan/Hari", f"{jatah_per_hari:,.0f}", f"Sisa {sisa_hari} hari")

st.markdown("---")

col_left, col_right = st.columns([1, 2])
with col_left:
    st.subheader("Porsi Pengeluaran")
    df_out = df_this_year[df_this_year['Tipe'] == 'Pengeluaran']
    if not df_out.empty:
        fig = px.pie(df_out, values='Nominal', names='Kategori', hole=0.5, color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), font=dict(color="black"))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data.")

with col_right:
    st.subheader("Monitoring Budget")
    df_mon = df_budget.copy()
    if not df_this_year.empty:
        used = df_this_year[df_this_year['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum()
        df_mon['Terpakai'] = df_mon['Kategori'].map(used).fillna(0)
    else:
        df_mon['Terpakai'] = 0
    df_mon['Persen'] = (df_mon['Terpakai'] / df_mon['Batas_Anggaran']).fillna(0) * 100
    
    st.dataframe(
        df_mon[['Kategori', 'Batas_Anggaran', 'Terpakai', 'Persen']],
        column_config={
            "Batas_Anggaran": st.column_config.NumberColumn("Jatah", format="Rp %d"),
            "Terpakai": st.column_config.NumberColumn("Habis", format="Rp %d"),
            "Persen": st.column_config.ProgressColumn("Status", format="%.1f%%", min_value=0, max_value=100),
        },
        use_container_width=True, hide_index=True
    )