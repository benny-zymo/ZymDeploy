import os
import pandas as pd
import numpy as np
from math import sqrt


def getWellResultFile(folder_path):
    """
    Récupère les fichiers de résultats de puits du dossier spécifié.

    :param folder_path: Chemin vers le dossier contenant les fichiers de résultats de puits.
    :return: Chemin vers le fichier de résultats de puits.
    """
    # Vérifier si le dossier existe
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Le dossier {folder_path} n'existe pas.")

    # Parcourir les fichiers dans le dossier
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xlsx') and "WellResults" in file_name:
            return os.path.join(folder_path, file_name)

    # Si aucun fichier trouvé, lever une erreur
    raise FileNotFoundError(f"Aucun fichier Excel WellResults trouvé dans {folder_path}")


def getNumberOfAreasInWellResultFile(file_path):
    """
    Cette fonction récupère le nombre d'areas dans un fichier de résultats de puits.
    Elle compte simplement le nombre de feuilles dans le xlsx
    :param file_path: Chemin vers le fichier de résultats de puits.
    """
    # Lire le fichier Excel
    try:
        xls = pd.ExcelFile(file_path)
        # Retourner le nombre de feuilles (areas) dans le fichier Excel
        return len(xls.sheet_names)
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier de résultats de puits: {e}")


def getDataForAreaInWellResultFile(file_path, area_index):
    """
    Cette fonction récupère les données pour une area spécifique du tableau WellCalibrationResult.

    :param file_path: Chemin vers le fichier de résultats de puits.
    :param area_index: Index de l'area (basé sur 0).
    :return: Dictionnaire avec les listes 'activity' et 'values'.
    """
    try:
        # Lire le fichier Excel
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names

        if area_index >= len(sheet_names):
            raise IndexError(f"L'index d'area {area_index} est hors limites. Areas disponibles: {len(sheet_names)}")

        # Lire la feuille spécifique
        sheet_name = sheet_names[area_index]
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Trouver la section WellCalibrationResult
        # Chercher la ligne qui contient "WellCalibrationResult"
        calibration_start_row = None
        for idx, row in df.iterrows():
            if any(str(cell).startswith('WellCalibrationResult') for cell in row if pd.notna(cell)):
                calibration_start_row = idx
                break

        if calibration_start_row is None:
            raise ValueError(f"Section WellCalibrationResult non trouvée dans {sheet_name}")

        # Les données actuelles commencent après la ligne d'en-tête
        # Chercher la ligne avec les en-têtes de colonnes (Activity, etc.)
        header_row = None
        for idx in range(calibration_start_row + 1, len(df)):
            row = df.iloc[idx]
            if 'Activity' in str(row.iloc[0]) or any('Activity' in str(cell) for cell in row if pd.notna(cell)):
                header_row = idx
                break

        if header_row is None:
            raise ValueError(f"En-tête de colonne Activity non trouvé dans {sheet_name}")

        # Extraire les données à partir de la ligne après les en-têtes
        data_start_row = header_row + 1

        # Extraire l'activité et les valeurs (4ème colonne = écart type)
        activities = []
        values = []

        for idx in range(data_start_row, len(df)):
            row = df.iloc[idx]

            # Arrêter si on rencontre une ligne vide ou une autre section
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == '':
                break

            # Vérifier si cela ressemble à une ligne de données (première colonne doit être une activité numérique)
            try:
                activity = float(str(row.iloc[0]).replace(',', '.'))  # Gérer le séparateur décimal virgule
                if len(row) >= 4 and pd.notna(row.iloc[3]):  # 4ème colonne (index 3)
                    value = float(str(row.iloc[3]).replace(',', '.'))  # Gérer le séparateur décimal virgule
                    activities.append(activity)
                    values.append(value)
            except (ValueError, IndexError):
                # Ignorer les lignes qui ne contiennent pas de données numériques
                continue

        return {
            'activity': activities,
            'values': values
        }

    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture de l'area {area_index} depuis {file_path}: {e}")


