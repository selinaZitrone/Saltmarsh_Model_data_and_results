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

# -------------------------------------------------------------------
# Output directory
# -------------------------------------------------------------------

# Directory where all comparison figures will be stored
output_dir = "../figures/box_violin_replicate_medians_comparison_all"
os.makedirs(output_dir, exist_ok=True)

# -------------------------------------------------------------------
# Load and preprocess data
# -------------------------------------------------------------------

# Load community data for static and dynamic simulations
df_static = pd.read_csv("../data/community/static/data.csv")
df_dynamic = pd.read_csv("../data/community/dynamic/data.csv")

# Restrict the two df to salinities between 35 and 105
df_static = df_static[df_static["salinity"].isin([35, 70, 105])]
df_dynamic = df_dynamic[df_dynamic["salinity"].isin([35, 70, 105])]

# Add setup identifier for later comparison
df_static["setup"] = "static"
df_dynamic["setup"] = "dynamic"

# Construct a version label for static runs:
df_static["version"] = df_static["salinity"].astype(str) + "_V0"  # static reference version

# -------------------------------------------------------------------
# Filter seedlings
# -------------------------------------------------------------------

# Remove seedlings: only consider plants older than 10 days
# age is in seconds → 864000 s = 10 days
df_static = df_static[df_static["age"] >= 864000]
df_dynamic = df_dynamic[df_dynamic["age"] >= 864000]

# -------------------------------------------------------------------
# Derived plant-level metrics
# -------------------------------------------------------------------

for df in [df_static, df_dynamic]:
    # Each row corresponds to one plant; volume_per_plant equals "volume"
    df["volume_per_plant"] = df["volume"]

# -------------------------------------------------------------------
# Count number of plants per timestep
# -------------------------------------------------------------------

# For each combination of salinity × version × replicate (n) × time,
# count how many plant records exist → number of plants in that community state
plant_counts_static = (
    df_static.groupby(["salinity", "version", "n", "time"])
    .size()
    .reset_index(name="num_plants")
)

plant_counts_dynamic = (
    df_dynamic.groupby(["salinity", "version", "n", "time"])
    .size()
    .reset_index(name="num_plants")
)

# Merge the plant counts back into the main dataframes.
# Each plant row now carries the number of plants present at that timestep.
df_static = pd.merge(
    df_static,
    plant_counts_static,
    on=["salinity", "version", "n", "time"],
    how="left",
)

df_dynamic = pd.merge(
    df_dynamic,
    plant_counts_dynamic,
    on=["salinity", "version", "n", "time"],
    how="left",
)

# -------------------------------------------------------------------
# Per-timestep aggregation (community + typical plant metrics)
# -------------------------------------------------------------------

# Total biovolume per timestep:
# Sum "volume" for all plants in the same salinity × version × replicate × time
community_volume_static = (
    df_static.groupby(["salinity", "version", "n", "time"])["volume"]
    .sum()
    .reset_index(name="total_volume")
)

community_volume_dynamic = (
    df_dynamic.groupby(["salinity", "version", "n", "time"])["volume"]
    .sum()
    .reset_index(name="total_volume")
)

# Additional metrics per timestep:
# For each timestep, compute typical (median) plant-level properties
# and the number of plants present in that community state.
per_timestep_static = (
    df_static.groupby(["salinity", "version", "n", "time"])
    .agg(
        {
            "volume_per_plant": "median",  # median plant biovolume at this timestep
            "h_ag": "median",              # median aboveground height at this timestep
            "ag_bg_ratio": "median",       # median AG/BG ratio at this timestep
            "num_plants": "max",           # number of plants at this timestep
        }
    )
    .reset_index()
)

per_timestep_dynamic = (
    df_dynamic.groupby(["salinity", "version", "n", "time"])
    .agg(
        {
            "volume_per_plant": "median",
            "h_ag": "median",
            "ag_bg_ratio": "median",
            "num_plants": "max",
        }
    )
    .reset_index()
)

# Combine community-level total_volume with per-timestep plant metrics
# so that each timestep record contains both community and typical-plant values.
per_timestep_static = pd.merge(
    community_volume_static,
    per_timestep_static,
    on=["salinity", "version", "n", "time"],
)

per_timestep_dynamic = pd.merge(
    community_volume_dynamic,
    per_timestep_dynamic,
    on=["salinity", "version", "n", "time"],
)

