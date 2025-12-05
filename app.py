import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# ===== Google Sheet 認證 =====
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# ===== 讀取資料 =====
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ===== 將民國日期轉成 datetime =====
def parse_minguo_date(s):
    s = str(s)
    year = int(s[:3]) + 1911
    month = int(s[3:5])
    day = int(s[5:7])
    return datetime(year, month, day)

df['日期_dt'] = df['日期'].apply(parse_minguo_date)

# ===== Streamlit 介面 =====
st.markdown("<b style='font-size:24px'>🔍 查詢近四個月資料</b>", unsafe_allow_html=True)

# 客戶名稱搜尋
search_customer = st.text_input("客戶名稱")

# 查詢近四個月日期區間
today = datetime.today()
start_date = (today.replace(day=1) - pd.DateOffset(months=3)).to_pydatetime()
end_date = today

# 初始不顯示資料，只有輸入才搜尋
if search_customer:
    filtered_df = df[
        (df['日期_dt'] >= start_date) &
        (df['日期_dt'] <= end_date) &
        (df['客戶名稱'].str.contains(search_customer))
    ]
    
    if not filtered_df.empty:
        # 格式化日期顯示
        filtered_df_display = filtered_df.copy()
        filtered_df_display['日期'] = filtered_df_display['日期_dt'].dt.strftime("%Y-%m-%d")
        st.dataframe(filtered_df_display.drop(columns=['日期_dt']), use_container_width=True)
    else:
        st.warning("❌ 沒有符合條件的資料")
