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

# Google credentials
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
client = gspread.authorize(creds)

# Open Google Sheet
sheet = client.open(SHEET_NAAM).worksheet(TABBLAD_NAAM)

# Data laden
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
# SESSION STATE INIT
# ----------------------
if "datum" not in st.session_state:
    st.session_state.datum = pd.to_datetime("today")

if "categorie_select" not in st.session_state:
    st.session_state.categorie_select = "Nieuwe categorie"

if "categorie_custom" not in st.session_state:
    st.session_state.categorie_custom = ""

if "omschrijving_select" not in st.session_state:
    st.session_state.omschrijving_select = "Nieuwe omschrijving"

if "omschrijving_custom" not in st.session_state:
    st.session_state.omschrijving_custom = ""

if "bedrag" not in st.session_state:
    st.session_state.bedrag = ""

if "transactietype" not in st.session_state:
    st.session_state.transactietype = "Uitgave"

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("Boekhouding")

# Datum
datum = st.date_input("Datum", value=st.session_state.datum, key="datum")

# Categorie
bestaande_categorieen = sorted(df["Categorie"].dropna().unique().tolist())
categorie_select = st.selectbox(
    "Kies een categorie (of selecteer 'Nieuwe categorie')",
    ["Nieuwe categorie"] + bestaande_categorieen,
    key="categorie_select"
)

if st.session_state.categorie_select == "Nieuwe categorie":
    categorie = st.text_input("Nieuwe categorie invoeren", key="categorie_custom")
else:
    categorie = st.session_state.categorie_select

# Omschrijving
bestaande_omschrijving = sorted(df["Omschrijving"].dropna().unique().tolist())
omschrijving_select = st.selectbox(
    "Kies een omschrijving (of selecteer 'Nieuwe omschrijving')",
    ["Nieuwe omschrijving"] + bestaande_omschrijving,
    key="omschrijving_select"
)

if st.session_state.omschrijving_select == "Nieuwe omschrijving":
    omschrijving = st.text_input("Nieuwe omschrijving invoeren", key="omschrijving_custom")
else:
    omschrijving = st.session_state.omschrijving_select

# Bedrag — standaard leeg
bedrag_input = st.text_input("Bedrag (€)", value=st.session_state.bedrag, key="bedrag")

# Transactie type
transactietype = st.radio(
    "Type transactie",
    ["Uitgave", "Inkomsten"],
    key="transactietype"
)

# ----------------------
# OPSLAAN KNOP
# ----------------------
if st.button("Opslaan"):

    # Validatie
    if bedrag_input.strip() == "":
        st.error("Vul een bedrag in.")
        st.stop()

    try:
        bedrag = float(bedrag_input.replace(",", "."))
    except:
        st.error("Ongeldig bedrag. Gebruik alleen cijfers.")
        st.stop()

    # Uitgave → negatief
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

    # ----------------------
    # Veld-reset (mag geen None zijn!)
    # ----------------------
    st.session_state.datum = pd.to_datetime("today")
    st.session_state.categorie_select = "Nieuwe categorie"
    st.session_state.categorie_custom = ""
    st.session_state.omschrijving_select = "Nieuwe omschrijving"
    st.session_state.omschrijving_custom = ""
    st.session_state.bedrag = ""        # leeg veld
    st.session_state.transactietype = "Uitgave"

    st.experimental_rerun()

# ----------------------
# Overzicht
# ----------------------
st.subheader("Overzicht ingevoerde data")
if df.empty:
    st.info("Er zijn nog geen gegevens ingevoerd.")
else:
    st.dataframe(df.sort_values("Datum", ascending=False))
