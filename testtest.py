import streamlit as st

st.title("Google Sheets verbindingstest")

# 1️⃣ Controleer gspread import
try:
    import gspread
    from gspread_dataframe import get_as_dataframe
    from google.oauth2.service_account import Credentials
    st.success("✅ gspread en gspread_dataframe zijn geïnstalleerd!")
except ImportError as e:
    st.error(f"❌ Import fout: {e}")
    st.stop()

# 2️⃣ Controleer of secret aanwezig is
if "gcp_service_account" not in st.secrets:
    st.error("❌ Secret 'gcp_service_account' niet gevonden. Voeg deze toe in Streamlit Cloud Secrets.")
    st.stop()
else:
    st.success("✅ Secret 'gcp_service_account' gevonden.")

SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# 3️⃣ Maak credentials
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
    client = gspread.authorize(creds)
    st.success("✅ Service account credentials werken!")
except Exception as e:
    st.error(f"❌ Fout bij aanmaken van credentials: {e}")
    st.stop()

# 4️⃣ Open de Google Sheet
SHEET_NAAM = st.text_input("Sheet naam", "Boekhouding_Rick")
TABBLAD_NAAM = st.text_input("Tabblad naam", "Blad1")

try:
    sheet = client.open(SHEET_NAAM)
    st.success(f"✅ Sheet '{SHEET_NAAM}' geopend!")
    
    # Toon beschikbare tabbladen
    tabbladen = [ws.title for ws in sheet.worksheets()]
    st.write("📄 Beschikbare tabbladen:", tabbladen)
    
    # Probeer een specifiek tabblad
    ws = sheet.worksheet(TABBLAD_NAAM)
    df = get_as_dataframe(ws)
    st.success(f"✅ Tabblad '{TABBLAD_NAAM}' geopend! Aantal rijen: {len(df)}")
    st.dataframe(df.head())
except gspread.exceptions.APIError as e:
    st.error(f"❌ APIError: {e.response.status_code} - {e.response.text}")
except gspread.SpreadsheetNotFound:
    st.error(f"❌ Sheet '{SHEET_NAAM}' niet gevonden of geen toegang!")
except gspread.WorksheetNotFound:
    st.error(f"❌ Tabblad '{TABBLAD_NAAM}' niet gevonden in Sheet '{SHEET_NAAM}'!")
except Exception as e:
    st.error(f"❌ Onbekende fout: {e}")
