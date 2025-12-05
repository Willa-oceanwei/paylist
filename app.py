import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from pandas.tseries.offsets import DateOffset

# =======================
# 1️⃣ Google Sheet 認證
# =======================
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES
)

gc = gspread.authorize(creds)

# =======================
# 2️⃣ 開啟 Google Sheet
# =======================
SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# =======================
# 3️⃣ 新增收帳資料
# =======================
st.header("新增收帳資料")
with st.form("add_form"):
    date = st.date_input("日期", datetime.today())
    customer = st.text_input("客戶名稱")
    amount = st.number_input("金額", min_value=0.0)
    type_ = st.text_input("型式")
    staff = st.text_input("負責人員")
    month = st.text_input("帳款月份", value=datetime.today().strftime("%Y-%m"))
    note = st.text_input("備註")
    submitted = st.form_submit_button("儲存")
    
    if submitted:
        sheet.append_row([date.strftime("%Y-%m-%d"), customer, amount, type_, staff, month, note])
        st.success("已儲存資料！")

# =======================
# 4️⃣ 查詢近四個月資料
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
