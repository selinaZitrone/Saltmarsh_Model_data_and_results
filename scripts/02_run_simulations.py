# -*- coding: utf-8 -*-
"""
Script to run multiple MANGA.py simulations using XML control files,
with parallel execution, logging, and runtime visualization.

Features:
- Category selection directly in the script via CATEGORIES_TO_RUN (supports "all")
- Optional CLI override (--override-only / --exclude)
- Option to recompute even if already logged as OK:
  - In-script: RECOMPUTE_COMPLETED = True/False
  - CLI: --include-done
- Retry only failed runs: --retry-errors
"""

import os
import glob
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import csv
import fnmatch

# ======================================================
# === USER CONFIGURATION ===============================
# ======================================================

MANGA_PATH = "../../pyMANGA-1/MANGA.py"
XML_FOLDER = "../xml_control_files"
PYTHON_EXEC = "py -3.12"
MAX_WORKERS = 6
LOG_DIR = "logs"
CSV_LOGFILE = "simulation_log.csv"

# Kategorien, die gerechnet werden sollen. Erlaubt sind:
# "community_dynamic", "community_static", "monoculture_static",
# "one_plant_static", "one_plant_dynamic", "two_plant_static", "two_plant_dynamic", "all"
CATEGORIES_TO_RUN = ["one_plant_static",
                     "one_plant_dynamic",
                     "community_dynamic",
                     "community_static"]  # z.B.: ["community_dynamic", "two_plant_dynamic"] oder ["all"]

# Sollen bereits erfolgreich gelaufene XMLs (laut CSV_LOGFILE) erneut berechnet werden?
RECOMPUTE_COMPLETED = True  # auf True setzen, um auch "fertige" erneut zu rechnen

# ======================================================
# === INTERNAL CONFIG ==================================
# ======================================================

CATEGORY_PATTERNS = {
    "community_dynamic":    "community_dynamic*.xml",
    "community_static":     "community_static*.xml",
    "monoculture_static":   "monoculture_static*.xml",
    "one_plant_static":     "one_plant_static*.xml",
    "one_plant_dynamic":    "one_plant_dynamic*.xml",
    "two_plant_static":     "two_plant_static*.xml",
    "two_plant_dynamic":    "two_plant_dynamic*.xml",
    "all":                  "*.xml",
}


# ======================================================
# === CORE FUNCTIONS ===================================
# ======================================================

def run_simulation(xml_file):
    xml_file = os.path.abspath(xml_file)
    xml_name = os.path.splitext(os.path.basename(xml_file))[0]
    log_path = os.path.join(LOG_DIR, f"{xml_name}.log")

    os.makedirs(LOG_DIR, exist_ok=True)

    manga_dir = os.path.abspath(os.path.dirname(MANGA_PATH))
    manga_py = os.path.abspath(MANGA_PATH)
    command = f'{PYTHON_EXEC} "{manga_py}" -i "{xml_file}"'

    start_time = datetime.now()
    with open(log_path, "w", encoding="utf-8") as logfile:
        process = subprocess.run(
            command,
            shell=True,
            cwd=manga_dir,
            stdout=logfile,
            stderr=logfile
        )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    return {
        "xml_file": xml_file,
        "log_file": log_path,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_sec": duration,
        "exit_code": process.returncode,
        "status": "OK" if process.returncode == 0 else "ERROR",
    }


