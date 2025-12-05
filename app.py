import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# ========================
# GCP 認證
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# ========================
# 載入 Google Sheet 資料
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 將民國年月日轉 datetime
def parse_minguo_date(s):
    s = str(s).strip()
    if len(s) != 7 or not s.isdigit():
        return pd.NaT
    year = int(s[:3]) + 1911
    month = int(s[3:5])
    day = int(s[5:7])
    try:
        return datetime(year, month, day)
    except ValueError:
        return pd.NaT

df['日期_dt'] = df['日期'].apply(parse_minguo_date)

# ========================
st.markdown("<b style='font-size:24px'>🔍 查詢近四個月資料</b>", unsafe_allow_html=True)

# 搜尋欄位
search_customer = st.text_input("客戶名稱", value="")

# 計算日期範圍 (本月 + 前三個月)
today = datetime.today()
first_day_this_month = datetime(today.year, today.month, 1)
start_date = first_day_this_month - pd.DateOffset(months=3)
end_date = today

# 查詢資料
if st.button("搜尋"):
    filtered_df = df[
        df['日期_dt'].notna() &
        (df['日期_dt'] >= start_date) &
        (df['日期_dt'] <= end_date)
    ]
    if search_customer:
        filtered_df = filtered_df[filtered_df['客戶名稱'].str.contains(search_customer)]
    
    if filtered_df.empty:
        st.error("❌ 沒有符合條件的資料")
    else:
        st.dataframe(
            filtered_df[['日期','客戶名稱','金額','型式','負責人員','帳款月份','備註']],
            use_container_width=True
        )

# ========================
st.markdown("<b style='font-size:24px'>➕ 新增收帳資料</b>", unsafe_allow_html=True)

with st.form("add_payment_form"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_date = st.date_input("日期")
    with col2:
        new_customer = st.text_input("客戶名稱", value="")
    with col3:
        new_amount = st.text_input("金額")
    with col4:
        new_type = st.selectbox("型式", ["支票", "現金", "支票+現金"])
    
    col5, col6, col7 = st.columns(3)
    with col5:
        new_responsible = st.selectbox("負責人", ["德","Q","其他"])
    with col6:
        new_month = st.text_input("帳款月份")
    with col7:
        new_note = st.text_input("備註", value="", max_chars=100)
    
    submitted = st.form_submit_button("新增")
    if submitted:
        # 新增到 Google Sheet
        row = [
            f"{new_date.year-1911:03d}{new_date.month:02d}{new_date.day:02d}",  # 民國日期
            new_customer,
            new_amount,
            new_type,
            new_responsible,
            new_month,
            new_note
        ]
        sheet.append_row(row)
        st.success("✅ 新增成功！")
