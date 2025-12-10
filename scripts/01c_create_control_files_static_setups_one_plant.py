# -*- coding: utf-8 -*-
"""
Created on Tue Aug  5 13:30:04 2025

@author: Jonas
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    return minidom.parseString(rough_string).toprettyxml(indent="    ")

def write_xml_file(filepath, salinity, pft):
    project = ET.Element("MangaProject")

    # === RESOURCES ===
    resources = ET.SubElement(project, "resources")

    ag = ET.SubElement(resources, "aboveground")
    ET.SubElement(ag, "type").text = "AsymmetricZOI"
    domain_ag = ET.SubElement(ag, "domain")
    ET.SubElement(domain_ag, "x_1").text = "0"
    ET.SubElement(domain_ag, "y_1").text = "0"
    ET.SubElement(domain_ag, "x_2").text = "2"
    ET.SubElement(domain_ag, "y_2").text = "2"
    ET.SubElement(ag, "x_resolution").text = "40"
    ET.SubElement(ag, "y_resolution").text = "40"

    bg = ET.SubElement(resources, "belowground")
    ET.SubElement(bg, "type").text = "Merge"
    ET.SubElement(bg, "modules").text = "FixedSalinity SymmetricZOI"
    domain_bg = ET.SubElement(bg, "domain")
    ET.SubElement(domain_bg, "x_1").text = "0"
    ET.SubElement(domain_bg, "y_1").text = "0"
    ET.SubElement(domain_bg, "x_2").text = "2"
    ET.SubElement(domain_bg, "y_2").text = "2"
    ET.SubElement(bg, "x_resolution").text = "40"
    ET.SubElement(bg, "y_resolution").text = "40"
    ET.SubElement(bg, "variant").text = "forman"
    ET.SubElement(bg, "min_x").text = "0"
    ET.SubElement(bg, "max_x").text = "2"
    ET.SubElement(bg, "salinity").text = f"{salinity:.3f} {salinity:.3f}"

    # === POPULATION ===
    population = ET.SubElement(project, "population")
    group = ET.SubElement(population, "group")
    ET.SubElement(group, "name").text = f"Saltmarsh_{pft}"
    ET.SubElement(group, "species").text = f"../data_and_results/input_files/species/Saltmarsh_{pft}.py"
    ET.SubElement(group, "vegetation_model_type").text = "Saltmarsh"
    ET.SubElement(group, "mortality").text = "Memory"
    ET.SubElement(group, "period").text = "3.154e+7*1"
    ET.SubElement(group, "threshold").text = "0.05"
    dist = ET.SubElement(group, "distribution")
    ET.SubElement(dist, "type").text = "FromFile"
    domain = ET.SubElement(dist, "domain")
    ET.SubElement(domain, "x_1").text = "0"
    ET.SubElement(domain, "y_1").text = "0"
    ET.SubElement(domain, "x_2").text = "2"
    ET.SubElement(domain, "y_2").text = "2"
    ET.SubElement(dist, "filename").text = "../data_and_results/input_files/plant_distribution/one_plant.csv"
    ET.SubElement(dist, "n_recruitment_per_step").text = "0"
    ET.SubElement(dist, "n_individuals").text = "1"

    # === TIME LOOP ===
    loop = ET.SubElement(project, "time_loop")
    ET.SubElement(loop, "type").text = "Simple"
    ET.SubElement(loop, "t_start").text = "0"
    ET.SubElement(loop, "t_end").text = "3.154e+8"
    ET.SubElement(loop, "delta_t").text = "86400"
    ET.SubElement(loop, "terminal_print").text = "days"

    # === VISUALIZATION ===
    vis = ET.SubElement(project, "visualization")
    ET.SubElement(vis, "type").text = "NONE"

    # === OUTPUT ===
    output = ET.SubElement(project, "output")
    ET.SubElement(output, "type").text = "OneFile"
    ET.SubElement(output, "output_time_range").text = "[0, 3.154e+8]"
    ET.SubElement(output, "allow_previous_output").text = "True"
    ET.SubElement(output, "output_dir").text = f"../data_and_results/data_raw/one_plant/static/{salinity:.3f}/pft_{pft}"

    for g in ["r_ag", "h_ag", "r_bg", "h_bg"]:
        ET.SubElement(output, "geometry_output").text = g
    for g in ["w_r_ag", "w_h_ag", "w_r_bg", "w_h_bg",
              "adjustment", "ratio_ag", "w_ratio_b_a",
              "growth", "maint", "ag_factor", "bg_factor", "age"]:
        ET.SubElement(output, "growth_output").text = g

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(prettify(project))


# === MAIN LOOP ===
setup_name = "one_plant_static"
os.makedirs("../xml_control_files", exist_ok=True)

for salinity in [0.035, 0.070, 0.105, 0.140]:
    for pft in range(1, 5):
        xml_filename = f"../xml_control_files/{setup_name}_{salinity:.3f}_pft_{pft}.xml"
        os.makedirs(f"../data_raw/one_plant/static/{salinity:.3f}/pft_{pft}", exist_ok=True)
        write_xml_file(xml_filename, salinity=salinity, pft=pft)
