import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd


def getLogFile(folder_path: str) -> str:
    """
    Récupère le fichier de log du dossier spécifié.

    :param folder_path: Chemin vers le dossier contenant le fichier de log.
    :return: Chemin vers le fichier de log.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Le dossier {folder_path} n'existe pas.")

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.log'):
            return os.path.join(folder_path, file_name)

    raise FileNotFoundError(f"Aucun fichier de log trouvé dans {folder_path}")


def identifyAcquisitionType(log_file_path: str) -> str:
    """
    Identifie le type d'acquisition (prior ou custom focus) en analysant le contenu du log.

    :param log_file_path: Chemin vers le fichier de log.
    :return: "prior" si le log contient "loop", "custom_focus" sinon.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if "loop" in content.lower():
            return "prior"
        return "custom_focus"
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier de log: {e}")


def findLastAcquisition(log_file_path: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Trouve la dernière acquisition dans le fichier de log.
    Cherche soit "Starting acquisition" soit "Reference wells A1 A12 H12 re-aligned."

    :param log_file_path: Chemin vers le fichier de log.
    :return: Tuple contenant la ligne de la dernière acquisition et son numéro de ligne, ou (None, None) si aucune trouvée.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        last_acquisition_line = None
        last_acquisition_line_number = None

        for i, line in enumerate(lines):
            if "Starting" in line and "acquisition" in line:
                last_acquisition_line = line.strip()
                last_acquisition_line_number = i

        return last_acquisition_line, last_acquisition_line_number
    except Exception as e:
        raise ValueError(f"Erreur lors de la recherche de la dernière acquisition: {e}")


def extractWellName(line: str) -> Optional[str]:
    """
    Extrait le nom du puits d'une ligne contenant 'Going to well'.

    :param line: Ligne de log à analyser.
    :return: Nom du puits ou None si non trouvé.
    """
    match = re.search(r'Going to well\s+"([^"]+)"', line)
    if match:
        well_name = match.group(1)
        print(f"[DEBUG] Well name extracted: {well_name}")
        return well_name
    return None


def extractTimestamp(line: str) -> Optional[datetime]:
    """
    Extrait le timestamp d'une ligne de log.

    :param line: Ligne de log à analyser.
    :return: Objet datetime ou None si non trouvé.
    """
    timestamp_pattern = r'\[(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})\]'
    match = re.search(timestamp_pattern, line)
    if match:
        try:
            return datetime.strptime(match.group(1), '%d/%m/%Y %H:%M:%S')
        except ValueError:
            return None
    return None


def calculateAcquisitionDuration(log_file_path: str) -> Dict[str, any]:
    """
    Calcule la durée d'acquisition entre "Starting acquisition..." et "Stopping".

    :param log_file_path: Chemin vers le fichier de log.
    :return: Dictionnaire avec les informations de durée.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        start_acquisition_time = None
        end_acquisition_time = None
        start_line = None
        end_line = None

        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if "Starting acquisition" in line:
                timestamp = extractTimestamp(line)
                if timestamp:
                    start_acquisition_time = timestamp
                    start_line = i
                    break

        if start_acquisition_time:
            for i in range(len(lines) - 1, start_line, -1):
                line = lines[i]
                if "Stopping" in line:
                    timestamp = extractTimestamp(line)
                    if timestamp:
                        end_acquisition_time = timestamp
                        end_line = i
                        break

        if start_acquisition_time and end_acquisition_time:
            duration = end_acquisition_time - start_acquisition_time
            duration_seconds = duration.total_seconds()
            duration_minutes = duration_seconds / 60
            return {
                "start_time": start_acquisition_time,
                "end_time": end_acquisition_time,
                "duration_seconds": round(duration_seconds, 2),
                "duration_minutes": round(duration_minutes, 2),
                "duration_formatted": str(duration),
                "start_line": start_line,
                "end_line": end_line,
                "success": True
            }
        return {
            "start_time": start_acquisition_time,
            "end_time": end_acquisition_time,
            "duration_seconds": 0,
            "duration_minutes": 0,
            "duration_formatted": "N/A",
            "start_line": start_line,
            "end_line": end_line,
            "success": False,
            "error": "Unable to find both start and end timestamps"
        }
    except Exception as e:
        return {
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "duration_minutes": 0,
            "duration_formatted": "N/A",
            "start_line": None,
            "end_line": None,
            "success": False,
            "error": str(e)
        }


def countNumberOfDriftFix(log_file_path: str, last_acquisition_line_number: Optional[int] = None) -> int:
    """
    Compte le nombre de fois où le drift fix est appliqué dans le fichier de log.

    :param log_file_path: Chemin vers le fichier de log.
    :param last_acquisition_line_number: Numéro de ligne de la dernière acquisition.
    :return: Nombre de drift fixes appliqués.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        drift_fix_count = 0
        start_line = 0 if last_acquisition_line_number is None else last_acquisition_line_number

        for line in lines[start_line:]:
            if "DRIFT FIX:" in line:
                drift_fix_count += 1

        return drift_fix_count
    except Exception as e:
        raise ValueError(f"Erreur lors du comptage des drift fixes: {e}")


def calculateAverageLoopsPrior(log_file_path: str, last_acquisition_line_number: Optional[int] = None) -> Dict[
    str, any]:
    """
    Calcule le nombre moyen de loops pour un système prior.
    Détecte automatiquement le nombre de cycles par puits.
    Exclut les mesures des puits de référence utilisés pour l'alignement.
    Inclut SEULEMENT les "Done after X loop(s)" dans la moyenne.
    Les "Time out after X loop(s)" sont comptés comme "Mesures 'Timeout'".

    :param log_file_path: Chemin vers le fichier de log.
    :param last_acquisition_line_number: Numéro de ligne de la dernière acquisition.
    :return: Dictionnaire avec la moyenne des loops et les données des puits.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        done_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Done after\s+(\d+)\s+loop\(s\)'
        timeout_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Time out after\s+(\d+)\s+loop\(s\)'
        reference_pattern = r'Reference wells\s+.*\s+re-aligned'

        wells_data = {}
        current_well = "Unknown"
        all_loops_values = []
        all_measurements_count = 0
        timeout_count = 0
        debug_log = []

        # Variables pour gérer les phases d'alignement
        alignment_phases = []
        in_alignment_phase = False

        start_line = 0 if last_acquisition_line_number is None else last_acquisition_line_number

        # Première passe : identifier les phases d'alignement
        auto_position_start_line = None
        reference_aligned_line = None

        for i, line in enumerate(lines):
            if i <= start_line:
                continue

            if "Starting auto-position of wells:" in line:
                auto_position_start_line = i
                debug_log.append(f"[DEBUG] Début alignement détecté à la ligne {i + 1}")

            if re.search(reference_pattern, line):
                reference_aligned_line = i
                debug_log.append(f"[DEBUG] Fin alignement détectée à la ligne {i + 1}")
                break  # On prend seulement le premier après "Starting acquisition"

        # Deuxième passe : analyser les mesures APRÈS la fin d'alignement
        acquisition_started = False
        if reference_aligned_line is not None:
            acquisition_started = True
            debug_log.append(f"[DEBUG] Comptage des mesures commence après la ligne {reference_aligned_line + 1}")

        for i, line in enumerate(lines):
            if i <= start_line:
                continue

            # Ignorer tout ce qui est avant la fin de l'alignement
            if not acquisition_started or i <= reference_aligned_line:
                continue

            well_name = extractWellName(line)
            if well_name:
                current_well = well_name
                if current_well not in wells_data:
                    wells_data[current_well] = {
                        "loops": [],
                        "timeouts": [],
                        "done_count": 0,
                        "timeout_count": 0,
                        "measurements": 0
                    }
                continue

            done_match = re.search(done_pattern, line)
            if done_match:
                loop_count = int(done_match.group(1))
                all_measurements_count += 1
                all_loops_values.append(loop_count)
                wells_data[current_well]["loops"].append(loop_count)
                wells_data[current_well]["done_count"] += 1
                wells_data[current_well]["measurements"] += 1
                debug_log.append(
                    f"Puits {current_well}: Done après {loop_count} loop(s), mesure {wells_data[current_well]['measurements']}")
                continue

            timeout_match = re.search(timeout_pattern, line)
            if timeout_match:
                loop_count = int(timeout_match.group(1))
                all_measurements_count += 1
                wells_data[current_well]["timeouts"].append(loop_count)
                wells_data[current_well]["timeout_count"] += 1
                wells_data[current_well]["measurements"] += 1
                timeout_count += 1
                debug_log.append(
                    f"Puits {current_well}: Timeout après {loop_count} loop(s), mesure {wells_data[current_well]['measurements']}")
                continue

        # Filtrer les puits sans mesures valides
        wells_data = {k: v for k, v in wells_data.items() if v["loops"] or v["timeouts"]}

        # Détection automatique du nombre de cycles
        cycles_detected = 0
        if wells_data:
            # Prendre le nombre de mesures du premier puits complet (qui a des mesures)
            first_well_measurements = max([v["measurements"] for v in wells_data.values()]) if wells_data else 0
            cycles_detected = first_well_measurements

            # Validation : vérifier que la plupart des puits ont le même nombre de mesures
            measurement_counts = [v["measurements"] for v in wells_data.values()]
            most_common_count = max(set(measurement_counts), key=measurement_counts.count)
            cycles_detected = most_common_count

            debug_log.append(f"[DEBUG] Cycles détectés automatiquement : {cycles_detected}")
            debug_log.append(f"[DEBUG] Distribution des mesures par puits : {sorted(set(measurement_counts))}")

        average_loops = 0 if not all_loops_values else sum(all_loops_values) / len(all_loops_values)

        print("\n=== Journal de débogage ===")
        for entry in debug_log:
            print(entry)
        print(f"[DEBUG] Nombre de cycles détectés : {cycles_detected}")
        print(f"[DEBUG] Puits analysés : {len(wells_data)}")
        print(
            f"[DEBUG] Mesures totales théoriques : {len(wells_data)} puits × {cycles_detected} cycles = {len(wells_data) * cycles_detected}")
        print(f"[DEBUG] Mesures totales réelles : {all_measurements_count}")

        return {
            "average_loops": round(average_loops, 2),
            "total_measurements": all_measurements_count,
            "done_measurements": len(all_loops_values),
            "timeout_measurements": timeout_count,
            "total_wells": len(wells_data),
            "cycles_detected": cycles_detected,
            "loops_values": all_loops_values,
            "wells_data": wells_data
        }
    except Exception as e:
        raise ValueError(f"Erreur lors du calcul des loops moyens (prior): {e}")


def calculateAverageMovesCustomFocus(log_file_path: str, last_acquisition_line_number: Optional[int] = None) -> Dict[
    str, float]:
    """
    Calcule le nombre moyen de moves pour un système custom focus.
    Inclut uniquement les moves menant à une réussite ou à un timeout.
    Compte les "Still not" comme "Mesures 'Timeout'".
    IGNORE les mesures faites pendant la phase d'auto-positionnement/alignement.

    :param log_file_path: Chemin vers le fichier de log.
    :param last_acquisition_line_number: Numéro de ligne de la dernière acquisition.
    :return: Dictionnaire avec la moyenne des moves et les données des puits.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        move_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Adjusting.*move:\s+(\d+)'
        max_retry_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Focus not reached after\s+(\d+)\s+moves\.\s+Trying alternate commands'
        still_not_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Still not'
        autofocus_done_pattern = r'\[AUTOFOCUS\]\[OFF\]\s+Done'

        # Patterns pour détecter la phase d'alignement
        auto_position_start_pattern = r'Starting auto-position of wells:'
        reference_aligned_pattern = r'Reference wells\s+.*\s+re-aligned'

        wells_data = {}
        current_well = "Unknown"
        current_well_moves = []
        last_processed_well = None  # Pour éviter les doublons
        all_moves_values = []
        timeout_count = 0
        debug_log = []

        # Variables pour gérer la phase d'alignement
        in_alignment_phase = False
        alignment_start_line = None
        alignment_end_line = None

        start_line = 0 if last_acquisition_line_number is None else last_acquisition_line_number

        # Première passe : identifier les phases d'alignement
        for i, line in enumerate(lines):
            if i <= start_line:
                continue

            if re.search(auto_position_start_pattern, line):
                in_alignment_phase = True
                alignment_start_line = i
                debug_log.append(f"[DEBUG] Début de la phase d'alignement à la ligne {i + 1}")
                continue

            if re.search(reference_aligned_pattern, line):
                if in_alignment_phase:
                    in_alignment_phase = False
                    alignment_end_line = i
                    debug_log.append(f"[DEBUG] Fin de la phase d'alignement à la ligne {i + 1}")
                continue

        # Deuxième passe : analyser les moves en ignorant la phase d'alignement
        in_alignment_phase = False
        for i, line in enumerate(lines):
            if i <= start_line:
                continue

            # Vérifier si on est dans une phase d'alignement
            if alignment_start_line and alignment_end_line and alignment_start_line <= i <= alignment_end_line:
                if not in_alignment_phase:
                    in_alignment_phase = True
                    debug_log.append(
                        f"[DEBUG] Ignorage des mesures d'alignement de la ligne {alignment_start_line + 1} à {alignment_end_line + 1}")
                continue
            else:
                in_alignment_phase = False

            well_name = extractWellName(line)
            if well_name and well_name != current_well:
                # Finaliser le puits précédent
                if current_well_moves and current_well != "Unknown" and not in_alignment_phase:
                    final_move = max(current_well_moves) if current_well_moves else 0
                    if current_well not in wells_data:
                        wells_data[current_well] = {"moves": [], "timeouts": 0, "done_count": 0}
                    wells_data[current_well]["moves"].append(final_move)
                    wells_data[current_well]["done_count"] += 1
                    all_moves_values.append(final_move)
                    debug_log.append(
                        f"Puits {current_well}: {len(current_well_moves)} tentatives, move final = {final_move} (Done)")

                current_well = well_name
                current_well_moves = []
                continue

            # Ignorer les mesures pendant l'alignement
            if in_alignment_phase:
                continue

            if re.search(autofocus_done_pattern, line):
                if current_well != "Unknown" and current_well != last_processed_well:
                    # Si pas de moves détectés, c'est move = 0 (pas d'ajustement nécessaire)
                    final_move = max(current_well_moves) if current_well_moves else 0
                    if current_well not in wells_data:
                        wells_data[current_well] = {"moves": [], "timeouts": 0, "done_count": 0}
                    wells_data[current_well]["moves"].append(final_move)
                    wells_data[current_well]["done_count"] += 1
                    all_moves_values.append(final_move)

                    move_info = f"{len(current_well_moves)} tentatives" if current_well_moves else "0 moves (pas d'ajustement)"
                    debug_log.append(f"Puits {current_well}: {move_info}, move final = {final_move} (fin autofocus)")

                    last_processed_well = current_well
                elif current_well == last_processed_well:
                    debug_log.append(f"[DEBUG] Mesure ignorée pour {current_well} (déjà traitée)")

                current_well_moves = []
                continue

            if re.search(still_not_pattern, line):
                if current_well_moves and current_well != "Unknown":
                    final_move = max(current_well_moves) if current_well_moves else 0
                    if current_well not in wells_data:
                        wells_data[current_well] = {"moves": [], "timeouts": 0, "done_count": 0}
                    wells_data[current_well]["moves"].append(final_move)
                    wells_data[current_well]["timeouts"] += 1
                    all_moves_values.append(final_move)
                    timeout_count += 1
                    debug_log.append(
                        f"Puits {current_well}: {len(current_well_moves)} tentatives, move final = {final_move} (Timeout)")
                current_well_moves = []
                continue

            max_retry_match = re.search(max_retry_pattern, line)
            if max_retry_match:
                current_well_moves = []
                debug_log.append(f"Puits {current_well}: max retry détecté, moves réinitialisés")
                continue

            move_match = re.search(move_pattern, line)
            if move_match:
                move_count = int(move_match.group(1))
                current_well_moves.append(move_count)
                debug_log.append(f"Puits {current_well}: move détecté, {move_count} moves")

        # Finaliser le dernier puits
        if current_well_moves and current_well != "Unknown" and not in_alignment_phase:
            final_move = max(current_well_moves) if current_well_moves else 0
            if current_well not in wells_data:
                wells_data[current_well] = {"moves": [], "timeouts": 0, "done_count": 0}
            wells_data[current_well]["moves"].append(final_move)
            wells_data[current_well]["done_count"] += 1
            all_moves_values.append(final_move)
            debug_log.append(
                f"Puits {current_well}: {len(current_well_moves)} tentatives, move final = {final_move} (dernier puits)")

        wells_data = {k: v for k, v in wells_data.items() if v["moves"]}
        average_moves = 0 if not all_moves_values else sum(all_moves_values) / len(all_moves_values)

        print("\n=== Journal de débogage ===")
        for entry in debug_log:
            print(entry)

        return {
            "average_moves": round(average_moves, 2),
            "total_measurements": len(all_moves_values),
            "done_measurements": len(all_moves_values) - timeout_count,
            "timeout_measurements": timeout_count,
            "total_wells": len(wells_data),
            "moves_values": all_moves_values,
            "wells_data": wells_data
        }
    except Exception as e:
        raise ValueError(f"Erreur lors du calcul des moves moyens (custom focus): {e}")

def analyzeLogFile(log_file_path: str) -> Dict[str, any]:
    """
    Analyse complète d'un fichier de log.

    :param log_file_path: Chemin vers le fichier de log.
    :return: Dictionnaire avec toutes les informations d'analyse.
    """
    try:
        acquisition_type = identifyAcquisitionType(log_file_path)
        last_acquisition, last_acquisition_line_number = findLastAcquisition(log_file_path)
        acquisition_duration = calculateAcquisitionDuration(log_file_path)
        drift_fix_count = countNumberOfDriftFix(log_file_path, last_acquisition_line_number)

        if acquisition_type == "prior":
            stats = calculateAverageLoopsPrior(log_file_path, last_acquisition_line_number)
            analysis_results = {
                "acquisition_type": acquisition_type,
                "last_acquisition": last_acquisition,
                "average_value": stats["average_loops"],
                "total_measurements": stats["total_measurements"],
                "done_measurements": stats["done_measurements"],
                "timeout_measurements": stats["timeout_measurements"],
                "total_wells": stats["total_wells"],
                "cycles_detected": stats["cycles_detected"],
                "values": stats["loops_values"],
                "wells_data": stats["wells_data"],
                "acquisition_duration": acquisition_duration
            }
        else:  # custom_focus
            stats = calculateAverageMovesCustomFocus(log_file_path, last_acquisition_line_number)
            analysis_results = {
                "acquisition_type": acquisition_type,
                "last_acquisition": last_acquisition,
                "average_value": stats["average_moves"],
                "total_measurements": stats["total_measurements"],
                "done_measurements": stats["done_measurements"],
                "timeout_measurements": stats["timeout_measurements"],
                "total_wells": stats["total_wells"],
                "values": stats["moves_values"],
                "wells_data": stats["wells_data"],
                "acquisition_duration": acquisition_duration
            }

        analysis_results["drift_fix_count"] = drift_fix_count
        return analysis_results
    except Exception as e:
        raise ValueError(f"Erreur lors de l'analyse du fichier de log: {e}")


def generateLogAnalysisReport(folder_path: str) -> pd.DataFrame:
    """
    Génère un rapport d'analyse pour un dossier contenant un fichier de log.

    :param folder_path: Chemin vers le dossier contenant le fichier de log.
    :return: DataFrame avec les résultats d'analyse.
    """
    try:
        log_file_path = getLogFile(folder_path)
        analysis = analyzeLogFile(log_file_path)

        report_data = {
            "Type d'acquisition": [analysis["acquisition_type"]],
            "Durée d'acquisition (minutes)": [analysis["acquisition_duration"]["duration_minutes"]],
            "Nombre moyen de loops/moves": [analysis["average_value"]],
            "Nombre total de mesures": [analysis["total_measurements"]],
            "Nombre total de puits": [analysis["total_wells"]],
            "Mesures 'Done'": [analysis["done_measurements"]],
            "Mesures 'Timeout'": [analysis["timeout_measurements"]],
            "Nombre de Drift Fix": [analysis["drift_fix_count"]],
        }

        return pd.DataFrame(report_data)
    except Exception as e:
        raise ValueError(f"Erreur lors de la génération du rapport d'analyse: {e}")


def generateSummaryReport(folder_path: str) -> Dict[str, any]:
    """
    Génère un résumé complet de l'analyse.

    :param folder_path: Chemin vers le dossier contenant le fichier de log.
    :return: Dictionnaire avec le résumé complet.
    """
    try:
        log_file_path = getLogFile(folder_path)
        analysis = analyzeLogFile(log_file_path)
        summary = {
            "file_path": log_file_path,
            "acquisition_type": analysis["acquisition_type"],
            "acquisition_duration_minutes": analysis["acquisition_duration"]["duration_minutes"],
            "total_wells": analysis["total_wells"],
            "total_measurements": analysis["total_measurements"],
            "average_value": analysis["average_value"],
            "timeout_measurements": analysis["timeout_measurements"]
        }
        return summary
    except Exception as e:
        raise ValueError(f"Erreur lors de la génération du résumé: {e}")


if __name__ == "__main__":
    try:
        folder_path = "C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/log/nouveau_focus"
        print("=== Résumé de l'analyse ===")
        summary = generateSummaryReport(folder_path)
        for key, value in summary.items():
            print(f"{key}: {value}")

        print("\n=== Analyse du fichier de log ===")
        report = generateLogAnalysisReport(folder_path)
        print("Rapport d'analyse:")
        print(report.to_string(index=False))

        report.to_csv("analyse_log.csv", index=False)
        print(f"\nRapport sauvegardé: analyse_log.csv")
    except Exception as e:
        print(f"Erreur: {e}")