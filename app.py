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
    sheet = gc.open_by_url(SHEET_URL).sheet1

    st.success("連線成功！")

except Exception as e:
    import traceback
    st.error("❌ Google Sheet 錯誤，以下是完整堆疊：")
    st.code(traceback.format_exc())
