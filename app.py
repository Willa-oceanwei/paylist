import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ===== 產生民國日期 =====
def to_roc_date(dt):
    return f"{dt.year-1911:03d}/{dt.month:02d}/{dt.day:02d}"

def to_roc_month(dt):
    return f"{dt.year-1911:03d}/{dt.month:02d}"

def get_recent_4_months_roc():
    today = pd.Timestamp.today()
    months = []
    for i in range(4):
        m = today - pd.DateOffset(months=i)
        months.append(to_roc_month(m))
    return months


# ===== 查詢區 =====
with st.expander("🔍 查詢近四個月資料", expanded=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        search_customer = st.text_input("輸入客戶名稱")
    with col2:
        search_btn = st.button("搜尋")

    if search_customer or search_btn:
        filtered = df.copy()

        # 客戶搜尋
        filtered = filtered[
            filtered['客戶名稱'].str.contains(search_customer, case=False, na=False)
        ]

        # 自動取近四月（西元）
        today = pd.Timestamp.today()
        start_date = (today - pd.DateOffset(months=3)).replace(day=1)
        end_date = today

        filtered = filtered[
            (filtered['日期'] >= start_date) &
            (filtered['日期'] <= end_date)
        ]

        if not filtered.empty:
            show_df = filtered.copy()

            # ➜ 統一轉民國日期顯示
            show_df['日期'] = show_df['日期'].apply(to_roc_date)

            # 日期由新到舊排序
            show_df = show_df.sort_values(by='日期', ascending=False)

            st.table(show_df)
        else:
            st.warning("❌ 沒有符合條件的資料")


# ===== 新增資料區 =====
with st.expander("➕ 新增收帳資料", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_date = st.date_input("日期")

    with col2:
        new_customer = st.text_input("客戶名稱", value="")

    with col3:
        new_amount = st.number_input("金額", min_value=0)

    with col4:
        new_type = st.selectbox("型式", ["", "支票", "現金", "支票+現金"])

    col5, col6, col7 = st.columns(3)
    with col5:
        new_person = st.selectbox("負責人員", ["", "德", "Q", "其他"])

    with col6:
        # 帳款月份改用民國格式
        recent_months = get_recent_4_months_roc()
        new_month = st.selectbox("帳款月份", [""] + recent_months)

    with col7:
        new_note = st.text_input("備註", max_chars=200)

    if st.button("儲存新增資料"):
        # 民國日期寫入 Google Sheet（無斜線，維持原格式要求）
        roc_compact = f"{new_date.year-1911:03d}{new_date.month:02d}{new_date.day:02d}"

        new_row = [
            roc_compact,  # 民國日期 例如 1150105
            new_customer,
            new_amount,
            new_type,
            new_person,
            new_month,    # 民國月份 例如 115/01
            new_note
        ]
        sheet.append_row(new_row)
        st.success("✅ 已新增資料！")