#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kalibrierung der maintenance-Faktoren für vier PFTs
so, dass am Ende (nach N_DAYS) h_ag für alle PFTs gleich hoch ist.

Basis:
- Gleichungen aus der Saltmarsh-Klasse (equation_new)
- Startwerte (Geometrie + Parameter) kommen 1:1 aus createPlant()
- PFT1 dient als Referenz (maint_factor bekannt = 1.5e-6)
- Für PFT2–PFT4 wird der maint_factor per Binärsuche so gewählt,
  dass das finale h_ag dem Referenz-h_ag entspricht.
"""

import numpy as np

# =====================================================================
# createPlant() wie von dir vorgegeben
# =====================================================================

def createPlant():
    geometry = {}
    parameter = {}

    parameter["sun_c"] = 1361
    parameter["water_c"] = 1.5

    geometry["r_ag"] = 0.05
    geometry["r_ag_ic"] = 0.05
    geometry["h_ag"] = 0.1

    geometry["r_bg"] = 0.05
    geometry["r_bg_ic"] = 0.05
    geometry["h_bg"] = 0.1

    geometry["volume_ic"] = 0.0007853975

    parameter["maint_factor"] = 1.5e-6
    parameter["growth_factor"] = 5e-9
    parameter["w_b_a"] = 0.5
    parameter["w_ag"] = 0.5
    parameter["w_bg"] = 0.5

    parameter["r_salinity"] = "forman"
    # resource module FON
    parameter["aa"] = 10
    parameter["bb"] = 1
    parameter["fmin"] = 0.1
    parameter["salt_effect_d"] = -0.045
    parameter["salt_effect_ui"] = 60

    return geometry, parameter


# =====================================================================
# Vereinfachte Saltmarsh-Klasse mit deinen Gleichungen
# =====================================================================

class SimpleSaltmarsh:
    def __init__(self, parameter, geometry):
        """
        parameter : dict
            Muss u.a. enthalten:
            - 'maint_factor'
            - 'sun_c'
            - 'water_c'
            - 'growth_factor'
            - 'w_b_a'
            - 'w_ag'
            - 'w_bg'

        geometry : dict
            Muss u.a. enthalten:
            - 'r_ag', 'h_ag', 'r_bg', 'h_bg'
            - 'r_ag_ic', 'r_bg_ic', 'volume_ic'
        """
        self.parameter = parameter.copy()

        # Geometrie
        self.r_ag = geometry["r_ag"]
        self.h_ag = geometry["h_ag"]
        self.r_bg = geometry["r_bg"]
        self.h_bg = geometry["h_bg"]
        self.r_ag_ic = geometry["r_ag_ic"]
        self.r_bg_ic = geometry["r_bg_ic"]
        self.volume_ic = geometry["volume_ic"]

        # Platzhalter
        self.time = 0.0
        self.w_h_bg = 0
        self.w_r_bg = 0
        self.w_h_ag = 0
        self.w_r_ag = 0

        # Ressourcenfaktoren
        self.ag_factor = 1.0
        self.bg_factor = 1.0

    # -----------------------------
    # Methoden wie in deiner Klasse
    # -----------------------------

    def prepareNextTimeStep(self, t_ini, t_end):
        """
        1:1 aus deiner Saltmarsh-Klasse übernommen.
        """
        self.time = t_end - t_ini  # Duration of timestep in seconds

        # Reset growth weight variables (used to store deltas)
        self.w_h_bg = 0  # Change in belowground height
        self.w_r_bg = 0  # Change in belowground radius
        self.w_h_ag = 0  # Change in aboveground height
        self.w_r_ag = 0  # Change in aboveground radius

    def plantVolume(self):
        """
        1:1 aus deiner Klasse übernommen.
        """
        self.V_ag = np.pi * self.r_ag ** 2 * self.h_ag  # [m^3]
        self.V_bg = np.pi * self.r_bg ** 2 * self.h_bg  # [m^3]
        self.r_V_ag_bg = self.V_ag / max(self.V_bg, 1e-6)  # [-]
        self.volume = self.V_ag + self.V_bg  # [m^3]

    def plantMaintenance(self):
        """
        1:1 aus deiner Klasse übernommen.
        """
        self.maint = self.volume * self.parameter["maint_factor"] * self.time  # [m³]

    def agResources(self):
        """
        1:1 aus deiner Klasse übernommen.
        """
        self.ag_resources = (
            self.ag_factor
            * np.pi
            * self.r_ag ** 2
            * self.parameter["sun_c"]
            * self.time
        )  # [J]

    def bgResources(self):
        """
        1:1 aus deiner Klasse übernommen,
        aber mit Schutz vor Division durch 0.
        """
        denom = max(self.h_ag + 0.5 * self.h_bg, 1e-9)

        self.bg_resources = (
            self.bg_factor
            * np.pi
            * self.r_bg ** 2
            * self.h_bg
            * self.parameter["sun_c"]
            * self.parameter["water_c"]
            * 1.0 / denom
            * self.time
        )  # [J]

    def growthResources(self):
        """
        1:1 aus deiner Klasse übernommen.
        """
        self.available_resources = min(self.ag_resources, self.bg_resources)  # [J]
        self.growth_pot = (
            self.available_resources * self.parameter["growth_factor"]
        )  # [m³]
        self.grow = self.growth_pot - self.maint  # [m³]

    def plantGrowth(self):
        """
        1:1 Gleichungen & Variablen wie in deiner Klasse.
        """
        ag = self.ag_factor  # [-]
        bg = self.bg_factor  # [-]

        # Resource ratio from AG perspective (normalized between 0 and 1)
        self.ratio_ag = np.clip(ag / (ag + bg + 1e-22), 1e-6, 0.999999)

        if self.grow > 0:
            # Compare current AG/BG volume ratio with "optimal" range
            ratio_vol = self.V_ag / max(self.V_bg, 1e-6)

            # Shift AG/BG allocation depending on mismatch between current ratio and resource ratio
            self.adjustment = 0.5 - self.ratio_ag

            if ratio_vol > 2.5 and self.adjustment < 0:
                pass  # AG volume too high → reduce AG growth
            elif ratio_vol < 0.15 and self.adjustment > 0:
                pass  # BG volume too high → reduce BG growth
            elif 0.15 <= ratio_vol <= 2.5:
                pass  # within target zone
            else:
                self.adjustment = 0  # prevent maladaptive adjustment

            # Compute AG/BG allocation weight
            self.w_ratio_ag_bg = self.parameter["w_b_a"] * (1 - self.adjustment)

            # Split net growth based on calculated ratio
            V_ag_incr = self.grow * (1 - self.w_ratio_ag_bg)
            V_bg_incr = self.grow * self.w_ratio_ag_bg

        else:
            V_ag_incr = self.grow * 0.5
            V_bg_incr = self.grow * 0.5

        self.V_ag += V_ag_incr
        self.V_bg += V_bg_incr

        # Recalculate plant geometry (cylinder geometry → invert volume formula)

        self.V_ag = max(self.V_ag, 0.0)
        self.V_bg = max(self.V_bg, 0.0)

        self.h_ag = (self.V_ag / (np.pi * self.parameter["w_ag"] ** 2)) ** (1.0 / 3.0)
        self.r_ag = self.parameter["w_ag"] * self.h_ag
        self.h_bg = (self.V_bg / (np.pi * self.parameter["w_bg"] ** 2)) ** (1.0 / 3.0)
        self.r_bg = self.parameter["w_bg"] * self.h_bg

    # -------------------------------------------------

    def progress_one_timestep(self, aboveground_factor, belowground_factor, dt):
        """
        Entspricht inhaltlich deiner progressPlant-Logik,
        reduziert auf das, was wir für die Kalibrierung brauchen.
        """
        # prepareNextTimeStep
        self.prepareNextTimeStep(0.0, dt)

        # Ressourcenfaktoren setzen
        self.ag_factor = aboveground_factor
        self.bg_factor = belowground_factor

        # 1: Volumen
        self.plantVolume()

        # 2: Maintenance
        self.plantMaintenance()

        # 3: Ressourcen
        self.agResources()
        self.bgResources()

        # 4: Wachstum aus Ressourcen
        self.growthResources()

        # 5: Geometrisches Wachstum
        self.plantGrowth()

        # 6: Volumen nach Wachstum
        self.plantVolume()


# =====================================================================
# Simulations- und Kalibrierfunktionen
# =====================================================================

def simulate_h_ag(bg_factor, maint_factor, n_steps, dt, parameter_base, geometry_init, ag_factor=1.0):
    """
    Simuliert eine Pflanze über n_steps Zeitschritte und gibt h_ag am Ende zurück.
    Nutzt exakt die Gleichungen der SimpleSaltmarsh-Klasse.
    """
    # Parameter kopieren und maint_factor setzen
    parameter = parameter_base.copy()
    parameter["maint_factor"] = maint_factor

    # Geometrie kopieren
    geometry = geometry_init.copy()

    sm = SimpleSaltmarsh(parameter, geometry)

    for _ in range(n_steps):
        sm.progress_one_timestep(ag_factor, bg_factor, dt)

    return sm.h_ag


def calibrate_maintenance_for_bg_factor(bg_factor,
                                        target_h_ag,
                                        n_steps,
                                        dt,
                                        parameter_base,
                                        geometry_init,
                                        ag_factor=1.0,
                                        f_min=1e-8,
                                        f_max=1e-4,
                                        tol_h=1e-4,
                                        max_iter=60):
    """
    Binärsuche auf maint_factor, sodass das finale h_ag möglichst
    nah an target_h_ag liegt.
    """
    # Werte am Rand des Intervalls
    h_low = simulate_h_ag(bg_factor, f_min, n_steps, dt, parameter_base, geometry_init, ag_factor)
    h_high = simulate_h_ag(bg_factor, f_max, n_steps, dt, parameter_base, geometry_init, ag_factor)

    # Wenn Relation invertiert: tauschen
    if h_low < h_high:
        f_min, f_max = f_max, f_min
        h_low, h_high = h_high, h_low

    f_best = None
    h_best = None

    for _ in range(max_iter):
        f_mid = 0.5 * (f_min + f_max)
        h_mid = simulate_h_ag(bg_factor, f_mid, n_steps, dt, parameter_base, geometry_init, ag_factor)

        f_best, h_best = f_mid, h_mid

        if abs(h_mid - target_h_ag) < tol_h:
            break

        # Pflanze zu hoch -> mehr Maintenance
        if h_mid > target_h_ag:
            f_min = f_mid
        # Pflanze zu klein -> weniger Maintenance
        else:
            f_max = f_mid

    return f_best, h_best


# =====================================================================
# Hauptprogramm: 4 PFTs auf gemeinsames h_ag kalibrieren
# =====================================================================

if __name__ == "__main__":
    # Zeitschema
    DT = 60.0 * 60.0 * 24.0   # [s] Zeitschritt (1 Tag)
    N_DAYS = 200
    N_STEPS = N_DAYS

    # Startgeometrie und Basisparameter aus createPlant()
    geometry_init, parameter_base = createPlant()

    # bg_factors der vier PFTs
    pfts = {
        "pft_1": {
            "bg_factor": 0.389360756,
        },
        "pft_2": {
            "bg_factor": 0.5,
        },
        "pft_3": {
            "bg_factor": 0.610639274,
        },
        "pft_4": {
            "bg_factor": 0.710949481,
        },
    }

    # Referenz-PFT (PFT1 mit maint_factor = 1.5e-6 aus createPlant)
    reference_pft = "pft_1"
    ref_bg = pfts[reference_pft]["bg_factor"]
    ref_maint = parameter_base["maint_factor"]

    target_h_ag = simulate_h_ag(
        bg_factor=ref_bg,
        maint_factor=ref_maint,
        n_steps=N_STEPS,
        dt=DT,
        parameter_base=parameter_base,
        geometry_init=geometry_init,
        ag_factor=1.0,
    )

    print(f"Referenz: {reference_pft}")
    print(f"  bg_factor     = {ref_bg:.9f}")
    print(f"  maint_factor  = {ref_maint:.6e}")
    print(f"  Ziel-h_ag     = {target_h_ag:.6f} m\n")

    # Kalibrierung für alle 4 PFTs
    results = {}

    for name, info in pfts.items():
        bg = info["bg_factor"]

        if name == reference_pft:
            # Referenz unverändert übernehmen
            results[name] = (bg, ref_maint, target_h_ag)
            print(f"{name}: (Referenz)")
            print(f"  bg_factor     = {bg:.9f}")
            print(f"  maint_factor  = {ref_maint:.6e}")
            print(f"  h_ag_result   = {target_h_ag:.6f} m\n")
        else:
            f_cal, h_cal = calibrate_maintenance_for_bg_factor(
                bg_factor=bg,
                target_h_ag=target_h_ag,
                n_steps=N_STEPS,
                dt=DT,
                parameter_base=parameter_base,
                geometry_init=geometry_init,
                ag_factor=1.0,
            )
            results[name] = (bg, f_cal, h_cal)
            print(f"{name}:")
            print(f"  bg_factor     = {bg:.9f}")
            print(f"  maint_factor  = {f_cal:.6e}")
            print(f"  h_ag_result   = {h_cal:.6f} m\n")
