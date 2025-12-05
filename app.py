import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# =========================
# 頁面設定
# =========================
st.set_page_config(
    page_title="💰 收帳查詢系統",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# 連線 Google Sheet
# =========================
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
gc = gspread.authorize(creds)

# 直接用 Sheet URL，避免名稱錯誤
SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# =========================
# 新增收帳資料
# =========================
st.header("新增收帳資料")
with st.form("add_form"):
    date_input = st.date_input("日期", datetime.today())
    customer = st.text_input("客戶名稱")
    amount = st.number_input("金額", min_value=0.0)
    type_ = st.text_input("型式")
    staff = st.text_input("負責人員")
    month = st.text_input("帳款月份", value=datetime.today().strftime("%Y-%m"))
    note = st.text_input("備註")
    submitted = st.form_submit_button("儲存")

    if submitted:
        try:
            sheet.append_row([
                date_input.strftime("%Y-%m-%d"),
                customer,
                amount,
                type_,
                staff,
                month,
                note
            ])
            st.success("✅ 已儲存資料")
        except Exception as e:
            st.error(f"⚠️ 儲存失敗：{e}")

# =========================
# 查詢近四個月資料
# =========================
st.header("查詢近四個月資料")
today = datetime.today()
start_date = (today.replace(day=1) - relativedelta(months=3)).date()  # 當月 + 前三個月

try:
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'])
        filtered = df[(df['日期'] >= pd.Timestamp(start_date)) & (df['日期'] <= pd.Timestamp(today))]
        st.dataframe(filtered, use_container_width=True)
    else:
        st.info("目前 Google Sheet 尚無資料")
except Exception as e:
    st.error(f"⚠️ 查詢資料失敗：{e}")
