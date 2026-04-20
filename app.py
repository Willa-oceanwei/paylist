import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import os
os.environ["STREAMLIT_WATCH_RELOAD"] = "false"

st.set_page_config(page_title="收帳查詢", layout="wide")

# ============================
# 工具：西元轉民國 yyyy/mm/dd
# ============================
def to_minguo(x):
    try:
        x = str(x).strip()
        # 如果是民國數字格式，例如 1130105
        if len(x) == 7 and x.isdigit():
            year = int(x[:3]) + 1911
            month = int(x[3:5])
            day = int(x[5:7])
            d = pd.Timestamp(year, month, day)
        # 如果已經是民國斜線格式，例如 "113/01/05"
        elif "/" in x:
            parts = x.split("/")
            if len(parts) == 3:
                year = int(parts[0]) + 1911
                month = int(parts[1])
                day = int(parts[2])
                d = pd.Timestamp(year, month, day)
            else:
                d = pd.to_datetime(x)
        else:
            # 嘗試解析一般西元日期
            d = pd.to_datetime(x)
        return f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"
    except:
        return ""

# ============================
# Google Sheet 連線
# ============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["GCP_SERVICE_ACCOUNT_JSON"],
    scopes=SCOPES
)
client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs"
).sheet1

df = pd.DataFrame(sheet.get_all_records())

# 修正日期 — 原本是民國數字「1130105」等
def convert_roc_to_date(x):
    try:
        x = str(x)
        if len(x) == 7:  # 1130105
            y = int(x[:3]) + 1911
            m = int(x[3:5])
            d = int(x[5:7])
            return f"{y}-{m:02d}-{d:02d}"
        else:
            return x
    except:
        return x

# ============================
# 標題
# ============================
st.title("💰 收帳查詢")
st.divider()

# ============================
# 🔍 查詢區：僅顯示近四個月資料
# ============================
st.subheader("🍭 查詢區")

# 初始化 session state
if "do_search" not in st.session_state:
    st.session_state["do_search"] = False

# 公司名稱輸入
keyword = st.text_input("公司名稱（支援 Enter 搜尋）", key="keyword")

# 搜尋按鈕
search_now = st.button("搜尋")

# 控制搜尋狀態
if search_now or keyword:
    st.session_state["do_search"] = True
elif keyword == "":
    st.session_state["do_search"] = False

# ============================
# 執行搜尋
# ============================
if st.session_state.get("do_search", False) and keyword:

    df_show = df.copy()

    # -------- 1️⃣ 將民國日期轉為 datetime --------
    def parse_roc_to_datetime(x):
        try:
            x = str(x).strip()
            if len(x) == 7 and x.isdigit():  # 1130105
                year = int(x[:3]) + 1911
                month = int(x[3:5])
                day = int(x[5:7])
                return pd.Timestamp(year, month, day)
            else:
                return pd.to_datetime(x)
        except:
            return pd.NaT

    df_show["日期_dt"] = df_show["日期"].apply(parse_roc_to_datetime)

    # 移除無效日期
    df_show = df_show[df_show["日期_dt"].notna()]

    # -------- 2️⃣ 限制近四個月 --------
    today = pd.Timestamp.today().normalize()
    four_months_ago = today - pd.DateOffset(months=4)

    df_show = df_show[df_show["日期_dt"] >= four_months_ago]

    # -------- 3️⃣ 公司名稱關鍵字搜尋 --------
    df_show = df_show[
        df_show["客戶名稱"].str.contains(keyword, case=False, na=False)
    ]

    # -------- 4️⃣ 由近到遠排序（真正日期排序）--------
    df_show = df_show.sort_values(by="日期_dt", ascending=False)

    # -------- 5️⃣ 轉為民國顯示格式 --------
    def to_minguo_display(dt):
        return f"{dt.year - 1911}/{dt.month:02d}/{dt.day:02d}"

    df_show["日期"] = df_show["日期_dt"].apply(to_minguo_display)

    # 移除內部用欄位
    df_show = df_show.drop(columns=["日期_dt"])

    # -------- 6️⃣ 顯示 --------
    if df_show.empty:
        st.warning("❌ 近四個月內沒有符合的資料")
    else:
        st.success(f"找到 {len(df_show)} 筆資料（近四個月內）")
        st.table(df_show)

# ============================
#  新增收帳資料
# ============================
st.subheader("🍯 新增區")

with st.form("add_form"):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        new_date = st.date_input("日期")

    with col2:
        new_customer = st.text_input("客戶名稱")

    with col3:
        new_amount = st.number_input("金額", min_value=0)

    with col4:
        new_type = st.selectbox("型式", ["", "支票", "現金", "支票+現金"])

    col5, col6 = st.columns(2)

    with col5:
        new_person = st.selectbox("負責人", ["", "德", "Q", "其他"])

    today = date.today()
    months = []
    for i in range(4):
        d = pd.to_datetime(f"{today.year}-{today.month}-01") - pd.DateOffset(months=i)
        months.append(f"{d.year - 1911}/{d.month:02d}")

    with col6:
        new_acct_month = st.selectbox("帳款月份 (民國)", months)

    new_note = st.text_area("備註（可留空）", "", max_chars=300, height=80)

    submit = st.form_submit_button("新增資料")

if submit:

    new_row = [
        f"{new_date.year - 1911}{new_date.month:02d}{new_date.day:02d}",
        new_customer,
        int(new_amount),
        new_type,
        new_person,
        new_acct_month,
        new_note
    ]

    try:
        sheet.append_row(new_row)
        st.success("新增成功！")
        st.rerun()
    except Exception as e:
        st.error(f"新增失敗：{e}")
