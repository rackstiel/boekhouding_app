import streamlit as st
import random
import matplotlib.pyplot as plt
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ----------------------
# CONFIGURATIE GOOGLE SHEET
# ----------------------
SHEET_NAAM = "Dartapp"
TABBLAD_NAAM = "Blad1"
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAAM).worksheet(TABBLAD_NAAM)

# ----------------------
# FUNCTIE OM DATA OP TE SLAAN
# ----------------------
def sla_data_op(naam, vak, aantal_pijlen, timestamp):
    sheet.append_row([naam, timestamp, vak, aantal_pijlen])
    st.success(f"Gegevens voor vak '{get_focus_display_name(vak)}' opgeslagen!")

# ----------------------
# Dartbord instellingen
# ----------------------
ring_radii = {
    "Double": (9.5, 10),
    "Single boven": (6, 9.5),
    "Triple": (5.5, 6),
    "Single onder": (1.25, 5.5),
    "Outer Bull": (1.5, 1.25),
    "Bullseye": (0, 0.6)
}

dartbord_volgorde = [20,1,18,4,13,6,10,15,2,17,3,19,7,16,8,11,14,9,12,5]

def get_type(vak):
    vak_lower = vak.lower()
    if vak_lower.startswith("single") and "onder" in vak_lower:
        return "Single onder"
    elif vak_lower.startswith("single") and "boven" in vak_lower:
        return "Single boven"
    elif vak_lower.startswith("double"):
        return "Double"
    elif vak_lower.startswith("triple"):
        return "Triple"
    elif "outer bull" in vak_lower:
        return "Outer Bull"
    elif "bullseye" in vak_lower:
        return "Bullseye"
    else:
        raise ValueError(f"Onbekend vak: {vak}")

def kleur(vak, focus_vak):
    return (1,0,0) if vak == focus_vak else (0.9,0.9,0.9)

def get_focus_display_name(vak):
    if vak in ["Bullseye", "Outer Bull"]:
        return vak
    vak_parts = vak.split()
    type_vak = vak_parts[0]
    if type_vak == "Single":
        if vak_parts[-1].isdigit():
            nummer_in_vak = int(vak_parts[-1])
            position = ""
        else:
            nummer_in_vak = int(vak_parts[-2])
            position = vak_parts[-1]
        echte_nummer = dartbord_volgorde[nummer_in_vak - 1]
        return f"{type_vak} {position} ({echte_nummer})".strip()
    else:
        nummer_in_vak = int(vak_parts[1])
        echte_nummer = dartbord_volgorde[nummer_in_vak - 1]
        return f"{type_vak} {echte_nummer}"

def teken_dartbord(focus_vak):
    sectoren = range(1, 21)
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 10)
    theta_width = 2*np.pi / 20
    for i, s in enumerate(sectoren):
        vakken_in_sector = [
            f"Double {s}",
            f"Single {s} boven",
            f"Triple {s}",
            f"Single {s} onder"
        ]
        for vak in vakken_in_sector:
            vak_type = get_type(vak)
            r_start, r_end = ring_radii[vak_type]
            ax.bar(
                i*theta_width,
                r_end - r_start,
                width=theta_width*0.95,
                bottom=r_start,
                color=kleur(vak, focus_vak),
                edgecolor='black',
                linewidth=0.5
            )
    for vak, radius in [("Outer Bull", ring_radii["Outer Bull"]), ("Bullseye", ring_radii["Bullseye"])]:
        r_start, r_end = radius
        circle = plt.Circle((0,0), r_end, transform=ax.transData._b, color=kleur(vak, focus_vak), ec='black')
        ax.add_artist(circle)
    for i, nummer in enumerate(dartbord_volgorde):
        theta = i * theta_width + theta_width/2 - (2*np.pi / 40)
        ax.text(theta, 10.7, str(nummer), ha='center', va='center', fontsize=12, fontweight='bold')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.title(get_focus_display_name(focus_vak), pad=30, fontsize=18, fontweight='bold')
    return fig

# ----------------------
# STREAMLIT APP
# ----------------------
st.title("Welkom bij de Dartbord App")

