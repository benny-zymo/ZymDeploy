#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 1 de l'assistant d'installation ZymoSoft : Saisie des informations client
"""

import os
import logging
import json
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFrame, QFileDialog, QMessageBox, QGroupBox, QWidget)
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
        Crée les widgets de l'étape 1 avec une hiérarchie claire et cohérente
        """
        # === CONSTANTES DE DESIGN ===
        SPACING_LARGE = 24
        SPACING_MEDIUM = 16
        SPACING_SMALL = 8
        LABEL_WIDTH = 180
        FIELD_WIDTH = 350


        # === SECTION FORMULAIRE ===
        form_group = QGroupBox("Informations client")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                color: #333333;
                border: none;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
            }
        """)
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(SPACING_MEDIUM)
        form_layout.setContentsMargins(SPACING_LARGE, SPACING_LARGE, SPACING_LARGE, SPACING_MEDIUM)

        # === CHAMPS DU FORMULAIRE ===
        # Fonction helper pour créer un champ uniformément avec label au-dessus
        def create_field(label_text, required=True):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(SPACING_SMALL)

            # Label
            label = QLabel(label_text + (" *" if required else ""))
            label.setStyleSheet("font-weight: normal; font-size: 11pt;")
            layout.addWidget(label)

            # Champ de saisie
            field = QLineEdit()
            field.setFixedWidth(FIELD_WIDTH)
            field.setObjectName(label_text.lower().replace(" ", "_"))
            field.setStyleSheet("""
                QLineEdit {
                    padding: 8px 12px;
                    border: 2px solid #E0E0E0;
                    border-radius: 4px;
                    font-size: 11pt;
                    background-color: white;
                }
                QLineEdit:focus {
                    border-color: """ + COLOR_SCHEME['primary'] + """;
                }
                QLineEdit:hover {
                    border-color: #C0C0C0;
                }
                QLineEdit[error=true] {
                    border-color: """ + COLOR_SCHEME['error'] + """;
                }
            """)
            layout.addWidget(field)

            return container, field

        # Nom du client
        client_container, self.client_name_edit = create_field("Nom du client")
        form_layout.addWidget(client_container)

        # Responsable CS
        cs_container, self.cs_responsible_edit = create_field("Responsable CS")
        form_layout.addWidget(cs_container)

        # Responsable instrumentation
        instr_container, self.instrumentation_responsible_edit = create_field("Responsable instrumentation")
        form_layout.addWidget(instr_container)

        self.layout.addWidget(form_group)

        # === SECTION ACTIONS ===
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(SPACING_MEDIUM)
        actions_layout.setContentsMargins(0, SPACING_LARGE, 0, 0)

        # Bouton charger informations précédentes
        load_button = QPushButton("📁 Charger informations précédentes")
        load_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #F8F9FA;
                color: {COLOR_SCHEME['primary']};
                border: 2px solid {COLOR_SCHEME['primary']};
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SCHEME['primary']};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_SCHEME['primary_pressed']};
            }}
        """)
        load_button.clicked.connect(self.load_previous_info)
        actions_layout.addWidget(load_button)

        actions_layout.addStretch(1)
        self.layout.addLayout(actions_layout)

        # === ZONE D'INFORMATION ET ERREURS ===
        info_section = QVBoxLayout()
        info_section.setSpacing(SPACING_SMALL)
        info_section.setContentsMargins(0, SPACING_LARGE, 0, 0)

        # Information obligatoire
        info_label = QLabel("* Tous les champs sont obligatoires")
        info_label.setStyleSheet("font-size: 10pt; color: #888888; font-style: italic;")
        info_section.addWidget(info_label)

        # Message d'erreur (initialement caché)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"""
            color: {COLOR_SCHEME['error']};
            background-color: #FFF5F5;
            border: 1px solid {COLOR_SCHEME['error']};
            border-radius: 4px;
            padding: 12px 16px;
            font-size: 11pt;
            font-weight: 500;
            margin-top: 8px;
        """)
        self.error_label.setWordWrap(True)
        self.error_label.hide()  # Caché par défaut
        # Réserve l'espace pour éviter le compactage des champs lors de l'affichage du message d'erreur
        self.error_label.setMinimumHeight(40)
        info_section.addWidget(self.error_label)

        self.layout.addLayout(info_section)

        # === ESPACE FLEXIBLE ===
        self.layout.addStretch(1)

        # === CONNEXION
        # S DES SIGNAUX ===
        # Validation en temps réel
        self.client_name_edit.textChanged.connect(self.validate)
        self.cs_responsible_edit.textChanged.connect(self.validate)
        self.instrumentation_responsible_edit.textChanged.connect(self.validate)

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

        # Réinitialiser les états d'erreur des champs
        self.client_name_edit.setProperty("error", False)
        self.cs_responsible_edit.setProperty("error", False)
        self.instrumentation_responsible_edit.setProperty("error", False)

        # Appliquer les styles pour refléter les changements
        self.client_name_edit.style().unpolish(self.client_name_edit)
        self.client_name_edit.style().polish(self.client_name_edit)
        self.cs_responsible_edit.style().unpolish(self.cs_responsible_edit)
        self.cs_responsible_edit.style().polish(self.cs_responsible_edit)
        self.instrumentation_responsible_edit.style().unpolish(self.instrumentation_responsible_edit)
        self.instrumentation_responsible_edit.style().polish(self.instrumentation_responsible_edit)

        if not valid:
            # Marquer les champs spécifiques en erreur
            for error in errors:
                if "Nom du client" in error:
                    self.client_name_edit.setProperty("error", True)
                    self.client_name_edit.style().unpolish(self.client_name_edit)
                    self.client_name_edit.style().polish(self.client_name_edit)
                if "Responsable CS" in error:
                    self.cs_responsible_edit.setProperty("error", True)
                    self.cs_responsible_edit.style().unpolish(self.cs_responsible_edit)
                    self.cs_responsible_edit.style().polish(self.cs_responsible_edit)
                if "Responsable instrumentation" in error:
                    self.instrumentation_responsible_edit.setProperty("error", True)
                    self.instrumentation_responsible_edit.style().unpolish(self.instrumentation_responsible_edit)
                    self.instrumentation_responsible_edit.style().polish(self.instrumentation_responsible_edit)

            # Afficher le message d'erreur de manière plus lisible
           # self.error_label.setText("Veuillez remplir tous les champs obligatoires marqués en rouge.")
            #self.error_label.show()
            logger.warning(f"Validation de l'étape 1 échouée: {errors}")
            return False

        # Effacer le message d'erreur
        self.error_label.hide()
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

        # Réinitialiser les états d'erreur
        self.client_name_edit.setProperty("error", False)
        self.cs_responsible_edit.setProperty("error", False)
        self.instrumentation_responsible_edit.setProperty("error", False)

        # Appliquer les styles
        self.client_name_edit.style().unpolish(self.client_name_edit)
        self.client_name_edit.style().polish(self.client_name_edit)
        self.cs_responsible_edit.style().unpolish(self.cs_responsible_edit)
        self.cs_responsible_edit.style().polish(self.cs_responsible_edit)
        self.instrumentation_responsible_edit.style().unpolish(self.instrumentation_responsible_edit)
        self.instrumentation_responsible_edit.style().polish(self.instrumentation_responsible_edit)

        # Masquer le message d'erreur
        self.error_label.hide()

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
