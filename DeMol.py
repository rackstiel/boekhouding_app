import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ----------------------
# CONFIGURATIE
# ----------------------
SHEET_NAAM = "DeMol"
KANDIDATEN_TAB = "kandidaten"
SPELERS_TAB = "spelers"
INZET_TAB = "inzetten"
AFLEVERING_TAB = "aflevering"

SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ----------------------
# GOOGLE SHEETS CONNECTIE
# ----------------------
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO, scopes=scope
)
client = gspread.authorize(creds)
spreadsheet = client.open(SHEET_NAAM)

kandidaten_sheet = spreadsheet.worksheet(KANDIDATEN_TAB)
spelers_sheet = spreadsheet.worksheet(SPELERS_TAB)
inzet_sheet = spreadsheet.worksheet(INZET_TAB)
aflevering_sheet = spreadsheet.worksheet(AFLEVERING_TAB)

# ----------------------
# DATA INLEZEN FUNCTIE
# ----------------------
def load_sheet(sheet, default_columns=None):
    df = pd.DataFrame(sheet.get_all_records())
    if df.empty and default_columns:
        df = pd.DataFrame(columns=default_columns)
    df.columns = df.columns.str.strip().str.lower()
    return df

# ----------------------
# LAAD DATA
# ----------------------
kandidaten_df = load_sheet(kandidaten_sheet, default_columns=["naam", "actief"])
spelers_df = load_sheet(spelers_sheet, default_columns=["naam", "punten"])
spelers_df["punten"] = spelers_df["punten"].astype(int)

inzetten_df = load_sheet(inzet_sheet, default_columns=["speler", "kandidaat", "punten", "aflevering"])

aflevering_df = load_sheet(aflevering_sheet, default_columns=["aflevering"])
AFLEVERING = int(aflevering_df.loc[0, "aflevering"]) if not aflevering_df.empty else 1

# ----------------------
# PAGINA NAVIGATIE
# ----------------------
pagina = st.sidebar.selectbox("Pagina", ["Speler", "Beheer"])

# ----------------------
# FUNCTIE: AFLEVERING VERWERKEN
# ----------------------
def verwerk_aflevering(aflevering):
    """Verwerk alle inzetten: verdubbel punten voor actieve kandidaten, verwijder punten voor uitgevallen kandidaten,
       en verhoog aflevering in sheet."""
    global spelers_df, inzetten_df, AFLEVERING

    inzetten_aflr = inzetten_df[inzetten_df["aflevering"] == aflevering]
    actieve_kandidaten = kandidaten_df[kandidaten_df["actief"].str.lower() == "ja"]["naam"].tolist()

    for speler_naam in inzetten_aflr["speler"].unique():
        speler_inzetten = inzetten_aflr[inzetten_aflr["speler"] == speler_naam]

        # Bereken nieuwe punten: alleen verdubbelde inzet op actieve kandidaten
        totaal_voor_actieve = speler_inzetten[
            speler_inzetten["kandidaat"].isin(actieve_kandidaten)
        ]["punten"].sum()
        nieuwe_punten = totaal_voor_actieve * 2

        # Zet het puntenaantal van de speler op deze nieuwe waarde
        spelers_df.loc[spelers_df["naam"] == speler_naam, "punten"] = nieuwe_punten

    # Update spelers sheet
    spelers_sheet.update([spelers_df.columns.tolist()] + spelers_df.values.tolist())

    # Verhoog AFLEVERING met 1 en update sheet
    AFLEVERING += 1
    aflevering_sheet.update([["aflevering"]] + [[AFLEVERING]])
    st.success(f"Aflevering {aflevering} verwerkt! Nieuwe AFLEVERING is {AFLEVERING}")