# ----------------------
# SESSION STATE INIT
# ----------------------
for key in ['pagina', 'naam', 'vakken', 'index', 'pijlen', 'timestamp', 'dropdown_naam', 'tekst_naam']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'pijlen' else {}
# ----------------------
# Pagina 1: Naam dropdown + tekst
# ----------------------
if st.session_state.pagina == 1 or st.session_state.pagina is None:
    try:
        alle_rows = sheet.get_all_values()[1:]  # skip header
        bestaande_namen = sorted(list(set(row[0] for row in alle_rows if row[0])))
    except:
        bestaande_namen = []

    if not st.session_state.dropdown_naam:
        st.session_state.dropdown_naam = "Zelf je naam invoeren"
    if st.session_state.tekst_naam is None:
        st.session_state.tekst_naam = ""

    gekozen_naam = st.selectbox(
        "Kies een bestaande naam of voer zelf je naam in:",
        ["Zelf je naam invoeren"] + bestaande_namen,
        index=0,
        key='dropdown_naam'
    )

    if gekozen_naam == "Zelf je naam invoeren":
        st.text_input("Voer je naam in:", key="tekst_naam")

    def start_app():
        naam = st.session_state.tekst_naam if gekozen_naam == "Zelf je naam invoeren" else gekozen_naam
        if not naam.strip():
            st.warning("Vul een naam in of selecteer een bestaande naam.")
            return

        st.session_state.naam = naam
        st.session_state.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --------- Vakken instellen ----------
        aantal_totaal_vakken = 5
        alle_vakken = []
        for n in range(1,21):
            alle_vakken.extend([f"Double {n}", f"Single {n} boven", f"Triple {n}", f"Single {n} onder"])
        alle_vakken.extend(["Outer Bull","Bullseye"])

        verplichte_vakken = ["Triple 1", random.choice(["Bullseye","Outer Bull"])]
        overige_vakken = list(set(alle_vakken) - set(verplichte_vakken))
        aantal_overige = aantal_totaal_vakken - len(verplichte_vakken)
        random_vakken = random.sample(overige_vakken, aantal_overige)

        st.session_state.vakken = verplichte_vakken + random_vakken
        random.shuffle(st.session_state.vakken)

        st.session_state.index = 0
        st.session_state.pagina = 2

    st.button("Start", on_click=start_app)

    # ---- DATA OPHALEN ----
    rows = sheet.get_all_values()[1:]  # skip header
    # Structuur: [naam, timestamp, vak, aantal]

    import pandas as pd

    # ---------------------------
    # TABEL 1 — Beste totaalscore per persoon
    # ---------------------------
    st.subheader("🎯 Beste totaalscore per persoon")

    totals = {}  # naam → lijst totalen per sessie

    for r in rows:
        naam, ts, vak, aantal = r
        aantal = int(aantal)

        if naam not in totals:
            totals[naam] = {}

        # Voeg sessie toe
        if ts not in totals[naam]:
            totals[naam][ts] = 0

        totals[naam][ts] += aantal

    # Minimale score per persoon bepalen
    min_scores = []
    for naam, sessies in totals.items():
        beste_score = min(sessies.values())
        min_scores.append([naam, beste_score])

    df_totals = pd.DataFrame(min_scores, columns=["Naam", "Totaal worpen (minimaal)"])
    df_totals = df_totals.sort_values("Totaal worpen (minimaal)", ascending=True)
    df_totals.insert(0, "Positie", range(1, len(df_totals) + 1))
    st.dataframe(df_totals, use_container_width=True, hide_index=True)

# ----------------------
# Pagina 2: Step-by-step vakjes
# ----------------------
if st.session_state.pagina == 2:
    idx = st.session_state.index
    if idx >= len(st.session_state.vakken):
        st.success("Je hebt alle vakken voltooid!")
        st.session_state.pagina = 3  # GA DOOR NAAR RESULTATEN
        st.rerun()

    else:
        focus_vak = st.session_state.vakken[idx]
        fig = teken_dartbord(focus_vak)

        col1, col2, col3 = st.columns([1,6,1])
        with col2:
            st.pyplot(fig, use_container_width=False)

        key_input = f"aantal_{idx}"
        if key_input not in st.session_state.pijlen:
            st.session_state.pijlen[key_input] = 1
        aantal = st.number_input(
            f"Aantal pijlen op {get_focus_display_name(focus_vak)}:",
            min_value=1,
            step=1,
            key=key_input,
            value=st.session_state.pijlen[key_input]
        )

        def volgende_vak():
            aantal_widget = st.session_state[key_input]
            if aantal_widget <= 0:
                st.warning("Aantal pijlen moet minimaal 1 zijn.")
                return
            sla_data_op(st.session_state.naam, focus_vak, aantal_widget, st.session_state.timestamp)
            st.session_state.pijlen[key_input] = aantal_widget
            st.session_state.index += 1

        st.button("Volgende", on_click=volgende_vak)