# -------------------------------------------------------------------
# Replicate-level medians over the time series
# -------------------------------------------------------------------

# For each replicate (salinity × version × n), compute the median
# of the total biovolume time series (community-level response).
median_volume_static = (
    per_timestep_static.groupby(["salinity", "version", "n"])["total_volume"]
    .median()
    .reset_index()
)

median_volume_dynamic = (
    per_timestep_dynamic.groupby(["salinity", "version", "n"])["total_volume"]
    .median()
    .reset_index()
)

# For the same replicate, compute the median over time for all other metrics
# (based on the per-timestep aggregation above).
other_metrics_static = (
    per_timestep_static.groupby(["salinity", "version", "n"])
    .agg(
        {
            "volume_per_plant": "median",
            "h_ag": "median",
            "ag_bg_ratio": "median",
            "num_plants": "median",
        }
    )
    .reset_index()
)

other_metrics_dynamic = (
    per_timestep_dynamic.groupby(["salinity", "version", "n"])
    .agg(
        {
            "volume_per_plant": "median",
            "h_ag": "median",
            "ag_bg_ratio": "median",
            "num_plants": "median",
        }
    )
    .reset_index()
)

# Merge all replicate-level medians into static/dynamic dataframes
grouped_static = pd.merge(
    median_volume_static,
    other_metrics_static,
    on=["salinity", "version", "n"],
)

grouped_dynamic = pd.merge(
    median_volume_dynamic,
    other_metrics_dynamic,
    on=["salinity", "version", "n"],
)

# Concatenate static and dynamic into a single dataframe
grouped_all = pd.concat([grouped_static, grouped_dynamic], ignore_index=True)

# -------------------------------------------------------------------
# Ensure ordered salinity and version categories
# -------------------------------------------------------------------

# Explicit order of salinity categories for plotting
salinity_order = [35, 70, 105]
grouped_all["salinity"] = pd.Categorical(
    grouped_all["salinity"], categories=salinity_order, ordered=True
)

# Sort version labels by their numeric salinity and then by version string
version_order = sorted(
    grouped_all["version"].unique(),
    key=lambda x: (int(str(x).split("_")[0]), str(x)),
)
grouped_all["version"] = pd.Categorical(
    grouped_all["version"], categories=version_order, ordered=True
)

# -------------------------------------------------------------------
# Helper functions for secondary salinity x-axis
# -------------------------------------------------------------------

def get_salinity_group_centers(version_order_list):

    # Extract salinity value (before underscore) from each version string
    sal_list = [int(str(v).split("_")[0]) for v in version_order_list]
    unique_sals = sorted(set(sal_list))

    centers = []
    labels = []
    for s in unique_sals:
        # All positions (indices) where this salinity occurs in version_order_list
        idxs = [i for i, sv in enumerate(sal_list) if sv == s]
        if len(idxs) == 0:
            continue
        # Place the salinity label at the center of its block of versions
        center = sum(idxs) / len(idxs)
        centers.append(center)
        labels.append(str(s))
    return centers, labels


def add_bottom_salinity_axis(ax, version_order_list):

    centers, labels = get_salinity_group_centers(version_order_list)

    # Create a twin x-axis and align its limits with the primary axis
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())

    # Move the twin x-axis to the bottom and offset it downward
    ax2.xaxis.set_ticks_position("bottom")
    ax2.xaxis.set_label_position("bottom")
    ax2.spines["bottom"].set_position(("outward", 30))
    ax2.spines["top"].set_visible(False)

    # Set tick positions and labels for salinity groups
    ax2.set_xticks(centers)
    ax2.set_xticklabels(labels)
    ax2.set_xlabel("Salinity [ppt]")

    return ax2


# -------------------------------------------------------------------
# Boxplots: replicate medians per version (with salinity x-axis)
# -------------------------------------------------------------------

# Total biovolume (community scale)
plt.figure(figsize=(12, 6))
ax = sns.boxplot(
    data=grouped_all,
    x="version",
    y="total_volume",
    order=version_order,
    dodge=False,
    showfliers=False,
    linewidth=1.5,
)
plt.title("Replicate Median of Total Biovolume across Versions")
plt.xlabel("Version")
plt.ylabel("Total Biovolume [m³] ($\\sum V_{Plant_i}$)")
add_bottom_salinity_axis(ax, version_order)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "box_total_volume_by_version.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "box_total_volume_by_version.pdf"))
plt.show()
plt.close()

