import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from datetime import date
import pandas as pd

st.set_page_config(page_title="收帳查詢", layout="wide")

# ==========================
# 🎯 民國日期轉換
# ==========================
def to_minguo_display(dt):
    """西元 → 民國 yyyy/mm/dd"""
    try:
        d = pd.to_datetime(dt)
        return f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"
    except:
        return dt

def to_minguo_month(dt):
    d = pd.to_datetime(dt)
    return f"{d.year - 1911}/{d.month:02d}"

# ==========================
# 🎯 Google Sheet 連線
# ==========================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    st.secrets["GCP_SERVICE_ACCOUNT_JSON"],  # ← 使用你的 key
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs"
).sheet1

# 讀取資料
df = pd.DataFrame(sheet.get_all_records())

# 日期轉民國格式
if "日期" in df.columns:
    df["日期"] = df["日期"].apply(to_minguo_display)

# ==========================
# 🏷️ 標題
# ==========================
st.title("💰 收帳查詢")
st.divider()

# ==========================
# 🔍 查詢區（只查公司）
# ==========================
st.subheader("查詢資料")
keyword = st.text_input("輸入公司名稱關鍵字", "")

# 查詢結果
filtered = df.copy()
if keyword:
    filtered = filtered[filtered["客戶名稱"].str.contains(keyword, case=False, na=False)]

st.subheader("📋 查詢結果")
st.table(filtered)

st.divider()

# ==========================
# ➕ 新增資料
# ==========================
st.subheader("新增收帳資料")

col1, col2, col3, col4 = st.columns(4)

with col1:
    new_date = st.date_input("日期")

with col2:
    new_customer = st.text_input("客戶名稱")

with col3:
    new_amount = st.number_input("金額", min_value=0)

with col4:
    new_type = st.selectbox("型式", ["", "支票", "現金", "支票+現金"])

col5, col6 = st.columns(2)

with col5:
    new_person = st.selectbox("負責人", ["", "德", "Q", "其他"])

# ==========================
# 🗓️ 下拉月份（民國）
# ==========================
today = date.today()
months = []
for i in range(4):
    d = datetime(today.year, today.month, 1) - pd.DateOffset(months=i)
    months.append(f"{d.year - 1911}/{d.month:02d}")

with col6:
    new_acct_month = st.selectbox("帳款月份 (民國)", months)

# ==========================
# 💾 儲存
# ==========================
if st.button("新增資料"):

    row = [
        to_minguo_display(new_date),
        new_customer,
        int(new_amount),
        new_type,
        new_person,
        new_acct_month,
        ""
    ]

    try:
        sheet.append_row(row)
        st.success("新增成功！")
    except Exception as e:
        st.error(f"新增失敗：{e}")
