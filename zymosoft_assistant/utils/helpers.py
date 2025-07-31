#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de fonctions utilitaires pour l'assistant d'installation ZymoSoft
"""

import os
import uuid
import json
import logging
import configparser
import shutil
import datetime
import pefile
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .constants import TEMP_DIR, REPORTS_DIR

logger = logging.getLogger(__name__)

# Création des dossiers nécessaires
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_installation_id() -> str:
    """
    Génère un identifiant unique pour l'installation

    Returns:
        Identifiant unique au format UUID
    """
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """
    Retourne un horodatage formaté

    Returns:
        Horodatage au format ISO
    """
    return datetime.datetime.now().isoformat()

def find_zymosoft_installation() -> Optional[str]:
    """
    Recherche automatiquement le dossier d'installation ZymoSoft

    Returns:
        Chemin vers l'installation ZymoSoft ou None si non trouvée
    """
    base_dir = Path("C:/Users/Public/Zymoptiq")
    if not base_dir.exists():
        logger.warning(f"Dossier de base {base_dir} non trouvé")
        return None

    # Recherche des dossiers ZymoSoft_V*
    zymosoft_dirs = list(base_dir.glob("ZymoSoft_V*"))

    if not zymosoft_dirs:
        logger.warning("Aucune installation ZymoSoft trouvée")
        return None

    # Utilise l'installation la plus récente (par ordre alphabétique)
    installation_path = str(sorted(zymosoft_dirs)[-1])
    logger.info(f"Installation ZymoSoft trouvée: {installation_path}")
    return installation_path

def extract_version_from_path(path: str) -> str:
    """
    Extrait la version de ZymoSoft à partir du chemin d'installation

    Args:
        path: Chemin d'installation

    Returns:
        Version extraite ou "inconnue" si non trouvée
    """
    if not path:
        return "inconnue"

    path_obj = Path(path)
    if not "ZymoSoft_V" in path_obj.name:
        return "inconnue"

    return path_obj.name.replace("ZymoSoft_V", "")

def get_exe_version(file_path):
    try:
        pe = pefile.PE(file_path)
        for file_info in pe.FileInfo:
            for entry in file_info:
                if entry.Key == b'StringFileInfo':
                    for string_table in entry.StringTable:
                        for key, value in string_table.entries.items():
                            if key.decode() == "FileVersion":
                                return value.decode()
    except Exception as e:
        return f"Error reading version: {e}"


def save_session_data(data: Dict[str, Any], filename: str = None) -> str:
    """
    Sauvegarde les données de session dans un fichier JSON

    Args:
        data: Données à sauvegarder
        filename: Nom du fichier (par défaut: session_<timestamp>.json)

    Returns:
        Chemin vers le fichier sauvegardé
    """
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.json"

    file_path = os.path.join(TEMP_DIR, filename)

    # Classe d'encodeur personnalisée pour gérer les objets datetime
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient="records")
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, (np.ndarray,)):
                return obj.tolist()
            return super().default(obj)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)

    logger.info(f"Données de session sauvegardées dans {file_path}")
    return file_path

def load_session_data(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Charge les données de session depuis un fichier JSON

    Args:
        file_path: Chemin vers le fichier JSON

    Returns:
        Données chargées ou None en cas d'erreur
    """
    if not os.path.exists(file_path):
        logger.error(f"Fichier de session non trouvé: {file_path}")
        return None

    def convert_numpy_types(obj):
        if isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return obj

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as jde:
                logger.error(f"Erreur de décodage JSON dans {file_path} : {jde}")
                # Optionnel : log un extrait du fichier pour debug
                with open(file_path, 'r', encoding='utf-8') as f2:
                    lines = f2.readlines()
                    error_line = jde.lineno - 1
                    context = lines[max(0, error_line-2):error_line+3]
                    logger.error("Contexte autour de l'erreur JSON :\n" + "".join(context))
                return None
        # Conversion récursive des types numpy si jamais il y en a dans le JSON
        data = convert_numpy_types(data)
        logger.info(f"Données de session chargées depuis {file_path}")
        return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données de session: {str(e)}")
        return None