# Biovolume per plant
plt.figure(figsize=(12, 6))
ax = sns.boxplot(
    data=grouped_all,
    x="version",
    y="volume_per_plant",
    order=version_order,
    dodge=False,
    showfliers=False,
    linewidth=1.5,
)
plt.title("Replicate Median of Biovolume per Plant across Versions")
plt.xlabel("Version")
plt.ylabel("Biovolume per Plant [m³]")
add_bottom_salinity_axis(ax, version_order)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "box_volume_per_plant_by_version.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "box_volume_per_plant_by_version.pdf"))
plt.show()
plt.close()

# Aboveground height
plt.figure(figsize=(12, 6))
ax = sns.boxplot(
    data=grouped_all,
    x="version",
    y="h_ag",
    order=version_order,
    dodge=False,
    showfliers=False,
    linewidth=1.5,
)
plt.title("Replicate Median of Aboveground Height across Versions")
plt.xlabel("Version")
plt.ylabel("Aboveground Height [m]")
add_bottom_salinity_axis(ax, version_order)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "box_h_ag_by_version.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "box_h_ag_by_version.pdf"))
plt.show()
plt.close()

# AG/BG ratio
plt.figure(figsize=(12, 6))
ax = sns.boxplot(
    data=grouped_all,
    x="version",
    y="ag_bg_ratio",
    order=version_order,
    dodge=False,
    showfliers=False,
    linewidth=1.5,
)
plt.title("Replicate Median of AG/BG Ratio across Versions")
plt.xlabel("Version")
plt.ylabel("AG/BG Ratio [-]")
add_bottom_salinity_axis(ax, version_order)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "box_ag_bg_ratio_by_version.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "box_ag_bg_ratio_by_version.pdf"))
plt.show()
plt.close()

# Number of plants
plt.figure(figsize=(12, 6))
ax = sns.boxplot(
    data=grouped_all,
    x="version",
    y="num_plants",
    order=version_order,
    dodge=False,
    showfliers=False,
    linewidth=1.5,
)
plt.title("Replicate Median of Number of Plants across Versions")
plt.xlabel("Version")
plt.ylabel("Number of Plants")
add_bottom_salinity_axis(ax, version_order)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "box_num_plants_by_version.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "box_num_plants_by_version.pdf"))
plt.show()
plt.close()

# -------------------------------------------------------------------
# STACKED BARPLOTS
# -------------------------------------------------------------------

# Colorblind palette for PFT identifiers
colorblind_palette = {
    1: "#0173b2",  # blue
    2: "#de8f05",  # orange
    3: "#029e73",  # green
    4: "#d55e00",  # red
}

# Combine static and dynamic data after all preprocessing
df_all = pd.concat([df_static, df_dynamic], ignore_index=True)

# Ensure that PFT is an integer; extract numeric ID from labels if necessary
df_all["pft"] = df_all["pft"].astype(str).str.extract(r"(\d+)").astype(int)

# Time series for PFT-wise aggregation:
# Community- and plant-level metrics per version × replicate × time × PFT.
biovolume_ts = (
    df_all.groupby(["version", "n", "time", "pft"])["volume"]
    .sum()
    .reset_index()
)

vpp_ts = (
    df_all.groupby(["version", "n", "time", "pft"])["volume_per_plant"]
    .median()
    .reset_index()
)

height_ts = (
    df_all.groupby(["version", "n", "time", "pft"])["h_ag"]
    .median()
    .reset_index()
)

ratio_ts = (
    df_all.groupby(["version", "n", "time", "pft"])["ag_bg_ratio"]
    .median()
    .reset_index()
)

plants_ts = (
    df_all.groupby(["version", "n", "time", "pft"])
    .size()
    .reset_index(name="plant_count")
)

# ----- STACKED BARPLOTS: version × PFT (median over replicates/time) -----

# Total biovolume: median per version × PFT
biovolume_median = (
    biovolume_ts.groupby(["version", "pft"])["volume"]
    .median()
    .reset_index()
)
pivot_biovolume = (
    biovolume_median.pivot(index="version", columns="pft", values="volume")
    .fillna(0)
)
pivot_biovolume = pivot_biovolume.loc[
    sorted(pivot_biovolume.index, key=lambda x: (int(x.split("_")[0]), x))
]

