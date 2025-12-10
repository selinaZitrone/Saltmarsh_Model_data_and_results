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

# Load community data for static and dynamic salinity simulations
df_static = pd.read_csv('../data/community/static/data.csv')
df_dynamic = pd.read_csv('../data/community/dynamic/data.csv')

# Keep only the selected salinity levels
df_static = df_static[df_static['salinity'].isin([35, 70, 105])]
df_dynamic = df_dynamic[df_dynamic['salinity'].isin([35, 70, 105])]

# Add setup identifier
df_static["setup"] = "static"
df_dynamic["setup"] = "dynamic"

# Filter: remove seedlings (only consider plants older than 10 days)
# age is in seconds → 864000 s = 10 days
df_static = df_static[df_static['age'] >= 864000]
df_dynamic = df_dynamic[df_dynamic['age'] >= 864000]

# -------------------------------------------------------------------
# Derived metrics
# -------------------------------------------------------------------

EPS = 1e-6  # small epsilon to avoid division by zero

for df in [df_static, df_dynamic]:
    # Each row represents a single plant, so volume_per_plant equals "volume"
    df["volume_per_plant"] = df["volume"]

    # AG/BG volume ratio, with BG volume clipped to avoid division by zero
    df["ag_bg_ratio"] = df["ag_volume"] / df["bg_volume"].clip(lower=EPS)

# -------------------------------------------------------------------
# Count number of plants per timestep
# -------------------------------------------------------------------

# For each combination of salinity, setup, replicate (n), and time,
# count how many plant records exist → number of plants in that community state
plant_counts_static = (
    df_static.groupby(["salinity", "setup", "n", "time"])
             .size()
             .reset_index(name="num_plants")
)

plant_counts_dynamic = (
    df_dynamic.groupby(["salinity", "setup", "n", "time"])
              .size()
              .reset_index(name="num_plants")
)

# Merge the plant counts back into the main dataframes
# Each plant row now carries the number of plants present at that timestep
df_static = pd.merge(
    df_static,
    plant_counts_static,
    on=["salinity", "setup", "n", "time"],
    how="left"
)

df_dynamic = pd.merge(
    df_dynamic,
    plant_counts_dynamic,
    on=["salinity", "setup", "n", "time"],
    how="left"
)

# -------------------------------------------------------------------
# Aggregation per timestep and replicate
# -------------------------------------------------------------------

# Total biovolume of all plants per timestep
# Sum "volume" for all plants in the same salinity × setup × replicate × time
community_volume_static = (
    df_static.groupby(["salinity", "setup", "n", "time"])["volume"]
             .sum()
             .reset_index(name="total_volume")
)

community_volume_dynamic = (
    df_dynamic.groupby(["salinity", "setup", "n", "time"])["volume"]
              .sum()
              .reset_index(name="total_volume")
)

# Additional metrics per timestep:
# For each timestep, compute typical (median) plant-level properties
per_timestep_static = (
    df_static.groupby(["salinity", "setup", "n", "time"]).agg({
        "volume_per_plant": "median",   # median plant biovolume at this timestep
        "h_ag": "median",               # median aboveground height at this timestep
        "ag_bg_ratio": "median",        # median AG/BG ratio at this timestep
        "num_plants": "max"             # number of plants at this timestep
    })
    .reset_index()
)

per_timestep_dynamic = (
    df_dynamic.groupby(["salinity", "setup", "n", "time"]).agg({
        "volume_per_plant": "median",
        "h_ag": "median",
        "ag_bg_ratio": "median",
        "num_plants": "max"
    })
    .reset_index()
)

# Combine community-level total_volume with per-timestep plant metrics
per_timestep_static = pd.merge(
    community_volume_static,
    per_timestep_static,
    on=["salinity", "setup", "n", "time"]
)

per_timestep_dynamic = pd.merge(
    community_volume_dynamic,
    per_timestep_dynamic,
    on=["salinity", "setup", "n", "time"]
)

# -------------------------------------------------------------------
# Replicate-level medians over the time series
# -------------------------------------------------------------------

# For each replicate (salinity × setup × n), compute the median
# of the total biovolume time series
median_volume_static = (
    per_timestep_static.groupby(["salinity", "setup", "n"])["total_volume"]
    .median()
    .reset_index()
)

median_volume_dynamic = (
    per_timestep_dynamic.groupby(["salinity", "setup", "n"])["total_volume"]
    .median()
    .reset_index()
)

# For the same replicate, compute the median over time
# for all other metrics (based on per-timestep aggregation above)
other_metrics_static = (
    per_timestep_static.groupby(["salinity", "setup", "n"]).agg({
        "volume_per_plant": "median",
        "h_ag": "median",
        "ag_bg_ratio": "median",
        "num_plants": "median"
    })
    .reset_index()
)

other_metrics_dynamic = (
    per_timestep_dynamic.groupby(["salinity", "setup", "n"]).agg({
        "volume_per_plant": "median",
        "h_ag": "median",
        "ag_bg_ratio": "median",
        "num_plants": "median"
    })
    .reset_index()
)

# Merge all replicate-level medians into static/dynamic dataframes
grouped_static = pd.merge(
    median_volume_static,
    other_metrics_static,
    on=["salinity", "setup", "n"]
)

grouped_dynamic = pd.merge(
    median_volume_dynamic,
    other_metrics_dynamic,
    on=["salinity", "setup", "n"]
)

# Concatenate static and dynamic into a single dataframe
grouped_all = pd.concat([grouped_static, grouped_dynamic], ignore_index=True)

# -------------------------------------------------------------------
# Ensure salinity order on the x-axis (35, 70, 105)
# -------------------------------------------------------------------

salinity_order = [35, 70, 105]
grouped_all["salinity"] = pd.Categorical(
    grouped_all["salinity"],
    categories=salinity_order,
    ordered=True
)

# -------------------------------------------------------------------
# Plotting: boxplots of replicate medians comparing static vs dynamic
# -------------------------------------------------------------------

# Output directory
output_dir = "../figures/box_replicate_medians_comparison_static_dynamic_combined"
os.makedirs(output_dir, exist_ok=True)

# Parameters to plot and corresponding y-axis labels
metrics = {
    "total_volume": "Total Biovolume [m³] ($\\sum V_{Plant_i}$)",
    "volume_per_plant": "Biovolume per Plant [m³]",
    "h_ag": "Aboveground Height [m]",
    "ag_bg_ratio": "AG/BG Ratio [-]",
    "num_plants": "Number of Plants"
}

for metric, ylabel in metrics.items():

    plt.figure(figsize=(12, 6))
    ax = sns.boxplot(
        data=grouped_all,
        x="salinity",          # x-axis: salinity levels (35, 70, 105)
        y=metric,              # y-axis: replicate-level median metric
        hue="setup",           # compare static vs dynamic
        dodge=True,
        showfliers=False,
        linewidth=1.5
    )

    # Title and axis labels
    ax.set_title(f"Replicate Median of {ylabel} across salinity and setup")
    ax.set_xlabel("Salinity [ppt]")
    ax.set_ylabel(ylabel)

    # Let seaborn handle x-ticks via the categorical salinity order

    # Save figure
    plt.tight_layout()
    plt.savefig(f"{output_dir}/box_{metric}_by_replicate_all.png", dpi=300)
    # plt.savefig(f"{output_dir}/box_{metric}_by_replicate.pdf")

    plt.show()
    plt.close()