# ----------------------
# PAGINA 3: RESULTATEN & STATISTIEKEN
# ----------------------
if st.session_state.pagina == 3:

    st.header("📊 Resultaten & Statistieken")

    # ---- DATA OPHALEN ----
    rows = sheet.get_all_values()[1:]  # skip header
    # Structuur: [naam, timestamp, vak, aantal]

    import pandas as pd

    # ---------------------------
    # TABEL 1 — Beste totaalscore per persoon
    # ---------------------------
    st.subheader("🎯 Beste totaalscore per persoon")

    totals = {}  # naam → lijst totalen per sessie

    for r in rows:
        naam, ts, vak, aantal = r
        aantal = int(aantal)

        if naam not in totals:
            totals[naam] = {}

        # Voeg sessie toe
        if ts not in totals[naam]:
            totals[naam][ts] = 0

        totals[naam][ts] += aantal

    # Minimale score per persoon bepalen
    min_scores = []
    for naam, sessies in totals.items():
        beste_score = min(sessies.values())
        min_scores.append([naam, beste_score])

    df_totals = pd.DataFrame(min_scores, columns=["Naam", "Totaal worpen (minimaal)"])
    df_totals = df_totals.sort_values("Totaal worpen (minimaal)", ascending=True)
    df_totals.insert(0, "Positie", range(1, len(df_totals) + 1))
    st.dataframe(df_totals, use_container_width=True, hide_index=True)

    # ---------------------------
    # DROPDOWN VOOR PERSOONLIJKE STATISTIEKEN
    # ---------------------------
    st.subheader("Filter op speler")
    alle_namen = sorted(list(set(r[0] for r in rows if r[0])))

    # Initialiseer session_state als die nog niet bestaat
    if "gekozen_speler_stats" not in st.session_state:
        st.session_state.gekozen_speler_stats = (
            st.session_state.naam if st.session_state.naam in alle_namen else alle_namen[0]
        )

    # Dropdown koppelen aan session_state
    st.session_state.gekozen_speler_stats = st.selectbox(
        "Kies speler voor persoonlijke statistieken:",
        alle_namen,
        index=alle_namen.index(st.session_state.gekozen_speler_stats),
        key="dropdown_persoon"
    )

    gekozen_speler_stats = st.session_state.gekozen_speler_stats

    # ---------------------------
    # TABEL 2 — Beste prestaties per categorie (persoonlijk)
    # ---------------------------
    st.subheader(f"🏆 Beste prestaties van {gekozen_speler_stats} per categorie")

    categorie_data = {
        "Double": [],
        "Triple": [],
        "Single boven": [],
        "Single onder": [],
        "Outer Bull": [],
        "Bullseye": []
    }

    for r in rows:
        naam, ts, vak, aantal = r
        aantal = int(aantal)
        if naam != gekozen_speler_stats:
            continue

        vak_l = vak.lower()
        if "double" in vak_l and "bull" not in vak_l:
            categorie_data["Double"].append((vak, aantal))
        elif "triple" in vak_l:
            categorie_data["Triple"].append((vak, aantal))
        elif "boven" in vak_l:
            categorie_data["Single boven"].append((vak, aantal))
        elif "onder" in vak_l:
            categorie_data["Single onder"].append((vak, aantal))
        elif "outer bull" in vak_l:
            categorie_data["Outer Bull"].append((vak, aantal))
        elif "bullseye" in vak_l:
            categorie_data["Bullseye"].append((vak, aantal))

    beste_rows = []
    for cat, entries in categorie_data.items():
        if entries:
            beste = min(entries, key=lambda x: x[1])
            beste_rows.append([cat, beste[0], beste[1]])
        else:
            beste_rows.append([cat, "-", "-"])

    df_beste = pd.DataFrame(beste_rows, columns=["Categorie", "Vak", "Aantal worpen"])
    st.dataframe(df_beste, use_container_width=True, hide_index=True)

    # ---------------------------
    # TABEL 3 — Beste & Slechtste worpen per vak (persoonlijk)
    # ---------------------------
    st.subheader(f"📌 Beste & slechtste worpen per vak van {gekozen_speler_stats}")

    vak_data = {}  # vak → lijst worpen

    for r in rows:
        naam, ts, vak, aantal = r
        if naam != gekozen_speler_stats:
            continue
        aantal = int(aantal)
        if vak not in vak_data:
            vak_data[vak] = []
        vak_data[vak].append(aantal)

    vak_rows = []
    for vak, aantallen in vak_data.items():
        vak_rows.append([vak, min(aantallen), max(aantallen)])

    df_vakken = pd.DataFrame(
        vak_rows,
        columns=["Vak", "Beste worpen (min)", "Slechtste worpen (max)"]
    ).sort_values("Vak")

    st.dataframe(df_vakken, use_container_width=True, hide_index=True)
