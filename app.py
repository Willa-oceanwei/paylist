import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import os, json
import gspread
from google.oauth2.service_account import Credentials

# ===========================
# 頁面設定
# ===========================
st.set_page_config(
    page_title="收帳查詢系統（安全版）",
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

login_data[today_str]["count"] += 1
login_data[today_str]["times"].append(datetime.now(tz_taiwan).strftime("%H:%M:%S"))

with open(LOG_FILE, "w", encoding="utf-8") as f:
    json.dump(login_data, f, ensure_ascii=False, indent=2)

# 側邊欄登入資訊
st.sidebar.markdown(f"🕓 **今日登入次數：** {login_data[today_str]['count']}")
st.sidebar.markdown(f"🗓️ **最近登入時間：** {login_data[today_str]['times'][-1]}")

# ===========================
# Google Sheet 連線（Secrets）
# ===========================
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
gc = gspread.authorize(creds)
# 指定你的 Google Sheet URL
SHEET_URL = st.secrets["PAYLIST_SHEET_URL"]
sheet = gc.open_by_url(SHEET_URL).sheet1

# ===========================
# 系統標題
# ===========================
st.title("💰 收帳查詢系統（前四月 + 新增輸入）")

# ===========================
# 1️⃣ 新增資料表單
# ===========================
st.header("新增收帳資料")
with st.form("add_form"):
    input_date = st.date_input("日期", datetime.today())
    input_customer = st.text_input("客戶名稱")
    input_amount = st.number_input("金額", min_value=0.0)
    input_type = st.text_input("型式")
    input_staff = st.text_input("負責人員")
    input_month = st.text_input("帳款月份", value=datetime.today().strftime("%Y-%m"))
    input_note = st.text_input("備註")
    submitted = st.form_submit_button("儲存")
    
    if submitted:
        sheet.append_row([
            input_date.strftime("%Y-%m-%d"),
            input_customer,
            input_amount,
            input_type,
            input_staff,
            input_month,
            input_note
        ])
        st.success("✅ 已儲存資料到 Google Sheet！")

st.markdown("---")

# ===========================
# 2️⃣ 查詢資料
# ===========================
st.header("查詢近四個月資料")
today = datetime.today()
first_day_this_month = today.replace(day=1)
start_date = (first_day_this_month - pd.DateOffset(months=3)).date()

records = sheet.get_all_records()
df = pd.DataFrame(records)
if not df.empty:
    df['日期'] = pd.to_datetime(df['日期'])
    filtered = df[(df['日期'] >= start_date) & (df['日期'] <= today)]
    st.dataframe(filtered, use_container_width=True)
else:
    st.warning("⚠️ Google Sheet 尚無資料。")

st.markdown("---")

# ===========================
# 3️⃣ 現有 Paylist 查詢功能（保留舊版 CSV 查詢）
# ===========================
company_name = st.text_input("🔍 查詢 CSV 客戶名稱")
if company_name:
    DATA_FOLDER = "data"
    search_months = []
    # 計算近四個月的 ROC 月份
    today = datetime.today()
    roc_year = today.year - 1911
    roc_month = today.month
    current_roc = roc_year * 12 + roc_month
    for i in range(3, -1, -1):
        total = current_roc - i
        y = total // 12
        m = total % 12
        if m == 0:
            y -= 1
            m = 12
        search_months.append(f"{y:03d}{m:02d}")
    
    all_data = []
    for month in search_months:
        file_path = os.path.join(DATA_FOLDER, f"{month}.csv")
        if os.path.exists(file_path):
            try:
                df_csv = pd.read_csv(file_path, encoding="utf-8", dtype={"日期": str, "帳款月份": str})
                df_csv = df_csv.loc[:, ~df_csv.columns.str.contains("^Unnamed")]
                all_data.append(df_csv)
            except:
                continue
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        results = combined[combined["客戶名稱"].str.contains(company_name, case=False, na=False)]
        if not results.empty:
            st.success(f"✅ 找到 {len(results)} 筆資料")
            st.dataframe(results.reset_index(drop=True), use_container_width=True)
        else:
            st.warning("⚠️ 沒有找到該客戶近四個月資料。")
    else:
        st.warning("⚠️ 沒有可用 CSV 收帳資料。")

st.markdown("---")

# ===========================
# 4️⃣ 查看登入歷史紀錄
# ===========================
with st.expander("📜 查看登入歷史紀錄"):
    for d, info in sorted(login_data.items(), reverse=True):
        st.markdown(f"**{d}** — 共 {info['count']} 次： {', '.join(info['times'])}")
