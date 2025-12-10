# -*- coding: utf-8 -*-
"""
h_bg-Visualisierung als Facet-Grid + h_ag:

Abbildung 1 (wie zuvor, erweitert):
- Zeilen = Version (static, V1, V2)
- Spalten = PFT (1..4)
- Farben  = Salinitäten (35/70/105/140)
- Links: h_bg (solid) + h_ag (-.)
- Rechts (falls vorhanden): ag_resources (--), bg_resources (:)

NEU: Abbildung 2
- Zeilen = Szenario (Version × Salinität), z. B. "static · 35 ppt", "V1 · 70 ppt", ...
- Spalten = PFT (1..4)
- Links: h_bg (solid) + h_ag (-.)
- Rechts (falls vorhanden): ag_resources (--), bg_resources (:)

NEU: Abbildung 3 (wie Abbildung 2, aber Growth/Maintenance)
- Zeilen = Szenario (Version × Salinität)
- Spalten = PFT (1..4)
- Links: growth (—) + maint (--)
- Rechts: Δ = growth − maint (:)

Ordnerstruktur relativ zur Skriptdatei:
- ../data_raw/one_plant/dynamic/{35_V1,35_V2,70_V1,70_V2,105_V1,105_V2}/pft_{1..4}/Population.csv
- ../data_raw/one_plant/static/{0.035,0.070,0.105,0.140}/pft_{1..4}/Population.csv

Ausgabe:
- ../figures/one_plant/hbg_version_rows.png / .pdf
- ../figures/one_plant/hbg_scenario_rows_pft_cols.png / .pdf
- ../figures/one_plant/hbg_scenario_rows_growth_maint.png / .pdf
"""

import os
import re
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# === Pfade/Parameter ===
BASE_DIR = Path("../data_raw/one_plant")

OUT_DIR = Path("../figures/one_plant")
PNG_OUT = OUT_DIR / "hbg_version_rows.png"
PDF_OUT = OUT_DIR / "hbg_version_rows.pdf"

# NEU: Ausgabedateien für Abbildung 2
PNG_OUT_SCEN = OUT_DIR / "hbg_scenario_rows_pft_cols.png"
PDF_OUT_SCEN = OUT_DIR / "hbg_scenario_rows_pft_cols.pdf"

# NEU: Ausgabedateien für Abbildung 3 (growth/maint + Δ)
PNG_OUT_GM = OUT_DIR / "hbg_scenario_rows_growth_maint.png"
PDF_OUT_GM = OUT_DIR / "hbg_scenario_rows_growth_maint.pdf"

# feste Ordnungen
VERSION_ORDER  = ["static", "V1", "V2"]
PFT_ORDER      = ["1", "2", "3", "4"]
SALINITY_ORDER = ["35", "70", "105", "140"]

# feste Farben je Salinität (für Abb. 1)
SAL_COLORS = {
    "35":  "#1f77b4",
    "70":  "#ff7f0e",
    "105": "#2ca02c",
    "140": "#d62728",
}

# optionale Farben je PFT (für Abb. 2 & 3 – pro Spalte konsistent)
PFT_COLORS = {
    "1": "#3b7ddd",
    "2": "#f39c12",
    "3": "#27ae60",
    "4": "#8e44ad",
}

# ---------- Pfade robust auflösen & Diagnose ----------
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    SCRIPT_DIR = Path.cwd().resolve()

BASE_DIR = (SCRIPT_DIR / BASE_DIR).resolve() if not BASE_DIR.is_absolute() else BASE_DIR
OUT_DIR  = (SCRIPT_DIR / OUT_DIR).resolve() if not OUT_DIR.is_absolute() else OUT_DIR
PNG_OUT  = (SCRIPT_DIR / PNG_OUT).resolve() if not PNG_OUT.is_absolute() else PNG_OUT
PDF_OUT  = (SCRIPT_DIR / PDF_OUT).resolve() if not PDF_OUT.is_absolute() else PDF_OUT
PNG_OUT_SCEN = (SCRIPT_DIR / PNG_OUT_SCEN).resolve() if not PNG_OUT_SCEN.is_absolute() else PNG_OUT_SCEN
PDF_OUT_SCEN = (SCRIPT_DIR / PDF_OUT_SCEN).resolve() if not PDF_OUT_SCEN.is_absolute() else PDF_OUT_SCEN
PNG_OUT_GM = (SCRIPT_DIR / PNG_OUT_GM).resolve() if not PNG_OUT_GM.is_absolute() else PNG_OUT_GM
PDF_OUT_GM = (SCRIPT_DIR / PDF_OUT_GM).resolve() if not PDF_OUT_GM.is_absolute() else PDF_OUT_GM

