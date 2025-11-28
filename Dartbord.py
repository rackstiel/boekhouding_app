import random
import matplotlib.pyplot as plt
import numpy as np

# ---- Sectoren ----
sectoren = range(1, 21)  # 20 sectoren

# ---- Alle vakken ----
vakken = []
for n in sectoren:
    vakken.append(f"Single {n} onder")
    vakken.append(f"Single {n} boven")
    vakken.append(f"Double {n}")
    vakken.append(f"Triple {n}")
vakken.append("Outer Bull")
vakken.append("Bullseye")

# ---- Moeilijkheid per type ----
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

# ---- Willekeurige selectie ----
willekeurige_set = random.choices(vakken, k=20)
print("Willekeurige set:", willekeurige_set)
print("Totaal moeilijkheid:", sum(moeilijkheid(v) for v in willekeurige_set))

# ---- Ringafmetingen realistischer (van buiten naar binnen) ----
ring_radii = {
    "Double": (9.5, 10),          # dunne buitenring
    "Single boven": (6, 9.5),     # grote strook boven triple
    "Triple": (5.5, 6),           # dunne binnenring
    "Single onder": (1.25, 5.5),  # grote strook onder triple
    "Outer Bull": (1.5, 1.25),    # dunne single bull
    "Bullseye": (0, 0.6)          # bull
}

# ---- Functie om type te bepalen ----
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

# ---- Visualisatie ----
fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
ax.set_theta_offset(np.pi/2)  # 0 rad = bovenaan
ax.set_theta_direction(-1)     # tegen de klok in
ax.set_ylim(0, 10)
theta_width = 2*np.pi / 20  # 20 sectoren

# Kleurenfunctie op basis van moeilijkheid
def kleur(vak):
    score = moeilijkheid(vak)
    return (score/5, 1 - score/5, 0.1)  # groen=makkelijk, rood=moeilijk

# ---- Tekenen van de sectoren ----
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

# ---- Bulls ----
for vak, radius in [("Outer Bull", ring_radii["Outer Bull"]), ("Bullseye", ring_radii["Bullseye"])]:
    r_start, r_end = radius
    color = kleur(vak) if vak in willekeurige_set else (0.9,0.9,0.9)
    circle = plt.Circle((0,0), r_end, transform=ax.transData._b, color=color, ec='black')
    ax.add_artist(circle)

# Geen ticks
ax.set_xticks([])
ax.set_yticks([])

# ---- Dartbord nummers toevoegen ----
dartbord_volgorde = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
                     3, 19, 7, 16, 8, 11, 14, 9, 12, 5]

for i, nummer in enumerate(dartbord_volgorde):
    theta = i * theta_width + theta_width/2 - (2*np.pi / 40)  # midden van de sector
    ax.text(
        theta,
        10.7,  # net buiten double-ring
        str(nummer),
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=16,
        fontweight='bold'
    )

plt.title("Realistisch dartbord (groen=makkelijk, rood=moeilijk)", pad=30)  # titel hoger
plt.show()