# ----------------------
# SPELERSPAGINA
# ----------------------
if pagina == "Speler":
    st.title("🕵️ Wie is de Mol App")

    # Speler kiezen
    spelers_df["naam"] = spelers_df["naam"].astype(str)
    speler = st.selectbox("Wie ben jij?", spelers_df["naam"])

    # Check of al ingezet
    bestaande = inzetten_df[
        (inzetten_df["speler"] == speler) &
        (inzetten_df["aflevering"] == AFLEVERING)
    ]

    # Info over punten alleen tonen als nog niet ingezet
    if bestaande.empty:
        punten = int(spelers_df.loc[spelers_df["naam"] == speler, "punten"].values[0])
        st.info(f"Je hebt {punten} punten om in te zetten voor aflevering {AFLEVERING}")
    else:
        # Overzicht van huidige inzet
        st.warning(f"Je hebt al ingezet voor aflevering {AFLEVERING}")
        st.subheader("Je inzet voor deze aflevering")
        inzet_overzicht = bestaande[["kandidaat", "punten"]].copy()
        inzet_overzicht["punten"] = inzet_overzicht["punten"].astype(int)
        st.table(inzet_overzicht)
        totaal_ingezet = inzet_overzicht["punten"].sum()
        st.info(f"Totaal ingezet: {totaal_ingezet}")
    
    # Leaderboard altijd zichtbaar
    st.subheader("📊 Leaderboard")
    leaderboard = spelers_df.copy().sort_values(by="punten", ascending=False)
    st.dataframe(leaderboard.style.background_gradient(subset=["punten"], cmap="Greens"), hide_index=True)

    if not bestaande.empty:
        st.stop()

    # Actieve kandidaten
    actieve_kandidaten = kandidaten_df[kandidaten_df["actief"].str.lower() == "ja"]["naam"]
    if actieve_kandidaten.empty:
        st.warning("Geen actieve kandidaten meer!")
        st.stop()

    # Inzetten
    st.subheader("Verdeel je punten")
    inzet_data = {}
    totaal = 0
    for kandidaat in actieve_kandidaten:
        value = st.number_input(
            f"{kandidaat}",
            min_value=0,
            max_value=punten,
            step=1,
            key=f"inzet_{kandidaat}"
        )
        inzet_data[kandidaat] = value
        totaal += value

    st.write(f"Totaal ingezet: {totaal} / {punten}")

    if totaal > punten:
        st.error("Je hebt te veel punten ingezet!")
    elif totaal < punten:
        st.warning("Je hebt nog niet al je punten ingezet!")
    else:
        st.success("Inzet klopt precies ✅")

    # Opslaan
    def opslaan():
        if totaal != punten:
            st.error("Je moet precies al je punten inzetten!")
            return
        for k, p in inzet_data.items():
            if p > 0:
                inzet_sheet.append_row([speler, k, int(p), AFLEVERING])
        st.success("Je inzet is opgeslagen!")

    st.button("Opslaan", on_click=opslaan, disabled=(totaal != punten))

# ----------------------
# BEHEERPAGINA
# ----------------------
elif pagina == "Beheer":
    st.title("⚙️ Beheer Aflevering")

    st.markdown("**Stap 1: Selecteer kandidaten die eruit gaan**")
    kandidaten_df["actief"] = kandidaten_df["actief"].astype(str)
    kandidaten_uit = st.multiselect(
        "Kandidaten eruit:",
        kandidaten_df["naam"][kandidaten_df["actief"].str.lower() == "ja"]
    )

    if st.button("Update kandidaten status"):
        for k in kandidaten_uit:
            kandidaten_df.loc[kandidaten_df["naam"] == k, "actief"] = "Nee"
        kandidaten_sheet.update([kandidaten_df.columns.tolist()] + kandidaten_df.values.tolist())
        st.success("Kandidatenstatus bijgewerkt!")

    st.markdown("---")
    st.markdown(f"**Stap 2: Verwerk punten voor aflevering {AFLEVERING} en verhoog AFLEVERING**")
    if st.button(f"Verwerk aflevering {AFLEVERING}"):
        verwerk_aflevering(AFLEVERING)