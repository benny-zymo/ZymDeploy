#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de vérification de la configuration ZymoSoft
"""

import os
import logging
import configparser
from typing import Dict, Any, List, Tuple
from pathlib import Path
from zymosoft_assistant.utils.helpers import  get_exe_version

logger = logging.getLogger(__name__)

class ConfigChecker:
    """
    Classe responsable de la vérification de la structure d'installation
    et des fichiers de configuration de ZymoSoft
    """

    def __init__(self, base_path: str = None):
        """
        Initialise le vérificateur de configuration

        Args:
            base_path: Chemin de base de l'installation ZymoSoft
                      (par défaut: C:/Users/Public/Zymoptiq/ZymoSoft_V*)
        """
        self.base_path = base_path
        if not self.base_path:
            # Recherche automatique du dossier ZymoSoft
            self._find_zymosoft_installation()

        self.version = self._extract_version_from_path()
        logger.info(f"Vérification de l'installation ZymoSoft version {self.version} dans {self.base_path}")

    def _find_zymosoft_installation(self):
        """Recherche automatique du dossier d'installation ZymoSoft"""
        base_dir = Path("C:/Users/Public/Zymoptiq")
        if not base_dir.exists():
            logger.warning(f"Dossier de base {base_dir} non trouvé")
            return

        # Recherche des dossiers ZymoSoft_V*
        zymosoft_dirs = list(base_dir.glob("ZymoSoft_V*"))

        if not zymosoft_dirs:
            logger.warning("Aucune installation ZymoSoft trouvée")
            return

        # Utilise l'installation la plus récente (par ordre alphabétique)
        self.base_path = str(sorted(zymosoft_dirs)[-1])
        logger.info(f"Installation ZymoSoft trouvée: {self.base_path}")

    def _extract_version_from_path(self) -> str:
        """Extrait la version de ZymoSoft à partir du chemin d'installation"""
        if not self.base_path:
            return "inconnue"

        path = Path(self.base_path)
        if not "ZymoSoft_V" in path.name:
            return "inconnue"

        return path.name.replace("ZymoSoft_V", "")

    def check_installation_structure(self) -> Dict[str, bool]:
        """
        Vérifie la structure de l'installation ZymoSoft

        Returns:
            Dictionnaire avec les résultats des vérifications
        """
        if not self.base_path or not os.path.exists(self.base_path):
            logger.error(f"Chemin d'installation non valide: {self.base_path}")
            return {"installation_valid": False}

        results = {
            "installation_valid": True,
            "bin_exists": False,
            "etc_exists": False,
            "resultats_exists": False,
            "zymocubectrl_exists": False,
            "zymosoft_exists": False,
            "workers_exists": False,
            "version_match": False
        }

        # Vérification des dossiers principaux
        bin_path = os.path.join(self.base_path, "bin")
        etc_path = os.path.join(self.base_path, "etc")
        resultats_path = os.path.join(self.base_path, "Resultats")

        results["bin_exists"] = os.path.exists(bin_path)
        results["etc_exists"] = os.path.exists(etc_path)
        results["resultats_exists"] = os.path.exists(resultats_path)

        # si resultat n'existe pas, on le crée
        if not results["resultats_exists"]:
            try:
                os.makedirs(resultats_path)
                logger.info(f"Dossier Resultats créé: {resultats_path}")
                results["resultats_exists"] = True
            except Exception as e:
                logger.error(f"Erreur lors de la création du dossier Resultats: {e}")
                results["installation_valid"] = False
                return results

        # Vérification des fichiers dans bin/
        if results["bin_exists"]:
            zymocubectrl_path = os.path.join(bin_path, "ZymoCubeCtrl.exe")
            zymosoft_path = os.path.join(bin_path, "ZymoSoft.exe")
            workers_path = os.path.join(bin_path, "workers")

            results["zymocubectrl_exists"] = os.path.exists(zymocubectrl_path)
            results["zymosoft_exists"] = os.path.exists(zymosoft_path)
            results["workers_exists"] = os.path.exists(workers_path)

            # Vérification de la version de ZymoSoft.exe
            if results["zymosoft_exists"]:
                exe_version = get_exe_version(zymosoft_path)

                if exe_version and exe_version.startswith(self.version):
                    # afficher les deux versions
                    logger.info(f"Version de ZymoSoft.exe trouvée: {exe_version}")
                    logger.info(f"Version de ZymoSoft.exe correspondante: {self.version}")
                    results["version_match"] = True
                else:
                    logger.warning(f"Version de ZymoSoft.exe non correspondante: {exe_version} (attendu: {self.version})")
                    results["version_match"] = False


        # Mise à jour du statut global
        results["installation_valid"] = (
            results["bin_exists"] and
            results["etc_exists"] and
            results["resultats_exists"] and
            results["zymocubectrl_exists"] and
            results["zymosoft_exists"] and
            results["workers_exists"] and
            results["version_match"]
        )

        return results

    def validate_config_ini(self) -> Dict[str, Any]:
        """
        Valide le fichier Config.ini

        Returns:
            Dictionnaire avec les résultats de validation
        """
        config_path = os.path.join(self.base_path, "etc", "Config.ini")

        if not os.path.exists(config_path):
            logger.error(f"Fichier Config.ini non trouvé: {config_path}")
            return {"config_valid": False, "errors": ["Fichier Config.ini non trouvé"]}

        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8-sig')

        results = {
            "config_valid": True,
            "errors": [],
            "warnings": [],
            "values": {}
        }

        # Vérification des sections obligatoires
        required_sections = ["Application", "Hardware", "Interf", "Reflecto"]
        for section in required_sections:
            if section not in config:
                results["errors"].append(f"Section [{section}] manquante")
                results["config_valid"] = False

        # Vérification des propriétés obligatoires
        checks = [
            ("Application", "ExpertMode", "true"),
            ("Application", "ExportAcquisitionDetailResults", "true"),
            ("Hardware", "Controller", "ZymoCubeCtrl"),
        ]

        for section, key, expected_value in checks:
            if section in config and key in config[section]:
                value = config[section][key]
                results["values"][f"{section}.{key}"] = value

                if value.lower() != expected_value.lower():
                    results["warnings"].append(
                        f"Valeur incorrecte pour [{section}] {key}: "
                        f"'{value}' (attendu: '{expected_value}')"
                    )
            else:
                if section in config:
                    results["errors"].append(f"Propriété '{key}' manquante dans [{section}]")
                    results["config_valid"] = False

        # Vérification des workers
        worker_checks = [
            ("Interf", "Worker"),
            ("Reflecto", "Worker")
        ]

        for section, key in worker_checks:
            if section in config and key in config[section]:
                worker_path = config[section][key]
                results["values"][f"{section}.{key}"] = worker_path

                # Vérifier que le chemin du worker existe
                full_worker_path = os.path.normpath(
                    os.path.join(self.base_path, "bin", worker_path.replace("\\", os.path.sep))
                )

                if not os.path.exists(full_worker_path):
                    full_worker_path_with_exe = full_worker_path + ".exe"
                    if not os.path.exists(full_worker_path_with_exe):
                        results["errors"].append(
                            f"Worker non trouvé: {worker_path}"
                        )
                        results["config_valid"] = False


            else:
                if section in config:
                    results["errors"].append(f"Propriété '{key}' manquante dans [{section}]")
                    results["config_valid"] = False

        return results

    def validate_plate_config_ini(self) -> Dict[str, Any]:
        """
        Valide le fichier PlateConfig.ini

        Returns:
            Dictionnaire avec les résultats de validation
        """
        config_path = os.path.join(self.base_path, "etc", "PlateConfig.ini")

        if not os.path.exists(config_path):
            logger.error(f"Fichier PlateConfig.ini non trouvé: {config_path}")
            return {"config_valid": False, "errors": ["Fichier PlateConfig.ini non trouvé"]}

        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8-sig')

        results = {
            "config_valid": True,
            "errors": [],
            "warnings": [],
            "plate_types": [],
            "configs": {}
        }

        # Vérification de la section PlateType
        if "PlateType" not in config:
            results["errors"].append("Section [PlateType] manquante")
            results["config_valid"] = False
            return results

        # Liste des types de plaques
        for plate_type, config_name in config["PlateType"].items():
            results["plate_types"].append({
                "name": plate_type,
                "config": config_name
            })

        # Vérification des configurations de plaques
        for plate_info in results["plate_types"]:
            config_section = f"PlateConfig:{plate_info['config']}"

            if config_section not in config:
                results["errors"].append(f"Section [{config_section}] manquante")
                results["config_valid"] = False
                continue

            plate_config = {
                "name": plate_info["config"],
                "interf_params": None,
                "reflecto_params": None,
                "temperature_files": []
            }

            # Vérification des paramètres Interf et Reflecto - une config ne peut pas avoir les deux
            has_interf = False
            has_reflecto = False

            if "InterfParams" in config[config_section]:
                has_interf = True
                interf_params = config[config_section]["InterfParams"]
                plate_config["interf_params"] = interf_params

                # Vérifier que le fichier existe
                interf_path = os.path.join(self.base_path, "etc", "Interf", interf_params)
                if not os.path.exists(interf_path):
                    results["errors"].append(f"Fichier InterfParams non trouvé: {interf_params}")
                    results["config_valid"] = False

            if "ReflectoParams" in config[config_section]:
                has_reflecto = True
                reflecto_params = config[config_section]["ReflectoParams"]
                plate_config["reflecto_params"] = reflecto_params

                # Vérifier que le fichier existe
                reflecto_path = os.path.join(self.base_path, "etc", "Reflecto", reflecto_params)
                if not os.path.exists(reflecto_path):
                    results["errors"].append(f"Fichier ReflectoParams non trouvé: {reflecto_params}")
                    results["config_valid"] = False

            if not has_interf and not has_reflecto:
                results["errors"].append(f"Aucun paramètre InterfParams ou ReflectoParams dans [{config_section}]")
                results["config_valid"] = False
            elif has_interf and has_reflecto:
                results["errors"].append(
                    f"Les paramètres InterfParams et ReflectoParams ne peuvent pas être présents simultanément dans [{config_section}]")
                results["config_valid"] = False

            # Vérification des fichiers de température
            temp_files = [
                "IMin455", "IMax455", "IMin730", "IMax730"
            ]

            for temp_key in temp_files:
                if temp_key in config[config_section] and not config[config_section][temp_key].startswith("#"):
                    temp_file = config[config_section][temp_key]
                    plate_config["temperature_files"].append({
                        "key": temp_key,
                        "file": temp_file
                    })

                    # Vérifier que le fichier existe
                    temp_path = os.path.join(self.base_path, "etc", "Reflecto", temp_file)
                    if not os.path.exists(temp_path):
                        results["errors"].append(f"Fichier de température non trouvé: {temp_file}")
                        results["config_valid"] = False

            results["configs"][plate_info["config"]] = plate_config

        return results
    def validate_zymocube_ctrl_ini(self) -> Dict[str, Any]:
        """
        Valide le fichier ZymoCubeCtrl.ini

        Returns:
            Dictionnaire avec les résultats de validation
        """
        config_path = os.path.join(self.base_path, "etc", "ZymoCubeCtrl.ini")

        if not os.path.exists(config_path):
            logger.error(f"Fichier ZymoCubeCtrl.ini non trouvé: {config_path}")
            return {"config_valid": False, "errors": ["Fichier ZymoCubeCtrl.ini non trouvé"]}

        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8-sig')

        results = {
            "config_valid": True,
            "errors": [],
            "warnings": [],
            "values": {},
            "plate_types": []
        }

        # Vérification des sections obligatoires
        required_sections = ["Motors", "Defaults", "PlateType"]
        for section in required_sections:
            if section not in config:
                results["errors"].append(f"Section [{section}] manquante")
                results["config_valid"] = False

        # Vérification du port COM
        if "Motors" in config and "Port" in config["Motors"]:
            port = config["Motors"]["Port"]
            results["values"]["com_port"] = port
        else:
            if "Motors" in config:
                results["errors"].append("Propriété 'Port' manquante dans [Motors]")
                results["config_valid"] = False

        # Vérification des valeurs par défaut
        if "Defaults" in config:
            # Vérification de VideoPreview
            if "VideoPreview" in config["Defaults"]:
                video_preview = config["Defaults"]["VideoPreview"]
                results["values"]["video_preview"] = video_preview

                if video_preview.lower() != "false":
                    results["warnings"].append(
                        f"Valeur incorrecte pour [Defaults] VideoPreview: "
                        f"'{video_preview}' (attendu: 'false')"
                    )
            else:
                results["errors"].append("Propriété 'VideoPreview' manquante dans [Defaults]")
                results["config_valid"] = False

            # Vérification de ImageDestDir
            if "ImageDestDir" in config["Defaults"]:
                image_dest_dir = config["Defaults"]["ImageDestDir"]
                results["values"]["image_dest_dir"] = image_dest_dir

                # Vérifier que le dossier existe
                if not os.path.exists(image_dest_dir):
                    results["errors"].append(f"Dossier ImageDestDir non trouvé: {image_dest_dir}")
                    results["config_valid"] = False
            else:
                results["errors"].append("Propriété 'ImageDestDir' manquante dans [Defaults]")
                results["config_valid"] = False

        # Liste des types de plaques
        if "PlateType" in config:
            for plate_type, value in config["PlateType"].items():
                if not plate_type.startswith("#"):
                    results["plate_types"].append(plate_type)

        return results
