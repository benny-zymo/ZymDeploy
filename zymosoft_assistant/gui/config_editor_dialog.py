#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module pour l'édition du fichier config.ini
"""

import os
import logging
import configparser
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QCheckBox, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt

from zymosoft_assistant.utils.constants import COLOR_SCHEME
from zymosoft_assistant.utils.helpers import modify_config_ini

logger = logging.getLogger(__name__)

class ConfigEditorDialog(QDialog):
    """
    Dialogue pour éditer le fichier config.ini
    """

    def __init__(self, parent=None, zymosoft_path=None):
        """
        Initialise le dialogue d'édition du fichier config.ini

        Args:
            parent: Widget parent
            zymosoft_path: Chemin vers l'installation ZymoSoft
        """
        super().__init__(parent)
        self.setWindowTitle("Modifier config.ini")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        self.zymosoft_path = zymosoft_path
        self.config_path = os.path.join(self.zymosoft_path, 'etc', "config.ini") if self.zymosoft_path else None
        
        self.expert_mode_value = False
        self.expert_mode_checkbox = None
        
        self.create_widgets()
        self.load_current_values()
        
    def create_widgets(self):
        """
        Crée les widgets du dialogue
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Titre
        title_label = QLabel("Édition du fichier config.ini")
        title_label.setStyleSheet(f"""
            font-size: 16pt;
            font-weight: bold;
            color: {COLOR_SCHEME['primary']};
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title_label)
        
        # Chemin du fichier
        path_label = QLabel(f"Fichier: {self.config_path}")
        path_label.setStyleSheet("font-size: 10pt; color: #666;")
        main_layout.addWidget(path_label)
        
        # Groupe pour les options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        # Option Expert Mode
        expert_mode_layout = QHBoxLayout()
        expert_mode_label = QLabel("Mode Expert:")
        expert_mode_label.setMinimumWidth(150)
        expert_mode_layout.addWidget(expert_mode_label)
        
        self.expert_mode_checkbox = QCheckBox("Activé")
        self.expert_mode_checkbox.setChecked(self.expert_mode_value)
        expert_mode_layout.addWidget(self.expert_mode_checkbox)
        expert_mode_layout.addStretch(1)
        
        options_layout.addLayout(expert_mode_layout)
        main_layout.addWidget(options_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Enregistrer")
        save_button.clicked.connect(self.save_changes)
        buttons_layout.addWidget(save_button)
        
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch(1)
        
    def load_current_values(self):
        """
        Charge les valeurs actuelles du fichier config.ini
        """
        if not self.config_path or not os.path.exists(self.config_path):
            QMessageBox.critical(self, "Erreur", "Le fichier config.ini n'a pas été trouvé.")
            self.reject()
            return
        
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)
            
            if 'Application' in config and 'expertmode' in config['Application']:
                # Convertir la valeur en booléen
                value_str = config['Application']['ExpertMode'].lower()
                self.expert_mode_value = value_str == 'true'
                
                # Mettre à jour la case à cocher
                if self.expert_mode_checkbox:
                    self.expert_mode_checkbox.setChecked(self.expert_mode_value)
                
                logger.info(f"Valeur actuelle de application.expertmode: {self.expert_mode_value}")
            else:
                logger.warning("La clé Application.ExpertMode n'a pas été trouvée dans config.ini")
                QMessageBox.warning(self, "Attention", 
                                   "La clé 'ExpertMode' n'a pas été trouvée dans la section 'application' du fichier config.ini.")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier config.ini: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la lecture du fichier config.ini:\n{str(e)}")
            self.reject()
    
    def save_changes(self):
        """
        Enregistre les modifications dans le fichier config.ini
        """
        if not self.config_path or not os.path.exists(self.config_path):
            QMessageBox.critical(self, "Erreur", "Le fichier config.ini n'a pas été trouvé.")
            return
        
        try:
            # Récupérer la nouvelle valeur
            new_value = "true" if self.expert_mode_checkbox.isChecked() else "false"
            
            # Modifier le fichier
            if modify_config_ini(self.config_path, "Application", "expertmode", new_value):
                logger.info(f"Valeur Application.ExpertMode modifiée: {new_value}")
                QMessageBox.information(self, "Succès", "La configuration a été modifiée avec succès.")
                self.accept()
            else:
                logger.error("Échec de la modification du fichier config.ini")
                QMessageBox.critical(self, "Erreur", "La modification du fichier config.ini a échoué.")
        except Exception as e:
            logger.error(f"Erreur lors de la modification du fichier config.ini: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la modification du fichier config.ini:\n{str(e)}")