def getBlankDataForAreaInWellResultFile(file_path, area_index):
    """
    Cette fonction récupère les données des blancs pour une area spécifique du tableau WellBlankResult.

    :param file_path: Chemin vers le fichier de résultats de puits.
    :param area_index: Index de l'area (basé sur 0).
    :return: Liste des valeurs de dégradation des blancs non exclus.
    """
    try:
        # Lire le fichier Excel
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names

        if area_index >= len(sheet_names):
            raise IndexError(f"L'index d'area {area_index} est hors limites. Areas disponibles: {len(sheet_names)}")

        # Lire la feuille spécifique
        sheet_name = sheet_names[area_index]
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Trouver la section WellBlankResult
        blank_start_row = None
        for idx, row in df.iterrows():
            if any(str(cell).startswith('WellBlankResult') for cell in row if pd.notna(cell)):
                blank_start_row = idx
                break

        if blank_start_row is None:
            raise ValueError(f"Section WellBlankResult non trouvée dans {sheet_name}")

        # Chercher la ligne avec les en-têtes de colonnes
        header_row = None
        for idx in range(blank_start_row + 1, len(df)):
            row = df.iloc[idx]
            if 'Well' in str(row.iloc[0]) or any('Well' in str(cell) for cell in row if pd.notna(cell)):
                header_row = idx
                break

        if header_row is None:
            raise ValueError(f"En-tête de colonne Well non trouvé dans {sheet_name}")

        # Extraire les données à partir de la ligne après les en-têtes
        data_start_row = header_row + 1

        blank_values = []

        for idx in range(data_start_row, len(df)):
            row = df.iloc[idx]

            # Arrêter si on rencontre une ligne vide ou une autre section
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == '':
                break

            # Vérifier si la ligne contient des données de blancs
            try:
                # Colonnes attendues : Well, Trouble, Zymunit, Exclusion, Exclusion comment
                well = str(row.iloc[0]).strip()
                if len(row) >= 4:
                    zymunit_value = row.iloc[2]  # Colonne Zymunit (index 2)
                    exclusion = row.iloc[3]  # Colonne Exclusion (index 3)

                    # Vérifier que l'exclusion est False et que la valeur Zymunit est valide
                    if (str(exclusion).lower() == 'false' and
                            pd.notna(zymunit_value) and
                            str(zymunit_value).strip() != ''):
                        zymunit_float = float(str(zymunit_value).replace(',', '.'))
                        blank_values.append(zymunit_float)

            except (ValueError, IndexError):
                # Ignorer les lignes qui ne contiennent pas de données numériques valides
                continue

        return blank_values

    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture des blancs pour l'area {area_index} depuis {file_path}: {e}")


def calculateLODLOQ(file_path, area_index):
    """
    Calcule la LOD et LOQ pour une area spécifique.

    :param file_path: Chemin vers le fichier de résultats de puits.
    :param area_index: Index de l'area (basé sur 0).
    :return: Dictionnaire avec les valeurs LOD et LOQ.
    """
    try:
        # Récupérer les données des blancs
        blank_values = getBlankDataForAreaInWellResultFile(file_path, area_index)

        if not blank_values:
            raise ValueError(f"Aucune donnée de blanc valide trouvée pour l'area {area_index + 1}")

        if len(blank_values) < 2:
            raise ValueError(f"Nombre insuffisant de blancs pour l'area {area_index + 1} (minimum 2 requis)")

        # Calculer la moyenne des blancs
        mean_blank = np.mean(blank_values)

        # Calculer l'écart-type des blancs
        std_blank = np.std(blank_values, ddof=0)  # ddof=0 pour la population complète

        # Calculer LOD et LOQ
        lod = mean_blank + 3 * std_blank
        loq = mean_blank + 10 * std_blank

        return {
            'lod': lod,
            'loq': loq,
            'mean_blank': mean_blank,
            'std_blank': std_blank,
            'n_blanks': len(blank_values)
        }

    except Exception as e:
        raise ValueError(f"Erreur lors du calcul LOD/LOQ pour l'area {area_index + 1}: {e}")


