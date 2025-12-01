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
    df = pd.DataFrame(columns=["Datum", "Categorie", "Bedrag", "Omschrijving", "Soort"])
else:
    df["Datum"] = pd.to_datetime(df["Datum"])
    if "Omschrijving" not in df.columns:
        df["Omschrijving"] = ""
    if "Bedrag" not in df.columns:
        df.rename(columns={"Waarde": "Bedrag"}, inplace=True)
    if "Soort" not in df.columns:   # nieuwe kolomnaam
        df["Soort"] = ""

# ----------------------
# SESSION STATE INIT
# ----------------------
if "categorie_select" not in st.session_state:
    st.session_state["categorie_select"] = "Nieuwe categorie"
if "categorie_nieuw" not in st.session_state:
    st.session_state["categorie_nieuw"] = ""
if "omschrijving_select" not in st.session_state:
    st.session_state["omschrijving_select"] = "Nieuwe omschrijving"
if "omschrijving_nieuw" not in st.session_state:
    st.session_state["omschrijving_nieuw"] = ""
if "bedrag" not in st.session_state:
    st.session_state["bedrag"] = 0.0
if "transactietype" not in st.session_state:
    st.session_state["transactietype"] = "Uitgave"

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("Boekhouding")

# Datum invoer
datum = st.date_input("Datum")

# NIEUW: Soort onder Datum
type_last = st.radio(
    "Is dit een vaste last of een variabele transactie?",
    ["Vaste last", "Variabel"]
)

# Dropdown categorieën
bestaande_categorieen = df["Categorie"].dropna().unique().tolist()
bestaande_categorieen.sort()
categorie_select = st.selectbox(
    "Kies een categorie (of selecteer 'Nieuwe categorie')",
    ["Nieuwe categorie"] + bestaande_categorieen,
    key="categorie_select"
)
if st.session_state.categorie_select == "Nieuwe categorie":
    categorie = st.text_input("Nieuwe categorie invoeren", key="categorie_nieuw")
else:
    categorie = st.session_state.categorie_select

# Dropdown omschrijving
bestaande_omschrijving = df["Omschrijving"].dropna().unique().tolist()
bestaande_omschrijving.sort()
omschrijving_select = st.selectbox(
    "Kies een omschrijving (of selecteer 'Nieuwe omschrijving')",
    ["Nieuwe omschrijving"] + bestaande_omschrijving,
    key="Omschrijving_select"
)
if st.session_state.get("Omschrijving_select") == "Nieuwe omschrijving":
    omschrijving = st.text_input("Nieuwe omschrijving invoeren", key="omschrijving_nieuw")
else:
    omschrijving = st.session_state.get("Omschrijving_select")

# Bedrag veld
bedrag = st.number_input(
    "Bedrag (€)",
    step=0.01,
    format="%.2f",
    key="bedrag"
)

# Keuze tussen uitgave of inkomsten
transactietype = st.radio(
    "Type transactie",
    ["Uitgave", "Inkomsten"],
    index=0,
    key="transactietype"
)

# ----------------------
# OPSLAAN FUNCTIE
# ----------------------
def opslaan():
    if not categorie:
        st.warning("Vul een categorie in.")
        return
    
    # Negatief bij uitgave
    bedrag_final = bedrag * (-1 if transactietype == "Uitgave" else 1)

    nieuwe_rij = {
        "Datum": pd.to_datetime(datum),
        "Categorie": categorie,
        "Bedrag": bedrag_final,
        "Omschrijving": omschrijving,
        "Soort": type_last   # nieuwe kolomnaam
    }

    global df
    df = pd.concat([df, pd.DataFrame([nieuwe_rij])], ignore_index=True)

    # Schrijf naar Google Sheet
    set_with_dataframe(sheet, df)

    st.success(
        f"Gegevens opgeslagen! Categorie '{categorie}', omschrijving '{omschrijving}' en soort '{type_last}' toegevoegd."
    )

    # Reset sessie velden
    st.session_state.categorie_select = "Nieuwe categorie"
    st.session_state.categorie_nieuw = ""
    st.session_state.omschrijving_select = "Nieuwe omschrijving"
    st.session_state.omschrijving_nieuw = ""
    st.session_state.bedrag = 0.0
    st.session_state.transactietype = "Uitgave"

# Opslaan knop
st.button("Opslaan", on_click=opslaan)

# ----------------------
# OVERZICHT
# ----------------------
st.subheader("Overzicht ingevoerde data")
if df.empty:
    st.info("Er zijn nog geen gegevens ingevoerd.")
else:
    df_sorted = df.sort_values(by="Datum", ascending=False)
    st.dataframe(df_sorted, hide_index=True)  # geen index meer