plt.figure(figsize=(12, 6))
ax = pivot_biovolume.plot(
    kind="bar",
    stacked=True,
    figsize=(12, 6),
    color=[colorblind_palette.get(pft, "#999999") for pft in pivot_biovolume.columns],
)
plt.title("Stacked Barplot: Median Total Biovolume per Version and PFT")
plt.xlabel("Version")
plt.ylabel("Median Total Biovolume [m³]")
plt.legend(title="PFT")
# Add salinity axis for stacked barplot (groups of versions per salinity)
add_bottom_salinity_axis(ax, list(pivot_biovolume.index))
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "stacked_total_biovolume_by_version_pft.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "stacked_total_biovolume_by_version_pft.pdf"))
plt.show()
plt.close()

# Number of plants: median per version × PFT
plants_median = (
    plants_ts.groupby(["version", "pft"])["plant_count"]
    .median()
    .reset_index()
)
pivot_plants = (
    plants_median.pivot(index="version", columns="pft", values="plant_count")
    .fillna(0)
)
pivot_plants = pivot_plants.loc[
    sorted(pivot_plants.index, key=lambda x: (int(x.split("_")[0]), x))
]

plt.figure(figsize=(12, 6))
ax = pivot_plants.plot(
    kind="bar",
    stacked=True,
    figsize=(12, 6),
    color=[colorblind_palette.get(pft, "#999999") for pft in pivot_plants.columns],
)
plt.title("Stacked Barplot: Median Number of Plants per Version and PFT")
plt.xlabel("Version")
plt.ylabel("Median Number of Plants")
plt.legend(title="PFT")
add_bottom_salinity_axis(ax, list(pivot_plants.index))
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "stacked_num_plants_by_version_pft.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "stacked_num_plants_by_version_pft.pdf"))
plt.show()
plt.close()

# Aboveground height: median per version × PFT
height_median = (
    height_ts.groupby(["version", "pft"])["h_ag"]
    .median()
    .reset_index()
)
pivot_height = (
    height_median.pivot(index="version", columns="pft", values="h_ag")
    .fillna(0)
)
pivot_height = pivot_height.loc[
    sorted(pivot_height.index, key=lambda x: (int(x.split("_")[0]), x))
]

plt.figure(figsize=(12, 6))
ax = pivot_height.plot(
    kind="bar",
    stacked=True,
    figsize=(12, 6),
    color=[colorblind_palette.get(pft, "#999999") for pft in pivot_height.columns],
)
plt.title("Stacked Barplot: Median Aboveground Height per Version and PFT")
plt.xlabel("Version")
plt.ylabel("Median Aboveground Height [m]")
plt.legend(title="PFT")
add_bottom_salinity_axis(ax, list(pivot_height.index))
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "stacked_h_ag_by_version_pft.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "stacked_h_ag_by_version_pft.pdf"))
plt.show()
plt.close()

# -------------------------------------------------------------------
# PFT-based violin plots (median per replicate, version × PFT)
# -------------------------------------------------------------------

# Explicit version order for PFT-based plots
version_order_pft = sorted(
    df_all["version"].unique(), key=lambda x: (int(x.split("_")[0]), x)
)