def calculateLODLOQComparison(acquisition_folder, reference_folder):
    """
    Calcule et compare la LOD et LOQ entre les fichiers d'acquisition et de référence.

    :param acquisition_folder: Chemin vers le dossier contenant le fichier de résultats de puits d'acquisition.
    :param reference_folder: Chemin vers le dossier contenant le fichier de résultats de puits de référence.
    :return: DataFrame avec les résultats de comparaison LOD/LOQ.
    """
    # Obtenir les chemins des fichiers
    acquisition_file_path = getWellResultFile(acquisition_folder)
    reference_file_path = getWellResultFile(reference_folder)

    if not acquisition_file_path or not reference_file_path:
        raise FileNotFoundError("Fichiers de résultats de puits non trouvés dans les dossiers spécifiés.")

    # Obtenir le nombre d'areas
    acquisition_number_of_areas = getNumberOfAreasInWellResultFile(acquisition_file_path)
    reference_number_of_areas = getNumberOfAreasInWellResultFile(reference_file_path)

    if acquisition_number_of_areas != reference_number_of_areas:
        raise ValueError(
            "Le nombre d'areas dans les fichiers de résultats d'acquisition et de référence ne correspondent pas.")

    # Préparer les résultats
    comparison_results = []

    # Traiter chaque area
    for area_index in range(acquisition_number_of_areas):
        try:
            # Calculer LOD/LOQ pour l'acquisition
            acq_results = calculateLODLOQ(acquisition_file_path, area_index)

            # Calculer LOD/LOQ pour la référence
            ref_results = calculateLODLOQ(reference_file_path, area_index)

            # Calculer les différences
            diff_lod = acq_results['lod'] - ref_results['lod']
            diff_loq = acq_results['loq'] - ref_results['loq']

            # Verifier la validité des résultats avec la tolérance acceptable
            lod_tolerance = calculate_lod_loq_tolerance(ref_results['lod'])
            loq_tolerance = calculate_lod_loq_tolerance(ref_results['loq'])

            is_lod_valid = abs(diff_lod) <= lod_tolerance
            is_loq_valid = abs(diff_loq) <= loq_tolerance

            print("is_lod_valid:", is_lod_valid, "is_loq_valid:", is_loq_valid)


            # Calculer les différences relatives en pourcentage
            # diff_lod_percent = (diff_lod / ref_results['lod']) * 100 if ref_results['lod'] != 0 else 0
            # diff_loq_percent = (diff_loq / ref_results['loq']) * 100 if ref_results['loq'] != 0 else 0

            comparison_results.append({
                'Area': area_index + 1,
                'LOD_Ref': round(ref_results['lod'], 4),
                'LOD_Acq': round(acq_results['lod'], 4),
                'LOQ_Ref': round(ref_results['loq'], 4),
                'LOQ_Acq': round(acq_results['loq'], 4),
                'Diff_LOD': round(diff_lod, 4),
                'Diff_LOQ': round(diff_loq, 4),
                'Lod_Valid': is_lod_valid,
                'Loq_Valid': is_loq_valid,
                'N_Blanks_Ref': ref_results['n_blanks'],
                'N_Blanks_Acq': acq_results['n_blanks']
            })

        except Exception as e:
            print(f"Erreur lors du traitement de l'area {area_index + 1}: {e}")
            comparison_results.append({
                'Area': area_index + 1,
                'LOD_Ref': 'ERROR',
                'LOD_Acq': 'ERROR',
                'LOQ_Ref': 'ERROR',
                'LOQ_Acq': 'ERROR',
                'Diff_LOD': 'ERROR',
                'Diff_LOQ': 'ERROR',
                'Diff_LOD_%': 'ERROR',
                'Diff_LOQ_%': 'ERROR',
                'N_Blanks_Ref': 'ERROR',
                'N_Blanks_Acq': 'ERROR'
            })

    # Convertir en DataFrame
    comparison_df = pd.DataFrame(comparison_results)

    return comparison_df


