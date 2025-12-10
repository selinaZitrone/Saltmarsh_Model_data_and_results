#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Findet automatisch alle Population.csv unter BASE_DIR (rekursiv)
und plottet in EINEM Diagramm:
  - links: ag_resources & bg_resources für zwei Pflanzen
  - rechts: r_ag & r_bg für zwei Pflanzen
Farben: Pflanze A = Orange, Pflanze B = Grün.

Robuste Pfade:
- BASE_DIR/OUTPUT_DIR werden relativ zum Speicherort dieser Datei aufgelöst.
- Debug-Ausgaben zeigen die absoluten Pfade und Existenzchecks.
"""

from pathlib import Path
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter

# ========= DEINE EINSTELLUNGEN (unverändert) =========
_BASE_DIR_RAW    = Path("../data_raw/two_plants")     # Input-Ordner
_OUTPUT_DIR_RAW  = Path("../figure/two_plants_plots") # Zielordner (Achtung: "figure" vs "figures"?)
TIME_UNIT        = "days"  # "seconds" | "hours" | "days" | "years"
PLANT_ORDER      = None    # z.B. ["Saltmarsh_1_1_000000001", "Saltmarsh_1_2_000000001"] oder None

# ========= Farben & Stil =========
COLOR_A = "tab:orange"
COLOR_B = "tab:green"
LW_MAIN = 1.8
LW_SEC  = 1.4
MS      = 4.5
MEC, MFC, MEW, ALPHA = "black", "white", 0.7, 0.95

# ========= Robuste Pfade relativ zum Skript =========
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR   = (SCRIPT_DIR / _BASE_DIR_RAW).resolve()
OUTPUT_DIR = (SCRIPT_DIR / _OUTPUT_DIR_RAW).resolve()

print(f"[DEBUG] script_dir: {SCRIPT_DIR}")
print(f"[DEBUG] BASE_DIR:   {BASE_DIR} (exists={BASE_DIR.exists()})")
print(f"[DEBUG] OUTPUT_DIR: {OUTPUT_DIR}")

if not BASE_DIR.exists():
    # Fallback: Suche nach einem Ordner "two_plants" mit Population.csv in der Nähe
    candidates = []
    for p in SCRIPT_DIR.rglob("two_plants"):
        try:
            if any(p.rglob("Population.csv")):
                candidates.append(p.resolve())
        except PermissionError:
            pass
    if candidates:
        BASE_DIR = candidates[0]
        print(f"[HINWEIS] BASE_DIR nicht gefunden, benutze Fundstelle: {BASE_DIR}")
    else:
        raise FileNotFoundError(f"BASE_DIR existiert nicht: {BASE_DIR}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ========= Hilfsfunktionen =========
def _read_table_auto(path: Path) -> pd.DataFrame:
    for sep in ("\t", ",", ";", r"\s+"):
        try:
            df = pd.read_csv(path, sep=sep)
            if {"time", "ag_resources", "bg_resources"}.issubset(df.columns):
                return df
        except Exception:
            pass
    return pd.read_csv(path)

def _convert_time(x: np.ndarray, unit: str):
    if unit == "seconds":
        return x, "Zeit [s]"
    if unit == "hours":
        return x / 3600.0, "Zeit [h]"
    if unit == "days":
        return x / (3600.0 * 24.0), "Zeit [d]"
    if unit == "years":
        return x / (3600.0 * 24.0 * 365.25), "Zeit [a]"
    return x, "Zeit"

def _ensure_two_plants(df: pd.DataFrame):
    if "plant" not in df.columns:
        raise ValueError("Erwarte eine Spalte 'plant' in der Datei.")
    uniq = df["plant"].dropna().astype(str).unique().tolist()
    if len(uniq) < 2:
        raise ValueError(f"Weniger als zwei Pflanzen gefunden: {uniq}")
    if PLANT_ORDER is not None:
        return PLANT_ORDER
    return sorted(uniq)[:2]

def _has_radii(df: pd.DataFrame) -> bool:
    return "r_ag" in df.columns and "r_bg" in df.columns

def _markevery(n: int) -> int:
    if n <= 60:  return 2
    if n <= 150: return 4
    return max(1, n // 40)

# ========= Hauptplot pro Datei =========
def plot_file(csv_path: Path) -> None:
    df = _read_table_auto(csv_path)

    need_cols = {"time", "ag_resources", "bg_resources", "plant"}
    if not need_cols.issubset(df.columns):
        missing = need_cols - set(df.columns)
        raise ValueError(f"Spalten fehlen in {csv_path.name}: {missing}")

    plantA, plantB = _ensure_two_plants(df)
    a = df[df["plant"].astype(str) == str(plantA)].sort_values("time")
    b = df[df["plant"].astype(str) == str(plantB)].sort_values("time")

    tx_a, xlabel = _convert_time(a["time"].to_numpy(dtype=float), TIME_UNIT)
    tx_b, _      = _convert_time(b["time"].to_numpy(dtype=float), TIME_UNIT)

    me_a = _markevery(len(a))
    me_b = _markevery(len(b))

    fig, axL = plt.subplots(figsize=(11.5, 6.2))
    title = str(csv_path.relative_to(BASE_DIR).as_posix())
    # Suptitel etwas tiefer, damit oben Platz für Legenden bleibt
    fig.suptitle(title, fontsize=12, y=0.94)

    # ---- linke y-Achse: Ressourcen – GRÜN zuerst, ORANGE danach (sichtbar) ----
    line_b_ag, = axL.plot(
        tx_b, b["ag_resources"], color=COLOR_B, lw=LW_MAIN, ls="-",
        marker="o", markevery=me_b, ms=MS, mec=MEC, mfc=MFC, mew=MEW,
        alpha=ALPHA, zorder=2, label=f"{plantB} AG"
    )
    line_b_bg, = axL.plot(
        tx_b, b["bg_resources"], color=COLOR_B, lw=LW_SEC, ls="--",
        marker="s", markevery=me_b, ms=MS-0.5, mec=MEC, mfc=MFC, mew=MEW,
        alpha=ALPHA, zorder=2, label=f"{plantB} BG"
    )
    line_a_ag, = axL.plot(
        tx_a, a["ag_resources"], color=COLOR_A, lw=LW_MAIN, ls="-",
        marker="o", markevery=me_a, ms=MS, mec=MEC, mfc=MFC, mew=MEW,
        alpha=ALPHA, zorder=3, label=f"{plantA} AG"
    )
    line_a_bg, = axL.plot(
        tx_a, a["bg_resources"], color=COLOR_A, lw=LW_SEC, ls="--",
        marker="s", markevery=me_a, ms=MS-0.5, mec=MEC, mfc=MFC, mew=MEW,
        alpha=ALPHA, zorder=3, label=f"{plantA} BG"
    )

    axL.set_xlabel(xlabel)
    axL.set_ylabel("ag/bg resources")
    axL.grid(True, alpha=0.35)

    # **Achsenformat sauber:** 10^n Multiplikator statt Offset „1e-…“
    sf = ScalarFormatter(useMathText=True)
    sf.set_powerlimits((0, 0))
    axL.yaxis.set_major_formatter(sf)
    axL.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useMathText=True)

    # ---- rechte y-Achse: Radien (falls vorhanden) ----
    if _has_radii(df):
        axR = axL.twinx()
        line_rb_ag, = axR.plot(
            tx_b, b["r_ag"], color=COLOR_B, lw=LW_MAIN, ls="-.", marker=None,
            alpha=0.9, zorder=1, label=f"{plantB} r_ag"
        )
        line_rb_bg, = axR.plot(
            tx_b, b["r_bg"], color=COLOR_B, lw=LW_SEC, ls=":", marker=None,
            alpha=0.9, zorder=1, label=f"{plantB} r_bg"
        )
        line_ra_ag, = axR.plot(
            tx_a, a["r_ag"], color=COLOR_A, lw=LW_MAIN, ls="-.", marker=None,
            alpha=0.95, zorder=2, label=f"{plantA} r_ag"
        )
        line_ra_bg, = axR.plot(
            tx_a, a["r_bg"], color=COLOR_A, lw=LW_SEC, ls=":", marker=None,
            alpha=0.95, zorder=2, label=f"{plantA} r_bg"
        )
        axR.set_ylabel("r_ag / r_bg [m]")

    # ===== Legenden (oberhalb der Abbildung, zentriert) =====
    plant_handles = [
        Line2D([0],[0], color=COLOR_A, lw=LW_MAIN, label=str(plantA)),
        Line2D([0],[0], color=COLOR_B, lw=LW_MAIN, label=str(plantB)),
    ]
    style_handles = [
        Line2D([0],[0], color="black", lw=LW_MAIN, ls="-",  marker="o", ms=MS, mfc="white", mec="black", mew=MEW, label="AG resources"),
        Line2D([0],[0], color="black", lw=LW_SEC,  ls="--", marker="s", ms=MS-0.5, mfc="white", mec="black", mew=MEW, label="BG resources"),
        Line2D([0],[0], color="black", lw=LW_MAIN, ls="-.", marker=None, label="r_ag (rechts)"),
        Line2D([0],[0], color="black", lw=LW_SEC,  ls=":",  marker=None, label="r_bg (rechts)"),
    ]

    # — zuerst die Größen-/Stil-Legende ganz oben —
    fig.legend(
        style_handles, [h.get_label() for h in style_handles],
        title="Größen (Linienstil/Marker)", frameon=False,
        loc="upper center", bbox_to_anchor=(0.5, 1.11), ncols=4
    )
    # — darunter die Pflanzen-Farblegende —
    fig.legend(
        plant_handles, [str(plantA), str(plantB)],
        title="Pflanzen (Farben)", frameon=False,
        loc="upper center", bbox_to_anchor=(0.5, 1.03), ncols=2
    )

    # ---- Ausgabepfade spiegeln ----
    rel = csv_path.relative_to(BASE_DIR)
    out_dir = (OUTPUT_DIR / rel.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = rel.stem
    out_png = out_dir / f"{stem}__resources_radii.png"
    out_pdf = out_dir / f"{stem}__resources_radii.pdf"

    # Platz für die zwei Zeilen Legende + Suptitel schaffen
    fig.subplots_adjust(top=0.76)
    plt.tight_layout(rect=[0, 0, 1, 0.76])

    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.show()
    plt.close()
    print(f"[OK] {rel} -> {out_png.name}, {out_pdf.name}")

# ========= Main =========
def main():
    csvs = sorted(BASE_DIR.rglob("Population.csv"))
    print(f"[DEBUG] Anzahl gefundener Population.csv: {len(csvs)}")
    if not csvs:
        raise FileNotFoundError(f"Keine Population.csv unter {BASE_DIR} gefunden.")
    for p in csvs:
        try:
            plot_file(p)
        except Exception as e:
            print(f"[FEHLER] Übersprungen: {p.relative_to(BASE_DIR)} :: {e}")

if __name__ == "__main__":
    main()
