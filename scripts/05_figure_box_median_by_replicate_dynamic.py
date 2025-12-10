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
# Load and preprocess data
# -------------------------------------------------------------------

# Load community data for dynamic salinity simulations
df = pd.read_csv('../data/community/dynamic/data.csv')

# Filter: remove seedlings (only consider plants older than 10 days)
# age is in seconds → 864000 s = 10 days
df = df[df['age'] >= 864000]

# Derived metrics
# Each row represents a single plant, so volume_per_plant equals "volume"
df["volume_per_plant"] = df["volume"]

# -------------------------------------------------------------------
# Count number of plants per timestep
# -------------------------------------------------------------------

# For each combination of version, PFT, replicate (n), and time,
# count how many plant records exist → number of plants in that community state
plant_counts = (
    df.groupby(["version", "pft", "n", "time"])
      .size()
      .reset_index(name="num_plants")
)

# Merge the plant counts back into the main dataframe
# Each plant row now carries the number of plants present at that timestep
df = pd.merge(
    df,
    plant_counts,
    on=["version", "pft", "n", "time"],
    how="left"
)

# -------------------------------------------------------------------
# Aggregation per timestep and replicate
# -------------------------------------------------------------------

# Total biovolume of all plants per timestep
# Sum "volume" for all plants in the same version × pft × replicate × time
community_volume = (
    df.groupby(["version", "pft", "n", "time"])["volume"]
      .sum()
      .reset_index(name="total_volume")
)

# Additional metrics per timestep:
# For each timestep, compute typical (median) plant-level properties
other_per_timestep = (
    df.groupby(["version", "pft", "n", "time"]).agg({
        "volume_per_plant": "median",   # median plant biovolume at this timestep
        "h_ag": "median",               # median aboveground height at this timestep
        "ag_bg_ratio": "median",        # median AG/BG ratio at this timestep
        "num_plants": "max"             # number of plants at this timestep
    })
    .reset_index()
)

# Combine community-level total_volume with per-timestep plant metrics
per_timestep = pd.merge(
    community_volume,
    other_per_timestep,
    on=["version", "pft", "n", "time"]
)

# -------------------------------------------------------------------
# Replicate-level medians over the time series
# -------------------------------------------------------------------

# For each replicate (version × pft × n), compute the median
# of the total biovolume time series
median_volume = (
    per_timestep.groupby(["version", "pft", "n"])["total_volume"]
    .median()
    .reset_index()
)

# For the same replicate, compute the median over time
# for all other metrics (based on per-timestep aggregation above)
other_metrics = (
    per_timestep.groupby(["version", "pft", "n"]).agg({
        "volume_per_plant": "median",
        "h_ag": "median",
        "ag_bg_ratio": "median",
        "num_plants": "median"
    })
    .reset_index()
)

# Merge all replicate-level medians into a single dataframe
grouped = pd.merge(
    median_volume,
    other_metrics,
    on=["version", "pft", "n"]
)

# -------------------------------------------------------------------
# Define custom ordering of versions on the x-axis
# -------------------------------------------------------------------

# Helper function to parse version strings like "35_V1", "70_V2", etc.
def parse_version(v):
    sal, idx = v.split('_V')
    return int(sal), int(idx)

# Create an ordered categorical for version so that the x-axis follows
# increasing salinity (35 before 70, etc.) and within each salinity
# increasing version index (V1, V2, ...).
version_order = sorted(grouped["version"].unique(), key=parse_version)
grouped["version"] = pd.Categorical(
    grouped["version"],
    categories=version_order,
    ordered=True
)

# -------------------------------------------------------------------
# Plotting: boxplots of replicate medians across versions and PFT
# -------------------------------------------------------------------

# Output directory for figures
output_dir = "../figures/box_replicate_medians_dynamic"
os.makedirs(output_dir, exist_ok=True)

# Metrics to plot and corresponding y-axis labels
metrics = {
    "total_volume": "Total Biovolume [m³] ($\\sum V_{{Plant}_i}$)",
    "volume_per_plant": "Biovolume per Plant [m³]",
    "h_ag": "Aboveground Height [m]",
    "ag_bg_ratio": "AG/BG Ratio [-]",
    "num_plants": "Number of Plants"
}

# Use the same color scheme for PFTs as in the static plots:
# seaborn's built-in "colorblind" palette
for metric, ylabel in metrics.items():
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        data=grouped,
        x="version",           # x-axis: salinity "version" (e.g. 35_V1, 35_V2, 70_V1, ...)
        y=metric,              # y-axis: selected metric (replicate medians)
        hue="pft",             # separate boxes by PFT
        palette="colorblind",  # same PFT colors as in the static script
        dodge=True,
        showfliers=False,      # hide outliers for cleaner presentation
        boxprops={'edgecolor': 'black', 'linewidth': 2},
        whiskerprops={'color': 'black', 'linewidth': 2},
        capprops={'color': 'black', 'linewidth': 2},
        medianprops={'color': 'black', 'linewidth': 2}
    )

    # Title and axis labels
    plt.title(f"Replicate Median of {ylabel} across dynamic salinity versions and PFT")
    plt.xlabel("Salinity version")
    plt.ylabel(ylabel)

    # Place legend outside the plot area on the right
    plt.legend(title="PFT", bbox_to_anchor=(1.05, 1), loc="upper left")

    # Adjust layout to prevent clipping of labels and legend
    plt.tight_layout()

    # Save as PNG (high resolution)
    plt.savefig(f"{output_dir}/box_{metric}_by_replicate_dynamic.png", dpi=300)

    # Optionally show the figure interactively
    plt.show()

    # Optionally save as PDF instead/in addition:
    # plt.savefig(f"{output_dir}/box_{metric}_by_replicate.pdf")

    # Close the figure to free memory when looping over multiple metrics
    plt.close()
