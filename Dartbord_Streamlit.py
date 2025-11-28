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
    """Sla naam, vak, aantal pijlen en timestamp op in Google Sheet."""
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
    """Kleur rood als het focusvak is, anders grijs."""
    return (1,0,0) if vak == focus_vak else (0.9,0.9,0.9)

def get_focus_display_name(vak):
    """Return het juiste type + nummer voor titel/melding."""
    if vak in ["Bullseye", "Outer Bull"]:
        return vak

    vak_parts = vak.split()
    type_vak = vak_parts[0]

    if type_vak == "Single":
        # Single boven/onder
        if vak_parts[-1].isdigit():
            nummer_in_vak = int(vak_parts[-1])
            position = ""
        else:
            nummer_in_vak = int(vak_parts[-2])
            position = vak_parts[-1]  # 'boven' of 'onder'
        echte_nummer = dartbord_volgorde[nummer_in_vak - 1]
        return f"{type_vak} {position} ({echte_nummer})".strip()
    else:
        # Double of Triple
        nummer_in_vak = int(vak_parts[1])
        echte_nummer = dartbord_volgorde[nummer_in_vak - 1]
        return f"{type_vak} {echte_nummer}"

def teken_dartbord(focus_vak):
    sectoren = range(1, 21)
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})  # originele grootte
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
if 'pagina' not in st.session_state:
    st.session_state.pagina = 1
if 'naam' not in st.session_state:
    st.session_state.naam = ""
if 'vakken' not in st.session_state:
    st.session_state.vakken = []
if 'index' not in st.session_state:
    st.session_state.index = 0
if 'pijlen' not in st.session_state:
    st.session_state.pijlen = {}
if 'timestamp' not in st.session_state:
    st.session_state.timestamp = None

# ----------------------
# Pagina 1: Naam invoer
# ----------------------
if st.session_state.pagina == 1:
    st.text_input("Voer je naam in:", key="naam_input")

    def start_app():
        if not st.session_state.naam_input:
            st.warning("Vul een naam in.")
        else:
            st.session_state.naam = st.session_state.naam_input
            st.session_state.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alle_vakken = []
            for n in range(1,21):
                alle_vakken.extend([f"Double {n}", f"Single {n} boven", f"Triple {n}", f"Single {n} onder"])
            alle_vakken.extend(["Outer Bull","Bullseye"])
            st.session_state.vakken = random.sample(alle_vakken, 5)
            st.session_state.index = 0
            st.session_state.pagina = 2

    st.button("Start", on_click=start_app)

# ----------------------
# Pagina 2: Step-by-step vakjes
# ----------------------
if st.session_state.pagina == 2:
    idx = st.session_state.index
    if idx >= len(st.session_state.vakken):
        st.success("Je hebt alle vakken voltooid!")
    else:
        focus_vak = st.session_state.vakken[idx]
        fig = teken_dartbord(focus_vak)

        # Centered column voor compacte weergave
        col1, col2, col3 = st.columns([1,6,1])
        with col2:
            st.pyplot(fig, use_container_width=False)

        # Number input (min 1)
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

        # Button callback
        def volgende_vak():
            aantal_widget = st.session_state[key_input]
            if aantal_widget <= 0:
                st.warning("Aantal pijlen moet minimaal 1 zijn.")
                return
            sla_data_op(st.session_state.naam, focus_vak, aantal_widget, st.session_state.timestamp)
            st.session_state.pijlen[key_input] = aantal_widget
            st.session_state.index += 1

        st.button("Volgende", on_click=volgende_vak)
