# ===============================
# app.py
# ===============================
import os
import json
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

st.write("Secret exists:", "GCP_SERVICE_ACCOUNT_JSON" in os.environ)

# -------------------------------
# Streamlit 頁面配置，必須最上面
# -------------------------------
st.set_page_config(
    page_title="收帳查詢系統",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# 時區設定
# -------------------------------
tz_taiwan = timezone(timedelta(hours=8))

# -------------------------------
# 登入紀錄
# -------------------------------
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
if today_str not in login_data:
    login_data[today_str] = {"count": 0, "times": []}
login_data[today_str]["count"] += 1
login_data[today_str]["times"].append(datetime.now(tz_taiwan).strftime("%H:%M:%S"))
with open(LOG_FILE, "w", encoding="utf-8") as f:
    json.dump(login_data, f, ensure_ascii=False, indent=2)

# 側邊欄顯示登入資訊
st.sidebar.markdown(f"🕓 **今日登入次數：** {login_data[today_str]['count']}")
st.sidebar.markdown(f"🗓️ **最近登入時間：** {login_data[today_str]['times'][-1]}")

# -------------------------------
# Streamlit 主標題
# -------------------------------
st.title("💰 收帳查詢系統（前四月）")
st.markdown("---")

# -------------------------------
# 上班時間判斷
# -------------------------------
now_taiwan = datetime.now(tz_taiwan)
weekday = now_taiwan.weekday()  # 週一=0
hour = now_taiwan.hour
minute = now_taiwan.minute

is_weekday = weekday < 5
is_worktime = (8 <= hour < 17) or (hour == 17 and minute <= 30)
if not (is_weekday and is_worktime):
    st.error("⛔ 系統僅於【週一至週五 08:00～17:30】開放查詢。\n請於上班時間使用。")
    st.stop()

# -------------------------------
# 客戶名稱輸入
# -------------------------------
company_name = st.text_input("🔍 請輸入客戶名稱")
st.markdown("---")

# -------------------------------
# Google Sheet 認證
# -------------------------------
service_account_info = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
gc = gspread.authorize(credentials)

SHEET_ID = "17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs"
worksheet = gc.open_by_key(SHEET_ID).sheet1

# -------------------------------
# 讀取 Sheet 成 DataFrame
# -------------------------------
def read_google_sheet_to_df():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    return df

# -------------------------------
# 查詢功能
# -------------------------------
if company_name:
    df = read_google_sheet_to_df()
    today = datetime.today()
    start_date = (today.replace(day=1) - timedelta(days=90)).replace(day=1)
    df_range = df[(df["日期"] >= start_date) & (df["日期"] <= today)]
    df_range = df_range[df_range["客戶名稱"].str.contains(company_name, case=False, na=False)]

    if not df_range.empty:
        st.success(f"✅ 找到 {len(df_range)} 筆資料")
        results_no_index = df_range.reset_index(drop=True)
        results_no_index.index = [""] * len(results_no_index)
        st.dataframe(results_no_index, use_container_width=True)
    else:
        st.warning("⚠️ 找不到該客戶近四個月的資料。")

st.markdown("---")

# -------------------------------
# 查看登入歷史
# -------------------------------
with st.expander("📜 查看登入歷史紀錄"):
    for d, info in sorted(login_data.items(), reverse=True):
        st.markdown(f"**{d}** — 共 {info['count']} 次： {', '.join(info['times'])}")

# -------------------------------
# 新增收帳記錄
# -------------------------------
st.subheader("➕ 新增收帳記錄")
with st.form("add_record"):
    col1, col2, col3 = st.columns(3)
    with col1:
        new_date = st.date_input("日期")
        new_customer = st.text_input("客戶名稱")
        new_amount = st.number_input("金額", min_value=0)
    with col2:
        new_type = st.text_input("型式")
        new_owner = st.text_input("負責人員")
    with col3:
        new_month = st.text_input("帳款月份")
        new_note = st.text_input("備註")
    submitted = st.form_submit_button("💾 新增資料")

if submitted:
    worksheet.append_row([
        new_date.strftime("%Y/%m/%d"),
        new_customer,
        new_amount,
        new_type,
        new_owner,
        new_month,
        new_note
    ])
    st.success("✅ 已成功新增一筆記錄！")

