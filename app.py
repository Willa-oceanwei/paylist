import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

# ==================== Google Sheets 連線 ====================
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# ==================== 讀取資料 ====================
records = sheet.get_all_records()
df = pd.DataFrame(records)

# debug：確認欄位與前五筆資料
st.write("欄位名稱:", df.columns.tolist())
st.write(df.head(5))

# 去掉客戶名稱空格
if "客戶名稱" in df.columns:
    df['客戶名稱'] = df['客戶名稱'].astype(str).str.strip()

# 日期轉 datetime
if "日期" in df.columns:
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')

# ==================== Streamlit UI ====================
st.header("📊 收帳資料查詢")

col1, col2 = st.columns(2)
with col1:
    search_customer = st.text_input("客戶名稱搜尋")
with col2:
    start_date = st.date_input("開始日期", value=None)
    end_date = st.date_input("結束日期", value=None)

# ==================== 資料篩選 ====================
filtered = df.copy()

# 篩選客戶名稱
if search_customer:
    filtered = filtered[filtered['客戶名稱'].str.contains(search_customer, case=False, na=False)]

# 篩選日期
today = datetime.today()
if not start_date or not end_date:
    # 預設抓本月 + 前三個月
    first_day_of_month = today.replace(day=1)
    start_date = first_day_of_month - pd.DateOffset(months=3)
    end_date = today
filtered = filtered[(filtered['日期'] >= pd.to_datetime(start_date)) &
                    (filtered['日期'] <= pd.to_datetime(end_date))]

# ==================== 顯示結果 ====================
if filtered.empty:
    st.warning("❌ 沒有符合條件的資料")
    st.dataframe(df.head(5))  # debug 原始資料
else:
    st.success(f"✅ 找到 {len(filtered)} 筆符合條件的資料")
    st.dataframe(filtered.reset_index(drop=True))
