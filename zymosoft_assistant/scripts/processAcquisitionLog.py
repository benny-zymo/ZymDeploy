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
    # Vérifier si le dossier existe
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Le dossier {folder_path} n'existe pas.")

    # Parcourir les fichiers dans le dossier
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.log'):
            return os.path.join(folder_path, file_name)

    # Si aucun fichier trouvé, lever une erreur
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

        # Rechercher le mot-clé "loop" dans le contenu
        if "loop" in content.lower():
            return "prior"
        else:
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

        # Rechercher la dernière ligne contenant "Starting acquisition" ou "Reference wells A1 A12 H12 re-aligned."
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
        return match.group(1)
    return None


def extractTimestamp(line: str) -> Optional[datetime]:
    """
    Extrait le timestamp d'une ligne de log.

    :param line: Ligne de log à analyser.
    :return: Objet datetime ou None si non trouvé.
    """
    # Pattern pour extraire le timestamp [DD/MM/YYYY HH:MM:SS]
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
    Calcule la durée d'acquisition entre "Starting acquisition..." et "MOTOR X SET ACTUAL POSITION 0".

    Cherche la dernière occurrence de "Starting acquisition" et la dernière occurrence de "MOTOR X SET ACTUAL POSITION 0"

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

        # Trouver la dernière occurrence de "Starting acquisition"
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if "Starting acquisition" in line:
                timestamp = extractTimestamp(line)
                if timestamp:
                    start_acquisition_time = timestamp
                    start_line = i
                    break

        # Chercher la dernière occurrence de "MOTOR X SET ACTUAL POSITION 0" après le début
        if start_acquisition_time:
            for i in range(len(lines) - 1, start_line, -1):
                line = lines[i]
                if "Stopping" in line :
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
        else:
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

        # Déterminer la ligne de départ pour l'analyse
        start_line = 0
        if last_acquisition_line_number is not None:
            start_line = last_acquisition_line_number

        for line in lines[start_line:]:
            if "DRIFT FIX:" in line:
                drift_fix_count += 1

        return drift_fix_count

    except Exception as e:
        raise ValueError(f"Erreur lors du comptage des drift fixes: {e}")

