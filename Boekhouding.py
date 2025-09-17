import streamlit as st
import pandas as pd
import pygsheets
import io

# ----------------------
# CONFIGURATIE
# ----------------------
SHEET_NAAM = "Boekhouding_Rick"
TABBLAD_NAAM = "Blad1"

# Maak credentials van secrets
gc = pygsheets.authorize(service_account_info=st.secrets["google_service_account"])
sh = gc.open(SHEET_NAAM)
worksheet = sh.worksheet_by_title(TABBLAD_NAAM)

# Laad bestaande data
try:
    df = pd.DataFrame(worksheet.get_all_records())
    if not df.empty:
        df["Datum"] = pd.to_datetime(df["Datum"])
    else:
        df = pd.DataFrame(columns=["Datum", "Categorie", "Waarde"])
except Exception:
    df = pd.DataFrame(columns=["Datum", "Categorie", "Waarde"])

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("Mijn Data Invoer App")

datum = st.date_input("Datum")

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
    nieuwe_rij = {"Datum": pd.to_datetime(datum).strftime("%Y-%m-%d"), "Categorie": categorie, "Waarde": waarde}
    df = pd.concat([df, pd.DataFrame([nieuwe_rij])], ignore_index=True)
    
    # Schrijf terug naar Google Sheet
    worksheet.set_dataframe(df, (1,1))
    
    st.success(f"Gegevens opgeslagen! Categorie '{categorie}' toegevoegd indien nieuw.")

    if categorie not in bestaande_categorieen:
        bestaande_categorieen.append(categorie)
        bestaande_categorieen.sort()

# Overzicht
st.subheader("Overzicht ingevoerde data")
if df.empty:
    st.info("Er zijn nog geen gegevens ingevoerd.")
else:
    df_sorted = df.sort_values(by="Datum", ascending=False)
    st.dataframe(df_sorted)

# Download knop
excel_buffer = io.BytesIO()
df.to_excel(excel_buffer, index=False)
st.download_button(
    label="Download Excel",
    data=excel_buffer,
    file_name="Boekhouding_Rick.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
