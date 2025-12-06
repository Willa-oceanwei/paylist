import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="收帳查詢", layout="wide")

# ==========================
# 🎯 民國日期轉換函式
# ==========================
def to_minguo(date_str):
    try:
        d = pd.to_datetime(date_str)
        return f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"
    except:
        return date_str

# ==========================
# 🎯 連線 Google Sheet
# ==========================
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
client = gspread.authorize(creds)
sheet = client.open("paylist").worksheet("工作表1")

# 讀取資料
df = pd.DataFrame(sheet.get_all_records())

# 日期欄位轉民國
if "日期" in df.columns:
    df["日期"] = df["日期"].apply(to_minguo)

# ==========================
# 🔰 標題
# ==========================
st.title("💰 收帳查詢")

st.divider()

# ==========================
# 🔍 查詢區域
# ==========================
st.subheader("查詢區域（公司名稱）")

col1, col2 = st.columns([2, 1])

with col1:
    keyword = st.text_input("公司名稱關鍵字", "")

# ==========================
# 🎯 帳款月份（近四月）下拉選單（民國）
# ==========================
def get_recent_4_months():
    today = datetime.today()
    result = []
    for i in range(4):
        d = today - pd.DateOffset(months=i)
        minguo_year = d.year - 1911
        result.append(f"{minguo_year}/{d.month:02d}")
    return result

months_list = get_recent_4_months()
selected_month = st.selectbox("帳款月份", months_list)

st.divider()

# ==========================
# 🔍 搜尋結果
# ==========================

filtered = df.copy()

if keyword:
    filtered = filtered[filtered["公司名稱"].str.contains(keyword, case=False, na=False)]

# 筆數不多 → 用 st.table(), 不要交錯底色
st.subheader("📋 查詢結果")
st.table(filtered)

st.divider()

# ==========================
# ➕ 新增資料區
# ==========================
st.subheader("新增收帳資料")

colA, colB, colC, colD = st.columns(4)

with colA:
    new_date = st.date_input("日期（自動民國）")

with colB:
    new_company = st.text_input("公司名稱")

with colC:
    new_amount = st.number_input("金額", min_value=0)

with colD:
    new_responsible = st.selectbox("負責人", ["", "德", "Q", "其他"])

# 帳款月份（民國格式）
new_month = f"{new_date.year - 1911}/{new_date.month:02d}"

if st.button("新增資料"):

    new_row = [
        f"{new_date.year - 1911}/{new_date.month:02d}/{new_date.day:02d}",
        new_company,
        int(new_amount),
        new_responsible,
        new_month,
    ]

    # ⚠️ 必須與 Google Sheet 表頭欄位一致
    try:
        sheet.append_row([str(x) for x in new_row])
        st.success("新增成功！")
    except Exception as e:
        st.error(f"新增失敗：{e}")
