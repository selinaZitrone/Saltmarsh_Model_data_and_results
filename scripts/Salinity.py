import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.pyplot import rcParams

# rcParams['font.family'] = 'Arial'
# rcParams['font.size'] = 9

# === Dateipfade ===
files = {
    "35_V1": "35_V1.csv",
    "35_V2": "35_V2.csv",
    "70_V1": "70_V1.csv",
    "70_V2": "70_V2.csv",
    "105_V1": "105_V1.csv",
    "105_V2": "105_V2.csv",
}

# === Mapping für Anzeige-Labels ===
scenario_labels = {
    "35_V1": "35 seasonality",
    "35_V2": "35 seasonality + tide",
    "70_V1": "70 seasonality",
    "70_V2": "70 seasonality + tide",
    "105_V1": "105 seasonality",
    "105_V2": "105 seasonality + tide",
}

# === Daten einlesen und zusammenführen ===
all_data = []
for name, path in files.items():
    df = pd.read_csv(os.path.join('../input_files/salinity', path))[:366]
    label = scenario_labels[name]
    df_clean = pd.DataFrame({
        "day": df["t_step"] / 86400,
        "salinity": df.iloc[:, 1],
        "scenario": label
    })
    all_data.append(df_clean)

df_long = pd.concat(all_data, ignore_index=True)

# Umrechnung in ppt
df_long['salinity'] *= 100

# === Farbpalette und Reihenfolge ===
palette = sns.color_palette("Blues", n_colors=6)
ordered_scenarios = [
    "35 seasonality", "35 seasonality + tide",
    "70 seasonality", "70 seasonality + tide",
    "105 seasonality", "105 seasonality + tide"
]
color_map = dict(zip(ordered_scenarios, palette))

# === Linienstile direkt auf Szenarien mappen ===
line_styles = {
    "35 seasonality": (4, 2),
    "35 seasonality + tide": (1, 2),
    "70 seasonality": (4, 2),
    "70 seasonality + tide": (1, 2),
    "105 seasonality": (4, 2),
    "105 seasonality + tide": (1, 2)
}

# === Plot ===
plt.figure(figsize=(12, 6))
sns.lineplot(
    data=df_long,
    x="day", y="salinity",
    hue="scenario",
    style="scenario",
    palette=color_map,
    hue_order=ordered_scenarios,
    style_order=ordered_scenarios,
    dashes=line_styles
)

plt.xlabel("Day of Year")
plt.ylabel("Porewater Salinity [ppt]")
plt.title("Annual Salinity Time Series (Six Scenarios)")
plt.grid(True)
plt.xlim(0, 360)
plt.legend(title="Scenario")
plt.tight_layout()

# === Speichern ===
plt.savefig("../figures/salinity_scenarios_dynamic.pdf")
plt.show()
