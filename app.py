import os
import re
import shutil
from datetime import datetime, time
import pandas as pd
import plotly.express as px
import streamlit as st

# ==============================================================================
# 1. KONFIGURASI HALAMAN UTAMA (WIDE LAYOUT & HUMAN-CRAFTED FLEET CONSOLE)
# ==============================================================================
st.set_page_config(
    page_title="Smart Logistics & Supply Chain Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Palet Warna Editorial Navy & Slate (Human-Crafted SaaS Palette)
NAVY_DEEP = "#0F172A"       # Oxford Slate Navy
NAVY_BRAND = "#1E3A8A"      # Executive Navy
COBALT_PRIMARY = "#2563EB"  # Royal Cobalt Blue
SKY_ACCENT = "#0EA5E9"      # Ocean Cyan
ROSE_ALERT = "#E11D48"      # Crimson Rose (Delayed)
TEAL_SUCCESS = "#0D9488"    # Emerald Teal

STATUS_COLOR_MAP = {
    "Delivered": "#1E3A8A",   # Executive Navy
    "In Transit": "#0EA5E9",  # Ocean Sky Blue
    "Delayed": "#E11D48",     # Crimson Rose
}

ORIGINAL_COLUMNS = [
    "Timestamp",
    "Asset_ID",
    "Latitude",
    "Longitude",
    "Inventory_Level",
    "Shipment_Status",
    "Temperature",
    "Humidity",
    "Traffic_Status",
    "Waiting_Time",
    "User_Transaction_Amount",
    "User_Purchase_Frequency",
    "Logistics_Delay_Reason",
    "Asset_Utilization",
    "Demand_Forecast",
    "Logistics_Delay",
]

GPS_PRESETS = {
    "Hub Tanjung Priok — Jakarta (-6.1045, 106.8806)": (-6.1045, 106.8806),
    "Hub Tanjung Perak — Surabaya (-7.2008, 112.7333)": (-7.2008, 112.7333),
    "Port of Singapore — Tuas (1.2644, 103.8405)": (1.2644, 103.8405),
    "Tokyo Bay Freight Hub (35.6197, 139.7798)": (35.6197, 139.7798),
    "Port of Rotterdam — Europort (51.9490, 4.1450)": (51.9490, 4.1450),
    "Sydney Port Botany (-33.9765, 151.2165)": (-33.9765, 151.2165),
    "Kustom (Isi Latitude & Longitude Manual di Bawah)": None,
}

# ==============================================================================
# 2. CUSTOM CSS (BESPOKE FLEET CONSOLE — PLUS JAKARTA SANS & JETBRAINS MONO)
# ==============================================================================
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        /* Dasar Kanvas & Tipografi Editorial */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: #F4F7FB;
            color: #0F172A;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            max-width: 96.5%;
        }

        /* Sidebar Bersih Bergaya Workspace Modern */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.25rem;
        }
        section[data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {
            background-color: #EFF6FF !important;
            color: #1E3A8A !important;
            border: 1px solid #BFDBFE !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            font-size: 0.76rem !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #F8FAFC !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            transition: all 0.18s ease;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {
            border-color: #94A3B8 !important;
        }

        /* Styling Semua Kartu Berbingkai st.container(border=True) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 1.15rem 1.25rem !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03), 0 4px 12px rgba(15, 23, 42, 0.02);
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #CBD5E1 !important;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
        }

        /* Menyulap st.metric Bawaan agar Menyatu di Dalam Kartu Kustom */
        div[data-testid="stMetric"] {
            background: transparent !important;
            border: none !important;
            padding: 0.15rem 0 0.25rem 0 !important;
            box-shadow: none !important;
        }
        div[data-testid="stMetricLabel"] > div {
            color: #64748B !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            letter-spacing: 0.01em;
        }
        div[data-testid="stMetricValue"] > div {
            color: #0F172A !important;
            font-weight: 700 !important;
            font-size: 1.85rem !important;
            letter-spacing: -0.025em;
            font-variant-numeric: tabular-nums;
            line-height: 1.2 !important;
        }
        div[data-testid="stMetricDelta"] > div {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.74rem !important;
            font-weight: 500 !important;
            font-variant-numeric: tabular-nums;
        }

        /* Top Workspace Bar */
        .workspace-topbar {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.15rem 1.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
        }
        .topbar-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .brand-icon-box {
            width: 44px;
            height: 44px;
            border-radius: 11px;
            background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #FFFFFF;
            flex-shrink: 0;
            box-shadow: 0 4px 10px rgba(30, 58, 138, 0.2);
        }
        .topbar-title {
            margin: 0;
            font-size: 1.32rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.02em;
            line-height: 1.25;
        }
        .topbar-subtitle {
            margin: 0.18rem 0 0 0;
            font-size: 0.84rem;
            color: #64748B;
            font-weight: 400;
        }
        .topbar-right {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            flex-wrap: wrap;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            color: #334155;
            padding: 0.4rem 0.8rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }
        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: #0D9488;
            box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.18);
        }

        /* Elemen Dekoratif Kartu KPI (Header Badge & Mini Progress Bar) */
        .kpi-header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.1rem;
        }
        .kpi-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #1E3A8A;
            background-color: #EFF6FF;
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
        }
        .kpi-icon-circle {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #1E3A8A;
        }
        .kpi-progress-track {
            width: 100%;
            height: 5px;
            background-color: #F1F5F9;
            border-radius: 999px;
            overflow: hidden;
            margin-top: 0.55rem;
        }
        .kpi-progress-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 0.4s ease;
        }

        /* Header Kartu Grafik & Peta */
        .card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.35rem;
        }
        .card-head-title {
            font-size: 0.98rem;
            font-weight: 700;
            color: #0F172A;
            margin: 0;
            letter-spacing: -0.01em;
        }
        .card-head-sub {
            font-size: 0.8rem;
            color: #64748B;
            margin: 0.15rem 0 0 0;
        }
        .card-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
            color: #334155;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 0.22rem 0.6rem;
            border-radius: 6px;
            white-space: nowrap;
        }

        /* Early Warning Operational Strip */
        .telemetry-alert-strip {
            background-color: #FFFFFF;
            border: 1px solid #FECDD3;
            border-radius: 12px;
            padding: 0.75rem 1.15rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.75rem;
            box-shadow: 0 1px 2px rgba(225, 29, 72, 0.04);
        }
        .alert-left {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.85rem;
            color: #334155;
        }
        .alert-badge-pill {
            background-color: #FFF1F2;
            color: #BE123C;
            border: 1px solid #FECDD3;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            white-space: nowrap;
        }

        /* Panel Telemetri Cuaca & Kargo di Samping Peta */
        .env-stat-item {
            padding: 0.75rem 0;
            border-bottom: 1px solid #F1F5F9;
        }
        .env-stat-item:last-child {
            border-bottom: none;
            padding-bottom: 0.2rem;
        }
        .env-stat-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.82rem;
            color: #475569;
            font-weight: 500;
            margin-bottom: 0.35rem;
        }
        .env-stat-val {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            font-size: 0.92rem;
            color: #0F172A;
        }

        /* Label Filter di Sidebar */
        .sidebar-filter-label {
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #475569;
            margin: 0.9rem 0 0.35rem 0;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        /* Styling Tabs (CRUD Workspace Tabs) */
        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            color: #475569 !important;
            padding: 0.6rem 1.1rem !important;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            color: #1E3A8A !important;
        }

        /* Tombol Download CSV */
        div[data-testid="stDownloadButton"] > button {
            background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 9px !important;
            padding: 0.55rem 1.15rem !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
            letter-spacing: 0.01em;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.14) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stDownloadButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 14px rgba(30, 58, 138, 0.24) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. FUNGSI PEMUATAN, PEMBERSIHAN & OPERASI CRUD CSV (ZERO DATA LOSS)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVE_CSV_PATH = os.path.join(BASE_DIR, "smart_logistics_dataset.csv")