def validate_client_info(client_info: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Valide les informations client

    Args:
        client_info: Dictionnaire contenant les informations client

    Returns:
        Tuple (valide, liste d'erreurs)
    """
    errors = []

    # Vérification des champs obligatoires
    required_fields = [
        ("name", "Nom du client"),
        ("cs_responsible", "Responsable CS"),
        ("instrumentation_responsible", "Responsable instrumentation")
    ]

    for field_id, field_name in required_fields:
        if field_id not in client_info or not client_info[field_id].strip():
            errors.append(f"Le champ '{field_name}' est obligatoire")

    return len(errors) == 0, errors

def modify_config_ini(config_path: str, section: str, key: str, value: str) -> bool:
    """
    Modifie une valeur dans un fichier de configuration INI

    Args:
        config_path: Chemin vers le fichier INI
        section: Nom de la section
        key: Nom de la clé
        value: Nouvelle valeur

    Returns:
        True si la modification a réussi, False sinon
    """
    if not os.path.exists(config_path):
        logger.error(f"Fichier de configuration non trouvé: {config_path}")
        return False

    try:
        config = configparser.ConfigParser()
        config.read(config_path)

        if section not in config:
            logger.error(f"Section [{section}] non trouvée dans {config_path}")
            return False

        # Modification de la valeur
        config[section][key] = value

        # Sauvegarde du fichier
        with open(config_path, 'w') as f:
            config.write(f)

        logger.info(f"Valeur modifiée dans {config_path}: [{section}] {key}={value}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la modification du fichier de configuration: {str(e)}")
        return False

def clean_temp_directory(temp_dir: str) -> bool:
    """
    Nettoie un répertoire temporaire

    Args:
        temp_dir: Chemin vers le répertoire à nettoyer

    Returns:
        True si le nettoyage a réussi, False sinon
    """
    if not os.path.exists(temp_dir) or not os.path.isdir(temp_dir):
        logger.error(f"Répertoire temporaire non trouvé: {temp_dir}")
        return False

    try:
        # Suppression de tous les fichiers dans le répertoire
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        logger.info(f"Répertoire temporaire nettoyé: {temp_dir}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du répertoire temporaire: {str(e)}")
        return False

def clean_acquisition_data(results_dir: str) -> bool:
    """
    Nettoie les données d'acquisition de test

    Args:
        results_dir: Chemin vers le répertoire de résultats

    Returns:
        True si le nettoyage a réussi, False sinon
    """
    if not os.path.exists(results_dir) or not os.path.isdir(results_dir):
        logger.error(f"Répertoire de résultats non trouvé: {results_dir}")
        return False

    try:
        # Recherche des dossiers contenant "test" dans leur nom
        test_dirs = []
        for item in os.listdir(results_dir):
            item_path = os.path.join(results_dir, item)
            if os.path.isdir(item_path) and "test" in item.lower():
                test_dirs.append(item_path)

        # Suppression des dossiers de test
        for test_dir in test_dirs:
            shutil.rmtree(test_dir)
            logger.info(f"Dossier de test supprimé: {test_dir}")

        logger.info(f"Données d'acquisition de test nettoyées: {len(test_dirs)} dossiers supprimés")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des données d'acquisition: {str(e)}")
        return False

def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille de fichier en unités lisibles

    Args:
        size_bytes: Taille en octets

    Returns:
        Taille formatée (ex: "1.23 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def is_valid_directory(path: str) -> bool:
    """
    Vérifie si un chemin est un répertoire valide et accessible

    Args:
        path: Chemin à vérifier

    Returns:
        True si le chemin est un répertoire valide, False sinon
    """
    return os.path.exists(path) and os.path.isdir(path) and os.access(path, os.R_OK)

def is_valid_file(path: str) -> bool:
    """
    Vérifie si un chemin est un fichier valide et accessible

    Args:
        path: Chemin à vérifier

    Returns:
        True si le chemin est un fichier valide, False sinon
    """
    return os.path.exists(path) and os.path.isfile(path) and os.access(path, os.R_OK)

def create_empty_session() -> Dict[str, Any]:
    """
    Crée une structure de données de session vide

    Returns:
        Dictionnaire de session vide
    """
    return {
        "installation_id": generate_installation_id(),
        "timestamp_start": get_timestamp(),
        "client_info": {
            "name": "",
            "cs_responsible": "",
            "instrumentation_responsible": ""
        },
        "step2_checks": {
            "software_structure": False,
            "config_validation": False,
            "files_found": []
        },
        "acquisitions": [],
        "final_comments": "",
        "cleanup_actions": []
    }

def get_file_extension(file_path: str) -> str:
    """
    Récupère l'extension d'un fichier

    Args:
        file_path: Chemin du fichier

    Returns:
        Extension du fichier (avec le point)
    """
    return os.path.splitext(file_path)[1].lower()

def is_image_file(file_path: str) -> bool:
    """
    Vérifie si un fichier est une image

    Args:
        file_path: Chemin du fichier

    Returns:
        True si le fichier est une image, False sinon
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
    return get_file_extension(file_path) in image_extensions

def is_csv_file(file_path: str) -> bool:
    """
    Vérifie si un fichier est un CSV

    Args:
        file_path: Chemin du fichier

    Returns:
        True si le fichier est un CSV, False sinon
    """
    return get_file_extension(file_path) == '.csv'

def resource_path(relative_path: str) -> str:
    """
    Récupère le chemin absolu d'une ressource, compatible avec PyInstaller

    Cette fonction permet d'accéder aux ressources de l'application, qu'elle soit
    exécutée normalement ou packagée avec PyInstaller.

    Args:
        relative_path: Chemin relatif de la ressource par rapport au répertoire de base

    Returns:
        Chemin absolu vers la ressource
    """
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_path, relative_path)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du chemin de ressource: {str(e)}")
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)
