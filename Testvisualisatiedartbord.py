import matplotlib.pyplot as plt
import numpy as np

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

def get_focus_display_name(vak):
    return vak

# ----------------------
# Functie voor dartbord met accent
# ----------------------
def teken_dartbord(focus_vak=None):
    sectoren = range(20)
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 10)
    theta_width = 2*np.pi / 20

    # kleurenpatroon per sector
    kleuren_pattern = [
        [(1,0,0), (0,0,0), (1,0,0), (0,0,0)],       # rood-zwart
        [(0,0.5,0), (0.96,0.96,0.86), (0,0.5,0), (0.96,0.96,0.86)]  # groen-beige
    ]

    for i, s in enumerate(sectoren):
        vakken_in_sector = [
            f"Double {s+1}",
            f"Single {s+1} boven",
            f"Triple {s+1}",
            f"Single {s+1} onder"
        ]
        # Omgekeerd zodat kleuren buiten→binnen correct zijn
        pattern = kleuren_pattern[i % 2]

        for j, vak in enumerate(vakken_in_sector):
            vak_type = get_type(vak)
            r_start, r_end = ring_radii[vak_type]

            # Accentueer focusvak
            if vak == focus_vak:
                color = (0,0,1)  # fel rood
                edge = 'gold'    # gouden rand
                lw = 2           # dikkere lijn
            else:
                color = pattern[j]
                edge = 'black'
                lw = 0.5

            ax.bar(
                i*theta_width,
                r_end - r_start,
                width=theta_width*0.95,
                bottom=r_start,
                color=color,
                edgecolor=edge,
                linewidth=lw
            )

    # Bulls
    for vak, radius in [("Outer Bull", ring_radii["Outer Bull"]), ("Bullseye", ring_radii["Bullseye"])]:
        r_start, r_end = radius
        circle_color = (0,1,0) if vak == "Outer Bull" else (1,0,0)
        # Accent voor focusvak (optioneel)
        edge_color = 'gold' if vak == focus_vak else 'black'
        lw = 2 if vak == focus_vak else 0.5
        circle = plt.Circle((0,0), r_end, transform=ax.transData._b, color=circle_color, ec=edge_color, linewidth=lw)
        ax.add_artist(circle)

    # Nummering
    for i, nummer in enumerate(dartbord_volgorde):
        theta = i * theta_width + theta_width/2 - (2*np.pi / 40)
        ax.text(theta, 10.7, str(nummer), ha='center', va='center', fontsize=12, fontweight='bold')

    ax.set_xticks([])
    ax.set_yticks([])
    plt.title(get_focus_display_name(focus_vak), pad=30, fontsize=18, fontweight='bold')
    plt.show()
teken_dartbord()
# ----------------------
# TEST: accent op Triple 1
# ----------------------
#teken_dartbord(focus_vak="Double 13")

