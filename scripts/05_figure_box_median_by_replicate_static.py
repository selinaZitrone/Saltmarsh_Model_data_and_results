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

# Load community data for static salinity simulations
df = pd.read_csv('../data/community/static/data.csv')

# Filter: remove seedlings (only consider plants older than 10 days)
# age is in seconds → 864000 s = 10 days
df = df[df['age'] >= 864000]

# Derived metric: volume per plant
# Each row represents a single plant, so volume_per_plant equals "volume"
df["volume_per_plant"] = df["volume"]

# -------------------------------------------------------------------
# Count number of plants per timestep
# -------------------------------------------------------------------

# For each combination of salinity, PFT, replicate (n), and time,
# count how many plant records exist → number of plants in that community state
plant_counts = (
    df.groupby(["salinity", "pft", "n", "time"])
      .size()
      .reset_index(name="num_plants")
)

# Merge the plant counts back into the main dataframe
# Each plant row now carries the number of plants present at that timestep
df = pd.merge(
    df,
    plant_counts,
    on=["salinity", "pft", "n", "time"],
    how="left"
)

# -------------------------------------------------------------------
# Aggregation per timestep and replicate
# -------------------------------------------------------------------

# Total biovolume of all plants per timestep
# Sum "volume" for all plants in the same salinity × pft × replicate × time
community_volume = (
    df.groupby(["salinity", "pft", "n", "time"])["volume"]
      .sum()
      .reset_index(name="total_volume")
)

# Additional metrics per timestep:
# For each timestep, compute typical (median) plant-level properties
other_per_timestep = (
    df.groupby(["salinity", "pft", "n", "time"]).agg({
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
    on=["salinity", "pft", "n", "time"]
)

# -------------------------------------------------------------------
# Replicate-level medians over the time series
# -------------------------------------------------------------------

# For each replicate (salinity × pft × n), compute the median
# of the total biovolume time series
median_volume = (
    per_timestep.groupby(["salinity", "pft", "n"])["total_volume"]
    .median()
    .reset_index()
)

# For the same replicate, compute the median over time
# for all other metrics (based on per-timestep aggregation above)
other_metrics = (
    per_timestep.groupby(["salinity", "pft", "n"]).agg({
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
    on=["salinity", "pft", "n"]
)

# -------------------------------------------------------------------
# Plotting: boxplots of replicate medians across salinity and PFT
# -------------------------------------------------------------------

# Output directory for figures
output_dir = "../figures/box_replicate_medians_static"
os.makedirs(output_dir, exist_ok=True)

# Metrics to plot and corresponding y-axis labels
metrics = {
    "total_volume": "Total Biovolume [m³] ($\\sum V_{{Plant}_i}$)",
    "volume_per_plant": "Biovolume per Plant [m³]",
    "h_ag": "Aboveground Height [m]",
    "ag_bg_ratio": "AG/BG Ratio [-]",
    "num_plants": "Number of Plants"
}

# Create one boxplot per metric
# Each box shows the distribution of replicate medians
# across salinities and PFTs
for metric, ylabel in metrics.items():
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        data=grouped,
        x="salinity",          # x-axis: salinity levels
        y=metric,              # y-axis: selected metric (replicate medians)
        hue="pft",             # separate boxes by PFT
        palette="colorblind",  # colorblind-friendly palette
        dodge=True,
        showfliers=False,      # hide outliers for cleaner presentation
        boxprops={'edgecolor': 'black', 'linewidth': 2},
        whiskerprops={'color': 'black', 'linewidth': 2},
        capprops={'color': 'black', 'linewidth': 2},
        medianprops={'color': 'black', 'linewidth': 2}
    )

    # Title and axis labels
    plt.title(f"Replicate Median of {ylabel} across Salinity and PFT")
    plt.xlabel("Salinity [ppt]")
    plt.ylabel(ylabel)

    # Place legend outside the plot area on the right
    plt.legend(title="PFT", bbox_to_anchor=(1.05, 1), loc="upper left")

    # Adjust layout to prevent clipping of labels and legend
    plt.tight_layout()

    # Save as PNG (high resolution)
    plt.savefig(f"{output_dir}/box_{metric}_by_replicate_static.png", dpi=300)

    # Optionally show the figure interactively
    plt.show()

    # Optionally save as PDF instead/in addition:
    # plt.savefig(f"{output_dir}/box_{metric}_by_replicate.pdf")

    # Close the figure to free memory when looping over multiple metrics
    plt.close()
