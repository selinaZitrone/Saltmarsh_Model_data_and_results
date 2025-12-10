import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    return minidom.parseString(rough_string).toprettyxml(indent="    ")

def write_xml_file(filepath, salinity, replicate, pft_idx):
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

    # Genau EINE Gruppe pro XML (die angegebene PFT)
    group = ET.SubElement(population, "group")
    ET.SubElement(group, "name").text = f"Saltmarsh_{pft_idx}"
    ET.SubElement(group, "species").text = f"../data_and_results/input_files/species/Saltmarsh_{pft_idx}.py"
    ET.SubElement(group, "vegetation_model_type").text = "Saltmarsh"
    ET.SubElement(group, "mortality").text = "Memory Random"
    ET.SubElement(group, "period").text = "3.154e+7*1"
    ET.SubElement(group, "threshold").text = "0.05"
    ET.SubElement(group, "probability").text = "0.25"
    dist = ET.SubElement(group, "distribution")
    ET.SubElement(dist, "type").text = "Random"
    domain = ET.SubElement(dist, "domain")
    ET.SubElement(domain, "x_1").text = "0"
    ET.SubElement(domain, "y_1").text = "0"
    ET.SubElement(domain, "x_2").text = "2"
    ET.SubElement(domain, "y_2").text = "2"
    ET.SubElement(dist, "n_recruitment_per_step").text = "16"
    ET.SubElement(dist, "n_individuals").text = "160"

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
    ET.SubElement(output, "output_time_range").text = "[1.577e+8, 3.154e+8]"
    ET.SubElement(output, "allow_previous_output").text = "True"
    ET.SubElement(output, "output_each_nth_timestep").text = "[0, 10]"
    # Neuer Pfad: monoculture/static
    ET.SubElement(output, "output_dir").text = (
        f"../data_and_results/data_raw/monoculture/static/{salinity:.3f}/PFT_{pft_idx}/{replicate:02d}"
    )
    for g in ["r_ag", "h_ag", "r_bg", "h_bg"]:
        ET.SubElement(output, "geometry_output").text = g
    for g in ["growth", "maint", "ag_factor", "bg_factor", "age"]:
        ET.SubElement(output, "growth_output").text = g

    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(prettify(project))


# === MAIN LOOP ===
setup_name = "monoculture_static"

salinities = [0.035, 0.070, 0.105, 0.140]
replicates = range(1, 11)
pfts = [1, 2, 3, 4]

for salinity in salinities:
    for pft_idx in pfts:
        for n in replicates:
            # Dateiname enthält PFT
            xml_filename = f"../xml_control_files/{setup_name}_monoculture_pft{pft_idx}_{salinity:.3f}_{n:02d}.xml"

            # Ordner entspricht dem output_dir im XML
            out_dir = f"../data_and_results/data_raw/monoculture/static/{salinity:.3f}/pft_{pft_idx}/{n:02d}"
            os.makedirs(out_dir, exist_ok=True)

            write_xml_file(
                xml_filename,
                salinity=salinity,
                replicate=n,
                pft_idx=pft_idx
            )
