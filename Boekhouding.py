import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ----------------------
# CONFIGURATIE
# ----------------------
SHEET_NAAM = "Boekhouding_Rick"
TABBLAD_NAAM = "Blad1"
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
    df = pd.DataFrame(columns=["Datum", "Categorie", "Bedrag", "Omschrijving"])
else:
    df["Datum"] = pd.to_datetime(df["Datum"])
    if "Omschrijving" not in df.columns:
        df["Omschrijving"] = ""  # Voeg kolom toe als die nog niet bestaat
    if "Bedrag" not in df.columns:
        df.rename(columns={"Waarde": "Bedrag"}, inplace=True)

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("Boekhouding")

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

# Nieuw optioneel veld Omschrijving boven Bedrag
omschrijving = st.text_input("Omschrijving (optioneel)")

# Bedrag veld als valuta
bedrag = st.number_input("Bedrag (€)", step=0.01, format="%.2f")

# Opslaan knop
if st.button("Opslaan") and categorie:
    nieuwe_rij = {
        "Datum": pd.to_datetime(datum),
        "Categorie": categorie,
        "Bedrag": bedrag,
        "Omschrijving": omschrijving
    }
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