def getActivityRangeFromAreaInWellResultFile(file_path, area_index):
    """
    Cette fonction récupère la plage d'activité pour une area spécifique dans un fichier de résultats de puits.

    :param file_path: Chemin vers le fichier de résultats de puits.
    :param area_index: Index de l'area (basé sur 0).
    :return: Liste des valeurs d'activité.
    """
    data = getDataForAreaInWellResultFile(file_path, area_index)
    return data['activity']


def compareActivityRanges(acquisition_range, reference_range):
    """
    Compare les plages d'activité des fichiers de résultats de puits d'acquisition et de référence.

    :param acquisition_range: Plage d'activité du fichier de résultats de puits d'acquisition.
    :param reference_range: Plage d'activité du fichier de résultats de puits de référence.
    :return: Résultat de comparaison indiquant si les plages correspondent.
    """
    # Convertir en arrays numpy pour faciliter la comparaison
    acq_array = np.array(acquisition_range)
    ref_array = np.array(reference_range)

    # Vérifier s'ils ont la même longueur et les mêmes valeurs
    if len(acq_array) != len(ref_array):
        return False

    # Vérifier si les valeurs sont approximativement égales (permettant de petites différences de virgule flottante)
    return np.allclose(acq_array, ref_array, rtol=1e-6)


def calculate_tolerance(reference_value):
    """
    Calcule la tolérance basée sur la valeur de référence.
        y = mx + b
        Où :
        m = (y₂ - y₁) / (x₂ - x₁)  ← pente

    :param reference_value: Valeur de référence pour calculer la tolérance.
    :return: Valeur de tolérance.
    """
    if reference_value <= 0:
        return 5
    elif reference_value <= 5:
        # Interpolation linéaire entre 0 et 5: la tolérance va de 5 à 3
        # Équation: y = 5 - 0.4*x
        return 5 - 0.4 * reference_value
    elif reference_value <= 10:
        # Interpolation linéaire entre 5 et 10: la tolérance va de 3 à 2
        # Équation: y = 4 - 0.2*x
        return 4 - 0.2 * reference_value
    else:
        # Pour les valeurs > 10, la tolérance est toujours 2
        return 2


def calculate_lod_loq_tolerance(reference_value):
    """
    Calcule la tolérance pour LOD/LOQ basée sur la valeur de référence.
    La tolérance est calculée comme suit:
    - Pour les valeurs <= 0, la tolérance est 5.
    - Pour les valeurs > 0 et <= 5, la tolérance est interpolée linéairement de 5 à 3.
    - Pour les valeurs > 5 et <= 10, la tolérance est interpolée linéairement de 3 à 2.
    :param reference_value:
    :return: float: Valeur de tolérance calculée.
    """

    if reference_value <= 0:
        return 5
    elif reference_value <= 5:
        # Interpolation linéaire entre 0 et 5: la tolérance va de 5 à 3
        # Équation: y = 5 - 0.4*x
        return 5 - 0.4 * reference_value
    elif reference_value <= 10:
        # Interpolation linéaire entre 5 et 10: la tolérance va de 3 à 2
        # Équation: y = 4 - 0.2*x
        return 4 - 0.2 * reference_value
    else:
        # Pour les valeurs > 10, la tolérance est toujours 2
        return 2

