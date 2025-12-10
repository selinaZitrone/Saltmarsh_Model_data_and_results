# -*- coding: utf-8 -*-
"""
Created on 2025-06-17
"""

import os
import pandas as pd
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from PIL import Image
import imageio

# ===================== Domain-Parameter =====================
DOMAIN_SIZE = 1.5          # <<< Fläche in Metern (1.0 für 1x1 m, 2.0 für 2x2 m)
CELLS_PER_METER = 20       # Rasterdichte (~5 cm Zellgröße)
HALF = 0.5 # DOMAIN_SIZE / 2.0   # Mittelpunkt-Koordinate
IRES = int(CELLS_PER_METER * DOMAIN_SIZE)
JRES = int(CELLS_PER_METER * DOMAIN_SIZE)
# ============================================================

# input parameters
salinity = "140"
input_file = f"../../data_and_results_bu_20250723/data_raw/community/static_salinity/{salinity}/1/Population.csv"
# Fallback falls Verzeichnis "01" nicht existiert
if not os.path.exists(input_file):
    alt = f"../data_raw/community/static_salinity/{salinity}/1/Population.csv"
    if os.path.exists(alt):
        input_file = alt

output_folder = "../figures/videos/frames"
video_path = f"../figures/videos/{salinity}ppt_4x3.mp4"
fps = 10
image_width = 1600
image_height = 1200

# Ratio of figures
plant_width = image_width // 2
chart_width = image_width // 2
chart_height_each = image_height // 2

os.makedirs(output_folder, exist_ok=True)

# color map (Seaborn/Matplotlib "deep" palette – first four colors)
color_map = {
    1: (0.298, 0.447, 0.690),
    2: (0.866, 0.517, 0.321),
    3: (0.333, 0.659, 0.408),
    4: (0.769, 0.306, 0.322)
}

# Load data and calculate biovolume
df = pd.read_csv(input_file, sep="\t")
df["pft"] = df["plant"].apply(lambda x: int(x.split("_")[1]))
df["volume"] = np.pi * df["r_ag"]**2 * df["h_ag"] + np.pi * df["r_bg"]**2 * df["h_bg"]
time_steps = sorted(df["time"].unique())

# Sichtbarkeits-Maske global (für konsistente y-Skalen)
visible_mask_global = df["r_ag"] > 0.05
df_visible = df.loc[visible_mask_global].copy()

# Look for global maxima (mit derselben Sichtbarkeitslogik)
count_max = (
    df_visible.groupby(["time", "pft"]).size()
              .groupby("pft").max().max()
)
volume_max = (
    df_visible.groupby(["time", "pft"])["volume"].sum()
              .groupby("pft").max().max()
)

# Map Plants as Cylinders
def add_plant_cylinders(pl, group, color):
    for _, row in group.iterrows():
        if row["h_ag"] > 0.05:
            pl.add_mesh(
                pv.Cylinder(
                    center=(row["x"], row["y"], 0.5 * row["h_ag"]),
                    direction=(0, 0, 1),
                    radius=row["r_ag"],
                    height=row["h_ag"],
                    resolution=50,
                    capping=True,
                ),
                color=color,
            )
        if row["h_bg"] > 0.05:
            pl.add_mesh(
                pv.Cylinder(
                    center=(row["x"], row["y"], -0.5 * row["h_bg"]),
                    direction=(0, 0, -1),
                    radius=row["r_bg"],
                    height=row["h_bg"],
                    resolution=50,
                    capping=True,
                ),
                color="brown",
            )

# === FRAME GENERIERUNG ===
image_paths = []

