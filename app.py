# ===========================
# app.py - Streamlit Paylist
# ===========================

import streamlit as st
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------
# 1️⃣ Streamlit 頁面設定
# ---------------------------
st.set_page_config(
    page_title="Paylist App",
    page_icon="💰",
    layout="wide"
)

# ---------------------------
# 2️⃣ 讀取 GCP Service Account 金鑰
# ---------------------------
# 從 Streamlit Secrets 取得
try:
    service_account_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
except KeyError:
    st.error("⚠️ GCP_SERVICE_ACCOUNT_JSON not found in Streamlit Secrets.")
    st.stop()

# ---------------------------
# 3️⃣ 建立 Google Sheet 連線
# ---------------------------
try:
    creds = Credentials.from_service_account_info(service_account_info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    gc = gspread.authorize(creds)
except Exception as e:
    st.error(f"⚠️ 無法連線到 Google Sheet: {e}")
    st.stop()

# ---------------------------
# 4️⃣ 你的其他程式碼
# ---------------------------
st.title("💰 Paylist App")
st.write("連線成功！可以開始操作資料。")