def processWellResults(acquisition_folder, reference_folder):
    """
    Traite les résultats de puits pour extraire les données pertinentes et créer un tableau de comparaison.

    :param acquisition_folder: Chemin vers le dossier contenant le fichier de résultats de puits d'acquisition.
    :param reference_folder: Chemin vers le dossier contenant le fichier de résultats de puits de référence.
    :return: DataFrame avec les résultats de comparaison.
    """
    # Obtenir les chemins des fichiers
    acquisition_file_path = getWellResultFile(acquisition_folder)
    reference_file_path = getWellResultFile(reference_folder)

    if not acquisition_file_path or not reference_file_path:
        raise FileNotFoundError("Fichiers de résultats de puits non trouvés dans les dossiers spécifiés.")

    # Obtenir le nombre d'areas
    acquisition_number_of_areas = getNumberOfAreasInWellResultFile(acquisition_file_path)
    reference_number_of_areas = getNumberOfAreasInWellResultFile(reference_file_path)

    if acquisition_number_of_areas != reference_number_of_areas:
        raise ValueError(
            "Le nombre d'areas dans les fichiers de résultats d'acquisition et de référence ne correspondent pas.")

    # Préparer les résultats finaux
    final_results = []

    # Traiter chaque area
    for area_index in range(acquisition_number_of_areas):
        # Obtenir les plages d'activité
        acquisition_activities = getActivityRangeFromAreaInWellResultFile(acquisition_file_path, area_index)
        reference_activities = getActivityRangeFromAreaInWellResultFile(reference_file_path, area_index)

        # Vérifier que les activités correspondent
        if not compareActivityRanges(acquisition_activities, reference_activities):
            raise ValueError(f"Les plages d'activité ne correspondent pas pour l'area {area_index + 1}")

        # Obtenir les données pour les deux fichiers
        acquisition_data = getDataForAreaInWellResultFile(acquisition_file_path, area_index)
        reference_data = getDataForAreaInWellResultFile(reference_file_path, area_index)

        # Créer les lignes pour cette area
        for i, activity in enumerate(acquisition_data['activity']):
            acquisition_value = acquisition_data['values'][i]
            reference_value = reference_data['values'][i]
            diff = abs(acquisition_value - reference_value)  # Utiliser la différence absolue pour la validation

            # Calculer la tolérance basée sur la valeur de référence
            tolerance = calculate_tolerance(reference_value)

            # Déterminer si la différence est dans la tolérance
            is_valid = diff <= tolerance

            final_results.append({
                'activité': activity,
                'area': area_index + 1,  # Indexation basée sur 1 pour l'area
                'acquisition': acquisition_value,
                'reference': reference_value,
                'CV': acquisition_value - reference_value,  # Renommé de diff, garder la différence signée
                'valid': is_valid
            })

    # Convertir en DataFrame
    results_df = pd.DataFrame(final_results)

    return results_df



# Exemple d'utilisation
if __name__ == "__main__":
    try:
        # Chemins des dossiers
        acquisition_folder = "C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/routine_deploiement_demo_07072025/acquisition_deploiement/AM_v3_GPAm241204-25_ZC27_VALID_05062025_01"
        reference_folder = "C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/routine_deploiement_demo_07072025/acquisition_reference/GPAm241204-25"

        # Calculer et comparer LOD/LOQ
        print("=== Comparaison LOD/LOQ ===")
        lod_loq_comparison = calculateLODLOQComparison(acquisition_folder, reference_folder)
        print("Résultats de comparaison LOD/LOQ:")
        print(lod_loq_comparison.to_string(index=False))

        # Sauvegarder le tableau LOD/LOQ
        lod_loq_comparison.to_csv("comparaison_lod_loq.csv", index=False)
        print(f"\nTableau LOD/LOQ sauvegardé: comparaison_lod_loq.csv")

        # Traiter les résultats de puits (fonctionnalité existante)
        print("\n=== Comparaison des résultats de puits ===")
        results = processWellResults(acquisition_folder, reference_folder)

        # Afficher les résultats détaillés
        print("Résultats de comparaison détaillés:")
        print(results.to_string(index=False))

        # Afficher les statistiques de validation
        total_tests = len(results)
        valid_tests = results['valid'].sum()
        validation_rate = (valid_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\nRésumé de validation:")
        print(f"Total des tests: {total_tests}")
        print(f"Tests valides: {valid_tests}")
        print(f"Taux de validation global: {validation_rate:.2f}%")

        # Sauvegarder en CSV
        results.to_csv("comparaison_resultats_puits.csv", index=False)

        print(f"\nFichiers sauvegardés:")
        print(f"- Comparaison LOD/LOQ: comparaison_lod_loq.csv")
        print(f"- Résultats détaillés: comparaison_resultats_puits.csv")

    except Exception as e:
        print(f"Erreur: {e}")