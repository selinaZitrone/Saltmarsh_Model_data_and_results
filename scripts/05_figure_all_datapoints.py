# -*- coding: utf-8 -*-
"""
Created December 2025

@author: Jonas Vollhüter

tba
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from matplotlib import rcParams

# -------------------------------------------------------------------
# Global plot style and PFT color palette
# -------------------------------------------------------------------

# Use Arial with relatively small font size for dense multi-panel figures
rcParams['font.family'] = 'Arial'
rcParams['font.size'] = 9

# Colorblind-safe palette for PFTs (consistent across all scripts)
colorblind_palette = {
    1: "#0173b2",  # blue
    2: "#de8f05",  # orange
    3: "#029e73",  # green
    4: "#d55e00",  # red
}

# -------------------------------------------------------------------
# Output directory
# -------------------------------------------------------------------

output_dir = "../figures/all_datapoints"
os.makedirs(output_dir, exist_ok=True)

# -------------------------------------------------------------------
# Load and combine static / dynamic data
# -------------------------------------------------------------------

# Load static community output and construct a reference version "V0" per salinity
df_static = pd.read_csv("../data/community/static/data.csv")
df_static["version"] = df_static["salinity"].astype(str) + "_V0"

# Load dynamic community output (versions already encoded in "version")
df_dynamic = pd.read_csv("../data/community/dynamic/data.csv")

# Concatenate static and dynamic runs into one dataframe
df = pd.concat([df_static, df_dynamic], ignore_index=True)

# Make sure PFT codes are numeric (1–4)
df["pft"] = df["pft"].astype(int)

# -------------------------------------------------------------------
# Filter by salinity range and minimum plant age
# -------------------------------------------------------------------

# Keep only salinities up to 105 ppt and plants older than 10 days
# (age is in seconds: 864000 s = 10 days)
df = df[(df["salinity"] <= 105) & (df["age"] >= 864000)]

# -------------------------------------------------------------------
# Version ordering and human-readable labels
# -------------------------------------------------------------------

# Explicit ordering of all salinity × version combinations
version_order = [
    "35_V0", "35_V1", "35_V2",
    "70_V0", "70_V1", "70_V2",
    "105_V0", "105_V1", "105_V2",
]

# Map versions to descriptive scenario labels for figure axes and legends
version_label_map = {
    "35_V0": "35 ppt constant",
    "35_V1": "35 ppt seasonality",
    "35_V2": "35 ppt seasonality + tide",
    "70_V0": "70 ppt constant",
    "70_V1": "70 ppt seasonality",
    "70_V2": "70 ppt seasonality + tide",
    "105_V0": "105 ppt constant",
    "105_V1": "105 ppt seasonality",
    "105_V2": "105 ppt seasonality + tide",
}

# Keep only rows that belong to one of the defined versions
df = df[df["version"].isin(version_order)]

# Ensure that "version" follows the desired categorical order
df["version"] = pd.Categorical(
    df["version"],
    categories=version_order,
    ordered=True,
)

# Add version labels for plotting
df["version_label"] = df["version"].map(version_label_map)

# For convenience when specifying order in plots
version_label_order = [version_label_map[v] for v in version_order]

# -------------------------------------------------------------------
# AG/BG ratio subset for nicer plots
# -------------------------------------------------------------------

# Remove extreme AG/BG ratios (e.g. very large values) for visualization
df_temp = df[df["ag_bg_ratio"] < 3].copy()
df_temp["version_label"] = df_temp["version"].map(version_label_map)

# -------------------------------------------------------------------
# Violinplots: biovolume, height, AG/BG ratio (with PFT resolution)
# -------------------------------------------------------------------

# --- Biovolume with PFTs ---
plt.figure(figsize=(12, 6))
sns.violinplot(
    data=df,
    x="version_label",
    y="volume",
    hue="pft",
    palette=colorblind_palette,
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints $V_{BIO}$ per Plant")
plt.xlabel("Scenario")
plt.xticks(rotation=45)
plt.ylabel("Biovolume [m³]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_volume_withPFT.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_volume_withPFT.pdf")
plt.show()
plt.close()

# --- Aboveground height with PFTs ---
plt.figure(figsize=(12, 6))
sns.violinplot(
    data=df,
    x="version_label",
    y="h_ag",
    hue="pft",
    palette=colorblind_palette,
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints Plant Height")
plt.xlabel("Scenario")
plt.xticks(rotation=45)
plt.ylabel("$h_{ag}$ [m]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_height_withPFT.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_height_withPFT.pdf")
plt.show()
plt.close()

# --- AG/BG ratio with PFTs ---
plt.figure(figsize=(12, 6))
sns.violinplot(
    data=df_temp,
    x="version_label",
    y="ag_bg_ratio",
    hue="pft",
    palette=colorblind_palette,
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
# Reference line where AG volume equals BG volume
plt.axhline(y=1, color="black", linestyle="--")
plt.title("All Datapoints AG/BG Ratio")
plt.xlabel("Scenario")
plt.xticks(rotation=45)
plt.ylabel("AG/BG $[-]$")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_agbg_withPFT.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_agbg_withPFT.pdf")
plt.show()
plt.close()

# -------------------------------------------------------------------
# Violinplots: pooled over PFT (no PFT resolution)
# -------------------------------------------------------------------

# --- Biovolume without PFTs ---
plt.figure(figsize=(12, 6))
sns.violinplot(
    data=df,
    x="version_label",
    y="volume",
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints $V_{BIO}$ per Plant")
plt.xlabel("Scenario")
plt.xticks(rotation=45)
plt.ylabel("Biovolume [m³]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_volume_noPFT.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_volume_noPFT.pdf")
plt.show()
plt.close()

# --- Aboveground height without PFTs ---
plt.figure(figsize=(12, 6))
sns.violinplot(
    data=df,
    x="version_label",
    y="h_ag",
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints Plant Height")
plt.xlabel("Scenario")
plt.xticks(rotation=45)
plt.ylabel("$h_{ag}$ [m]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_height_noPFT.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_height_noPFT.pdf")
plt.show()
plt.close()

# --- AG/BG ratio without PFTs ---
plt.figure(figsize=(12, 6))
sns.violinplot(
    data=df_temp,
    x="version_label",
    y="ag_bg_ratio",
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.axhline(y=1, color="black", linestyle="--")
plt.title("All Datapoints AG/BG Ratio")
plt.xlabel("Scenario")
plt.xticks(rotation=45)
plt.ylabel("AG/BG $[-]$")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_agbg_noPFT.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_agbg_noPFT.pdf")
plt.show()
plt.close()

# -------------------------------------------------------------------
# Transposed violinplots (y-axis = scenario)
# -------------------------------------------------------------------

# --- Biovolume with PFTs (transposed) ---
plt.figure(figsize=(6, 12))
sns.violinplot(
    data=df,
    y="version_label",
    x="volume",
    hue="pft",
    palette=colorblind_palette,
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints $V_{BIO}$ per Plant (Transposed)")
plt.ylabel("Scenario")
plt.xlabel("Biovolume [m³]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_volume_withPFT_transposed.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_volume_withPFT_transposed.pdf")
plt.show()
plt.close()

# --- Aboveground height with PFTs (transposed) ---
plt.figure(figsize=(6, 12))
sns.violinplot(
    data=df,
    y="version_label",
    x="h_ag",
    hue="pft",
    palette=colorblind_palette,
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints Plant Height (Transposed)")
plt.ylabel("Scenario")
plt.xlabel("$h_{ag}$ [m]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_height_withPFT_transposed.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_height_withPFT_transposed.pdf")
plt.show()
plt.close()

# --- AG/BG ratio with PFTs (transposed) ---
plt.figure(figsize=(6, 12))
sns.violinplot(
    data=df_temp,
    y="version_label",
    x="ag_bg_ratio",
    hue="pft",
    palette=colorblind_palette,
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.axvline(x=1, color="black", linestyle="--")
plt.title("All Datapoints AG/BG Ratio (Transposed)")
plt.ylabel("Scenario")
plt.xlabel("AG/BG $[-]$")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_agbg_withPFT_transposed.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_agbg_withPFT_transposed.pdf")
plt.show()
plt.close()

# --- Biovolume without PFTs (transposed) ---
plt.figure(figsize=(6, 12))
sns.violinplot(
    data=df,
    y="version_label",
    x="volume",
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints $V_{BIO}$ per Plant (Transposed, no PFT)")
plt.ylabel("Scenario")
plt.xlabel("Biovolume [m³]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_volume_noPFT_transposed.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_volume_noPFT_transposed.pdf")
plt.show()
plt.close()

# --- Aboveground height without PFTs (transposed) ---
plt.figure(figsize=(6, 12))
sns.violinplot(
    data=df,
    y="version_label",
    x="h_ag",
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.title("All Datapoints Plant Height (Transposed, no PFT)")
plt.ylabel("Scenario")
plt.xlabel("$h_{ag}$ [m]")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_height_noPFT_transposed.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_height_noPFT_transposed.pdf")
plt.show()
plt.close()

# --- AG/BG ratio without PFTs (transposed) ---
plt.figure(figsize=(6, 12))
sns.violinplot(
    data=df_temp,
    y="version_label",
    x="ag_bg_ratio",
    order=version_label_order,
    dodge=True,
    linewidth=1.2,
    inner="quartile",
    scale="width",
)
plt.axvline(x=1, color="black", linestyle="--")
plt.title("All Datapoints AG/BG Ratio (Transposed, no PFT)")
plt.ylabel("Scenario")
plt.xlabel("AG/BG $[-]$")
plt.tight_layout()
plt.savefig(f"{output_dir}/violin_agbg_noPFT_transposed.png", dpi=300)
# plt.savefig(f"{output_dir}/violin_agbg_noPFT_transposed.pdf")
plt.show()
plt.close()
