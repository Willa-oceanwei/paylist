import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

st.set_page_config(page_title="收帳查詢", layout="wide")

# ============================
# 工具：西元轉民國 yyyy/mm/dd
# ============================
def to_minguo_display(dt):
    try:
        d = pd.to_datetime(dt)
        return f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"
    except:
        return ""

def to_minguo_month(dt):
    d = pd.to_datetime(dt)
    return f"{d.year - 1911}/{d.month:02d}"

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

df["日期"] = df["日期"].apply(convert_roc_to_date)
df["日期"] = df["日期"].apply(to_minguo_display)

# ============================
# 標題
# ============================
st.title("💰 收帳查詢")
st.divider()

# ============================
# 🔍 查詢區：需要按按鈕才會搜尋
# ============================
# ========= 搜尋區 =========

st.subheader("🍭 收帳查詢")

# 1) 公司名稱
keyword = st.text_input("公司名稱（支援 Enter 搜尋）", key="keyword")

# 2) 搜尋按鈕
search_now = st.button("搜尋")

# 3) 控制是否顯示結果
if search_now:
    st.session_state["do_search"] = True
elif keyword == "":
    st.session_state["do_search"] = False

# 4) 只有在「按搜尋鍵」或「Enter 造成 keyword 更新後」才搜尋
if st.session_state.get("do_search", False):

    df_show = df.copy()

    # 安全轉民國日期
    def to_minguo(x):
        try:
            d = pd.to_datetime(x)
            return f"{d.year - 1911:03d}/{d.month:02d}/{d.day:02d}"
        except:
            return ""
        
    df_show["帳款日期"] = df_show["帳款日期"].apply(to_minguo)

    # 關鍵字搜尋
    df_show = df_show[df_show["公司名稱"].str.contains(keyword, na=False)]

    st.table(df_show)
# ============================
# 📋 搜尋結果
# ============================
if show_result and keyword:
    filtered = df[df["客戶名稱"].str.contains(keyword, case=False, na=False)]
    st.subheader("📋 查詢結果")
    st.table(filtered)
elif show_result:
    st.info("請輸入關鍵字再搜尋")

st.divider()

# ============================
# 🍯 新增收帳資料
# ============================
st.subheader("新增收帳資料")

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

# 下拉月份（動態民國年月）
today = date.today()
months = []
for i in range(4):
    d = pd.to_datetime(f"{today.year}-{today.month}-01") - pd.DateOffset(months=i)
    months.append(f"{d.year - 1911}/{d.month:02d}")

with col6:
    new_acct_month = st.selectbox("帳款月份 (民國)", months)

# 備註（長欄位）
new_note = st.text_area("備註（可留空）", "", max_chars=300, height=80)

# ============================
# 💾 儲存
# ============================
if st.button("新增資料"):
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
    except Exception as e:
        st.error(f"新增失敗：{e}")
