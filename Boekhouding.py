import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import io

# ----------------------
# CONFIGURATIE
# ----------------------
SHEET_NAAM = "Boekhouding_Rick"  # je Google Sheet naam
TABBLAD_NAAM = "Blad1"           # jouw tabbladnaam
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Maak credentials
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
client = gspread.authorize(creds)

# Open Google Sheet
sheet = client.open(SHEET_NAAM).worksheet(TABBLAD_NAAM)

# Laad bestaande data
df = get_as_dataframe(sheet)
if df is None or df.empty:
    df = pd.DataFrame(columns=["Datum", "Categorie", "Waarde"])
else:
    df["Datum"] = pd.to_datetime(df["Datum"])

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("Boekhouding Rick")

# Datum invoer
datum = st.date_input("Datum")

# Dropdown categorieën
bestaande_categorieen = df["Categorie"].dropna().unique().tolist()
bestaande_categorieen.sort()

categorie_select = st.selectbox(
    "Kies een categorie (of selecteer 'Nieuwe categorie')",
    ["Nieuwe categorie"] + bestaande_categorieen
)

if categorie_select == "Nieuwe categorie":
    categorie = st.text_input("Nieuwe categorie invoeren")
else:
    categorie = categorie_select

waarde = st.number_input("Waarde", step=1.0)

# Opslaan knop
if st.button("Opslaan") and categorie:
    nieuwe_rij = {"Datum": pd.to_datetime(datum), "Categorie": categorie, "Waarde": waarde}
    df = pd.concat([df, pd.DataFrame([nieuwe_rij])], ignore_index=True)
    
    # Schrijf terug naar Google Sheet
    set_with_dataframe(sheet, df)
    
    st.success(f"Gegevens opgeslagen! Categorie '{categorie}' toegevoegd indien nieuw.")

    # Update dropdown in huidige sessie
    if categorie not in bestaande_categorieen:
        bestaande_categorieen.append(categorie)
        bestaande_categorieen.sort()

# Overzicht van data
st.subheader("Overzicht ingevoerde data")
if df.empty:
    st.info("Er zijn nog geen gegevens ingevoerd.")
else:
    df_sorted = df.sort_values(by="Datum", ascending=False)
    st.dataframe(df_sorted)

# Optioneel: download knop
excel_buffer = io.BytesIO()
df.to_excel(excel_buffer, index=False)
st.download_button(
    label="Download Excel",
    data=excel_buffer,
    file_name="Boekhouding_Rick.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