for i, t in enumerate(time_steps):
    df_t = df[df["time"] == t]

    # === 3D-VISUALISIERUNG ===
    pl = pv.Plotter(off_screen=True, window_size=(plant_width, image_height))
    pl.set_background("white")

    # Bodenebene DOMAIN_SIZE x DOMAIN_SIZE
    ground = pv.Plane(
        center=(HALF, HALF, 0),
        direction=(0, 0, 1),
        i_size=DOMAIN_SIZE, j_size=DOMAIN_SIZE,
        i_resolution=IRES, j_resolution=JRES
    )
    pl.add_mesh(ground, opacity=0.4)

    # dünner Rahmen um die Fläche
    border = pv.Cube(center=(HALF, HALF, 0),
                     x_length=DOMAIN_SIZE, y_length=DOMAIN_SIZE, z_length=0.01)
    pl.add_mesh(border, style="wireframe", color="black", line_width=1)

    # Pflanzen
    for pft, group in df_t.groupby("pft"):
        color = color_map.get(int(pft), "gray")
        add_plant_cylinders(pl, group, color)

    # Kamera so setzen, dass nichts abgeschnitten wird
    z_ag = float(df_t["h_ag"].max() if len(df_t) else 0.0)
    z_bg = float(df_t["h_bg"].max() if len(df_t) else 0.0)
    z_max = max(z_ag, z_bg, 0.1)
    bounds = (0.0, DOMAIN_SIZE, 0.0, DOMAIN_SIZE, -1.05 * z_max, 1.05 * z_max)

    pl.reset_camera(bounds=bounds)
    pl.enable_parallel_projection()  # orthografisch
    pl.set_focus((HALF, HALF, 0))
    # Kamera grob proportional skaliert zur Flächengröße
    pl.set_position((HALF, -2.0 * DOMAIN_SIZE, 1.6 * DOMAIN_SIZE))
    pl.set_viewup((0, 0, 1))
    pl.camera.zoom(0.95)

    frame_path = os.path.join(output_folder, f"plant_{i:04d}.png")
    pl.screenshot(frame_path)
    pl.close()

    # === Number of Plants Figure ===
    mask = df_t["r_ag"] > 0.05
    counts = (df_t.loc[mask, "pft"]
                  .value_counts()
                  .reindex([1, 2, 3, 4], fill_value=0)
                  .sort_index())

    fig, ax = plt.subplots(figsize=(chart_width / 100, chart_height_each / 100), dpi=100)
    ax.bar(counts.index, counts.values,
           color=[color_map.get(int(p), "gray") for p in counts.index])
    ax.set_ylim(0, count_max * 1.1)
    ax.set_title("Plant Count")
    ax.set_xlabel("PFT")
    ax.set_ylabel("Count")
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels([f"PFT {p}" for p in [1, 2, 3, 4]])
    plt.tight_layout()
    chart1_path = os.path.join(output_folder, f"chart_count_{i:04d}.png")
    plt.savefig(chart1_path)
    plt.close()

    # === Biovolume Figure ===
    volumes = (df_t.loc[mask]
                  .groupby("pft")["volume"].sum()
                  .reindex([1, 2, 3, 4], fill_value=0.0))

    fig, ax = plt.subplots(figsize=(chart_width / 100, chart_height_each / 100), dpi=100)
    ax.bar(volumes.index, volumes.values,
           color=[color_map.get(int(p), "gray") for p in volumes.index])
    ax.set_ylim(0, volume_max * 1.1)
    ax.set_title("Total Volume")
    ax.set_xlabel("PFT")
    ax.set_ylabel("Volume [m³]")
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels([f"PFT {p}" for p in [1, 2, 3, 4]])
    plt.tight_layout()
    chart2_path = os.path.join(output_folder, f"chart_volume_{i:04d}.png")
    plt.savefig(chart2_path)
    plt.close()

    # Combine Figures
    plant_img = Image.open(frame_path).resize((plant_width, image_height))
    chart1_img = Image.open(chart1_path).resize((chart_width, chart_height_each))
    chart2_img = Image.open(chart2_path).resize((chart_width, chart_height_each))

    chart_combined = Image.new("RGB", (chart_width, image_height), "white")
    chart_combined.paste(chart1_img, (0, 0))
    chart_combined.paste(chart2_img, (0, chart_height_each))

    combined_img = Image.new("RGB", (image_width, image_height), "white")
    combined_img.paste(plant_img, (0, 0))
    combined_img.paste(chart_combined, (plant_width, 0))

    combined_path = os.path.join(output_folder, f"combined_{i:04d}.png")
    combined_img.save(combined_path)
    image_paths.append(combined_path)

# Create Video
with imageio.get_writer(video_path, fps=fps) as writer:
    for path in sorted(image_paths):
        writer.append_data(imageio.imread(path))
