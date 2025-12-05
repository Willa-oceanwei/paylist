import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# =========================
# 樣式設定
st.markdown(
    "<style>h2{font-size:24px; font-weight:bold;} .small-text{font-size:14px;}</style>",
    unsafe_allow_html=True
)

# =========================
# 模擬 Google Sheet 資料
data = [
    ["1140901", "亞詮", 194, "現", "德", "11407", ""],
    ["1140901", "唐美", 66770, "支", "德", "11407", "RA8701568"],
    ["1140902", "明慈", 137, "現", "德", "11407", ""]
]
columns = ["日期","客戶名稱","金額","型式","負責人","帳款月份","備註"]
df = pd.DataFrame(data, columns=columns)

# =========================
# 查詢區
st.markdown("<h2>🔍 查詢近四個月資料</h2>", unsafe_allow_html=True)

with st.expander("查詢條件", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_customer = st.text_input("客戶名稱", key="search_customer", placeholder="輸入客戶名稱")
    with col2:
        # 這裡可加其他查詢欄位，如金額範圍
        search_dummy1 = st.text_input("金額(範圍)", key="search_dummy1")
    with col3:
        search_dummy2 = st.text_input("型式", key="search_dummy2")
    with col4:
        search_dummy3 = st.text_input("負責人", key="search_dummy3")
    
    search_btn = st.button("搜尋", key="search_btn")

# =========================
# 顯示查詢結果
if search_btn:
    # 範例過濾
    filtered_df = df[df["客戶名稱"].str.contains(search_customer)] if search_customer else df
    if not filtered_df.empty:
        st.dataframe(filtered_df.style.set_properties(**{
            'background-color': '#f0f0f0',
            'color': 'black',
            'border-color': 'black'
        }).set_table_styles(
            [{'selector': 'tr:nth-child(even)', 'props': [('background-color', '#e6f2ff')]}]
        ), height=300)
    else:
        st.warning("❌ 沒有符合條件的資料")

# =========================
# 新增收帳資料區
st.markdown("<h2>➕ 新增收帳資料</h2>", unsafe_allow_html=True)

with st.expander("填寫資料", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_date = st.date_input("日期", key="add_date")
    with col2:
        new_customer = st.text_input("客戶名稱", value="", key="add_customer")
    with col3:
        new_amount = st.text_input("金額", key="add_amount")
    with col4:
        new_type = st.selectbox("型式", ["支票", "現金", "支票+現金"], key="add_type")
    
    col5, col6, col7 = st.columns([2,1,3])
    with col5:
        new_responsible = st.selectbox("負責人", ["德","Q","其他"], key="add_responsible")
    with col6:
        new_account_month = st.text_input("帳款月份", key="add_account_month")
    with col7:
        new_note = st.text_input("備註", key="add_note")

    add_btn = st.button("儲存資料", key="add_btn")
    if add_btn:
        # 儲存動作範例
        st.success(f"已新增 {new_customer} 的收帳資料")
