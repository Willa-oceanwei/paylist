import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from pandas.tseries.offsets import DateOffset

# =======================
# Google Sheet 認證
# =======================
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

# =======================
# 開啟 Google Sheet
# =======================
SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# =======================
# 查詢近四個月資料
# =======================
st.header("查詢近四個月資料")
today = datetime.today()
start_date = (today.replace(day=1) - DateOffset(months=3)).date()

records = sheet.get_all_records()
df = pd.DataFrame(records)
if not df.empty:
    df['日期'] = pd.to_datetime(df['日期'])
    filtered = df[(df['日期'] >= pd.Timestamp(start_date)) & (df['日期'] <= pd.Timestamp(today))]
    st.dataframe(filtered)
else:
    st.info("目前沒有任何資料")

# =======================
# 新增收帳資料
# =======================
st.header("新增收帳資料")
with st.form("add_form"):
    # 上排四欄
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date = st.date_input("日期", datetime.today())
    with col2:
        customer = st.text_input("客戶名稱")
    with col3:
        amount = st.text_input("金額")  # 開放欄位
    with col4:
        type_ = st.selectbox("型式", ["支票", "現金", "支票+現金"])

    # 下排三欄
    col5, col6, col7 = st.columns([1,1,2])
    with col5:
        staff = st.text_input("負責人員")
    with col6:
        month = st.text_input("帳款月份", value=datetime.today().strftime("%Y-%m"))
    with col7:
        note = st.text_input("備註")  # 拉長欄位

    submitted = st.form_submit_button("儲存")
    
    if submitted:
        sheet.append_row([date.strftime("%Y-%m-%d"), customer, amount, type_, staff, month, note])
        st.success("已儲存資料！")
