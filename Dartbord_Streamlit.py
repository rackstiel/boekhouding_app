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
# FUNCTIE OM NAAM OP TE SLAAN
# ----------------------
def sla_naam_op(naam):
    if not naam:
        st.warning("Vul een naam in.")
        return
    tijdstip = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Voeg rij toe: [Naam, Timestamp]
    sheet.append_row([naam, tijdstip])
    st.success(f"Naam '{naam}' opgeslagen!")

# ----------------------
# FUNCTIES VOOR DARTBORD
# ----------------------
ring_radii = {
    "Double": (9.5, 10),
    "Single boven": (6, 9.5),
    "Triple": (5.5, 6),
    "Single onder": (1.25, 5.5),
    "Outer Bull": (1.5, 1.25),
    "Bullseye": (0, 0.6)
}

moeilijkheid_per_type = {
    "Single onder": 1.5,
    "Single boven": 1,
    "Double": 3,
    "Triple": 4,
    "Outer Bull": 2.5,
    "Bullseye": 5
}

def moeilijkheid(vak):
    vak_lower = vak.lower()
    for key in moeilijkheid_per_type:
        if key.lower() in vak_lower:
            return moeilijkheid_per_type[key]
    return 1

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

def kleur(vak):
    score = moeilijkheid(vak)
    return (score/5, 1 - score/5, 0.1)

def teken_dartbord():
    sectoren = range(1, 21)
    vakken = []
    for n in sectoren:
        vakken.append(f"Single {n} onder")
        vakken.append(f"Single {n} boven")
        vakken.append(f"Double {n}")
        vakken.append(f"Triple {n}")
    vakken.append("Outer Bull")
    vakken.append("Bullseye")

    willekeurige_set = random.choices(vakken, k=20)

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
            color = kleur(vak) if vak in willekeurige_set else (0.9,0.9,0.9)
            ax.bar(
                i*theta_width,
                r_end - r_start,
                width=theta_width*0.95,
                bottom=r_start,
                color=color,
                edgecolor='black',
                linewidth=0.5
            )

    # Bulls
    for vak, radius in [("Outer Bull", ring_radii["Outer Bull"]), ("Bullseye", ring_radii["Bullseye"])]:
        r_start, r_end = radius
        color = kleur(vak) if vak in willekeurige_set else (0.9,0.9,0.9)
        circle = plt.Circle((0,0), r_end, transform=ax.transData._b, color=color, ec='black')
        ax.add_artist(circle)

    # Dartbord nummers
    dartbord_volgorde = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
                         3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
    for i, nummer in enumerate(dartbord_volgorde):
        theta = i * theta_width + theta_width/2 - (2*np.pi / 40)  # midden van de sector
        ax.text(theta, 10.7, str(nummer), ha='center', va='center', fontsize=16, fontweight='bold')

    ax.set_xticks([])
    ax.set_yticks([])
    plt.title(f"Succes {naam}!", pad=35)
    return fig

# ----------------------
# STREAMLIT APP
# ----------------------
st.title("Welkom bij de Dartbord App")

# Session state
if 'pagina' not in st.session_state:
    st.session_state.pagina = 1

if st.session_state.pagina == 1:
    naam = st.text_input("Voer je naam in:")
    start = st.button("Start")
    if start:
        if not naam:
            st.warning("Vul een naam in.")
        else:
            st.session_state.naam = naam
            sla_naam_op(naam)  # sla naam op in Google Sheet
            st.session_state.pagina = 2

if st.session_state.pagina == 2:
    st.write(f"Hallo, {st.session_state.naam}! Hier is je dartbord:")
    fig = teken_dartbord()
    st.pyplot(fig)
