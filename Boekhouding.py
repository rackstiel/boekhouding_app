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
        df["Omschrijving"] = ""
    if "Bedrag" not in df.columns:
        df.rename(columns={"Waarde": "Bedrag"}, inplace=True)

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("Boekhouding")

# ----------------------
# SESSION STATE INITIALISEREN (voor reset)
# ----------------------
if "datum" not in st.session_state:
    st.session_state.datum = None
if "categorie_select" not in st.session_state:
    st.session_state.categorie_select = "Nieuwe categorie"
if "categorie_custom" not in st.session_state:
    st.session_state.categorie_custom = ""
if "omschrijving_select" not in st.session_state:
    st.session_state.omschrijving_select = "Nieuwe omschrijving"
if "omschrijving_custom" not in st.session_state:
    st.session_state.omschrijving_custom = ""
if "bedrag" not in st.session_state:
    st.session_state.bedrag = None
if "transactietype" not in st.session_state:
    st.session_state.transactietype = "Uitgave"

# ----------------------
# INVOERVELDEN
# ----------------------

# Datum invoer
datum = st.date_input("Datum", value=st.session_state.datum, key="datum")

# Dropdown categorieën
bestaande_categorieen = df["Categorie"].dropna().unique().tolist()
bestaande_categorieen.sort()

categorie_select = st.selectbox(
    "Kies een categorie (of selecteer 'Nieuwe categorie')",
    ["Nieuwe categorie"] + bestaande_categorieen,
    key="categorie_select"
)

if st.session_state.categorie_select == "Nieuwe categorie":
    categorie = st.text_input("Nieuwe categorie invoeren", key="categorie_custom")
else:
    categorie = st.session_state.categorie_select

# Dropdown omschrijving
bestaande_omschrijving = df["Omschrijving"].dropna().unique().tolist()
bestaande_omschrijving.sort()

omschrijving_select = st.selectbox(
    "Kies een omschrijving (of selecteer 'Nieuwe omschrijving')",
    ["Nieuwe omschrijving"] + bestaande_omschrijving,
    key="omschrijving_select"
)

if st.session_state.omschrijving_select == "Nieuwe omschrijving":
    omschrijving = st.text_input("Nieuwe omschrijving invoeren", key="omschrijving_custom")
else:
    omschrijving = st.session_state.omschrijving_select

# Bedrag veld – nu LEGE standaardwaarde
bedrag = st.number_input(
    "Bedrag (€)",
    step=0.01,
    format="%.2f",
    value=st.session_state.bedrag,
    key="bedrag"
)

# Nieuw: keuze tussen uitgave of inkomsten
transactietype = st.radio(
    "Type transactie",
    ["Uitgave", "Inkomsten"],
    index=0,
    key="transactietype"
)

# ----------------------
# OPSLAAN + RESET
# ----------------------
if st.button("Opslaan") and categorie:

    bedrag_final = bedrag * (-1 if transactietype == "Uitgave" else 1)

    nieuwe_rij = {
        "Datum": pd.to_datetime(datum),
        "Categorie": categorie,
        "Bedrag": bedrag_final,
        "Omschrijving": omschrijving
    }

    df = pd.concat([df, pd.DataFrame([nieuwe_rij])], ignore_index=True)
    set_with_dataframe(sheet, df)

    st.success("Gegevens opgeslagen!")

    # 🔄 Velden resetten
    st.session_state.datum = None
    st.session_state.categorie_select = "Nieuwe categorie"
    st.session_state.categorie_custom = ""
    st.session_state.omschrijving_select = "Nieuwe omschrijving"
    st.session_state.omschrijving_custom = ""
    st.session_state.bedrag = None
    st.session_state.transactietype = "Uitgave"

    st.experimental_rerun()

# ----------------------
# Overzicht
# ----------------------
st.subheader("Overzicht ingevoerde data")
if df.empty:
    st.info("Er zijn nog geen gegevens ingevoerd.")
else:
    st.dataframe(df.sort_values(by="Datum", ascending=False))