def calculateAverageLoopsPrior(log_file_path: str, last_acquisition_line_number: Optional[int] = None) -> Dict[
    str, float]:
    """
    Calcule le nombre moyen de loops pour un système prior.
    Inclut SEULEMENT les "Done after X loop(s)" dans la moyenne.
    Les "Time out after X loop(s)" ne sont PAS inclus dans la moyenne mais sont comptés dans le total des mesures.

    :param log_file_path: Chemin vers le fichier de log.
    :param last_acquisition_line_number: Numéro de ligne de la dernière acquisition.
    :return: Dictionnaire avec la moyenne des loops et les données des puits.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Patterns pour extraire le nombre de loops
        done_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Done after\s+(\d+)\s+loop\(s\)'
        timeout_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Time out after\s+(\d+)\s+loop\(s\)'

        # Dictionnaire pour stocker les loops par puits
        wells_data = {}
        current_well = "Unknown"
        all_loops_values = []  # Seulement pour les "Done" (calcul de la moyenne)
        all_measurements_count = 0  # Compte toutes les mesures (Done + Timeout)

        # Déterminer la ligne de départ pour l'analyse
        start_line = 0
        if last_acquisition_line_number is not None:
            start_line = last_acquisition_line_number

        # Chercher aussi "Reference wells re-aligned" pour mettre à jour start_line
        for i, line in enumerate(lines):
            if i <= start_line:
                continue
            if "Reference wells" in line and "re-aligned" in line:
                start_line = i
                break



        for i, line in enumerate(lines):
            if i <= start_line:
                continue

            # Vérifier si on change de puits
            well_name = extractWellName(line)
            if well_name and well_name != current_well:
                current_well = well_name
                if current_well not in wells_data:
                    wells_data[current_well] = {"loops": [], "timeouts": [], "done_count": 0, "timeout_count": 0}
                continue

            # Chercher les "Done after"
            done_match = re.search(done_pattern, line)
            if done_match:
                loop_count = int(done_match.group(1))
                all_measurements_count += 1  # Compter dans le total
                all_loops_values.append(loop_count)  # Inclure dans la moyenne

                # S'assurer que le puits actuel existe
                if current_well not in wells_data:
                    wells_data[current_well] = {"loops": [], "timeouts": [], "done_count": 0, "timeout_count": 0}

                wells_data[current_well]["loops"].append(loop_count)
                wells_data[current_well]["done_count"] += 1
                continue

            # Chercher les "Time out after"
            timeout_match = re.search(timeout_pattern, line)
            if timeout_match:
                loop_count = int(timeout_match.group(1))
                all_measurements_count += 1  # Compter dans le total
                # NE PAS ajouter à all_loops_values (pas dans la moyenne)

                # S'assurer que le puits actuel existe
                if current_well not in wells_data:
                    wells_data[current_well] = {"loops": [], "timeouts": [], "done_count": 0, "timeout_count": 0}

                wells_data[current_well]["timeouts"].append(loop_count)
                wells_data[current_well]["timeout_count"] += 1

        # Nettoyer les puits sans données
        wells_data = {k: v for k, v in wells_data.items() if v["loops"] or v["timeouts"]}

        # Calcul de la moyenne seulement sur les valeurs "Done"
        if not all_loops_values:
            average_loops = 0
        else:
            average_loops = sum(all_loops_values) / len(all_loops_values)

        return {
            "average_loops": round(average_loops, 2),
            "total_measurements": all_measurements_count,  # Toutes les mesures (Done + Timeout)
            "done_measurements": len(all_loops_values),  # Seulement les "Done"
            "timeout_measurements": all_measurements_count - len(all_loops_values),  # Seulement les timeouts
            "total_wells": len(wells_data),
            "loops_values": all_loops_values,  # Seulement les valeurs "Done"
            "wells_data": wells_data
        }

    except Exception as e:
        raise ValueError(f"Erreur lors du calcul des loops moyens (prior): {e}")


def calculateAverageMovesCustomFocus(log_file_path: str, last_acquisition_line_number: Optional[int] = None) -> Dict[
    str, float]:
    """
    Calcule le nombre moyen de moves pour un système custom focus.
    Inclut les moves des max retry dans la moyenne.

    :param log_file_path: Chemin vers le fichier de log.
    :param last_acquisition_line_number: Numéro de ligne de la dernière acquisition.
    :return: Dictionnaire avec la moyenne des moves et les données des puits.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Patterns
        move_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Adjusting.*move:\s+(\d+)'
        max_retry_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Focus not reached after\s+(\d+)\s+moves\.\s+Trying alternate commands'

        # Variables pour tracker les puits
        wells_data = {}
        current_well = "Unknown"
        current_well_moves = []
        previous_move_count = 0
        is_max_retry_context = False
        all_moves_values = []

        # Déterminer la ligne de départ pour l'analyse
        start_line = 0
        if last_acquisition_line_number is not None:
            start_line = last_acquisition_line_number

        # Chercher aussi "Reference wells re-aligned" pour mettre à jour start_line
        '''for i, line in enumerate(lines):
            if i <= start_line:
                continue
            if "Reference wells" in line and "re-aligned" in line:
                start_line = i
                break'''

        for i, line in enumerate(lines):
            if i <= start_line:
                continue

            # Vérifier si on change de puits selon le log
            well_name = extractWellName(line)
            if well_name and well_name != current_well:
                # Sauvegarder les moves du puits précédent
                if current_well_moves and current_well != "Unknown":
                    final_move = max(current_well_moves)
                    if current_well not in wells_data:
                        wells_data[current_well] = {"moves": []}
                    wells_data[current_well]["moves"].append(final_move)
                    all_moves_values.append(final_move)

                current_well = well_name
                current_well_moves = []
                previous_move_count = 0
                is_max_retry_context = False
                continue

            # Détecter max retry
            max_retry_match = re.search(max_retry_pattern, line)
            if max_retry_match:
                is_max_retry_context = True
                # Ajouter les moves du max retry
                max_retry_moves = int(max_retry_match.group(1))
                current_well_moves.append(max_retry_moves)
                continue

            # Chercher les moves
            move_match = re.search(move_pattern, line)
            if move_match:
                move_count = int(move_match.group(1))

                # Logique pour détecter un changement de puits
                new_well = False

                if not current_well_moves:
                    new_well = False
                elif is_max_retry_context:
                    new_well = False
                    is_max_retry_context = False
                elif move_count <= previous_move_count:
                    new_well = True

                if new_well:
                    # Sauvegarder les moves du puits précédent
                    if current_well_moves:
                        final_move = max(current_well_moves)
                        if current_well not in wells_data:
                            wells_data[current_well] = {"moves": []}
                        wells_data[current_well]["moves"].append(final_move)
                        all_moves_values.append(final_move)

                    # Commencer un nouveau puits
                    current_well_moves = [move_count]
                    current_well = f"Well_{len(wells_data) + 1}"
                else:
                    current_well_moves.append(move_count)

                previous_move_count = move_count

        # Traiter le dernier puits
        if current_well_moves:
            final_move = max(current_well_moves)
            if current_well not in wells_data:
                wells_data[current_well] = {"moves": []}
            wells_data[current_well]["moves"].append(final_move)
            all_moves_values.append(final_move)

        if not all_moves_values:
            return {
                "average_moves": 0,
                "total_measurements": 0,
                "total_wells": 0,
                "moves_values": [],
                "wells_data": wells_data
            }

        average_moves = sum(all_moves_values) / len(all_moves_values)

        return {
            "average_moves": round(average_moves, 2),
            "total_measurements": len(all_moves_values),
            "total_wells": len(wells_data),
            "moves_values": all_moves_values,
            "wells_data": wells_data
        }

    except Exception as e:
        raise ValueError(f"Erreur lors du calcul des moves moyens (custom focus): {e}")


