import streamlit as st

# ----------------------
# Pakket check
# ----------------------
try:
    import gspread
    from gspread_dataframe import get_as_dataframe
    from google.oauth2.service_account import Credentials
    st.success("✅ gspread en gspread_dataframe zijn geïnstalleerd!")
except ImportError as e:
    st.error(f"❌ Fout bij import: {e}")
    st.stop()

# ----------------------
# Verbinding met Google Sheet
# ----------------------
try:
    SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
    client = gspread.authorize(creds)

    SHEET_NAAM = "Boekhouding_Rick"  # Pas aan als nodig
    TABBLAD_NAAM = "Blad1"
    
    sheet = client.open(SHEET_NAAM).worksheet(TABBLAD_NAAM)
    df = get_as_dataframe(sheet)
    
    st.success(f"✅ Verbonden met Google Sheet '{SHEET_NAAM}'! Rijen in sheet: {len(df)}")
except Exception as e:
    st.error(f"❌ Kan geen verbinding maken met Google Sheet: {e}")
