import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ====== Google Sheets 連線 ======
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)
SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# ====== 讀取資料 ======
records = sheet.get_all_records()
df = pd.DataFrame(records)

# 去除前後空格
df['客戶名稱'] = df['客戶名稱'].astype(str).str.strip()
df['日期'] = pd.to_datetime(df['日期'], errors='coerce')

# ====== 查詢區 ======
st.header("📊 收帳資料查詢")

col1, col2 = st.columns(2)
with col1:
    search_customer = st.text_input("客戶名稱", "").strip()
with col2:
    start_date = st.date_input("開始日期", value=None)
    end_date = st.date_input("結束日期", value=None)

# 預設日期區間：本月 + 前三個月
today = datetime.today()
if start_date is None or end_date is None:
    start_date = (today.replace(day=1) - relativedelta(months=3))
    end_date = today

# 篩選資料
filtered = df.copy()

# 客戶名稱篩選
if search_customer:
    filtered = filtered[filtered['客戶名稱'].str.contains(search_customer, case=False, na=False)]

# 日期篩選
filtered = filtered[
    (filtered['日期'] >= pd.to_datetime(start_date)) &
    (filtered['日期'] <= pd.to_datetime(end_date))
]

st.write("篩選結果:")
if filtered.empty:
    st.warning("❌ 沒有符合條件的資料")
else:
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)

# ====== 新增收帳資料區 ======
st.header("➕ 新增收帳資料")

with st.form("add_payment_form"):
    # 上方四欄
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_date = st.date_input("日期", value=today)
    with col2:
        new_customer = st.text_input("客戶名稱")
    with col3:
        new_amount = st.text_input("金額")  # 開放文字輸入
    with col4:
        new_type = st.selectbox("型式", ["支票", "現金", "支票+現金"])

    # 下方三欄
    col5, col6, col7 = st.columns([1,1,2])
    with col5:
        new_person = st.text_input("負責人員")
    with col6:
        new_month = st.text_input("帳款月份 (YYYY-MM)")
    with col7:
        new_note = st.text_area("備註", height=50)

    submitted = st.form_submit_button("新增收帳資料")
    if submitted:
        new_row = [
            new_date.strftime("%Y-%m-%d"),
            new_customer.strip(),
            new_amount.strip(),
            new_type,
            new_person.strip(),
            new_month.strip(),
            new_note.strip()
        ]
        sheet.append_row(new_row)
        st.success("✅ 新增成功！")