def countMaxRetryCustomFocus(log_file_path: str, last_acquisition_line_number: Optional[int] = None) -> Dict[str, int]:
    """
    Compte le nombre de fois où le max retry est atteint pour un système custom focus.

    :param log_file_path: Chemin vers le fichier de log.
    :param last_acquisition_line_number: Numéro de ligne de la dernière acquisition.
    :return: Dictionnaire avec le nombre de max retry et les lignes correspondantes.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Pattern pour détecter le max retry - VERSION CORRIGÉE
        # Le pattern doit gérer les points de suspension éventuels
        pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Focus not reached after\s+(\d+)\s+moves\.\s+Trying alternate commands\.?\.*'



        max_retry_count = 0
        max_retry_lines = []
        current_well = "Unknown"
        number_of_well = 0

        # Déterminer la ligne de départ pour l'analyse
        start_line = 0
        if last_acquisition_line_number is not None:
            start_line = last_acquisition_line_number


        # Chercher aussi "Reference wells re-aligned" pour mettre à jour start_line
        '''for i, line in enumerate(lines):
            if i <= start_line:
                continue
            if "Reference wells" in line and "re-aligned" in line:
                start_line = i
                break'''

        for line_num, line in enumerate(lines, 1):
            if line_num - 1 <= start_line:
                continue

            # Vérifier si on change de puits
            well_name = extractWellName(line)

            if well_name and well_name != current_well:
                number_of_well += 1
                current_well = well_name
                continue

            match = re.search(pattern, line)
            if match:
                max_retry_count += 1
                max_retry_lines.append({
                    "line_number": line_num,
                    "well": current_well,
                    "moves": int(match.group(1)),
                    "line_content": line.strip()
                })

        return {
            "max_retry_count": max_retry_count,
            "max_retry_lines": max_retry_lines
        }

    except Exception as e:
        raise ValueError(f"Erreur lors du comptage des max retry (custom focus): {e}")


def countMaxRetryPrior(log_file_path: str, last_acquisition_line_number: Optional[int] = None) -> Dict[str, int]:
    """
    Compte le nombre de fois où le max retry est atteint pour un système prior.
    Cherche les lignes contenant "Time out after X loop(s)".

    :param log_file_path: Chemin vers le fichier de log.
    :param last_acquisition_line_number: Numéro de ligne de la dernière acquisition.
    :return: Dictionnaire avec le nombre de max retry et les lignes correspondantes.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Pattern pour détecter les timeouts
        timeout_pattern = r'\[AUTOFOCUS\]\[FOCUS\]\s+Time out after\s+(\d+)\s+loop\(s\)'

        max_retry_count = 0
        max_retry_lines = []
        current_well = "Unknown"
        processed_wells = set()

        # Déterminer la ligne de départ pour l'analyse
        start_line = 0
        if last_acquisition_line_number is not None:
            start_line = last_acquisition_line_number

        # Chercher aussi "Reference wells re-aligned" pour mettre à jour start_line
        for i, line in enumerate(lines):
            if i <= start_line:
                continue
            if "Reference wells" in line and "re-aligned" in line:
                start_line = i
                break

        for line_num, line in enumerate(lines, 1):
            if line_num - 1 <= start_line:
                continue

            # Vérifier si on change de puits
            well_name = extractWellName(line)
            if well_name and well_name != current_well:
                current_well = well_name
                processed_wells.add(well_name)
                continue

            # Chercher les timeouts
            match = re.search(timeout_pattern, line)
            if match:
                max_retry_count += 1
                max_retry_lines.append({
                    "line_number": line_num,
                    "well": current_well,
                    "loops": int(match.group(1)),
                    "line_content": line.strip()
                })

        # Convert set to sorted list for consistent output
        wells_list = sorted(list(processed_wells))


        return {
            "max_retry_count": max_retry_count,
            "max_retry_lines": max_retry_lines,
            "processed_wells": wells_list
        }

    except Exception as e:
        raise ValueError(f"Erreur lors du comptage des max retry (prior): {e}")