# Total biovolume per replicate (median over time)
df_repl_vol = (
    biovolume_ts.groupby(["version", "pft", "n"])["volume"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_vol,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
sns.stripplot(
    data=df_repl_vol,
    x="version",
    y="median_value",
    hue="pft",
    palette=colorblind_palette,
    dodge=True,
    size=5,
    alpha=0.8,
    order=version_order_pft,
)
plt.title("Violinplot: Median Total Biovolume per PFT and Version")
plt.xlabel("Version")
plt.ylabel("Median Total Biovolume [m³]")
handles, labels = plt.gca().get_legend_handles_labels()
unique = dict(zip(labels, handles))
plt.legend(unique.values(), unique.keys(), title="PFT")
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_total_volume_by_version_pft_points.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_total_volume_by_version_pft_points.pdf"))
plt.show()
plt.close()

# Biovolume per plant per replicate
df_repl_vpp = (
    vpp_ts.groupby(["version", "pft", "n"])["volume_per_plant"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_vpp,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
sns.stripplot(
    data=df_repl_vpp,
    x="version",
    y="median_value",
    hue="pft",
    palette=colorblind_palette,
    dodge=True,
    size=5,
    alpha=0.8,
    order=version_order_pft,
)
plt.title("Violinplot: Median Biovolume per Plant per PFT and Version")
plt.xlabel("Version")
plt.ylabel("Median Biovolume per Plant [m³]")
handles, labels = plt.gca().get_legend_handles_labels()
unique = dict(zip(labels, handles))
plt.legend(unique.values(), unique.keys(), title="PFT")
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_vpp_by_version_pft_points.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_vpp_by_version_pft_points.pdf"))
plt.show()
plt.close()

# Aboveground height per replicate
df_repl_height = (
    height_ts.groupby(["version", "pft", "n"])["h_ag"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_height,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
sns.stripplot(
    data=df_repl_height,
    x="version",
    y="median_value",
    hue="pft",
    palette=colorblind_palette,
    dodge=True,
    size=5,
    alpha=0.8,
    order=version_order_pft,
)
plt.title("Violinplot: Median Aboveground Height per PFT and Version")
plt.xlabel("Version")
plt.ylabel("Median Aboveground Height [m]")
handles, labels = plt.gca().get_legend_handles_labels()
unique = dict(zip(labels, handles))
plt.legend(unique.values(), unique.keys(), title="PFT")
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_h_ag_by_version_pft_points.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_h_ag_by_version_pft_points.pdf"))
plt.show()
plt.close()

# AG/BG ratio per replicate
df_repl_ratio = (
    ratio_ts.groupby(["version", "pft", "n"])["ag_bg_ratio"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_ratio,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
sns.stripplot(
    data=df_repl_ratio,
    x="version",
    y="median_value",
    hue="pft",
    palette=colorblind_palette,
    dodge=True,
    size=5,
    alpha=0.8,
    order=version_order_pft,
)
plt.title("Violinplot: Median AG/BG Ratio per PFT and Version")
plt.xlabel("Version")
plt.ylabel("Median AG/BG Ratio [-]")
handles, labels = plt.gca().get_legend_handles_labels()
unique = dict(zip(labels, handles))
plt.legend(unique.values(), unique.keys(), title="PFT")
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_ag_bg_ratio_by_version_pft_points.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_ag_bg_ratio_by_version_pft_points.pdf"))
plt.show()
plt.close()

# Median number of plants per replicate
plants_median_full = (
    plants_ts.groupby(["version", "pft", "n"])["plant_count"]
    .median()
    .reset_index(name="median_num_plants")
)

plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=plants_median_full,
    x="version",
    y="median_num_plants",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
sns.stripplot(
    data=plants_median_full,
    x="version",
    y="median_num_plants",
    hue="pft",
    palette=colorblind_palette,
    dodge=True,
    size=5,
    alpha=0.8,
    order=version_order_pft,
)
plt.title("Violinplot: Median Number of Plants per Version and PFT")
plt.xlabel("Version")
plt.ylabel("Median Number of Plants")
plt.ylim(0, 25)
handles, labels = plt.gca().get_legend_handles_labels()
unique = dict(zip(labels, handles))
plt.legend(unique.values(), unique.keys(), title="PFT")
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_num_plants_by_version_pft_points.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_num_plants_by_version_pft_points.pdf"))
plt.show()
plt.close()

# -------------------------------------------------------------------
# Helper for overlay: mean ± SD on top of violin plots
# -------------------------------------------------------------------

def overlay_mean_sd_on_axis(ax, df_repl, value_col, version_order_list, color_palette):

    # Compute mean and SD across replicates for each version × PFT
    summary = (
        df_repl.groupby(["version", "pft"])[value_col]
        .agg(["mean", "std"])
        .reset_index()
    )

    version_list = list(version_order_list)
    pfts = sorted(summary["pft"].unique())
    n_pfts = len(pfts)

    # Horizontal offset between different PFTs at the same version
    width = 0.15

    for i, pft in enumerate(pfts):
        df_p = summary[summary["pft"] == pft].copy()

        # Map version labels to numeric positions (0, 1, 2, ...)
        x_base = [version_list.index(v) for v in df_p["version"]]

        # Apply small offsets per PFT to avoid overlapping markers
        offset = (i - (n_pfts - 1) / 2) * width
        x_positions = [x + offset for x in x_base]

        means = df_p["mean"].values
        stds = df_p["std"].values

        # Plot mean ± SD as error bars with a single point (no connecting line)
        ax.errorbar(
            x_positions,
            means,
            yerr=stds,
            fmt="o",
            capsize=4,
            markersize=5,
            linewidth=1,
            color=color_palette.get(pft, "#999999"),
            label=f"PFT {pft}",
        )

    # Build a clean legend (one entry per PFT)
    handles = []
    labels = []
    for pft in pfts:
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                linestyle="",
                color=color_palette.get(pft, "#999999"),
            )
        )
        labels.append(f"PFT {pft}")
    ax.legend(handles, labels, title="PFT")


# -------------------------------------------------------------------
# PFT-based violin plots (median per replicate, version × PFT)
#  + overlay of mean ± SD as single points with error bars
# -------------------------------------------------------------------

version_order_pft = sorted(
    df_all["version"].unique(), key=lambda x: (int(x.split("_")[0]), x)
)

# Total biovolume per replicate (median over time)
df_repl_vol = (
    biovolume_ts.groupby(["version", "pft", "n"])["volume"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_vol,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
plt.title("Violinplot: Median Total Biovolume per PFT and Version (with mean ± SD)")
plt.xlabel("Version")
plt.ylabel("Median Total Biovolume [m³]")
overlay_mean_sd_on_axis(
    ax, df_repl_vol, "median_value", version_order_pft, colorblind_palette
)
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_total_volume_by_version_pft_overlay.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_total_volume_by_version_pft_overlay.pdf"))
plt.show()
plt.close()

# Biovolume per plant per replicate
df_repl_vpp = (
    vpp_ts.groupby(["version", "pft", "n"])["volume_per_plant"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_vpp,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
plt.title("Violinplot: Median Biovolume per Plant per PFT and Version (with mean ± SD)")
plt.xlabel("Version")
plt.ylabel("Median Biovolume per Plant [m³]")
overlay_mean_sd_on_axis(
    ax, df_repl_vpp, "median_value", version_order_pft, colorblind_palette
)
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_vpp_by_version_pft_overlay.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_vpp_by_version_pft_overlay.pdf"))
plt.show()
plt.close()

# Aboveground height per replicate
df_repl_height = (
    height_ts.groupby(["version", "pft", "n"])["h_ag"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_height,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
plt.title("Violinplot: Median Aboveground Height per PFT and Version (with mean ± SD)")
plt.xlabel("Version")
plt.ylabel("Median Aboveground Height [m]")
overlay_mean_sd_on_axis(
    ax, df_repl_height, "median_value", version_order_pft, colorblind_palette
)
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_h_ag_by_version_pft_overlay.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_h_ag_by_version_pft_overlay.pdf"))
plt.show()
plt.close()

# AG/BG ratio per replicate
df_repl_ratio = (
    ratio_ts.groupby(["version", "pft", "n"])["ag_bg_ratio"]
    .median()
    .reset_index(name="median_value")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=df_repl_ratio,
    x="version",
    y="median_value",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
plt.title("Violinplot: Median AG/BG Ratio per PFT and Version (with mean ± SD)")
plt.xlabel("Version")
plt.ylabel("Median AG/BG Ratio [-]")
overlay_mean_sd_on_axis(
    ax, df_repl_ratio, "median_value", version_order_pft, colorblind_palette
)
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_ag_bg_ratio_by_version_pft_overlay.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_ag_bg_ratio_by_version_pft_overlay.pdf"))
plt.show()
plt.close()

# Median number of plants per replicate
plants_median_full = (
    plants_ts.groupby(["version", "pft", "n"])["plant_count"]
    .median()
    .reset_index(name="median_num_plants")
)
plt.figure(figsize=(12, 6))
ax = sns.violinplot(
    data=plants_median_full,
    x="version",
    y="median_num_plants",
    color="white",
    linewidth=1.2,
    inner=None,
    scale="width",
    order=version_order_pft,
)
plt.title("Violinplot: Median Number of Plants per Version and PFT (with mean ± SD)")
plt.xlabel("Version")
plt.ylabel("Median Number of Plants")
plt.ylim(0, 25)
overlay_mean_sd_on_axis(
    ax, plants_median_full, "median_num_plants", version_order_pft, colorblind_palette
)
add_bottom_salinity_axis(ax, version_order_pft)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "violin_median_num_plants_by_version_pft_overlay.png"), dpi=300)
# plt.savefig(os.path.join(output_dir, "violin_median_num_plants_by_version_pft_overlay.pdf"))
plt.show()
plt.close()
