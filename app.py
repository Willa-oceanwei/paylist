import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import os

os.environ["STREAMLIT_WATCH_RELOAD"] = "false"

st.set_page_config(page_title="收帳查詢", layout="wide")

# =========================
# Google Sheet 連線
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["GCP_SERVICE_ACCOUNT_JSON"],
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs"
).sheet1


# =========================
# 讀取資料（快取）
# =========================
@st.cache_data(ttl=60)
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()


# =========================
# 民國日期 → datetime
# =========================
def parse_roc(x):
    try:
        x = str(x)
        if len(x) == 7 and x.isdigit():
            y = int(x[:3]) + 1911
            m = int(x[3:5])
            d = int(x[5:7])
            return pd.Timestamp(y, m, d)
        return pd.to_datetime(x)
    except:
        return pd.NaT


# =========================
# datetime → 民國
# =========================
def to_minguo(dt):
    return f"{dt.year - 1911}/{dt.month:02d}/{dt.day:02d}"


# =========================
# 標題
# =========================
st.markdown(
    "<h2 style='margin-top:0px'>💰 收帳查詢系統</h2>",
    unsafe_allow_html=True
)

st.divider()


# =========================
# 🔍 查詢區
# =========================
st.subheader("🔍 收帳查詢")

keyword = st.text_input("公司名稱 (Enter 搜尋)", key="search_keyword")

if keyword:

    df_show = df.copy()

    df_show["日期_dt"] = df_show["日期"].apply(parse_roc)

    df_show = df_show[df_show["日期_dt"].notna()]

    # 限制近四個月
    today = pd.Timestamp.today().normalize()
    four_months_ago = today - pd.DateOffset(months=4)

    df_show = df_show[df_show["日期_dt"] >= four_months_ago]

    # 公司名稱搜尋
    df_show = df_show[
        df_show["客戶名稱"].str.contains(keyword, case=False, na=False)
    ]

    # 排序
    df_show = df_show.sort_values(by="日期_dt", ascending=False)

    # 顯示民國
    df_show["日期"] = df_show["日期_dt"].apply(to_minguo)

    df_show = df_show.drop(columns=["日期_dt"])

    if df_show.empty:

        st.warning("❌ 近四個月沒有資料")

    else:

        st.success(f"找到 {len(df_show)} 筆資料")

        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True
        )


# =========================
# 🍯 新增區
# =========================
st.subheader("🍯 新增收帳資料")

with st.form("add_form"):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        new_date = st.date_input("日期")

    with col2:
        new_customer = st.text_input("客戶名稱")

    with col3:
        new_amount = st.number_input("金額", min_value=0)

    with col4:
        new_type = st.selectbox(
            "型式",
            ["支票", "現金", "支票+現金"],
            index=None,
            placeholder="請選擇型式"
        )

    col5, col6 = st.columns(2)

    with col5:
        new_person = st.selectbox(
            "負責人",
            ["德", "Q", "其他"],
            index=None,
            placeholder="請選擇負責人"
        )

    # 帳款月份
    today = date.today()
    months = []

    for i in range(4):
        d = pd.to_datetime(f"{today.year}-{today.month}-01") - pd.DateOffset(months=i)
        months.append(f"{d.year - 1911}/{d.month:02d}")

    with col6:
        new_acct_month = st.selectbox("帳款月份", months)

    new_note = st.text_area("備註", "", height=80)

    submit = st.form_submit_button("新增資料")


# =========================
# 寫入資料
# =========================
if submit:

    if not new_customer:
        st.warning("請輸入客戶名稱")
        st.stop()

    if new_type is None:
        st.warning("請選擇型式")
        st.stop()

    if new_person is None:
        st.warning("請選擇負責人")
        st.stop()

    roc_date = f"{new_date.year - 1911}{new_date.month:02d}{new_date.day:02d}"

    new_row = [
        roc_date,
        new_customer,
        int(new_amount),
        new_type,
        new_person,
        new_acct_month,
        new_note
    ]

    try:

        sheet.append_row(
            new_row,
            value_input_option="USER_ENTERED"
        )

        st.toast("新增成功", icon="✅")

        st.cache_data.clear()

        st.rerun()

    except Exception as e:

        st.error(f"新增失敗：{e}")