def analyzeLogFile(log_file_path: str) -> Dict[str, any]:
    """
    Analyse complète d'un fichier de log.

    :param log_file_path: Chemin vers le fichier de log.
    :return: Dictionnaire avec toutes les informations d'analyse.
    """
    try:
        # 1. Identifier le type d'acquisition
        acquisition_type = identifyAcquisitionType(log_file_path)

        # 2. Trouver la dernière acquisition
        last_acquisition, last_acquisition_line_number = findLastAcquisition(log_file_path)

        # 3. Calculer la durée d'acquisition
        acquisition_duration = calculateAcquisitionDuration(log_file_path)

        # 4. Compter le nombre de drift fix
        drift_fix_count = countNumberOfDriftFix(log_file_path, last_acquisition_line_number)

        # 5. Calculer les moyennes selon le type
        if acquisition_type == "prior":
            loops_stats = calculateAverageLoopsPrior(log_file_path, last_acquisition_line_number)
            max_retry_stats = countMaxRetryPrior(log_file_path, last_acquisition_line_number)

            analysis_results = {
                "acquisition_type": acquisition_type,
                "last_acquisition": last_acquisition,
                "average_value": loops_stats["average_loops"],
                "total_measurements": loops_stats["total_measurements"],  # Toutes les mesures
                "done_measurements": loops_stats["done_measurements"],  # Seulement les Done
                "timeout_measurements": loops_stats["timeout_measurements"],  # Seulement les Timeout
                "total_wells": loops_stats["total_wells"],
                "values": loops_stats["loops_values"],
                "wells_data": loops_stats["wells_data"],
                "max_retry_count": max_retry_stats["max_retry_count"],
                "max_retry_details": max_retry_stats["max_retry_lines"],
                "acquisition_duration": acquisition_duration
            }
        else:  # custom_focus
            moves_stats = calculateAverageMovesCustomFocus(log_file_path, last_acquisition_line_number)
            max_retry_stats = countMaxRetryCustomFocus(log_file_path, last_acquisition_line_number)

            analysis_results = {
                "acquisition_type": acquisition_type,
                "last_acquisition": last_acquisition,
                "average_value": moves_stats["average_moves"],
                "total_measurements": moves_stats["total_measurements"],
                "total_wells": moves_stats["total_wells"],
                "values": moves_stats["moves_values"],
                "wells_data": moves_stats["wells_data"],
                "max_retry_count": max_retry_stats["max_retry_count"],
                "max_retry_details": max_retry_stats["max_retry_lines"],
                "acquisition_duration": acquisition_duration
            }

        # Ajouter les informations de drift fix
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
        # Obtenir le fichier de log
        log_file_path = getLogFile(folder_path)

        # Analyser le fichier
        analysis = analyzeLogFile(log_file_path)

        # Créer le DataFrame de résultats
        if analysis["acquisition_type"] == "prior":
            report_data = {
                "Type d'acquisition": [analysis["acquisition_type"]],
                "Durée d'acquisition (minutes)": [analysis["acquisition_duration"]["duration_minutes"]],
                "Nombre moyen de loops": [analysis["average_value"]],
                "Nombre total de mesures": [analysis["total_measurements"]],  # Inclut Done + Timeout
                "Mesures 'Done'": [analysis.get("done_measurements", "N/A")],  # Seulement les Done
                "Mesures 'Timeout'": [analysis.get("timeout_measurements", "N/A")],  # Seulement les Timeout
                "Nombre total de puits": [analysis["total_wells"]],
                "Nombre de max retry": [analysis["max_retry_count"]],
                "Nombre de Drift Fix": [analysis["drift_fix_count"]],

            }
        else:  # custom_focus
            report_data = {
                "Type d'acquisition": [analysis["acquisition_type"]],
                "Durée d'acquisition (minutes)": [analysis["acquisition_duration"]["duration_minutes"]],
                "Nombre moyen de moves": [analysis["average_value"]],
                "Nombre total de mesures": [analysis["total_measurements"]],
                "Nombre total de puits": [analysis["total_wells"]],
                "Nombre de max retry": [analysis["max_retry_count"]],
                "Nombre de Time out": [len(analysis["max_retry_details"])],
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
        # Obtenir le fichier de log
        log_file_path = getLogFile(folder_path)

        # Analyser le fichier
        analysis = analyzeLogFile(log_file_path)

        summary = {
            "file_path": log_file_path,
            "acquisition_type": analysis["acquisition_type"],
            "acquisition_duration_minutes": analysis["acquisition_duration"]["duration_minutes"],
            "total_wells": analysis["total_wells"],
            "total_measurements": analysis["total_measurements"],
            "average_value": analysis["average_value"],
            "max_retry_count": analysis["max_retry_count"]
        }

        return summary

    except Exception as e:
        raise ValueError(f"Erreur lors de la génération du résumé: {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    try:
        # Chemin vers le dossier contenant le fichier de log
        folder_path = "C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/log"

        # Résumé complet
        print("=== Résumé de l'analyse ===")
        summary = generateSummaryReport(folder_path)
        for key, value in summary.items():
            print(f"{key}: {value}")



        # Analyse d'un seul fichier
        print("\n=== Analyse du fichier de log ===")
        report = generateLogAnalysisReport(folder_path)
        print("Rapport d'analyse:")
        print(report.to_string(index=False))

        # Sauvegarder le rapport
        report.to_csv("analyse_log.csv", index=False)
        print(f"\nRapport sauvegardé: analyse_log.csv")

    except Exception as e:
        print(f"Erreur: {e}")