print(f"Aktuelles Arbeitsverzeichnis : {Path.cwd().resolve()}")
print(f"Skript liegt in            : {SCRIPT_DIR}")
print(f"Suche Daten unter BASE_DIR : {BASE_DIR}")

if not BASE_DIR.exists():
    raise SystemExit(
        f"BASE_DIR existiert nicht: {BASE_DIR}\n"
        "Bitte Pfad prüfen (relativ zur Skriptdatei) oder BASE_DIR anpassen."
    )

# ---------- Alle Population.csv sammeln ----------
csv_paths = []
for root, _, files in os.walk(BASE_DIR):
    if "Population.csv" in files:
        csv_paths.append(Path(root) / "Population.csv")

print(f"Gefundene Population.csv: {len(csv_paths)}")
for p in csv_paths[:6]:
    print(f"  - {p}")

if not csv_paths:
    raise SystemExit("Keine Population.csv gefunden – bitte Ordnerstruktur prüfen.")

# ---------- CSVs lesen & Metadaten aus Pfad extrahieren ----------
frames = []
resources_found_anywhere = False
hag_found_anywhere = False
growth_found_anywhere = False
maint_found_anywhere  = False

for fp in csv_paths:
    df = pd.read_csv(fp, sep="\t", low_memory=False)

    # Minimal-Check
    if "time" not in df.columns:
        raise SystemExit(f"Fehlende Spalte 'time' in {fp}.")
    if "h_bg" not in df.columns:
        raise SystemExit(f"Fehlende Spalte 'h_bg' in {fp}.")

    if "plant" not in df.columns:
        df["plant"] = 1  # fallback

    # PFT aus Pfad
    pft_val = "unknown"
    for part in fp.parts:
        m = re.match(r"pft_(\d+)", part)
        if m:
            pft_val = m.group(1)
            break

    # Version & Salinität aus Pfad
    parts = fp.parts
    version = "unknown"        # "static" | "V1" | "V2"
    sal_val = "unknown"        # "35" | "70" | "105" | "140"

    if "dynamic" in parts:
        i = parts.index("dynamic")
        if i + 1 < len(parts):
            m = re.match(r"(\d+)(?:_(V[12]))?$", parts[i + 1])
            if not m:
                raise SystemExit(f"Unerwarteter dynamischer Ordnername: {parts[i+1]}")
            sal_val = str(int(m.group(1)))
            version = m.group(2) if m.group(2) else "V1"
    elif "static" in parts:
        i = parts.index("static")
        if i + 1 < len(parts):
            try:
                sal_val = str(int(round(float(parts[i + 1]) * 1000)))
            except Exception as e:
                raise SystemExit(f"Konnte Salinität aus Ordner '{parts[i+1]}' nicht lesen: {e}")
        version = "static"
    else:
        raise SystemExit(f"Weder 'dynamic' noch 'static' im Pfad: {fp}")

    # gewünschte Spalten übernehmen (nur wenn vorhanden)
    cols = ["plant", "time", "h_bg"]
    if "h_ag" in df.columns:
        cols.append("h_ag")
        hag_found_anywhere = True

    for rescol in ("ag_resources", "bg_resources"):
        if rescol in df.columns:
            cols.append(rescol)
            resources_found_anywhere = True

    if "growth" in df.columns:
        cols.append("growth")
        growth_found_anywhere = True
    if "maint" in df.columns:
        cols.append("maint")
        maint_found_anywhere = True

    tmp = df[cols].copy()
    tmp["pft"]      = str(pft_val)
    tmp["salinity"] = str(sal_val)
    tmp["version"]  = str(version)
    frames.append(tmp)

# ---------- Daten zusammenführen ----------
df = pd.concat(frames, ignore_index=True)

# Robuste Zeiteinheiten-Erkennung:
sorted_times = np.sort(df["time"].unique())
if len(sorted_times) > 2:
    diffs = np.diff(sorted_times)
    med_step = float(np.median(diffs))
else:
    med_step = float(df["time"].max() if len(sorted_times) else 0.0)

if 80000 <= med_step <= 90000:
    df["time_years"] = df["time"] / (3600 * 24 * 365.25)