MASTER_BACKUP_PATH = os.path.join(BASE_DIR, "archive", "smart_logistics_dataset.csv")


def ensure_active_csv_exists() -> str:
    """Memastikan file CSV utama tersedia di root; jika belum, salin dari archive/."""
    if os.path.exists(ACTIVE_CSV_PATH):
        return ACTIVE_CSV_PATH
    if os.path.exists(MASTER_BACKUP_PATH):
        shutil.copyfile(MASTER_BACKUP_PATH, ACTIVE_CSV_PATH)
        return ACTIVE_CSV_PATH
    return ""


def extract_truck_number(asset_id: str) -> int:
    """Mengekstrak nomor urut truk untuk pengurutan natural (Truck_1 s/d Truck_10)."""
    match = re.search(r"(\d+)", str(asset_id))
    return int(match.group(1)) if match else 999


@st.cache_data(show_spinner=False)
def load_and_clean_data(file_source) -> pd.DataFrame:
    """
    Memuat dataset CSV, mengonversi tipe data Timestamp, membersihkan nilai 'None'
    pada Logistics_Delay_Reason, menyiapkan koordinat lat/lon untuk st.map,
    dan menetapkan _row_id unik untuk operasi CRUD yang aman.
    """
    df = pd.read_csv(file_source)

    # 1. Konversi Timestamp ke tipe datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"]).copy()

    # 2. Bersihkan nilai 'None' / kosong pada Logistics_Delay_Reason menjadi NaN asli
    if "Logistics_Delay_Reason" in df.columns:
        df["Logistics_Delay_Reason"] = (
            df["Logistics_Delay_Reason"]
            .astype(str)
            .str.strip()
            .replace({"None": pd.NA, "nan": pd.NA, "NaN": pd.NA, "": pd.NA, "<NA>": pd.NA})
        )

    # 3. Pengurutan natural pada Asset_ID (Truck_1, Truck_2, ..., Truck_10)
    all_truck_labels = [f"Truck_{i}" for i in range(1, 11)]
    existing_trucks = sorted(df["Asset_ID"].dropna().unique(), key=extract_truck_number)
    categories = sorted(list(set(all_truck_labels + existing_trucks)), key=extract_truck_number)
    df["Asset_ID"] = pd.Categorical(df["Asset_ID"], categories=categories, ordered=True)

    # 4. Urutkan dari yang terbaru dan tetapkan _row_id unik untuk pelacakan CRUD
    df = df.sort_values("Timestamp", ascending=False).reset_index(drop=True)
    df["_row_id"] = df.index

    # 5. Kolom bantu waktu untuk filter dan tren bulanan
    df["Date"] = df["Timestamp"].dt.date
    df["YearMonth"] = df["Timestamp"].dt.to_period("M").astype(str)

    # 6. Penyesuaian nama kolom koordinat agar terbaca langsung oleh st.map
    df["lat"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["lon"] = pd.to_numeric(df["Longitude"], errors="coerce")

    return df


def save_master_dataframe(df_to_save: pd.DataFrame) -> None:
    """
    Menyimpan DataFrame kembali ke smart_logistics_dataset.csv secara utuh (16 kolom baku)
    dan langsung membersihkan cache memori agar perubahan terlihat seketika.
    """
    out = df_to_save[ORIGINAL_COLUMNS].copy()
    out["Timestamp"] = pd.to_datetime(out["Timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    out["Logistics_Delay_Reason"] = out["Logistics_Delay_Reason"].fillna("None").replace({"": "None", "<NA>": "None"})
    out.to_csv(ACTIVE_CSV_PATH, index=False)
    st.cache_data.clear()


# Tampilkan pesan sukses dari aksi CRUD sebelumnya (jika ada di session_state)
if "crud_flash_msg" in st.session_state:
    st.toast(st.session_state["crud_flash_msg"])
    del st.session_state["crud_flash_msg"]


# ==============================================================================
# 4. SIDEBAR FILTER INTERAKTIF & KONTROL DATABASE LATIHAN
# ==============================================================================
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:11px; padding-bottom:14px; border-bottom:1px solid #E2E8F0; margin-bottom:10px;">
            <div style="width:36px; height:36px; border-radius:9px; background:#0F172A; display:flex; align-items:center; justify-content:center; color:#38BDF8;">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                </svg>
            </div>
            <div>
                <div style="font-weight:700; font-size:0.95rem; color:#0F172A; letter-spacing:-0.01em;">Filter &amp; Kontrol Data</div>
                <div style="font-size:0.74rem; color:#64748B;">Parameter Pemantauan Armada</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Sumber Dataset CSV", expanded=False):
        uploaded_file = st.file_uploader(
            "Unggah file CSV eksternal",
            type=["csv"],
            help="Kosongkan untuk menggunakan database aktif smart_logistics_dataset.csv (mendukung CRUD penuh).",
        )

# Memuat dataset
default_csv_path = ensure_active_csv_exists()
is_using_local_db = uploaded_file is None and bool(default_csv_path)

if uploaded_file is not None:
    raw_df = load_and_clean_data(uploaded_file)
    active_source_label = f"Unggahan: {uploaded_file.name}"
elif default_csv_path:
    raw_df = load_and_clean_data(default_csv_path)
    active_source_label = f"DB Aktif: {os.path.basename(default_csv_path)} ({len(raw_df):,} baris)"
else:
    st.error(
        "File `smart_logistics_dataset.csv` tidak ditemukan. "
        "Silakan unggah file CSV melalui menu **Sumber Dataset CSV** di Sidebar kiri."
    )
    st.stop()

# Rentang Tanggal Min & Max
min_date = raw_df["Date"].min()
max_date = raw_df["Date"].max()

all_trucks = list(raw_df["Asset_ID"].cat.categories)
all_shipment_statuses = ["Delivered", "In Transit", "Delayed"]
all_traffic_statuses = ["Clear", "Heavy", "Detour"]

with st.sidebar:
    # Filter 1: Rentang Tanggal (Timestamp)
    st.markdown(
        '<div class="sidebar-filter-label">1. Rentang Waktu (Timestamp)</div>',
        unsafe_allow_html=True,
    )
    selected_date_range = st.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
    )

    # Filter 2: Pilihan Truk (Asset_ID)
    st.markdown(
        '<div class="sidebar-filter-label">2. Unit Armada (Asset_ID)</div>',
        unsafe_allow_html=True,
    )
    select_all_trucks = st.checkbox("Tampilkan Semua Armada (10 Unit)", value=True)
    if select_all_trucks:
        selected_trucks = st.multiselect(
            "Pilih ID Truk",
            options=all_trucks,
            default=all_trucks,
            label_visibility="collapsed",
        )
    else:
        selected_trucks = st.multiselect(
            "Pilih ID Truk",
            options=all_trucks,
            default=all_trucks[:4],
            label_visibility="collapsed",
        )

    # Filter 3: Status Pengiriman (Shipment_Status)
    st.markdown(
        '<div class="sidebar-filter-label">3. Status Pengiriman</div>',
        unsafe_allow_html=True,
    )
    selected_shipment_status = st.multiselect(
        "Pilih Status Pengiriman",
        options=all_shipment_statuses,
        default=all_shipment_statuses,
        label_visibility="collapsed",
    )

    # Filter 4: Kondisi Lalu Lintas (Traffic_Status)
    st.markdown(
        '<div class="sidebar-filter-label">4. Kondisi Lalu Lintas</div>',
        unsafe_allow_html=True,
    )
    selected_traffic_status = st.multiselect(
        "Pilih Kondisi Lalu Lintas",
        options=all_traffic_statuses,
        default=all_traffic_statuses,
        label_visibility="collapsed",
    )

    st.markdown("<hr style='margin:1.1rem 0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-filter-label" style="margin-top:0;">Pemeliharaan Database</div>',
        unsafe_allow_html=True,
    )
    if st.button("Segarkan Cache Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if is_using_local_db and os.path.exists(MASTER_BACKUP_PATH):
        if st.button(
            "Pulihkan Data Awal (1.000 Baris)",
            use_container_width=True,
            help="Mengembalikan isi smart_logistics_dataset.csv ke kondisi awal dari cadangan archive/smart_logistics_dataset.csv.",
        ):
            shutil.copyfile(MASTER_BACKUP_PATH, ACTIVE_CSV_PATH)
            st.cache_data.clear()
            st.session_state["crud_flash_msg"] = "Database berhasil dipulihkan ke 1.000 baris latihan awal!"
            st.rerun()

# Validasi input rentang tanggal (jika pengguna baru memilih 1 tanggal di kalender)
if isinstance(selected_date_range, (list, tuple)):
    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range[0], selected_date_range[1]
    elif len(selected_date_range) == 1:
        start_date = end_date = selected_date_range[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = selected_date_range

# Eksekusi Penyaringan Data
filtered_df = raw_df[
    (raw_df["Date"] >= start_date)
    & (raw_df["Date"] <= end_date)
    & (raw_df["Asset_ID"].isin(selected_trucks))
    & (raw_df["Shipment_Status"].isin(selected_shipment_status))
    & (raw_df["Traffic_Status"].isin(selected_traffic_status))
].copy()


# ==============================================================================
# 5. TOP WORKSPACE BAR & EARLY WARNING STRIP (BAGIAN ATAS)
# ==============================================================================
st.markdown(
    f"""
    <div class="workspace-topbar">
        <div class="topbar-left">
            <div class="brand-icon-box">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="1" y="3" width="15" height="13" rx="2"></rect>
                    <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
                    <circle cx="5.5" cy="18.5" r="2.5"></circle>
                    <circle cx="18.5" cy="18.5" r="2.5"></circle>
                </svg>
            </div>
            <div>
                <h1 class="topbar-title">Smart Logistics &amp; Supply Chain Monitoring Dashboard</h1>
                <p class="topbar-subtitle">Pusat Kendali Kinerja Pengiriman, Analitik Keterlambatan, dan Manajemen CRUD Armada</p>
            </div>
        </div>
        <div class="topbar-right">
            <span class="status-pill">
                <span class="status-dot"></span>
                {len(selected_trucks)}/{len(all_trucks)} Armada Aktif
            </span>
            <span class="status-pill">
                {start_date.strftime('%d %b %Y')} &ndash; {end_date.strftime('%d %b %Y')}
            </span>
            <span class="status-pill" style="background:#EFF6FF; color:#1E3A8A; border-color:#BFDBFE;">
                {active_source_label}
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Penanganan aman jika hasil filter kosong (0 baris)
if filtered_df.empty:
    st.warning(
        "Tidak ada data pengiriman yang cocok dengan kombinasi filter di Sidebar. "
        "Silakan perluas rentang tanggal atau pilih kembali status pengiriman/truk."
    )
    st.stop()

# Deteksi Dini Truk Bermasalah (Waiting Time > 45 menit atau Suhu > 28°C)
high_wait_count = int((filtered_df["Waiting_Time"] > 45).sum())
high_temp_count = int((filtered_df["Temperature"] > 28.0).sum())
if high_wait_count > 0 or high_temp_count > 0:
    st.markdown(
        f"""
        <div class="telemetry-alert-strip">
            <div class="alert-left">
                <span class="alert-badge-pill">PERINGATAN SLA</span>
                <span>
                    Terdeteksi <strong>{high_wait_count:,} pengiriman</strong> dengan waktu tunggu ekstrem (&gt;45 menit)
                    dan <strong>{high_temp_count:,} pengiriman</strong> dengan suhu ruang kargo &gt;28&deg;C pada filter aktif.
                </span>
            </div>
            <span style="font-size:0.78rem; color:#64748B; font-weight:500;">
                Gunakan Tabel Kerja CRUD di bagian bawah untuk memperbarui status truk terkait
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# 6. HIRARKI ATAS: 4 BESPOKE KPI CARDS (MENGGUNAKAN st.metric DI DALAM KARTU)
# ==============================================================================
total_shipments = len(filtered_df)
delayed_shipments = int((filtered_df["Shipment_Status"] == "Delayed").sum())
delay_rate = (delayed_shipments / total_shipments * 100) if total_shipments > 0 else 0.0
avg_waiting_time = filtered_df["Waiting_Time"].mean() if total_shipments > 0 else 0.0
avg_asset_utilization = filtered_df["Asset_Utilization"].mean() if total_shipments > 0 else 0.0

baseline_delay_rate = (raw_df["Shipment_Status"] == "Delayed").mean() * 100
baseline_wait = raw_df["Waiting_Time"].mean()
baseline_util = raw_df["Asset_Utilization"].mean()
volume_ratio = min(100.0, (total_shipments / len(raw_df)) * 100)

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    with st.container(border=True):
        st.markdown(
            """
            <div class="kpi-header-row">
                <span class="kpi-tag">VOLUME LOGISTIK</span>
                <div class="kpi-icon-circle">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                    </svg>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric(
            label="Total Pengiriman",
            value=f"{total_shipments:,}",
            delta=f"{volume_ratio:.1f}% dari total database",
            delta_color="off",
        )
        st.markdown(
            f"""
            <div class="kpi-progress-track">
                <div class="kpi-progress-fill" style="width:{volume_ratio:.1f}%; background:#1E3A8A;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with kpi_col2:
    with st.container(border=True):
        st.markdown(
            """
            <div class="kpi-header-row">
                <span class="kpi-tag" style="background:#FFF1F2; color:#BE123C;">RISIKO DELAY</span>
                <div class="kpi-icon-circle" style="color:#E11D48;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric(
            label="Tingkat Keterlambatan (Delay Rate)",
            value=f"{delay_rate:.1f}%",
            delta=f"{delay_rate - baseline_delay_rate:+.1f}% vs baseline ({delayed_shipments:,} unit)",
            delta_color="inverse",
        )
        st.markdown(
            f"""
            <div class="kpi-progress-track">
                <div class="kpi-progress-fill" style="width:{min(100.0, delay_rate):.1f}%; background:#E11D48;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with kpi_col3:
    with st.container(border=True):
        wait_pct = min(100.0, (avg_waiting_time / 60.0) * 100)
        st.markdown(
            """
            <div class="kpi-header-row">
                <span class="kpi-tag" style="background:#F0F9FF; color:#0369A1;">WAKTU TUNGGU</span>
                <div class="kpi-icon-circle" style="color:#0284C7;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric(
            label="Rata-rata Waktu Tunggu",
            value=f"{avg_waiting_time:.1f} Menit",
            delta=f"{avg_waiting_time - baseline_wait:+.1f} mnt vs rata-rata",
            delta_color="inverse",
        )
        st.markdown(
            f"""
            <div class="kpi-progress-track">
                <div class="kpi-progress-fill" style="width:{wait_pct:.1f}%; background:#0EA5E9;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with kpi_col4:
    with st.container(border=True):
        st.markdown(
            """
            <div class="kpi-header-row">
                <span class="kpi-tag" style="background:#F0FDFA; color:#0F766E;">EFISIENSI ARMADA</span>
                <div class="kpi-icon-circle" style="color:#0D9488;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                    </svg>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric(
            label="Rata-rata Utilisasi Aset",
            value=f"{avg_asset_utilization:.1f}%",
            delta=f"{avg_asset_utilization - baseline_util:+.1f}% vs rata-rata",
            delta_color="normal",
        )
        st.markdown(
            f"""
            <div class="kpi-progress-track">
                <div class="kpi-progress-fill" style="width:{min(100.0, avg_asset_utilization):.1f}%; background:#0D9488;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='margin-top:0.35rem;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 7. HIRARKI TENGAH: 4 GRAFIK ANALITIK DALAM KARTU BERBINGKAI (PLOTLY EXPRESS)
# ==============================================================================
def style_bespoke_plotly(fig, height: int = 330):
    """Menerapkan gaya grafik bersih ala produk SaaS modern."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155", size=12),
        margin=dict(l=12, r=16, t=14, b=16),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#1E293B",
            font=dict(family="Plus Jakarta Sans, sans-serif", size=12, color="#F8FAFC"),
        ),
    )
    return fig


chart_row1_col1, chart_row1_col2 = st.columns([1, 1.15])

# --- CHART 1 (DONUT CHART): Proporsi Status Pengiriman ---
with chart_row1_col1:
    with st.container(border=True):
        status_counts = (
            filtered_df["Shipment_Status"]
            .value_counts()
            .reindex(["Delivered", "In Transit", "Delayed"])
            .dropna()
            .reset_index()
        )
        status_counts.columns = ["Shipment_Status", "Jumlah"]
        delivered_cnt = int((filtered_df["Shipment_Status"] == "Delivered").sum())
        delivered_pct = (delivered_cnt / total_shipments * 100) if total_shipments > 0 else 0.0

        st.markdown(
            f"""
            <div class="card-head">
                <div>
                    <h3 class="card-head-title">Distribusi Status Pengiriman</h3>
                    <p class="card-head-sub">Proporsi pengiriman selesai, dalam perjalanan, dan tertunda</p>
                </div>
                <span class="card-badge">Delivered: {delivered_pct:.1f}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig_donut = px.pie(
            status_counts,
            names="Shipment_Status",
            values="Jumlah",
            hole=0.64,
            color="Shipment_Status",
            color_discrete_map=STATUS_COLOR_MAP,
        )
        fig_donut.update_traces(
            textposition="inside",
            textinfo="percent",
            insidetextfont=dict(color="#FFFFFF", size=12),
            marker=dict(line=dict(color="#FFFFFF", width=3)),
            hovertemplate="<b>%{label}</b><br>Volume: %{value:,} pengiriman<br>Porsi: %{percent}<extra></extra>",
        )
        fig_donut = style_bespoke_plotly(fig_donut, height=320)
        fig_donut.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.12,
                xanchor="center",
                x=0.5,
                font=dict(size=12, color="#0F172A"),
            ),
            annotations=[
                dict(
                    text=(
                        f"<b style='font-size:18px;color:#0F172A'>{total_shipments:,}</b>"
                        f"<br><span style='font-size:11px;color:#64748B'>Pengiriman</span>"
                    ),
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

# --- CHART 2 (BAR CHART): Penyebab Keterlambatan Terbanyak (Abaikan NaN/None) ---
with chart_row1_col2:
    with st.container(border=True):
        valid_reasons_df = filtered_df.dropna(subset=["Logistics_Delay_Reason"]).copy()
        top_reason_label = (
            valid_reasons_df["Logistics_Delay_Reason"].mode().iloc[0]
            if not valid_reasons_df.empty
            else "N/A"
        )

        st.markdown(
            f"""
            <div class="card-head">
                <div>
                    <h3 class="card-head-title">Akar Penyebab Keterlambatan (Delay Factors)</h3>
                    <p class="card-head-sub">Frekuensi kendala lapangan di luar pengiriman normal (tanpa nilai kosong)</p>
                </div>
                <span class="card-badge">Dominan: {top_reason_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not valid_reasons_df.empty:
            reason_counts = (
                valid_reasons_df["Logistics_Delay_Reason"]
                .value_counts()
                .reset_index()
            )
            reason_counts.columns = ["Logistics_Delay_Reason", "Jumlah_Kasus"]
            reason_counts = reason_counts.sort_values("Jumlah_Kasus", ascending=True)

            fig_reason = px.bar(
                reason_counts,
                x="Jumlah_Kasus",
                y="Logistics_Delay_Reason",
                orientation="h",
                text="Jumlah_Kasus",
                color="Logistics_Delay_Reason",
                color_discrete_sequence=["#38BDF8", "#2563EB", "#0F172A"],
            )
            fig_reason.update_traces(
                textposition="outside",
                cliponaxis=False,
                marker_cornerradius=6,
                hovertemplate="<b>%{y}</b><br>Tercatat: %{x:,} insiden<extra></extra>",
            )
            fig_reason = style_bespoke_plotly(fig_reason, height=320)
            fig_reason.update_layout(
                showlegend=False,
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#F1F5F9",
                    griddash="dot",
                    title="Jumlah Insiden Tercatat",
                    zeroline=False,
                ),
                yaxis=dict(showgrid=False, title=""),
            )
            st.plotly_chart(fig_reason, use_container_width=True)
        else:
            st.info("Tidak ada catatan alasan keterlambatan pada filter saat ini.")

chart_row2_col1, chart_row2_col2 = st.columns([1.15, 1])

# --- CHART 3 (GROUPED BAR CHART): Perbandingan Performa Tiap Truk ---
with chart_row2_col1:
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="card-head">
                <div>
                    <h3 class="card-head-title">Perbandingan Performa &amp; Beban Kerja Armada</h3>
                    <p class="card-head-sub">Distribusi status pengiriman untuk setiap unit truk (Truck_1 s/d Truck_10)</p>
                </div>
                <span class="card-badge">{len(selected_trucks)} Unit Ditampilkan</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        truck_perf = (
            filtered_df.groupby(["Asset_ID", "Shipment_Status"], observed=False)
            .size()
            .reset_index(name="Jumlah_Pengiriman")
        )
        truck_perf = truck_perf[truck_perf["Asset_ID"].isin(selected_trucks)]

        fig_truck = px.bar(
            truck_perf,
            x="Asset_ID",
            y="Jumlah_Pengiriman",
            color="Shipment_Status",
            barmode="group",
            color_discrete_map=STATUS_COLOR_MAP,
            category_orders={
                "Asset_ID": [t for t in all_trucks if t in selected_trucks],
                "Shipment_Status": ["Delivered", "In Transit", "Delayed"],
            },
        )
        fig_truck.update_traces(
            marker_cornerradius=4,
            hovertemplate="<b>%{x}</b> &bull; %{fullData.name}<br>Volume: %{y:,} pengiriman<extra></extra>",
        )
        fig_truck = style_bespoke_plotly(fig_truck, height=335)
        fig_truck.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.22,
                xanchor="center",
                x=0.5,
                title="",
            ),
            xaxis=dict(showgrid=False, title=""),
            yaxis=dict(
                showgrid=True,
                gridcolor="#F1F5F9",
                griddash="dot",
                title="Jumlah Pengiriman",
            ),
        )
        st.plotly_chart(fig_truck, use_container_width=True)

# --- CHART 4 (LINE CHART): Tren Waktu Tunggu Rata-rata per Bulan ---
with chart_row2_col2:
    with st.container(border=True):
        monthly_wait = (
            filtered_df.groupby("YearMonth", as_index=False)
            .agg(
                Rata_Rata_Waiting_Time=("Waiting_Time", "mean"),
                Total_Pengiriman=("Waiting_Time", "count"),
            )
            .sort_values("YearMonth")
        )
        monthly_wait["Bulan_Label"] = pd.to_datetime(monthly_wait["YearMonth"] + "-01").dt.strftime("%b %Y")
        peak_month_row = monthly_wait.loc[monthly_wait["Rata_Rata_Waiting_Time"].idxmax()]

        st.markdown(
            f"""
            <div class="card-head">
                <div>
                    <h3 class="card-head-title">Tren Waktu Tunggu Bulanan (Waiting Time)</h3>
                    <p class="card-head-sub">Rata-rata durasi antrean bongkar-muat armada (menit) sepanjang tahun</p>
                </div>
                <span class="card-badge">Puncak: {peak_month_row['Bulan_Label']} ({peak_month_row['Rata_Rata_Waiting_Time']:.1f}m)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig_trend = px.line(
            monthly_wait,
            x="Bulan_Label",
            y="Rata_Rata_Waiting_Time",
            markers=True,
        )
        fig_trend.update_traces(
            line=dict(color=COBALT_PRIMARY, width=3, shape="spline"),
            marker=dict(size=8, color=NAVY_DEEP, line=dict(width=2, color="#FFFFFF")),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.07)",
            hovertemplate="<b>%{x}</b><br>Rata-rata Waktu Tunggu: %{y:.1f} menit<extra></extra>",
        )
        fig_trend = style_bespoke_plotly(fig_trend, height=335)
        fig_trend.update_layout(
            xaxis=dict(showgrid=False, title=""),
            yaxis=dict(
                showgrid=True,
                gridcolor="#F1F5F9",
                griddash="dot",
                title="Durasi Tunggu (Menit)",
            ),
        )
        st.plotly_chart(fig_trend, use_container_width=True)


# ==============================================================================
# 8. HIRARKI BAWAH: PETA SEBARAN TRUK, TELEMETRI & WORKSPACE CRUD LENGKAP
# ==============================================================================
map_col, telemetry_col = st.columns([2.15, 1])

with map_col:
    with st.container(border=True):
        map_df = filtered_df.dropna(subset=["lat", "lon"])[
            ["lat", "lon", "Asset_ID", "Shipment_Status"]
        ].copy()
        st.markdown(
            f"""
            <div class="card-head" style="margin-bottom:0.65rem;">
                <div>
                    <h3 class="card-head-title">Peta Sebaran Titik Koordinat Armada</h3>
                    <p class="card-head-sub">Pemetaan GPS berdasarkan Latitude &amp; Longitude pengiriman aktif</p>
                </div>
                <span class="card-badge">{len(map_df):,} Titik GPS</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.map(
            map_df,
            latitude="lat",
            longitude="lon",
            color="#2563EB",
            size=42,
            use_container_width=True,
            height=360,
        )

with telemetry_col:
    with st.container(border=True):
        avg_temp = filtered_df["Temperature"].mean()
        avg_hum = filtered_df["Humidity"].mean()
        avg_inv = filtered_df["Inventory_Level"].mean()
        avg_demand = filtered_df["Demand_Forecast"].mean()
        dominant_traffic = (
            filtered_df["Traffic_Status"].mode().iloc[0]
            if not filtered_df["Traffic_Status"].empty
            else "-"
        )
        heavy_traffic_pct = (filtered_df["Traffic_Status"] == "Heavy").mean() * 100

        st.markdown(
            """
            <div class="card-head" style="margin-bottom:0.4rem;">
                <div>
                    <h3 class="card-head-title">Telemetri Kargo &amp; Rute</h3>
                    <p class="card-head-sub">Kondisi fisik muatan &amp; kepadatan jalur</p>
                </div>
                <span class="card-badge">Sensor Aktif</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="env-stat-item">
                <div class="env-stat-top">
                    <span>Rata-rata Suhu Kargo</span>
                    <span class="env-stat-val">{avg_temp:.1f} &deg;C</span>
                </div>
                <div class="kpi-progress-track">
                    <div class="kpi-progress-fill" style="width:{min(100.0, (avg_temp / 35.0) * 100):.1f}%; background:#0EA5E9;"></div>
                </div>
            </div>

            <div class="env-stat-item">
                <div class="env-stat-top">
                    <span>Rata-rata Kelembaban Udara</span>
                    <span class="env-stat-val">{avg_hum:.1f}%</span>
                </div>
                <div class="kpi-progress-track">
                    <div class="kpi-progress-fill" style="width:{min(100.0, avg_hum):.1f}%; background:#2563EB;"></div>
                </div>
            </div>

            <div class="env-stat-item">
                <div class="env-stat-top">
                    <span>Rata-rata Stok vs Prediksi Demand</span>
                    <span class="env-stat-val">{avg_inv:.0f} / {avg_demand:.0f} unit</span>
                </div>
                <div class="kpi-progress-track">
                    <div class="kpi-progress-fill" style="width:{min(100.0, (avg_inv / 500.0) * 100):.1f}%; background:#0D9488;"></div>
                </div>
            </div>

            <div class="env-stat-item">
                <div class="env-stat-top">
                    <span>Paparan Kemacetan Berat (Heavy Traffic)</span>
                    <span class="env-stat-val">{heavy_traffic_pct:.1f}% ({dominant_traffic})</span>
                </div>
                <div class="kpi-progress-track">
                    <div class="kpi-progress-fill" style="width:{min(100.0, heavy_traffic_pct):.1f}%; background:#E11D48;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# 9. PUSAT MANAJEMEN DATA OPERASIONAL (CRUD LENGKAP + EXPORT CSV)
# ==============================================================================
with st.container(border=True):
    st.markdown(
        f"""
        <div class="card-head" style="margin-bottom:0.25rem;">
            <div>
                <h3 class="card-head-title">Manajemen Data Operasional (CRUD) &amp; Eksportir Laporan CSV</h3>
                <p class="card-head-sub">
                    Kelola data pengiriman secara langsung: klik 2x pada sel tabel untuk <strong>Update</strong>, centang baris untuk <strong>Delete</strong>, atau buka tab <strong>Catat Pengiriman Baru (Create)</strong>.
                </p>
            </div>
            <span class="card-badge">{len(filtered_df):,} Baris Terfilter / {len(raw_df):,} Total</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_manage, tab_create = st.tabs(
        [
            "Tabel Kerja Interaktif (Edit, Hapus & Unduh CSV)",
            "+ Catat Pengiriman Baru (Create Data)",
        ]
    )

    # --------------------------------------------------------------------------
    # TAB 1: READ, UPDATE (INLINE EDIT), DELETE & EXPORT CSV
    # --------------------------------------------------------------------------
    with tab_manage:
        editor_df = filtered_df[["_row_id"] + ORIGINAL_COLUMNS].copy()
        editor_df.insert(0, "Hapus?", False)
        editor_df["Logistics_Delay_Reason"] = editor_df["Logistics_Delay_Reason"].fillna("None")

        edited_result = st.data_editor(
            editor_df,
            key="crud_table_editor",
            use_container_width=True,
            height=410,
            hide_index=True,
            disabled=["_row_id"],
            column_config={
                "Hapus?": st.column_config.CheckboxColumn(
                    "Hapus?",
                    help="Centang baris ini jika ingin menghapusnya dari database CSV.",
                    default=False,
                    width="small",
                ),
                "_row_id": None,  # Sembunyikan ID pelacak internal dari layar
                "Timestamp": st.column_config.DatetimeColumn(
                    "Waktu (Timestamp)",
                    format="YYYY-MM-DD HH:mm:ss",
                    required=True,
                ),
                "Asset_ID": st.column_config.SelectboxColumn(
                    "ID Armada",
                    options=[f"Truck_{i}" for i in range(1, 11)],
                    required=True,
                ),
                "Latitude": st.column_config.NumberColumn("Latitude", format="%.4f", min_value=-90.0, max_value=90.0),
                "Longitude": st.column_config.NumberColumn("Longitude", format="%.4f", min_value=-180.0, max_value=180.0),
                "Inventory_Level": st.column_config.NumberColumn("Stok Muatan", format="%d unit", min_value=0, max_value=2000),
                "Shipment_Status": st.column_config.SelectboxColumn(
                    "Status Pengiriman",
                    options=["Delivered", "In Transit", "Delayed"],
                    required=True,
                ),
                "Temperature": st.column_config.NumberColumn("Suhu Kargo", format="%.1f °C", min_value=-30.0, max_value=60.0),
                "Humidity": st.column_config.NumberColumn("Kelembaban", format="%.1f%%", min_value=0.0, max_value=100.0),
                "Traffic_Status": st.column_config.SelectboxColumn(
                    "Lalu Lintas",
                    options=["Clear", "Heavy", "Detour"],
                    required=True,
                ),
                "Waiting_Time": st.column_config.NumberColumn("Waktu Tunggu", format="%d mnt", min_value=0, max_value=600),
                "User_Transaction_Amount": st.column_config.NumberColumn("Nilai Transaksi", format="$%d", min_value=0),
                "User_Purchase_Frequency": st.column_config.NumberColumn("Frekuensi Beli", format="%d x", min_value=1, max_value=100),
                "Logistics_Delay_Reason": st.column_config.SelectboxColumn(
                    "Alasan Keterlambatan",
                    options=["None", "Weather", "Traffic", "Mechanical Failure"],
                    required=True,
                ),
                "Asset_Utilization": st.column_config.ProgressColumn(
                    "Utilisasi Aset (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Demand_Forecast": st.column_config.NumberColumn("Prediksi Demand", format="%d unit", min_value=0),
                "Logistics_Delay": st.column_config.NumberColumn("Flag Delay (0/1)", format="%d", min_value=0, max_value=1),
            },
        )

        selected_to_delete_ids = edited_result.loc[edited_result["Hapus?"] == True, "_row_id"].tolist()

        action_col1, action_col2, action_col3 = st.columns([1.3, 1.3, 1.4])

        with action_col1:
            if st.button(
                "Simpan Perubahan Edit ke CSV",
                type="primary",
                use_container_width=True,
                disabled=not is_using_local_db,
            ):
                master_copy = raw_df.set_index("_row_id")
                updated_rows = edited_result.set_index("_row_id")[ORIGINAL_COLUMNS].copy()

                # Sinkronkan otomatis flag Logistics_Delay jika status diubah menjadi Delayed
                updated_rows["Logistics_Delay"] = updated_rows.apply(
                    lambda r: 1 if str(r["Shipment_Status"]) == "Delayed" else int(r["Logistics_Delay"]),
                    axis=1,
                )

                master_copy.update(updated_rows)
                save_master_dataframe(master_copy.reset_index())
                st.session_state["crud_flash_msg"] = "Perubahan data pada tabel berhasil disimpan ke smart_logistics_dataset.csv!"
                st.rerun()

        with action_col2:
            delete_btn_label = (
                f"Hapus Baris Tercentang ({len(selected_to_delete_ids)} Baris)"
                if selected_to_delete_ids
                else "Hapus Baris Tercentang (0)"
            )
            if st.button(
                delete_btn_label,
                use_container_width=True,
                disabled=(not is_using_local_db) or (len(selected_to_delete_ids) == 0),
            ):
                remaining_df = raw_df[~raw_df["_row_id"].isin(selected_to_delete_ids)].copy()
                save_master_dataframe(remaining_df)
                st.session_state["crud_flash_msg"] = (
                    f"{len(selected_to_delete_ids)} baris pengiriman berhasil dihapus dari database CSV!"
                )
                st.rerun()

        with action_col3:
            export_clean_df = filtered_df[ORIGINAL_COLUMNS].copy()
            export_clean_df["Logistics_Delay_Reason"] = export_clean_df["Logistics_Delay_Reason"].fillna("None")
            csv_bytes = export_clean_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"Unduh Data Terfilter ({len(export_clean_df):,} Baris CSV)",
                data=csv_bytes,
                file_name=f"smart_logistics_filtered_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # --------------------------------------------------------------------------
    # TAB 2: CREATE (FORM INPUT PENGIRIMAN BARU)
    # --------------------------------------------------------------------------
    with tab_create:
        st.markdown(
            """
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:0.75rem 1rem; margin-bottom:1rem; font-size:0.83rem; color:#334155;">
                Isi formulir di bawah untuk mencatat pengiriman baru ke dalam <code>smart_logistics_dataset.csv</code>.
                Tanggal default disetel ke tanggal terakhir dataset agar data baru langsung masuk ke rentang filter Anda.
            </div>
            """,
            unsafe_allow_html=True,
        )

        preset_choice = st.selectbox(
            "Pilih Preset Titik Lokasi GPS (Atau Pilih Kustom untuk Input Koordinat Manual)",
            options=list(GPS_PRESETS.keys()),
            index=0,
        )
        preset_coords = GPS_PRESETS[preset_choice]
        default_lat = preset_coords[0] if preset_coords else -6.1045
        default_lon = preset_coords[1] if preset_coords else 106.8806

        with st.form("create_shipment_form", clear_on_submit=False):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)

            with f_col1:
                input_date = st.date_input("Tanggal Pengiriman", value=max_date)
                input_time = st.time_input("Jam Pengiriman", value=time(14, 30, 0))
                input_truck = st.selectbox(
                    "Pilih Unit Armada (Asset_ID)",
                    options=[f"Truck_{i}" for i in range(1, 11)],
                    index=0,
                )
                input_status = st.selectbox(
                    "Status Pengiriman (Shipment_Status)",
                    options=["In Transit", "Delivered", "Delayed"],
                    index=0,
                )

            with f_col2:
                input_traffic = st.selectbox(
                    "Kondisi Lalu Lintas (Traffic_Status)",
                    options=["Clear", "Heavy", "Detour"],
                    index=0,
                )
                input_reason = st.selectbox(
                    "Alasan Keterlambatan (Logistics_Delay_Reason)",
                    options=["None (Tidak Ada Kendala)", "Weather", "Traffic", "Mechanical Failure"],
                    index=0,
                )
                input_waiting = st.number_input(
                    "Waktu Tunggu / Waiting Time (Menit)",
                    min_value=0,
                    max_value=300,
                    value=25,
                    step=1,
                )
                input_util = st.slider(
                    "Utilisasi Aset / Asset Utilization (%)",
                    min_value=50.0,
                    max_value=100.0,
                    value=84.5,
                    step=0.5,
                )

            with f_col3:
                input_inventory = st.number_input(
                    "Jumlah Stok Barang (Inventory_Level)",
                    min_value=100,
                    max_value=500,
                    value=320,
                    step=10,
                )
                input_demand = st.number_input(
                    "Prediksi Permintaan (Demand_Forecast)",
                    min_value=100,
                    max_value=300,
                    value=240,
                    step=10,
                )
                input_temp = st.number_input(
                    "Suhu Kargo / Temperature (°C)",
                    min_value=18.0,
                    max_value=35.0,
                    value=24.0,
                    step=0.5,
                )
                input_hum = st.number_input(
                    "Kelembaban / Humidity (%)",
                    min_value=50.0,
                    max_value=85.0,
                    value=65.0,
                    step=0.5,
                )

            with f_col4:
                input_lat = st.number_input(
                    "Koordinat Latitude",
                    min_value=-90.0,
                    max_value=90.0,
                    value=float(default_lat),
                    format="%.4f",
                )
                input_lon = st.number_input(
                    "Koordinat Longitude",
                    min_value=-180.0,
                    max_value=180.0,
                    value=float(default_lon),
                    format="%.4f",
                )
                input_tx_amount = st.number_input(
                    "Nilai Transaksi (User_Transaction_Amount $)",
                    min_value=100,
                    max_value=1000,
                    value=350,
                    step=10,
                )
                input_tx_freq = st.number_input(
                    "Frekuensi Pembelian (User_Purchase_Frequency)",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1,
                )

            submitted_create = st.form_submit_button(
                "+ Simpan Pengiriman Baru ke Database CSV",
                type="primary",
                use_container_width=True,
                disabled=not is_using_local_db,
            )

            if submitted_create:
                clean_reason = "None" if input_reason.startswith("None") else input_reason
                computed_delay_flag = 1 if (input_status == "Delayed" or input_traffic == "Heavy") else 0
                combined_ts = datetime.combine(input_date, input_time).strftime("%Y-%m-%d %H:%M:%S")

                new_row_df = pd.DataFrame(
                    [
                        {
                            "Timestamp": combined_ts,
                            "Asset_ID": input_truck,
                            "Latitude": round(float(input_lat), 4),
                            "Longitude": round(float(input_lon), 4),
                            "Inventory_Level": int(input_inventory),
                            "Shipment_Status": input_status,
                            "Temperature": round(float(input_temp), 1),
                            "Humidity": round(float(input_hum), 1),
                            "Traffic_Status": input_traffic,
                            "Waiting_Time": int(input_waiting),
                            "User_Transaction_Amount": int(input_tx_amount),
                            "User_Purchase_Frequency": int(input_tx_freq),
                            "Logistics_Delay_Reason": clean_reason,
                            "Asset_Utilization": round(float(input_util), 1),
                            "Demand_Forecast": int(input_demand),
                            "Logistics_Delay": computed_delay_flag,
                        }
                    ]
                )

                updated_master_df = pd.concat([new_row_df, raw_df[ORIGINAL_COLUMNS]], ignore_index=True)
                save_master_dataframe(updated_master_df)
                st.session_state["crud_flash_msg"] = (
                    f"Pengiriman baru untuk {input_truck} ({input_status}) berhasil ditambahkan ke CSV!"
                )
                st.rerun()
