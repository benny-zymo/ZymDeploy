#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de validation des fichiers ZymoSoft
"""

import os
import logging
import configparser
from typing import Dict, Any, List, Tuple, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class FileValidator:
    """
    Classe responsable de la validation des fichiers et dossiers
    nécessaires pour l'installation ZymoSoft
    """
    
    def __init__(self, base_path: str):
        """
        Initialise le validateur de fichiers
        
        Args:
            base_path: Chemin de base de l'installation ZymoSoft
        """
        self.base_path = base_path
        logger.info(f"Validation des fichiers dans {self.base_path}")
    
    def validate_directory_structure(self) -> Dict[str, Any]:
        """
        Valide la structure des dossiers de l'installation
        
        Returns:
            Dictionnaire avec les résultats de validation
        """
        if not self.base_path or not os.path.exists(self.base_path):
            logger.error(f"Chemin d'installation non valide: {self.base_path}")
            return {
                "valid": False,
                "errors": [f"Chemin d'installation non valide: {self.base_path}"]
            }
        
        required_dirs = [
            "bin",
            "etc",
            "Resultats"
        ]
        
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "directories": {}
        }
        
        # Vérification des dossiers principaux
        for dir_name in required_dirs:
            dir_path = os.path.join(self.base_path, dir_name)
            exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
            
            results["directories"][dir_name] = {
                "exists": exists,
                "path": dir_path
            }
            
            if not exists:
                results["errors"].append(f"Dossier requis non trouvé: {dir_path}")
                results["valid"] = False
        
        # Vérification des sous-dossiers spécifiques
        if results["directories"]["bin"]["exists"]:
            bin_path = results["directories"]["bin"]["path"]
            workers_path = os.path.join(bin_path, "workers")
            
            if not os.path.exists(workers_path) or not os.path.isdir(workers_path):
                results["errors"].append(f"Dossier workers/ non trouvé: {workers_path}")
                results["valid"] = False
            else:
                results["directories"]["workers"] = {
                    "exists": True,
                    "path": workers_path
                }
        
        if results["directories"]["etc"]["exists"]:
            etc_path = results["directories"]["etc"]["path"]
            
            # Vérification des sous-dossiers etc/
            etc_subdirs = ["Interf", "Reflecto"]
            for subdir in etc_subdirs:
                subdir_path = os.path.join(etc_path, subdir)
                exists = os.path.exists(subdir_path) and os.path.isdir(subdir_path)
                
                results["directories"][f"etc_{subdir}"] = {
                    "exists": exists,
                    "path": subdir_path
                }
                
                if not exists:
                    results["warnings"].append(f"Sous-dossier etc/{subdir}/ non trouvé: {subdir_path}")
        
        return results
    
    def validate_required_files(self) -> Dict[str, Any]:
        """
        Valide la présence des fichiers requis pour l'installation
        
        Returns:
            Dictionnaire avec les résultats de validation
        """
        if not self.base_path or not os.path.exists(self.base_path):
            logger.error(f"Chemin d'installation non valide: {self.base_path}")
            return {
                "valid": False,
                "errors": [f"Chemin d'installation non valide: {self.base_path}"]
            }
        
        bin_path = os.path.join(self.base_path, "bin")
        etc_path = os.path.join(self.base_path, "etc")
        
        required_files = [
            {
                "name": "ZymoCubeCtrl.exe",
                "path": os.path.join(bin_path, "ZymoCubeCtrl.exe"),
                "required": True
            },
            {
                "name": "ZymoSoft.exe",
                "path": os.path.join(bin_path, "ZymoSoft.exe"),
                "required": True
            },
            {
                "name": "Config.ini",
                "path": os.path.join(etc_path, "Config.ini"),
                "required": True
            },
            {
                "name": "PlateConfig.ini",
                "path": os.path.join(etc_path, "PlateConfig.ini"),
                "required": True
            },
            {
                "name": "ZymoCubeCtrl.ini",
                "path": os.path.join(etc_path, "ZymoCubeCtrl.ini"),
                "required": True
            }
        ]
        
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "files": {}
        }
        
        # Vérification des fichiers requis
        for file_info in required_files:
            exists = os.path.exists(file_info["path"]) and os.path.isfile(file_info["path"])
            
            results["files"][file_info["name"]] = {
                "exists": exists,
                "path": file_info["path"]
            }
            
            if not exists and file_info["required"]:
                results["errors"].append(f"Fichier requis non trouvé: {file_info['path']}")
                results["valid"] = False
        
        return results
    
    def validate_workers(self, config_ini_path: str) -> Dict[str, Any]:
        """
        Valide la présence et la version des workers définis dans config.ini
        
        Args:
            config_ini_path: Chemin vers le fichier Config.ini
            
        Returns:
            Dictionnaire avec les résultats de validation
        """
        if not os.path.exists(config_ini_path):
            logger.error(f"Fichier Config.ini non trouvé: {config_ini_path}")
            return {
                "valid": False,
                "errors": [f"Fichier Config.ini non trouvé: {config_ini_path}"]
            }
        
        config = configparser.ConfigParser()
        config.read(config_ini_path)
        
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "workers": []
        }
        
        # Sections contenant des workers
        worker_sections = ["Interf", "Reflecto"]
        
        for section in worker_sections:
            if section not in config:
                results["errors"].append(f"Section [{section}] manquante dans Config.ini")
                results["valid"] = False
                continue
            
            if "Worker" not in config[section]:
                results["errors"].append(f"Propriété 'Worker' manquante dans [{section}]")
                results["valid"] = False
                continue
            
            worker_path = config[section]["Worker"]
            
            # Chemin complet du worker
            full_worker_path = os.path.normpath(
                os.path.join(self.base_path, "bin", worker_path)
            )
            
            worker_info = {
                "name": section,
                "path": worker_path,
                "full_path": full_worker_path,
                "exists": os.path.exists(full_worker_path),
                "version": self._extract_version_from_worker_path(worker_path)
            }
            
            results["workers"].append(worker_info)
            
            if not worker_info["exists"]:
                results["errors"].append(f"Worker non trouvé: {full_worker_path}")
                results["valid"] = False
        
        return results
    
    def _extract_version_from_worker_path(self, worker_path: str) -> str:
        """
        Extrait la version du worker à partir de son chemin
        
        Args:
            worker_path: Chemin du worker
            
        Returns:
            Version extraite ou chaîne vide si non trouvée
        """
        # Exemple: ./workers/Interf_V1.2.3/Interf
        parts = worker_path.split('/')
        
        for part in parts:
            if "_V" in part:
                version_part = part.split("_V")
                if len(version_part) > 1:
                    return version_part[1]
        
        return ""
    
    def validate_temperature_files(self, plate_config_ini_path: str) -> Dict[str, Any]:
        """
        Valide la présence des fichiers de température définis dans PlateConfig.ini
        
        Args:
            plate_config_ini_path: Chemin vers le fichier PlateConfig.ini
            
        Returns:
            Dictionnaire avec les résultats de validation
        """
        if not os.path.exists(plate_config_ini_path):
            logger.error(f"Fichier PlateConfig.ini non trouvé: {plate_config_ini_path}")
            return {
                "valid": False,
                "errors": [f"Fichier PlateConfig.ini non trouvé: {plate_config_ini_path}"]
            }
        
        config = configparser.ConfigParser()
        config.read(plate_config_ini_path)
        
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "temperature_files": []
        }
        
        # Vérification de la section PlateType
        if "PlateType" not in config:
            results["errors"].append("Section [PlateType] manquante dans PlateConfig.ini")
            results["valid"] = False
            return results
        
        # Parcours des configurations de plaques
        for plate_type, config_name in config["PlateType"].items():
            config_section = f"PlateConfig:{config_name}"
            
            if config_section not in config:
                results["warnings"].append(f"Section [{config_section}] manquante dans PlateConfig.ini")
                continue
            
            # Vérification des fichiers de température
            temp_keys = ["IMin455", "IMax455", "IMin730", "IMax730"]
            
            for temp_key in temp_keys:
                # ne pas vérifier les clés commentées
                if temp_key in config[config_section] and not config[config_section][temp_key].startswith("#"):
                    temp_file = config[config_section][temp_key]
                    
                    # Chemin complet du fichier de température
                    temp_path = os.path.join(self.base_path, "etc", "Reflecto", temp_file)
                    
                    temp_file_info = {
                        "plate_type": plate_type,
                        "config": config_name,
                        "key": temp_key,
                        "file": temp_file,
                        "path": temp_path,
                        "exists": os.path.exists(temp_path)
                    }
                    
                    results["temperature_files"].append(temp_file_info)
                    
                    if not temp_file_info["exists"]:
                        results["errors"].append(
                            f"Fichier de température non trouvé: {temp_path} "
                            f"(défini pour {plate_type} dans [{config_section}])"
                        )
                        results["valid"] = False
        
        return results
    
    def validate_params_files(self, plate_config_ini_path: str) -> Dict[str, Any]:
        """
        Valide la présence des fichiers de paramètres définis dans PlateConfig.ini
        
        Args:
            plate_config_ini_path: Chemin vers le fichier PlateConfig.ini
            
        Returns:
            Dictionnaire avec les résultats de validation
        """
        if not os.path.exists(plate_config_ini_path):
            logger.error(f"Fichier PlateConfig.ini non trouvé: {plate_config_ini_path}")
            return {
                "valid": False,
                "errors": [f"Fichier PlateConfig.ini non trouvé: {plate_config_ini_path}"]
            }
        
        config = configparser.ConfigParser()
        config.read(plate_config_ini_path)
        
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "params_files": []
        }
        
        # Vérification de la section PlateType
        if "PlateType" not in config:
            results["errors"].append("Section [PlateType] manquante dans PlateConfig.ini")
            results["valid"] = False
            return results
        
        # Parcours des configurations de plaques
        for plate_type, config_name in config["PlateType"].items():
            config_section = f"PlateConfig:{config_name}"
            
            if config_section not in config:
                results["warnings"].append(f"Section [{config_section}] manquante dans PlateConfig.ini")
                continue
            
            # Vérification des fichiers de paramètres
            param_keys = ["InterfParams", "ReflectoParams"]
            
            for param_key in param_keys:
                if param_key in config[config_section]:
                    param_file = config[config_section][param_key]
                    
                    # Déterminer le sous-dossier en fonction du type de paramètre
                    subdir = "Interf" if param_key == "InterfParams" else "Reflecto"
                    
                    # Chemin complet du fichier de paramètres
                    param_path = os.path.join(self.base_path, "etc", subdir, param_file)
                    
                    param_file_info = {
                        "plate_type": plate_type,
                        "config": config_name,
                        "key": param_key,
                        "file": param_file,
                        "path": param_path,
                        "exists": os.path.exists(param_path)
                    }
                    
                    results["params_files"].append(param_file_info)
                    
                    if not param_file_info["exists"]:
                        results["errors"].append(
                            f"Fichier de paramètres non trouvé: {param_path} "
                            f"(défini pour {plate_type} dans [{config_section}])"
                        )
                        results["valid"] = False
        
        return results
    
    def validate_image_dest_dir(self, zymocube_ctrl_ini_path: str) -> Dict[str, Any]:
        """
        Valide le dossier de destination des images défini dans ZymoCubeCtrl.ini
        
        Args:
            zymocube_ctrl_ini_path: Chemin vers le fichier ZymoCubeCtrl.ini
            
        Returns:
            Dictionnaire avec les résultats de validation
        """
        if not os.path.exists(zymocube_ctrl_ini_path):
            logger.error(f"Fichier ZymoCubeCtrl.ini non trouvé: {zymocube_ctrl_ini_path}")
            return {
                "valid": False,
                "errors": [f"Fichier ZymoCubeCtrl.ini non trouvé: {zymocube_ctrl_ini_path}"]
            }
        
        config = configparser.ConfigParser()
        config.read(zymocube_ctrl_ini_path)
        
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "image_dest_dir": None
        }
        
        # Vérification de la section Defaults
        if "Defaults" not in config:
            results["errors"].append("Section [Defaults] manquante dans ZymoCubeCtrl.ini")
            results["valid"] = False
            return results
        
        # Vérification de ImageDestDir
        if "ImageDestDir" not in config["Defaults"]:
            results["errors"].append("Propriété 'ImageDestDir' manquante dans [Defaults]")
            results["valid"] = False
            return results
        
        image_dest_dir = config["Defaults"]["ImageDestDir"]
        
        # Gestion des chemins Windows avec double backslash
        image_dest_dir = image_dest_dir.replace("\\\\", "\\")
        
        results["image_dest_dir"] = {
            "path": image_dest_dir,
            "exists": os.path.exists(image_dest_dir)
        }
        
        if not results["image_dest_dir"]["exists"]:
            results["errors"].append(f"Dossier ImageDestDir non trouvé: {image_dest_dir}")
            results["valid"] = False
        
        return results