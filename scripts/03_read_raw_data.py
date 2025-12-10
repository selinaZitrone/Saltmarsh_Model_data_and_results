# -*- coding: utf-8 -*-
"""
Created December 2025

@author: Jonas Vollhüter

This script aggregates pyMANGA Population.csv outputs from different
simulation setups into unified CSV files for further analysis.

It
- merges communitys simulations with all four pft with static salinity
- merges communitys simulations with all four pft with salinity
"""

import pandas as pd

# ============================================================
# community static salinity
# ============================================================

# list of salinities [kg/kg] as strings to match folder names
salinity = ['0.035', '0.070', '0.105', '0.140']

# list to collect data frames for all salinities
temp_dfs = []

# loop over all porewater salinities
for sal in salinity:

    # list to collect all replicates for this salinity
    temp_dfs_2 = []

    # loop over replicate numbers (01–10)
    for n in range(1, 11):

        # read Population.csv for this salinity and replicate
        temp_df = pd.read_csv(
            f'../data_raw/community/static/{sal}/{n:02d}/Population.csv',
            sep='\t'
        )

        # add metadata columns identifying simulation setup
        temp_df['pfts'] = 'all'                  # community: all PFTs present
        # encode salinity in [ppt] (e.g. '0.070 kg/kg' -> 70 ppt)
        temp_df['salinity'] = int(sal.split('.')[1])
        temp_df['setup'] = 'static'              # static salinity scenario
        temp_df['n'] = n                         # replicate ID

        # store replicate data frame
        temp_dfs_2.append(temp_df)

    # combine all replicates for this salinity
    temp_dfs.append(pd.concat(temp_dfs_2))

# combine all salinity levels into one community-static data frame
df_community_static = pd.concat(temp_dfs)

# write aggregated file to raw_data folder
df_community_static.to_csv('../data/community/static/raw_data.csv',
                           index=False)


# ============================================================
# community dynamic salinity
# ============================================================


# list of dynamic salinity versions (used in folder names and as metadata)
versions = ['35_V1', '35_V2', '70_V1', '70_V2', '105_V1', '105_V2']

# list to collect data frames for all versions
temp_dfs = []

# loop over all dynamic salinity versions
for version in versions:

    # list to collect all replicates for this version
    temp_dfs_2 = []

    # loop over replicate numbers (01–09)
    for n in range(1, 10):

        # read Population.csv for this version and replicate
        temp_df = pd.read_csv(
            f'../data_raw/community/dynamic/{version}/{n:02d}/Population.csv',
            sep='\t')

        # add metadata columns identifying simulation setup
        temp_df['pfts'] = 'all'             # community: all PFTs present
        temp_df['version'] = version        # full version label
        temp_df['salinity'] = temp_df['version'].str.split('_').str[0]
        # Salinity extracted from version

        temp_df['setup'] = 'dynamic'        # dynamic salinity scenario
        temp_df['n'] = n                    # replicate ID

        # store replicate data frame
        temp_dfs_2.append(temp_df)

    # combine all replicates for this version
    temp_dfs.append(pd.concat(temp_dfs_2))

# combine all versions into one community-dynamic data frame
df_community_dynamic = pd.concat(temp_dfs)

# write aggregated file to raw_data folder
df_community_dynamic.to_csv('../data/community/dynamic/raw_data.csv',
                            index=False)
