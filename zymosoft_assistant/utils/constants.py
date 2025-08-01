#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de constantes pour l'assistant d'installation ZymoSoft
"""

import os
from pathlib import Path
import sys


def resource_path(relative_path):
    """
    Retourne le chemin absolu d'une ressource, compatible PyInstaller et exécution normale.
    Exemple d'appel : resource_path("assets/icons/icon.png")
    """
    try:
        # Si exécuté comme un fichier compilé par PyInstaller
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            return os.path.join(base_path, "zymosoft_assistant", relative_path)
        else:
            # Si exécuté normalement
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)
    except Exception as e:
        print(f"Error resolving resource path: {e}")
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)

# Chemins de base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Chemin de base de l'installation ZymoSoft
ZYMOSOFT_BASE_PATH = "C:/Users/Public/Zymoptiq"

# Schéma de couleurs de l'interface
COLOR_SCHEME = {
    'primary': '#009967',
    'primary_hover': '#007d54',
    'primary_pressed': '#006b47',
    'light_background' : '#f0f0f0',
    'hightlight' : '#e0f7fa',
    'disabled' : '#cccccc',
    'background': 'white',
    'surface': '#ffffff',
    'text': '#333333',
    'text_secondary': '#666666',
    'border': '#cccccc',
    'disabled': '#cccccc',
    'error': '#ff0000',
    'success': '#28a745',
    'warning': '#ffc107',
    'info': '#17a2b8'
}

# Configuration de l'application
APP_CONFIG = {
    'title': "ZymDeploy",
    'version': '1.0.0',
    'window_width': 1200,
    'window_height': 1000,
    'min_width': 640,
    'min_height': 480,
    'icon_path': resource_path("assets/icons/icon.png"),
}

# Étapes de l'assistant
STEPS = [
    {
        'id': 'step1',
        'title': "Saisie des informations client",
        'description': "Entrez les informations du client pour cette installation"
    },
    {
        'id': 'step2',
        'title': "Vérifications pré-validation",
        'description': "Vérification de l'installation ZymoSoft et des fichiers de configuration"
    },
    {
        'id': 'step3',
        'title': "Validation par acquisitions",
        'description': "Réalisation et analyse des acquisitions de validation"
    },
    {
        'id': 'step4',
        'title': "Clôture de l'installation",
        'description': "Finalisation de l'installation et génération du rapport"
    }
]

# Types de plaques
PLATE_TYPES = [
    {
        'id': 'micro_depot',
        'name': "Micro dépôt",
        'description': "Plaque pour micro dépôts"
    },
    {
        'id': 'nanofilm',
        'name': "Nanofilm",
        'description': "Plaque pour nanofilms"
    }
]

# Modes d'acquisition
ACQUISITION_MODES = [
    {
        'id': 'client',
        'name': "Client",
        'description': "Mode client standard"
    },
    {
        'id': 'expert',
        'name': "Expert",
        'description': "Mode expert avec options avancées"
    }
]

# Actions de finalisation
CLEANUP_ACTIONS = [
    {
        'id': 'client_mode',
        'name': "Passer en mode client",
        'description': "Modifier Config.ini pour définir ExpertMode=false",
        'default': True
    },
    {
        'id': 'clean_pc',
        'name': "Nettoyer le PC",
        'description': "Supprimer les données d'acquisitions de test et vider le dossier Diag/Temp",
        'default': True
    }
]

# Structure de l'installation ZymoSoft
ZYMOSOFT_STRUCTURE = {
    'bin': {
        'required': True,
        'files': [
            {'name': 'ZymoCubeCtrl.exe', 'required': True},
            {'name': 'ZymoSoft.exe', 'required': True},
            {'name': 'Config.ini', 'required': True},
            {'name': 'PlateConfig.ini', 'required': True},
            {'name': 'ZymoCubeCtrl.ini', 'required': True}
        ],
        'dirs': [
            {'name': 'workers', 'required': True}
        ]
    },
    'etc': {
        'required': True,
        'dirs': [
            {'name': 'Interf', 'required': True},
            {'name': 'Reflecto', 'required': True}
        ]
    },
    'Resultats': {
        'required': True
    }
}

# Configuration requise dans Config.ini
CONFIG_INI_REQUIRED = {
    'Application': {
        'ExpertMode': 'true',
        'ExportAcquisitionDetailResults': 'true'
    },
    'Hardware': {
        'Controller': 'ZymoCubeCtrl'
    },
    'Interf': {
        'Worker': None,  # Vérifié dynamiquement
        'MaxProcesses': None  # Optionnel
    },
    'Reflecto': {
        'Worker': None,  # Vérifié dynamiquement
        'MaxProcesses': None  # Optionnel
    }
}

# Configuration requise dans ZymoCubeCtrl.ini
ZYMOCUBE_CTRL_INI_REQUIRED = {
    'Motors': {
        'Port': None  # Vérifié dynamiquement
    },
    'Defaults': {
        'VideoPreview': 'false',
        'ImageDestDir': None  # Vérifié dynamiquement
    },
    'PlateType': None  # Vérifié dynamiquement
}



# Fichiers de température à vérifier dans PlateConfig.ini
TEMPERATURE_FILES = [
    'IMin455',
    'IMax455',
    'IMin730',
    'IMax730'
]

# Critères de validation pour la comparaison acquisition déploiement vs acquisition référence
VALIDATION_CRITERIA = {
    'r2': {
        'min': 0.98,
        'max': 1.0,
        'description': "R² (coefficient de détermination)"
    },
    'intercept': {
        'min': -5.0,
        'max': 5.0,
        'description': "Ordonnée à l'origine"
    },
    'slope': {
        'min': 0.95,
        'max': 1.05,
        'description': "Pente"
    },
    'nb_puits_loin_fit': {
        'min': 0,
        'max': 10,
        'description': "Nombre de puits dont biais relatif > 5%"
    }
}
