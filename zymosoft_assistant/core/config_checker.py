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
from zymosoft_assistant.utils.helpers import get_exe_version

logger = logging.getLogger(__name__)

class ConfigChecker:
    """
    Classe responsable de la vérification de la structure d'installation
    et des fichiers de configuration de ZymoSoft
    """

    def __init__(self, base_path: str = None):
        """
        Initializes an instance for handling ZymoSoft installation verification.

        The class is responsible for initializing base configuration, checking
        if the provided path exists, and extracting version details from the ZymoSoft
        installation path.

        :param base_path: The base path of the ZymoSoft installation. If not
            provided, the system will automatically attempt to locate the installation
            directory.
        :type base_path: str
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
        """
        Extracts the version information from the base path if available.

        This method checks the `base_path` attribute and retrieves the version
        information encoded as a suffix in the form '_V' within the path name.
        If the `base_path` attribute is empty or does not contain the version
        identifier, it returns a placeholder value "inconnue".

        :return: The extracted version as a string if found; otherwise, "inconnue".
        :rtype: str
        """
        if not self.base_path:
            return "inconnue"

        path = Path(self.base_path)
        if not "_V" in path.name:
            return "inconnue"

        return path.name.split("_V")[-1]

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
            "installation_valid": False,
            "bin_exists": False,
            "etc_exists": False,
            "resultats_exists": False,
            "zymocubectrl_exists": False,
            "zymosoft_exists": False,
            "workers_exists": False,
            "version_match": False,
            "zymosoft_version": self.version,
            "exe_version": "N/A"
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
                results["exe_version"] = exe_version if exe_version else "N/A"

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
        required_sections = ["Application", "Hardware", "Interf"]
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
                    results["errors"].append(
                        f"Valeur incorrecte pour [{section}] {key}: "
                        f"'{value}' (attendu: '{expected_value}')"
                    )
                    results["config_valid"] = False
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
            if section == "Reflecto" and section not in config:
                # Vérifier si PlateConfig.ini contient ConfigLayer
                plate_config_path = os.path.join(self.base_path, "etc", "PlateConfig.ini")
                if os.path.exists(plate_config_path):
                    plate_config = configparser.ConfigParser()
                    plate_config.read(plate_config_path, encoding='utf-8-sig')
                    for plate_section in plate_config.sections():
                        if plate_section.startswith("PlateConfig:") and "ConfigLayer" in plate_config[plate_section]:
                            logger.debug(f"Détection de ConfigLayer dans {plate_section}, vérification de [Reflecto] et Worker")
                            results["errors"].append(
                                f"Section [Reflecto] et propriété 'Worker' manquantes dans Config.ini, mais ConfigLayer trouvé dans [{plate_section}] de PlateConfig.ini"
                            )
                            results["config_valid"] = False
            elif section in config and key in config[section]:
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
            elif section in config:
                if section == "Reflecto":
                    logger.debug(f"Section [Reflecto] présente mais propriété 'Worker' manquante")
                    results["errors"].append(f"Propriété '{key}' manquante dans [{section}]")
                    results["config_valid"] = False
                else:
                    results["errors"].append(f"Propriété '{key}' manquante dans [{section}]")
                    results["config_valid"] = False

        return results

    def validate_plate_config_ini(self) -> Dict[str, Any]:
        """
        Validates the PlateConfig.ini configuration file and checks for the presence and correctness
        of specified sections and parameters. The function verifies the existence of required
        sections, configuration parameters, and additional files listed within the PlateConfig.ini file.
        It processes data related to plate types, interf and reflecto parameters, as well as
        temperature-related files.

        The validation evaluates the following:
        - Presence of the "PlateType" section is required.
        - Existence of associated plate configurations for each plate type.
        - Validity of specified "InterfParams" and "ReflectoParams" ensuring no simultaneous usage and
          checks for file existence.
        - Presence and existence of required temperature-related files specified for each plate configuration.

        Returns a dictionary containing:
          - Whether the configuration is valid.
          - List of encountered errors and warnings.
          - List of plate types with their respective configuration names.
          - Processed plate configurations with interf parameters, reflecto parameters, and temperature
            file details.

        :param self: The class instance reference used to fetch the base path.
        :return: A dictionary containing validation results with keys:
                 - "config_valid" (bool): Indicates validity of the configuration.
                 - "errors" (list[str]): List of error messages.
                 - "warnings" (list[str]): List of warnings, if any.
                 - "plate_types" (list[dict]): Contains plate type names and their corresponding configs.
                 - "configs" (dict): Processed configurations with interf/reflecto and temperature details.
        :rtype: Dict[str, Any]
        """
        config_path = os.path.join(self.base_path, "etc", "PlateConfig.ini")

        if not os.path.exists(config_path):
            logger.error(f"Fichier PlateConfig.ini non trouvé: {config_path}")
            return {"config_valid": False, "errors": ["Fichier PlateConfig.ini non trouvé"]}

        try:
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8-sig')
        except configparser.Error as e:
            logger.error(f"Erreur de lecture du fichier PlateConfig.ini: {e}")
            return {"config_valid": False, "errors": [f"Erreur de lecture du fichier PlateConfig.ini: {e}"]}

        results = {
            "config_valid": True,
            "errors": [],
            "warnings": [],
            "plate_types": [],
            "configs": {}
        }

        # Vérification obligatoire de la section PlateType
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
                "temperature_files": [],
                "has_config_layer": False
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

            # Vérification de ConfigLayer
            if "ConfigLayer" in config[config_section]:
                plate_config["has_config_layer"] = True

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

        # Vérification des sections obligatoires (PlateType exclu car conditionnel)
        required_sections = ["Motors", "Defaults", "AutoFocus"]
        for section in required_sections:
            if section not in config:
                results["errors"].append(f"Section [{section}] manquante")
                results["config_valid"] = False

        # Vérification du port COM
        if "Motors" in config and "Port" in config["Motors"]:
            port = config["Motors"]["Port"]
            results["values"]["Motor Com Port"] = port
        else:
            if "Motors" in config:
                results["errors"].append("Propriété 'Port' manquante dans [Motors]")
                results["config_valid"] = False

        # Vérification du port COM de l'auto-focus
        if "AutoFocus" in config and "Port" in config["AutoFocus"]:
            port = config["AutoFocus"]["Port"]
            results["values"]["AutoFocus Com Port"] = port
        else:
            if "AutoFocus" in config:
                results["errors"].append("Propriété 'Port' manquante dans [AutoFocus]")
                results["config_valid"] = False

        # Vérification des valeurs par défaut
        if "Defaults" in config:
            # Vérification de VideoPreview
            if "VideoPreview" in config["Defaults"]:
                video_preview = config["Defaults"]["VideoPreview"]
                results["values"]["video_preview"] = video_preview

                if video_preview.lower() != "false":
                    results["errors"].append(
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

        # Vérification cohérente avec PlateConfig.ini (ConfigLayer)
        plate_config_results = self.validate_plate_config_ini()
        has_config_layer = any(
            config.get("has_config_layer", False) for config in plate_config_results.get("configs", {}).values())

        # Gestion des PlateType
        if "PlateType" in config:
            for plate_type, value in config["PlateType"].items():
                if not plate_type.startswith("#"):
                    results["plate_types"].append(plate_type)

        if has_config_layer:
            # Récupérer les PlateType avec ConfigLayer
            plate_types_with_config_layer = [
                pt["name"] for pt in plate_config_results["plate_types"]
                if
                pt["config"] in plate_config_results["configs"] and plate_config_results["configs"][pt["config"]].get(
                    "has_config_layer", False)
            ]

            if not results["plate_types"]:
                # PlateType est requis car ConfigLayer est présent
                results["errors"].append(
                    "Section [PlateType] manquante dans ZymoCubeCtrl.ini alors que des ConfigLayer sont présents dans PlateConfig.ini")
                results["config_valid"] = False
            else:
                # Vérifier que tous les PlateType avec ConfigLayer sont dans ZymoCubeCtrl.ini
                missing_plate_types = [pt for pt in plate_types_with_config_layer if pt not in results["plate_types"]]
                if missing_plate_types:
                    results["errors"].append(
                        f"Les PlateType suivants avec ConfigLayer manquent dans [PlateType] de ZymoCubeCtrl.ini: {', '.join(missing_plate_types)}"
                    )
                    results["config_valid"] = False

                # Vérifier que les PlateType dans ZymoCubeCtrl.ini ont un ConfigLayer dans PlateConfig.ini
                extra_plate_types = [pt for pt in results["plate_types"] if pt not in plate_types_with_config_layer]
                if extra_plate_types:
                    results["errors"].append(
                        f"Les PlateType suivants dans [PlateType] de ZymoCubeCtrl.ini n'ont pas de ConfigLayer dans PlateConfig.ini: {', '.join(extra_plate_types)}"
                    )
                    results["config_valid"] = False
        else:
            # Si aucun ConfigLayer dans PlateConfig.ini, PlateType est facultatif
            if "PlateType" in config and results["plate_types"]:
                logger.info(
                    "Présence de [PlateType] dans ZymoCubeCtrl.ini sans ConfigLayer dans PlateConfig.ini, considéré comme valide (facultatif)")

        return results