elif 0.5 <= med_step <= 2.0:
    df["time_years"] = df["time"] / 365.25
else:
    df["time_years"] = df["time"]

# nur die relevanten Werte behalten/ordnen
df["pft"]      = df["pft"].astype(str)
df["salinity"] = df["salinity"].astype(str)
df["version"]  = df["version"].astype(str)

print("Gefundene Versionen :", sorted(df["version"].unique()))
print("Gefundene PFTs      :", sorted(df["pft"].unique()))
print("Gefundene Salinität :", sorted(df["salinity"].unique()))
if resources_found_anywhere:
    print("Hinweis: Ressourcen-Spalten ('ag_resources', 'bg_resources') wurden gefunden und werden geplottet (rechte y-Achse in Abb. 1 & 2).")
else:
    print("Hinweis: Keine Ressourcen-Spalten gefunden – es werden nur h_bg/h_ag geplottet (links).")
if not hag_found_anywhere:
    print("Hinweis: 'h_ag' wurde in keinem Datensatz gefunden – es wird nur h_bg geplottet.")
if not (growth_found_anywhere or maint_found_anywhere):
    print("Hinweis: Weder 'growth' noch 'maint' gefunden – Abbildung 3 kann leer sein, falls keine Dateien diese Spalten enthalten.")

ver_order   = [v for v in VERSION_ORDER   if v in set(df["version"])]
pft_order   = [p for p in PFT_ORDER       if p in set(df["pft"])]
sal_present = [s for s in SALINITY_ORDER  if s in set(df["salinity"])]

if not ver_order or not pft_order or not sal_present:
    raise SystemExit(
        "Nicht genügend Dimensionen für den Plot gefunden:\n"
        f"  Versionen in Daten  : {sorted(df['version'].unique())}\n"
        f"  PFTs in Daten       : {sorted(df['pft'].unique())}\n"
        f"  Salinitäten in Daten: {sorted(df['salinity'].unique())}"
    )

# Diagnose: Zeilen pro (version, salinity, pft)
diag = (
    df.groupby(["version", "salinity", "pft"])
      .size()
      .rename("rows")
      .reset_index()
      .sort_values(["version", "salinity", "pft"])
)
print("\nZeilen je (Version, Salinität, PFT):")
print(diag.to_string(index=False))

# ----------------------------------------
# Abbildung 1: Zeilen=Version, Spalten=PFT, Farben=Salinität, rechts: Ressourcen
# ----------------------------------------
OUT_DIR.mkdir(parents=True, exist_ok=True)
n_rows, n_cols = len(ver_order), len(pft_order)
fig_w = max(12, n_cols * 3.8)
fig_h = max(6,  n_rows * 2.8)
fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_w, fig_h),
                         sharex=True, sharey=True, squeeze=False)

handles_seen = {}
for r, ver in enumerate(ver_order):
    for c, pft in enumerate(pft_order):
        ax = axes[r, c]
        sub = df[(df["version"] == ver) & (df["pft"] == pft)]
        if sub.empty:
            ax.text(0.5, 0.5, "keine Daten", ha="center", va="center", fontsize=9)
            ax.set_axis_off()
            continue

        has_ag = "ag_resources" in sub.columns
        has_bg = "bg_resources" in sub.columns
        has_hag = "h_ag" in sub.columns
        ax2 = None
        if has_ag or has_bg:
            ax2 = ax.twinx()
            ax2.set_ylabel("Ressourcen (ag/bg)")
            ax2.grid(False)

        for sal in sal_present:
            g = sub[sub["salinity"] == sal].sort_values("time_years")
            if g.empty:
                continue
            color = SAL_COLORS.get(sal, None)
            # h_bg links (solid)
            if len(g) <= 2:
                ln, = ax.plot(g["time_years"].values, g["h_bg"].values,
                              linewidth=1.6, alpha=0.95, label=f"{sal} ppt",
                              color=color, marker="o", linestyle="-")
            else:
                ln, = ax.plot(g["time_years"].values, g["h_bg"].values,
                              linewidth=1.8, alpha=0.95, label=f"{sal} ppt",
                              color=color, linestyle="-")
            if sal not in handles_seen:
                handles_seen[sal] = ln

            # h_ag links (-.) falls vorhanden
            if has_hag:
                ax.plot(g["time_years"].values, g["h_ag"].values,
                        linewidth=1.2, alpha=0.9, color=color, linestyle="-.")

            # Ressourcen rechts
            if ax2 is not None:
                if has_ag and "ag_resources" in g.columns:
                    ax2.plot(g["time_years"].values, g["ag_resources"].values,
                             linestyle="--", linewidth=1.2, alpha=0.85,
                             color=color, label="_nolegend_")
                if has_bg and "bg_resources" in g.columns:
                    ax2.plot(g["time_years"].values, g["bg_resources"].values,
                             linestyle=":", linewidth=1.2, alpha=0.85,
                             color=color, label="_nolegend_")

        if r == n_rows - 1:
            ax.set_xlabel("Zeit (Jahre)")
        if c == 0:
            ax.set_ylabel("h_bg / h_ag (m)")

        if r == 0:
            ax.set_title(f"PFT {pft}", pad=6)
        if c == 0:
            ax.text(-0.10, 1.02, f"Version: {ver}",
                    transform=ax.transAxes, ha="left", va="bottom", fontsize=10)

        ax.grid(True, linewidth=0.4, alpha=0.3)

