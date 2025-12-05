import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ===== 假設 Google Sheet 讀進 df =====
# df = pd.read_csv("your_data.csv") 或 gspread 讀取

# ---------- 查詢區 ----------
st.markdown("<h2><b>🔍 查詢近四個月資料</b></h2>", unsafe_allow_html=True)

with st.expander("查詢條件", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        customer_input = st.text_input("客戶名稱")
    with col2:
        start_date = st.date_input("開始日期", value=datetime.today() - timedelta(days=120))
    with col3:
        end_date = st.date_input("結束日期", value=datetime.today())
    with col4:
        search_btn = st.button("搜尋")

# 初始不顯示表格
search_results = None

if search_btn:
    # 範例過濾邏輯（依實際 df 欄位修改）
    df_filtered = df.copy()
    
    if customer_input:
        df_filtered = df_filtered[df_filtered["客戶名稱"].str.contains(customer_input)]
    
    df_filtered["日期"] = pd.to_datetime(df_filtered["日期"].astype(str))
    df_filtered = df_filtered[
        (df_filtered["日期"] >= pd.to_datetime(start_date)) &
        (df_filtered["日期"] <= pd.to_datetime(end_date))
    ]
    
    if not df_filtered.empty:
        search_results = df_filtered
    else:
        st.error("❌ 沒有符合條件的資料")

# 顯示表格
if search_results is not None:
    st.dataframe(search_results.style.set_table_styles(
        [{'selector': 'tr:nth-of-type(odd)', 'props':[('background-color', '#f0f0f0')]}]
    ))

# ---------- 新增收帳資料區 ----------
st.markdown("<h3><b>➕ 新增收帳資料</b></h3>", unsafe_allow_html=True)

with st.expander("填寫資料", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        new_date = st.date_input("日期", value=datetime.today())
    with col2:
        new_customer = st.text_input("客戶名稱", value="")
    with col3:
        new_amount = st.text_input("金額")
    with col4:
        new_type = st.selectbox("型式", ["支票", "現金", "支票+現金"])
    
    col5, col6, col7 = st.columns([1,1,2])
    with col5:
        new_responsible = st.selectbox("負責人", ["德", "Q", "其他"])
    with col6:
        new_account_month = st.text_input("帳款月份")
    with col7:
        new_note = st.text_input("備註")
    
    add_btn = st.button("新增資料")
    
    if add_btn:
        # 範例新增邏輯
        new_row = {
            "日期": new_date.strftime("%Y-%m-%d"),
            "客戶名稱": new_customer,
            "金額": new_amount,
            "型式": new_type,
            "負責人": new_responsible,
            "帳款月份": new_account_month,
            "備註": new_note
        }
        # df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.success("✅ 新增成功")
