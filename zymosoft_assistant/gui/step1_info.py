#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 1 de l'assistant d'installation ZymoSoft : Saisie des informations client
"""

import os
import logging
import json
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QFrame, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

from zymosoft_assistant.utils.constants import COLOR_SCHEME
from zymosoft_assistant.utils.helpers import validate_client_info
from .step_frame import StepFrame

logger = logging.getLogger(__name__)

class Step1Info(StepFrame):
    """
    Classe pour l'étape 1 : Saisie des informations client
    """

    def __init__(self, parent, main_window):
        """
        Initialise l'étape 1

        Args:
            parent: Widget parent
            main_window: Référence vers la fenêtre principale
        """
        # Variables pour les champs de saisie
        self.client_name = ""
        self.cs_responsible = ""
        self.instrumentation_responsible = ""

        # Références aux widgets
        self.client_name_edit = None
        self.cs_responsible_edit = None
        self.instrumentation_responsible_edit = None
        self.error_label = None

        super().__init__(parent, main_window)

        logger.info("Étape 1 initialisée")

    def create_widgets(self):
        """
        Crée les widgets de l'étape 1
        """
        # Utilisation du layout vertical principal
        main_layout = QVBoxLayout()
        self.layout.addLayout(main_layout)

        # Titre de l'étape
        title_label = QLabel("Étape 1 : Saisie des informations client")
        title_label.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {COLOR_SCHEME['primary']};")
        main_layout.addWidget(title_label)
        main_layout.addSpacing(20)

        # Description
        description_label = QLabel("Veuillez saisir les informations du client pour cette installation.")
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(600)
        main_layout.addWidget(description_label)
        main_layout.addSpacing(20)

        # Formulaire
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        main_layout.addWidget(form_frame)

        # Nom du client
        client_name_layout = QHBoxLayout()
        form_layout.addLayout(client_name_layout)

        client_name_label = QLabel("Nom du client :")
        client_name_label.setMinimumWidth(200)
        client_name_layout.addWidget(client_name_label)

        self.client_name_edit = QLineEdit()
        self.client_name_edit.setMinimumWidth(300)
        client_name_layout.addWidget(self.client_name_edit)
        client_name_layout.addStretch(1)

        form_layout.addSpacing(5)

        # Responsable CS
        cs_responsible_layout = QHBoxLayout()
        form_layout.addLayout(cs_responsible_layout)

        cs_responsible_label = QLabel("Responsable CS :")
        cs_responsible_label.setMinimumWidth(200)
        cs_responsible_layout.addWidget(cs_responsible_label)

        self.cs_responsible_edit = QLineEdit()
        self.cs_responsible_edit.setMinimumWidth(300)
        cs_responsible_layout.addWidget(self.cs_responsible_edit)
        cs_responsible_layout.addStretch(1)

        form_layout.addSpacing(5)

        # Responsable instrumentation
        instrumentation_layout = QHBoxLayout()
        form_layout.addLayout(instrumentation_layout)

        instrumentation_label = QLabel("Responsable instrumentation :")
        instrumentation_label.setMinimumWidth(200)
        instrumentation_layout.addWidget(instrumentation_label)

        self.instrumentation_responsible_edit = QLineEdit()
        self.instrumentation_responsible_edit.setMinimumWidth(300)
        instrumentation_layout.addWidget(self.instrumentation_responsible_edit)
        instrumentation_layout.addStretch(1)

        # Zone d'information
        main_layout.addSpacing(20)
        info_label = QLabel("Tous les champs sont obligatoires.")
        info_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # Bouton de chargement des informations précédentes
        main_layout.addSpacing(10)
        load_button = QPushButton("Charger informations précédentes")
        load_button.clicked.connect(self.load_previous_info)
        main_layout.addWidget(load_button, 0, Qt.AlignCenter)

        # Message d'erreur
        main_layout.addSpacing(10)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")
        self.error_label.setWordWrap(True)
        main_layout.addWidget(self.error_label)

        # Ajouter un espace extensible à la fin
        main_layout.addStretch(1)

    def validate(self):
        """
        Valide les données de l'étape 1

        Returns:
            True si les données sont valides, False sinon
        """
        client_info = {
            "name": self.client_name_edit.text(),
            "cs_responsible": self.cs_responsible_edit.text(),
            "instrumentation_responsible": self.instrumentation_responsible_edit.text()
        }

        valid, errors = validate_client_info(client_info)

        if not valid:
            self.error_label.setText("\n".join(errors))
            logger.warning(f"Validation de l'étape 1 échouée: {errors}")
            return False

        # Effacer le message d'erreur
        self.error_label.setText("")
        logger.info("Validation de l'étape 1 réussie")
        return True

    def save_data(self):
        """
        Sauvegarde les données de l'étape 1 dans la session
        """
        self.main_window.session_data["client_info"] = {
            "name": self.client_name_edit.text(),
            "cs_responsible": self.cs_responsible_edit.text(),
            "instrumentation_responsible": self.instrumentation_responsible_edit.text()
        }

        logger.info("Données de l'étape 1 sauvegardées")

    def load_data(self):
        """
        Charge les données de la session dans l'étape 1
        """
        client_info = self.main_window.session_data.get("client_info", {})

        self.client_name_edit.setText(client_info.get("name", ""))
        self.cs_responsible_edit.setText(client_info.get("cs_responsible", ""))
        self.instrumentation_responsible_edit.setText(client_info.get("instrumentation_responsible", ""))

        logger.info("Données de l'étape 1 chargées")

    def reset(self):
        """
        Réinitialise l'étape 1
        """
        self.client_name_edit.setText("")
        self.cs_responsible_edit.setText("")
        self.instrumentation_responsible_edit.setText("")
        self.error_label.setText("")

        logger.info("Étape 1 réinitialisée")

    def load_previous_info(self):
        """
        Charge les informations d'une session précédente
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self.widget,
            "Charger informations client",
            "",
            "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "client_info" in data:
                client_info = data["client_info"]

                self.client_name_edit.setText(client_info.get("name", ""))
                self.cs_responsible_edit.setText(client_info.get("cs_responsible", ""))
                self.instrumentation_responsible_edit.setText(client_info.get("instrumentation_responsible", ""))

                QMessageBox.information(self.widget, "Chargement", "Informations client chargées avec succès.")
                logger.info(f"Informations client chargées depuis {file_path}")
            else:
                QMessageBox.warning(self.widget, "Chargement", "Aucune information client trouvée dans le fichier.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des informations client: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors du chargement:\n{str(e)}")