# Globale Legenden
# (1) Salinitätenfarben für h-Kurven
if handles_seen:
    order_for_legend = [s for s in SALINITY_ORDER if s in handles_seen]
    leg_sal = fig.legend(
        handles=[handles_seen[s] for s in order_for_legend],
        labels=[f"{s} ppt" for s in order_for_legend],
        loc="upper center", ncol=len(order_for_legend),
        frameon=False, bbox_to_anchor=(0.5, 1.02)
    )
    fig.add_artist(leg_sal)

# (2) Linienstile für Größen links/rechts
style_handles = [
    Line2D([], [], color="black", linestyle="-",  linewidth=1.8, label="h_bg (links)"),
]
if hag_found_anywhere:
    style_handles.append(Line2D([], [], color="black", linestyle="-.", linewidth=1.4, label="h_ag (links)"))
if resources_found_anywhere:
    style_handles.extend([
        Line2D([], [], color="black", linestyle="--", linewidth=1.3, label="ag_resources (rechts)"),
        Line2D([], [], color="black", linestyle=":",  linewidth=1.3, label="bg_resources (rechts)"),
    ])
if style_handles:
    fig.legend(style_handles, [h.get_label() for h in style_handles],
               loc="upper right", frameon=False)

fig.suptitle("h_bg (solid) & h_ag (-.) links; Ressourcen ag/bg rechts — nach Version (Zeilen), PFT (Spalten), Salinität (Farben)", fontsize=12.5, y=0.995)
plt.tight_layout(rect=[0, 0, 1, 0.98])

fig.savefig(PNG_OUT, dpi=300)
fig.savefig(PDF_OUT)
print(f"\nGespeichert: {PNG_OUT}")
print(f"Gespeichert: {PDF_OUT}")
plt.show()

# ----------------------------------------
# Abbildung 2: Zeilen=Szenario (Version×Salinität), Spalten=PFT, rechts: Ressourcen
# ----------------------------------------
scenario_tuples = []
for ver in ver_order:
    for sal in SALINITY_ORDER:
        mask = (df["version"] == ver) & (df["salinity"] == sal)
        if mask.any():
            scenario_tuples.append((ver, sal))

n_rows2, n_cols2 = len(scenario_tuples), len(pft_order)
fig_w2 = max(12, n_cols2 * 3.8)
fig_h2 = max(6,  n_rows2 * 2.4)
fig2, axes2 = plt.subplots(n_rows2, n_cols2, figsize=(fig_w2, fig_h2),
                           sharex=True, sharey=True, squeeze=False)

