# -*- coding: utf-8 -*-
"""
Created December 2025

@author: Jonas Vollhüter

tba
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os

# -------------------------------------------------------------------
# Settings
# -------------------------------------------------------------------

SAVE_PDF = False  # set True to additionally save PDF versions

# Figure / style configuration
rcParams['font.family'] = 'Courier New'
sns.set_style("whitegrid")

# Output directory
output_dir = "../figures/time_series"
os.makedirs(output_dir, exist_ok=True)

# Colorblind-safe PFT color palette (consistent with other scripts)
pft_colors = {
    1: "#0173b2",  # blue
    2: "#de8f05",  # orange
    3: "#029e73",  # green
    4: "#d55e00",  # red
}

# Order of dynamic salinity scenarios (versions without V0 = static)
version_order = ['35_V1', '35_V2',
                 '70_V1', '70_V2',
                 '105_V1', '105_V2']

# -------------------------------------------------------------------
# Load and preprocess data
# -------------------------------------------------------------------

# Load dynamic community output
df = pd.read_csv('../data/community/dynamic/data.csv')

# If salinity 10 stands for 105 ppt (as in other scripts), recode it
df['salinity'] = df['salinity'].replace(10, 105)

# Keep only the three focal salinities
df = df[df['salinity'].isin([35, 70, 105])]

# Remove seedlings: only plants older than 10 days
# age is stored in seconds → 864000 s = 10 days
df = df[df['age'] >= 864000]

# Convert time from seconds to days for plotting
df['time_days'] = df['time'] / 86400.0

# Ensure PFT is integer-coded
if df['pft'].dtype == object:
    df['pft'] = df['pft'].astype(str).str.extract(r'(\d+)').astype(int)
else:
    df['pft'] = df['pft'].astype(int)

# Ensure that "version" follows the defined categorical order
df['version'] = pd.Categorical(
    df['version'],
    categories=version_order,
    ordered=True
)

# -------------------------------------------------------------------
# Per-timestep, per-replicate, per-PFT aggregation (same logic as others)
# -------------------------------------------------------------------

# For each timestep × replicate × PFT:
# - sum total biovolume,
# - compute typical plant-level metrics via median,
# - count number of plants.
per_timestep_pft = (
    df.groupby(['version', 'pft', 'n', 'time_days'])
      .agg(
          total_volume=('volume', 'sum'),       # community biovolume at this timestep
          volume_per_plant=('volume', 'median'),# median plant volume at this timestep
          ag_bg_ratio=('ag_bg_ratio', 'median'),
          h_ag=('h_ag', 'median'),
          num_plants=('volume', 'size')         # number of plant records
      )
      .reset_index()
)

# -------------------------------------------------------------------
# Helper: moving average for smoothing
# -------------------------------------------------------------------

def moving_average(series, window=5):

    return series.rolling(window=window, center=True).mean()

# -------------------------------------------------------------------
# Plot function: smoothed mean time series per version and PFT
# -------------------------------------------------------------------

def plot_smoothed_mean_timeseries_per_version(df_agg, y_column, ylabel, base_filename):

    # Mean over replicates (n) for each version × pft × time_days
    mean_df = (
        df_agg.groupby(['version', 'pft', 'time_days'])[y_column]
              .mean()
              .reset_index()
    )

    # Ensure version ordering
    mean_df['version'] = pd.Categorical(
        mean_df['version'],
        categories=version_order,
        ordered=True
    )

    # One figure per version
    for version in version_order:
        subset_df = mean_df[mean_df['version'] == version]
        if subset_df.empty:
            continue

        plt.figure(figsize=(10, 6))

        # Plot one smoothed line per PFT
        for pft in sorted(subset_df['pft'].unique()):
            sub = subset_df[subset_df['pft'] == pft].sort_values('time_days')
            if sub.empty:
                continue

            # Smooth the time series using a rolling mean
            y_smooth = moving_average(sub[y_column])

            plt.plot(
                sub['time_days'],
                y_smooth,
                label=f'PFT {pft}',
                color=pft_colors.get(pft, 'grey')
            )

        plt.xlabel('Time [days]', fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.title(f'{ylabel} – {version}', fontsize=14)
        plt.legend(title='PFT', fontsize=8)
        plt.tight_layout()

        # Save PNG (and optionally PDF) per version
        png_name = f'{base_filename}_{version}.png'
        plt.savefig(f'{output_dir}/{png_name}', bbox_inches="tight")
        if SAVE_PDF:
            pdf_name = png_name.replace('.png', '.pdf')
            plt.savefig(f'{output_dir}/{pdf_name}', bbox_inches="tight")

        plt.show()
        plt.close()

# -------------------------------------------------------------------
# Plot calls: time series per version and PFT
# -------------------------------------------------------------------

# Volume per plant (median per timestep and replicate, then mean across replicates)
plot_smoothed_mean_timeseries_per_version(
    per_timestep_pft,
    y_column='volume_per_plant',
    ylabel='Volume per Plant',
    base_filename='timeseries_volume_per_plant'
)

# AG/BG ratio
plot_smoothed_mean_timeseries_per_version(
    per_timestep_pft,
    y_column='ag_bg_ratio',
    ylabel='AG/BG Ratio',
    base_filename='timeseries_ag_bg_ratio'
)

# Aboveground height
plot_smoothed_mean_timeseries_per_version(
    per_timestep_pft,
    y_column='h_ag',
    ylabel='AG Height',
    base_filename='timeseries_height'
)

# Number of plants
plot_smoothed_mean_timeseries_per_version(
    per_timestep_pft,
    y_column='num_plants',
    ylabel='Number of Plants',
    base_filename='timeseries_num_plants'
)

# Total biovolume (community-level, per timestep)
plot_smoothed_mean_timeseries_per_version(
    per_timestep_pft,
    y_column='total_volume',
    ylabel='Total Biovolume',
    base_filename='timeseries_total_volume_by_pft'
)
