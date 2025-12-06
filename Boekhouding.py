import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ----------------------
# CONFIGURATIE
# ----------------------
SHEET_NAAM = "Boekhouding_Rick"
TABBLAD_NAAM = "Blad1"
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAAM).worksheet(TABBLAD_NAAM)

# ----------------------
# BESTAANDE DATA INLEZEN
# ----------------------
data = sheet.get_all_records()
if not data:
    df = pd.DataFrame(columns=["Datum", "Categorie", "Bedrag", "Omschrijving", "Soort"])
else:
    df = pd.DataFrame(data)
    # Zorg dat datum kolom strings in dd-mm-yyyy zijn
    if "Datum" in df.columns:
        df["Datum"] = pd.to_datetime(df["Datum"], errors='coerce').dt.strftime("%d-%m-%Y")
    # Zorg dat alle kolommen aanwezig zijn
    for col in ["Categorie", "Omschrijving", "Soort", "Bedrag"]:
        if col not in df.columns:
            if col == "Bedrag":
                df[col] = 0.0
            else:
                df[col] = ""

# ----------------------
# SESSION STATE INIT
# ----------------------
for key, default in {
    "categorie_select": "Nieuwe categorie",
    "categorie_nieuw": "",
    "omschrijving_select": "Nieuwe omschrijving",
    "omschrijving_nieuw": "",
    "bedrag": 0.0,
    "transactietype": "Uitgave"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("Boekhouding")

datum = st.date_input("Datum")

type_last = st.radio(
    "Is dit een vaste last of een variabele transactie?",
    ["Vaste last", "Variabel"]
)

# Categorieën
bestaande_categorieen = sorted(df["Categorie"].dropna().unique().tolist())
categorie_select = st.selectbox(
    "Kies een categorie (of selecteer 'Nieuwe categorie')",
    ["Nieuwe categorie"] + bestaande_categorieen,
    key="categorie_select"
)
if categorie_select == "Nieuwe categorie":
    categorie = st.text_input("Nieuwe categorie invoeren", key="categorie_nieuw")
else:
    categorie = categorie_select

# Omschrijving
bestaande_omschrijving = sorted(df["Omschrijving"].dropna().unique().tolist())
omschrijving_select = st.selectbox(
    "Kies een omschrijving (of selecteer 'Nieuwe omschrijving')",
    ["Nieuwe omschrijving"] + bestaande_omschrijving,
    key="omschrijving_select"
)
if omschrijving_select == "Nieuwe omschrijving":
    omschrijving = st.text_input("Nieuwe omschrijving invoeren", key="omschrijving_nieuw")
else:
    omschrijving = omschrijving_select

# Bedrag
bedrag = st.number_input(
    "Bedrag (€)",
    min_value=0.0,
    step=0.01,
    format="%.2f",
    key="bedrag"
)

# Type transactie
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

    # Correcte float en negatieve waarde bij uitgave
    bedrag_final = float(bedrag)
    if transactietype == "Uitgave":
        bedrag_final *= -1
    # Afronden op 2 decimalen
    bedrag_final = round(bedrag_final, 2)

    # Nieuwe rij als lijst, datum als string dd-mm-yyyy
    nieuwe_rij = [
        datum.strftime("%d-%m-%Y"),
        categorie,
        bedrag_final,
        omschrijving,
        type_last
    ]

    # Voeg nieuwe rij toe aan Google Sheet (append)
    sheet.append_row(nieuwe_rij, value_input_option="USER_ENTERED")

    # Voeg toe aan lokale DataFrame
    global df
    df = pd.concat([df, pd.DataFrame([{
        "Datum": nieuwe_rij[0],
        "Categorie": nieuwe_rij[1],
        "Bedrag": nieuwe_rij[2],
        "Omschrijving": nieuwe_rij[3],
        "Soort": nieuwe_rij[4]
    }])], ignore_index=True)

    st.success(
        f"Gegevens opgeslagen! Categorie '{categorie}', omschrijving '{omschrijving}' en soort '{type_last}' toegevoegd."
    )

    # Reset sessievelden
    st.session_state.categorie_select = "Nieuwe categorie"
    st.session_state.categorie_nieuw = ""
    st.session_state.omschrijving_select = "Nieuwe omschrijving"
    st.session_state.omschrijving_nieuw = ""
    st.session_state.bedrag = 0.0
    st.session_state.transactietype = "Uitgave"

st.button("Opslaan", on_click=opslaan)

import re

def europees_getal_naar_float(value):
    """
    Zet een waarde om naar float met Europese notatie:
    - Als float/int: gewoon behouden
    - Als string:
        - Komma aanwezig: vervang door punt
        - Geen komma: interpreteer als centen (laatste 2 cijfers decimaal)
    """
    import re

    if value is None:
        return 0.0

    # Float/int behouden
    if isinstance(value, (float, int)):
        return float(value)

    # Anders string
    s = str(value).strip()
    if s == "":
        return 0.0

    # Alleen cijfers, punt, komma
    s = re.sub(r"[^\d,\.]", "", s)

    if "," in s:
        # Europese notatie, vervang komma door punt, verwijder duizendtallen
        s = s.replace(".", "")
        s = s.replace(",", ".")
        try:
            return float(s)
        except:
            return 0.0
    else:
        # Geen komma: interpreteer als centen als > 100
        s_num = int(s)
        if s_num < 100:
            # minder dan 1 euro, bijv. "50" = 0,50
            return s_num / 100
        else:
            # laatste twee cijfers decimaal
            s = s.zfill(3)
            return float(s[:-2] + "." + s[-2:])

# ----------------------
# OVERZICHT
# ----------------------
st.subheader("Overzicht ingevoerde data")
if df.empty:
    st.info("Er zijn nog geen gegevens ingevoerd.")
else:
    df_preview = df.copy()

    # Datum als dd-mm-yyyy
    if "Datum" in df_preview.columns:
        df_preview["Datum"] = pd.to_datetime(df_preview["Datum"], errors='coerce').dt.strftime("%d-%m-%Y")

    # Bedrag: altijd float, 2 decimalen, komma als decimaal
    if "Bedrag" in df_preview.columns:
        df_preview["Bedrag"] = df_preview["Bedrag"].astype(float)/100
        df_preview["Bedrag"] = df_preview["Bedrag"].apply(lambda x: f"{x:.2f}".replace(".", ","))

    # Sorteer op datum (nieuwste eerst)
    df_sorted = df_preview.sort_values(by="Datum", ascending=False)

    st.dataframe(df_sorted, hide_index=True)