for r, (ver, sal) in enumerate(scenario_tuples):
    for c, pft in enumerate(pft_order):
        ax = axes2[r, c]
        sub = df[(df["version"] == ver) & (df["salinity"] == sal) & (df["pft"] == pft)]
        if sub.empty:
            ax.text(0.5, 0.5, "keine Daten", ha="center", va="center", fontsize=9)
            ax.set_axis_off()
            continue

        has_ag = "ag_resources" in sub.columns
        has_bg = "bg_resources" in sub.columns
        has_hag = "h_ag" in sub.columns
        axr = None
        if has_ag or has_bg:
            axr = ax.twinx()
            axr.set_ylabel("Ressourcen (ag/bg)")
            axr.grid(False)

        g = sub.sort_values("time_years")
        color = PFT_COLORS.get(pft, None)

        # h_bg links (solid)
        if len(g) <= 2:
            ax.plot(g["time_years"].values, g["h_bg"].values,
                    linewidth=1.6, alpha=0.95, color=color, marker="o", linestyle="-")
        else:
            ax.plot(g["time_years"].values, g["h_bg"].values,
                    linewidth=1.8, alpha=0.95, color=color, linestyle="-")

        # h_ag links (-.) falls vorhanden
        if has_hag:
            ax.plot(g["time_years"].values, g["h_ag"].values,
                    linewidth=1.2, alpha=0.9, color=color, linestyle="-.")

        # Ressourcen rechts
        if axr is not None:
            if has_ag and "ag_resources" in g.columns:
                axr.plot(g["time_years"].values, g["ag_resources"].values,
                         linestyle="--", linewidth=1.1, alpha=0.8, color=color, label="_nolegend_")
            if has_bg and "bg_resources" in g.columns:
                axr.plot(g["time_years"].values, g["bg_resources"].values,
                         linestyle=":", linewidth=1.1, alpha=0.8, color=color, label="_nolegend_")

        if r == n_rows2 - 1:
            ax.set_xlabel("Zeit (Jahre)")
        if c == 0:
            ax.set_ylabel("h_bg / h_ag (m)")

        # Spaltenüberschrift: PFT
        if r == 0:
            ax.set_title(f"PFT {pft}", pad=6)

        # Zeilenbeschriftung: Szenario
        if c == 0:
            ax.text(-0.12, 1.02, f"Szenario: {ver} · {sal} ppt",
                    transform=ax.transAxes, ha="left", va="bottom", fontsize=10)

        ax.grid(True, linewidth=0.4, alpha=0.3)

# === Legenden für Abbildung 2 ===
# PFT-Farblegende (oben zentriert)
pft_handles = []
pft_labels  = []
for p in pft_order:
    col = PFT_COLORS.get(p, None)
    if col is None:
        continue
    h = Line2D([], [], color=col, linewidth=2, label=f"PFT {p}", linestyle="-")
    pft_handles.append(h)
    pft_labels.append(f"PFT {p}")

