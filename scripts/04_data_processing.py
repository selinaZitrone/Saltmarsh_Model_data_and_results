# -*- coding: utf-8 -*-
"""
Created December 2025

@author: Jonas Vollhüter

tba
"""

import pandas as pd
import numpy as np
import os
from matplotlib import rcParams
rcParams['font.family'] = 'Courier New'


# ============================================================
# community static salinity
# ============================================================

# read aggregated file from script "03_read_raw_data.py"
df = pd.read_csv('../data/community/static/raw_data.csv')

# calculate volumes from plant geometries
df['ag_volume'] = np.pi * df['r_ag']**2 * df['h_ag']
df['bg_volume'] = np.pi * df['r_bg']**2 * df['h_bg']
df['volume'] = df['ag_volume'] + df['bg_volume']

# calculate aboveground - belowground ratio
df['ag_bg_ratio'] = df['ag_volume'] / df['bg_volume']

# extract PFT from plant id
df['pft'] = df['plant'].apply(lambda x: "_".join(x.split("_")[1])).astype(int)

# write dataframe as csv in data folder
os.makedirs('../data/community/static', exist_ok=True)
df.to_csv('../data/community/static/data.csv', index=False)

# loop over salinities
for salinity in [35, 70, 105, 140]:

    # create output folder
    outdir = f'../data/community/static/{salinity}'
    os.makedirs(outdir, exist_ok=True)

    # filtering the dataframe
    df_filtered = df[
        (df['setup'] == 'static') &
        (df['pfts'] == 'all') &
        (df['salinity'] == salinity)
    ]

    # write dataframe with only one salinity as csv
    df_filtered.to_csv(os.path.join(outdir, 'data.csv'), index=False)


# === COMMUNITY DYNAMIC SALINITY ===

# read aggregated file from script "03_read_raw_data.py"
df = pd.read_csv('../data/community/dynamic/raw_data.csv')

# calculate volumes from plant geometries
df['ag_volume'] = np.pi * df['r_ag']**2 * df['h_ag']
df['bg_volume'] = np.pi * df['r_bg']**2 * df['h_bg']
df['volume'] = df['ag_volume'] + df['bg_volume']

# calculate aboveground - belowground ratio
df['ag_bg_ratio'] = df['ag_volume'] / df['bg_volume']

# extract PFT from plant id
df['pft'] = df['plant'].apply(lambda x: "_".join(x.split("_")[1])).astype(int)

# write dataframe as csv in data folder
os.makedirs('../data/community/dynamic', exist_ok=True)
df.to_csv('../data/community/dynamic/data.csv', index=False)

# loop over versions
for salinity in ['35_V1', '35_V2', '70_V1', '70_V2', '105_V1', '105_V2']:

    # create output folder
    outdir = f'../data/community/dynamic/{salinity}'
    os.makedirs(outdir, exist_ok=True)

    # filtering the dataframe
    df_filtered = df[
        (df['setup'] == 'dynamic') &
        (df['pfts'] == 'all') &
        (df['salinity'] == int(salinity[:2])) &
        (df['version'] == salinity)
    ]

    df_filtered.to_csv(os.path.join(outdir, 'data.csv'), index=False)


# === MONOCULTURE STATIC SALINITY (optional, auskommentiert) ===

# df = pd.read_csv('../data/mono/static/raw_data.csv')

# df['ag_volume'] = np.pi * df['r_ag']**2 * df['h_ag']
# df['bg_volume'] = np.pi * df['r_bg']**2 * df['h_bg']
# df['volume'] = df['ag_volume'] + df['bg_volume']
# df['ag_bg_ratio'] = df['ag_volume'] / df['bg_volume']
# df['pft'] = df['plant'].apply(lambda x: "_".join(x.split("_")[:2]))

# os.makedirs('../data/mono/static', exist_ok=True)
# df.to_csv('../data/mono/static/data.csv', index=False)

# for salinity in [35, 105]:
#     for pft in ['pft_1', 'pft_2', 'pft_3', 'pft_4']:
#         outdir = f'../data/mono/static/{salinity}/{pft}'
#         os.makedirs(outdir, exist_ok=True)

#         df_gefiltert = df[
#             (df['setup'] == 'static') &
#             (df['pfts'] == pft) &
#             (df['salinity'] == salinity)
#         ]
#         df_gefiltert.to_csv(os.path.join(outdir, 'data.csv'), index=False)
