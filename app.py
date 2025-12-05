import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import json, os

# ===========================
# 頁面設定
# ===========================
st.set_page_config(
    page_title="💰 收帳查詢系統（安全版）",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================
# 登入紀錄功能
# ===========================
LOG_FILE = "login_log.json"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

with open(LOG_FILE, "r", encoding="utf-8") as f:
    try:
        login_data = json.load(f)
    except json.JSONDecodeError:
        login_data = {}

today_str = date.today().isoformat()
tz_taiwan = timezone(timedelta(hours=8))

if today_str not in login_data:
    login_data[today_str] = {"count": 0, "times": []}

# 紀錄今日登入（台灣時間）
login_data[today_str]["count"] += 1
login_data[today_str]["times"].append(datetime.now(tz_taiwan).strftime("%H:%M:%S"))

with open(LOG_FILE, "w", encoding="utf-8") as f:
    json.dump(login_data, f, ensure_ascii=False, indent=2)

# 側邊欄顯示登入資訊
st.sidebar.markdown(f"🕓 **今日登入次數：** {login_data[today_str]['count']}")
st.sidebar.markdown(f"🗓️ **最近登入時間：** {login_data[today_str]['times'][-1]}")

# ===========================
# Google Sheet 安全連線
# ===========================
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
gc = gspread.authorize(creds)

# TODO: 替換成你的 Google Sheet 網址
SHEET_URL = "你的Google Sheet網址"
sheet = gc.open_by_url(SHEET_URL).sheet1

# ===========================
# 系統標題
# ===========================
st.title("💰 收帳查詢系統（安全版）")

# ===========================
# 新增收帳資料區
# ===========================
st.header("📌 新增收帳資料")
with st.form("add_form"):
    date_input = st.date_input("日期", datetime.today())
    customer_input = st.text_input("客戶名稱")
    amount_input = st.number_input("金額", min_value=0.0)
    type_input = st.text_input("型式")
    staff_input = st.text_input("負責人員")
    month_input = st.text_input("帳款月份", value=datetime.today().strftime("%Y-%m"))
    note_input = st.text_input("備註")
    submitted = st.form_submit_button("儲存")
    
    if submitted:
        sheet.append_row([
            date_input.strftime("%Y-%m-%d"),
            customer_input,
            amount_input,
            type_input,
            staff_input,
            month_input,
            note_input
        ])
        st.success("✅ 已儲存資料")

st.markdown("---")

# ===========================
# 查詢近四個月資料
# ===========================
st.header("🔍 查詢近四個月資料")
company_name = st.text_input("🔎 請輸入客戶名稱查詢", "")

# 判斷當前時間是否在工作時間
now_taiwan = datetime.now(tz_taiwan)
weekday = now_taiwan.weekday()
hour = now_taiwan.hour
minute = now_taiwan.minute
is_weekday = weekday < 5
is_worktime = (8 <= hour < 17) or (hour == 17 and minute <= 30)

if not (is_weekday and is_worktime):
    st.error("⛔ 系統僅於【週一至週五 08:00～17:30】開放查詢。")
    st.stop()

if company_name:
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty and "日期" in df.columns:
        df['日期'] = pd.to_datetime(df['日期'])
        start_date = (datetime.today().replace(day=1) - pd.DateOffset(months=3)).date()
        filtered = df[(df['日期'] >= start_date) & (df['日期'] <= datetime.today())]
        filtered = filtered[filtered["客戶名稱"].str.contains(company_name, case=False, na=False)]

        if not filtered.empty:
            st.success(f"✅ 找到 {len(filtered)} 筆資料")
            filtered_no_index = filtered.reset_index(drop=True)
            filtered_no_index.index = [""] * len(filtered_no_index)
            hide_index_style = """
            <style>
            .stDataFrame > div > div > div > div > div > div:nth-child(1) {
                max-width: 10px;
                min-width: 10px;
                width: 10px;
            }
            </style>
            """
            st.markdown(hide_index_style, unsafe_allow_html=True)
            st.dataframe(filtered_no_index, use_container_width=True)
        else:
            st.warning("⚠️ 找不到該客戶近四個月的資料。")
    else:
        st.warning("⚠️ 沒有可用的收帳資料。")

st.markdown("---")

# ===========================
# 查看登入歷史紀錄
# ===========================
with st.expander("📜 查看登入歷史紀錄"):
    for d, info in sorted(login_data.items(), reverse=True):
        st.markdown(f"**{d}** — 共 {info['count']} 次： {', '.join(info['times'])}")