def read_logfile():
    if not os.path.isfile(CSV_LOGFILE):
        return []
    with open(CSV_LOGFILE, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_results_to_csv(results, mode='a'):
    file_exists = os.path.isfile(CSV_LOGFILE)
    with open(CSV_LOGFILE, mode, newline='', encoding='utf-8') as f:
        fieldnames = ["xml_file", "log_file", "start_time", "end_time",
                      "duration_sec", "exit_code", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or mode == 'w':
            writer.writeheader()
        for res in results:
            writer.writerow(res)


def list_all_xml():
    return sorted(glob.glob(os.path.join(XML_FOLDER, "*.xml")))


def _patterns_for(cats):
    pats = []
    for c in cats:
        pat = CATEGORY_PATTERNS.get(c)
        if pat is not None:
            pats.append(os.path.join(XML_FOLDER, pat))
    return pats


def filter_by_categories(files, only_categories=None, exclude_categories=None):
    """Filtere Dateiliste anhand von Kategorien (glob patterns)."""
    if not files:
        return []

    selected = files

    # ONLY filter
    if only_categories:
        # Wenn "all" in only_categories → keine Einschränkung
        if "all" not in only_categories:
            only_pats = _patterns_for(only_categories)
            selected = [
                f for f in selected
                if any(fnmatch.fnmatch(f, pat) for pat in only_pats)
            ]

    # EXCLUDE filter
    if exclude_categories:
        excl_pats = _patterns_for(exclude_categories)
        selected = [
            f for f in selected
            if not any(fnmatch.fnmatch(f, pat) for pat in excl_pats)
        ]

    return selected


def select_xml_files(
    retry_only=False,
    only_categories=None,
    exclude_categories=None,
    include_done=False
):
    """
    Auswahl der XML-Dateien gemäß Regeln:
    - Basis: alle XMLs
    - Kategorie-Filter (only/exclude)
    - Wenn retry_only=True → nur fehlgeschlagene aus dem Log
    - Sonst:
        - include_done=False → bereits OK gelaufene überspringen
        - include_done=True  → nichts überspringen (alles aus Auswahl)
    """
    all_xml = list_all_xml()
    filtered = filter_by_categories(all_xml, only_categories, exclude_categories)

    log = read_logfile()
    abs_filtered = {os.path.abspath(f) for f in filtered}

    if retry_only:
        failed = {os.path.abspath(row["xml_file"]) for row in log if row["status"] != "OK"}
        # nur die, die im Filter sind UND fehlgeschlagen sind
        return sorted(f for f in filtered if os.path.abspath(f) in failed)

    if include_done:
        # Nichts aus dem Log überspringen
        return filtered

    # Standard: bereits OK gelaufene überspringen
    done = {os.path.abspath(row["xml_file"]) for row in log if row["status"] == "OK"}
    return [f for f in filtered if os.path.abspath(f) not in done]


# ======================================================
# === MAIN =============================================
# ======================================================

def main():
    # Für CLI-Choices "all" zusätzlich erlauben
    choices = list(CATEGORY_PATTERNS.keys())

    parser = argparse.ArgumentParser(description="MANGA simulation controller")
    parser.add_argument("--retry-errors", action="store_true",
                        help="Rerun only failed simulations")
    parser.add_argument("--exclude", nargs="+", choices=[c for c in choices if c != "all"],
                        default=[],
                        help="Exclude these categories")
    parser.add_argument("--list-only", action="store_true",
                        help="Only list selected XMLs and exit")
    parser.add_argument("--override-only", nargs="+", choices=choices,
                        help="Override CATEGORIES_TO_RUN temporarily (supports 'all')")
    parser.add_argument("--include-done", action="store_true",
                        help="Include files already marked as OK in the log (recompute completed)")

    args = parser.parse_args()

    # Kategorien bestimmen:
    only_categories = args.override_only if args.override_only else CATEGORIES_TO_RUN
    # Falls jemand None oder leere Liste setzt → sinnvoller Fallback
    if not only_categories:
        only_categories = ["all"]

    # include_done final bestimmen (CLI hat Vorrang vor Skript-Flag)
    include_done = args.include_done or RECOMPUTE_COMPLETED

    xml_files = select_xml_files(
        retry_only=args.retry_errors,
        only_categories=only_categories,
        exclude_categories=args.exclude,
        include_done=include_done
    )

    if not xml_files:
        print("✅ No XML files to run (selection empty or all done).")
        return

    print("Categories used:", ", ".join(only_categories))
    if args.exclude:
        print("Excluded:", ", ".join(args.exclude))
    print(f"Include completed (OK in log): {include_done}")
    print("Selection:")
    for f in xml_files:
        print(" -", os.path.relpath(f, XML_FOLDER))

    if args.list_only:
        print(f"\nℹ️ {len(xml_files)} XML file(s) selected (list-only).")
        return

    print(f"\n🚀 Running {len(xml_files)} simulations with up to {MAX_WORKERS} parallel threads...\n")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(run_simulation, xml): xml for xml in xml_files}
        for future in as_completed(future_to_file):
            res = future.result()
            results.append(res)
            name = os.path.basename(res["xml_file"])
            if res["status"] == "OK":
                print(f"✅ {name} finished in {res['duration_sec']:.1f}s")
            else:
                print(f"❌ {name} FAILED (Exit code: {res['exit_code']})")

    write_results_to_csv(results)


if __name__ == "__main__":
    main()
