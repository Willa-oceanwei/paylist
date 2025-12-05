import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import os

# ===========================
# 頁面設定
# ===========================
st.set_page_config(
    page_title="收帳查詢系統",
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
# Google Sheet 連線
# ===========================
SERVICE_ACCOUNT_INFO = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
gc = gspread.authorize(creds)
sheet = gc.open("收帳記錄").sheet1  # 改成你的 Sheet 名稱

# ===========================
# 系統標題
# ===========================
st.title("💰 收帳查詢系統（前四月）")

# ===========================
# 客戶名稱輸入
# ===========================
company_name = st.text_input("🔍 請輸入客戶名稱")
st.markdown("---")

# ===========================
# 上班時間判斷（台灣時間）
# ===========================
now_taiwan = datetime.now(tz_taiwan)
weekday = now_taiwan.weekday()  # 週一=0, 週日=6
hour = now_taiwan.hour
minute = now_taiwan.minute

is_weekday = weekday < 5
is_worktime = (8 <= hour < 17) or (hour == 17 and minute <= 30)

if not (is_weekday and is_worktime):
    st.error("⛔ 系統僅於【週一至週五 08:00～17:30】開放查詢。\n\n請於上班時間使用。")
    st.stop()

# ===========================
# 新增資料表單
# ===========================
st.header("📥 新增收帳資料")
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
today = datetime.today()
start_date = (today.replace(day=1) - pd.DateOffset(months=3)).date()

records = sheet.get_all_records()
df = pd.DataFrame(records)
if not df.empty and '日期' in df.columns:
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    if company_name:
        filtered = df[(df['日期'] >= start_date) & (df['日期'] <= today)]
        filtered = filtered[filtered["客戶名稱"].str.contains(company_name, case=False, na=False)]
    else:
        filtered = df[(df['日期'] >= start_date) & (df['日期'] <= today)]

    if not filtered.empty:
        filtered = filtered.reset_index(drop=True)
        filtered.index = [""] * len(filtered)
        st.dataframe(filtered, use_container_width=True)
        st.success(f"✅ 共 {len(filtered)} 筆資料")
    else:
        st.warning("⚠️ 沒有符合條件的資料")
else:
    st.warning("⚠️ 尚未有任何資料")

st.markdown("---")

# ===========================
# 查看登入歷史
# ===========================
with st.expander("📜 查看登入歷史紀錄"):
    for d, info in sorted(login_data.items(), reverse=True):
        st.markdown(f"**{d}** — 共 {info['count']} 次： {', '.join(info['times'])}")
