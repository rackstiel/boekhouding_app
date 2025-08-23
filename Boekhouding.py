import streamlit as st
import pandas as pd
import os

bestand = "data.xlsx"

# Laad Excel of maak lege DataFrame
if os.path.exists(bestand):
    df = pd.read_excel(bestand)
    # Zorg dat 'Datum' altijd datetime is
    df["Datum"] = pd.to_datetime(df["Datum"])
else:
    df = pd.DataFrame(columns=["Datum", "Categorie", "Waarde"])

st.title("Mijn Data Invoer App")

# Invoer velden
datum = st.date_input("Datum")

# Huidige categorieën ophalen
bestaande_categorieen = df["Categorie"].dropna().unique().tolist()
bestaande_categorieen.sort()

# Dropdown met optie om nieuwe categorie in te voeren
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
    df.to_excel(bestand, index=False)
    st.success(f"Gegevens opgeslagen! Categorie '{categorie}' toegevoegd indien nieuw.")

    # Voeg nieuwe categorie direct toe aan dropdown lijst in huidige sessie
    if categorie not in bestaande_categorieen:
        bestaande_categorieen.append(categorie)
        bestaande_categorieen.sort()

# Overzicht van ingevoerde data
st.subheader("Overzicht ingevoerde data")
if df.empty:
    st.info("Er zijn nog geen gegevens ingevoerd.")
else:
    # Sorteer op datum, nieuwste bovenaan
    df_sorted = df.sort_values(by="Datum", ascending=False)
    st.dataframe(df_sorted)