if pft_handles:
    leg_pft = fig2.legend(pft_handles, pft_labels,
                          loc="upper center", ncol=len(pft_handles),
                          frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig2.add_artist(leg_pft)

# Linienstile-Legende (h_bg/h_ag links, Ressourcen rechts)
style_handles2 = [
    Line2D([], [], color="black", linestyle="-",  linewidth=1.8, label="h_bg (links)"),
]
if hag_found_anywhere:
    style_handles2.append(Line2D([], [], color="black", linestyle="-.", linewidth=1.4, label="h_ag (links)"))
if resources_found_anywhere:
    style_handles2.extend([
        Line2D([], [], color="black", linestyle="--", linewidth=1.3, label="ag_resources (rechts)"),
        Line2D([], [], color="black", linestyle=":",  linewidth=1.3, label="bg_resources (rechts)"),
    ])
fig2.legend(style_handles2, [h.get_label() for h in style_handles2],
            loc="upper right", frameon=False)

fig2.suptitle("h_bg (solid) & h_ag (-.) links; Ressourcen ag/bg rechts — je PFT pro Szenario eigenes Panel", fontsize=12.5, y=0.965)
plt.tight_layout(rect=[0, 0, 1, 0.94])  # Platz für PFT-Legende oben

fig2.savefig(PNG_OUT_SCEN, dpi=300)
fig2.savefig(PDF_OUT_SCEN)
print(f"Gespeichert: {PNG_OUT_SCEN}")
print(f"Gespeichert: {PDF_OUT_SCEN}")
plt.show()

# ----------------------------------------
# Abbildung 3: Zeilen=Szenario (Version×Salinität), Spalten=PFT — growth & maint links; Δ rechts
# ----------------------------------------
if not (growth_found_anywhere or maint_found_anywhere):
    print("\nAbbildung 3 übersprungen: Weder 'growth' noch 'maint' wurden in den Daten gefunden.")
else:
    n_rows3, n_cols3 = len(scenario_tuples), len(pft_order)
    fig_w3 = max(12, n_cols3 * 3.8)
    fig_h3 = max(6,  n_rows3 * 2.4)
    fig3, axes3 = plt.subplots(n_rows3, n_cols3, figsize=(fig_w3, fig_h3),
                               sharex=True, sharey=False, squeeze=False)

    for r, (ver, sal) in enumerate(scenario_tuples):
        for c, pft in enumerate(pft_order):
            ax = axes3[r, c]
            sub = df[(df["version"] == ver) & (df["salinity"] == sal) & (df["pft"] == pft)]
            if sub.empty:
                ax.text(0.5, 0.5, "keine Daten", ha="center", va="center", fontsize=9)
                ax.set_axis_off()
                continue

            has_growth = "growth" in sub.columns
            has_maint  = "maint"  in sub.columns
            if not (has_growth or has_maint):
                ax.text(0.5, 0.5, "keine growth/maint", ha="center", va="center", fontsize=9)
                ax.set_axis_off()
                continue

            g = sub.sort_values("time_years").copy()
            color = PFT_COLORS.get(pft, None)

            # linke Achse: growth / maint
            if has_growth:
                if len(g) <= 2:
                    ax.plot(g["time_years"].values, g["growth"].values,
                            linewidth=1.6, alpha=0.95, color=color, marker="o", linestyle="-", label="growth")
                else:
                    ax.plot(g["time_years"].values, g["growth"].values,
                            linewidth=1.8, alpha=0.95, color=color, linestyle="-", label="growth")

            if has_maint:
                ax.plot(g["time_years"].values, g["maint"].values,
                        linewidth=1.3, alpha=0.9, color=color, linestyle="--", label="maint")

            # rechte Achse: Δ = growth − maint (nur wenn beide vorhanden)
            axr = None
            if has_growth and has_maint:
                axr = ax.twinx()
                axr.grid(False)
                axr.set_ylabel("Δ = growth − maint (rechts)")
                g["diff_gm"] = g["growth"] - g["maint"]
                if len(g) <= 2:
                    axr.plot(g["time_years"].values, g["diff_gm"].values,
                             linewidth=1.3, alpha=0.85, color=color, marker="o", linestyle=":", label="Δ (rechts)")
                else:
                    axr.plot(g["time_years"].values, g["diff_gm"].values,
                             linewidth=1.4, alpha=0.85, color=color, linestyle=":", label="Δ (rechts)")

            if r == n_rows3 - 1:
                ax.set_xlabel("Zeit (Jahre)")
            if c == 0:
                ax.set_ylabel("growth / maint (Modelleinheiten)")

            # Spaltenüberschrift: PFT
            if r == 0:
                ax.set_title(f"PFT {pft}", pad=6)

            # Zeilenbeschriftung: Szenario
            if c == 0:
                ax.text(-0.12, 1.02, f"Szenario: {ver} · {sal} ppt",
                        transform=ax.transAxes, ha="left", va="bottom", fontsize=10)

            ax.grid(True, linewidth=0.4, alpha=0.3)

    # PFT-Farblegende (oben zentriert) — nur Farbeinordnung
    pft_handles3, pft_labels3 = [], []
    for p in pft_order:
        col = PFT_COLORS.get(p, None)
        if col is None:
            continue
        pft_handles3.append(Line2D([], [], color=col, linewidth=2, label=f"PFT {p}", linestyle="-"))
        pft_labels3.append(f"PFT {p}")
    if pft_handles3:
        leg_pft3 = fig3.legend(pft_handles3, pft_labels3,
                               loc="upper center", ncol=len(pft_handles3),
                               frameon=False, bbox_to_anchor=(0.5, 1.02))
        fig3.add_artist(leg_pft3)

    # Linienstile-Legende (links: growth/maint; rechts: Δ)
    style_handles3 = [
        Line2D([], [], color="black", linestyle="-",  linewidth=1.8, label="growth (links)"),
        Line2D([], [], color="black", linestyle="--", linewidth=1.4, label="maint (links)"),
        Line2D([], [], color="black", linestyle=":",  linewidth=1.4, label="Δ = growth − maint (rechts)"),
    ]
    fig3.legend(style_handles3, [h.get_label() for h in style_handles3],
                loc="upper right", frameon=False)

    fig3.suptitle("growth (—) & maint (--) — Δ = growth − maint (rechte Achse) — je PFT pro Szenario eigenes Panel",
                  fontsize=12.5, y=0.965)
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    fig3.savefig(PNG_OUT_GM, dpi=300)
    fig3.savefig(PDF_OUT_GM)
    print(f"Gespeichert: {PNG_OUT_GM}")
    print(f"Gespeichert: {PDF_OUT_GM}")
    plt.show()
# %%
