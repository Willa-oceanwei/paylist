import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("🔧 Google Sheet 連線測試")

SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=SCOPES
    )
    gc = gspread.authorize(creds)

    SHEET_URL = "https://docs.google.com/spreadsheets/d/17Tm4ua_vF6E5fi49eNDgHMI25us1Q-u6TqMXmLaGugs/edit#gid=0"
    sheet = gc.open_by_url(SHEET_URL).sheet1

    st.success("成功連線到 Google Sheet！")
    st.write("A1:", sheet.acell("A1").value)

except Exception as e:
    st.error("❌ 錯誤訊息：")
    st.code(str(e))
