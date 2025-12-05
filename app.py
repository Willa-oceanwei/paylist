import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ====== Google Sheet 設定 ======
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
sheet = gc.open_by_url(SHEET_URL).sheet1

# ====== 讀取 Google Sheet ======
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 處理欄位
df['客戶名稱'] = df['客戶名稱'].astype(str).str.strip()

# 民國日期轉西元，只保留年月日
def convert_roc_to_datetime(roc_date):
    try:
        roc_date = str(int(roc_date))
        year = int(roc_date[:3]) + 1911
        month = int(roc_date[3:5])
        day = int(roc_date[5:7])
        return pd.Timestamp(year, month, day)
    except:
        return pd.NaT

df['日期'] = df['日期'].apply(convert_roc_to_datetime)

# 型式轉換
type_map = {'現': '現金', '支': '支票', '支票+現金': '支票+現金'}
df['型式'] = df['型式'].map(type_map).fillna(df['型式'])

# ====== Streamlit UI ======
st.title("💰收帳資料查詢與新增")

# ====== 查詢區 ======
with st.expander("🔍 查詢近四個月資料", expanded=True):
    col1, col2, col3 = st.columns([3,3,1])
    with col1:
        search_customer = st.text_input("輸入客戶名稱")
    with col2:
        date_range = st.date_input(
            "選擇日期區間 (可留空，自動抓本月+前三月)",
            value=[]
        )
    with col3:
        search_btn = st.button("搜尋")

    # 判斷觸發搜尋
    if search_customer or date_range or search_btn:
        filtered = df.copy()
        if search_customer:
            filtered = filtered[filtered['客戶名稱'].str.contains(search_customer, case=False, na=False)]

        if date_range:
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date = date_range
                end_date = date_range
        else:
            today = pd.Timestamp.today()
            start_date = (today - pd.DateOffset(months=3)).replace(day=1)
            end_date = today

        filtered = filtered[(filtered['日期'] >= start_date) & (filtered['日期'] <= end_date)]

        if not filtered.empty:
            # 日期只顯示年/月/日
            filtered_display = filtered.copy()
            filtered_display['日期'] = filtered_display['日期'].dt.strftime("%Y/%m/%d")

            # 顯示表格，不交錯底色
            st.dataframe(filtered_display, use_container_width=True)
        else:
            st.warning("❌ 沒有符合條件的資料")

# ====== 新增資料區 ======
# ====== 新增資料區 ======
with st.expander("📥 新增收帳資料", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_date = st.date_input("日期")
    with col2:
        new_customer = st.text_input("客戶名稱", value="")  # 預設空白
    with col3:
        new_amount = st.number_input("金額", min_value=0)
    with col4:
        # 型式預設空白
        new_type = st.selectbox("型式", [""] + ["支票", "現金", "支票+現金"])

    col5, col6, col7 = st.columns(3)
    with col5:
        # 負責人預設空白
        new_person = st.selectbox("負責人員", [""] + ["德", "Q", "其他"])
    with col6:
        new_month = st.text_input("帳款月份")
    with col7:
        new_note = st.text_input("備註", max_chars=200)

    if st.button("儲存新增資料"):
        new_row = [
            f"{new_date.year-1911}{new_date.month:02d}{new_date.day:02d}", # 民國日期
            new_customer,
            new_amount,
            new_type,
            new_person,
            new_month,
            new_note
        ]
        sheet.append_row(new_row)
        st.success("✅ 已新增資料！")

