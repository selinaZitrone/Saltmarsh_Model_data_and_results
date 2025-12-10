

# 04_data_processing.py

- auskommentierten code raus
- Why do you need to save subsets in subfolders when data.csv contains everything? Do you ever use the filtered subset files again? If not, I would remove them because they are unused duplicate data with a complex folder structure.


# 05_figure_all_datapoints.py

- df_temp used for some plots where you remove data with AG/BG ratios > 3
- The `scale` parameter has been renamed and will be removed in v0.15.0. Pass `density_norm='width'` for the same effect.
- What it shows
  - 