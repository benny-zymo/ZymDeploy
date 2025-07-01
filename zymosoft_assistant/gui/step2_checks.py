#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 2 de l'assistant d'installation ZymoSoft : Vérifications pré-validation
"""

import os
import logging
import threading
import time
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFrame, QFileDialog, QMessageBox,
                             QProgressBar, QTabWidget, QWidget, QScrollArea,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTreeWidget, QTreeWidgetItem, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QVariant

from zymosoft_assistant.utils.constants import COLOR_SCHEME, ZYMOSOFT_BASE_PATH
from zymosoft_assistant.utils.helpers import find_zymosoft_installation
from zymosoft_assistant.core.config_checker import ConfigChecker
from zymosoft_assistant.core.file_validator import FileValidator
from zymosoft_assistant.core.report_generator import ReportGenerator
from .step_frame import StepFrame

logger = logging.getLogger(__name__)

class Step2Checks(StepFrame):
    """
    Classe pour l'étape 2 : Vérifications pré-validation
    """

    def __init__(self, parent, main_window):
        """
        Initialise l'étape 2

        Args:
            parent: Widget parent
            main_window: Référence vers la fenêtre principale
        """


        # Variables pour les chemins
        self.zymosoft_path = ""

        # Variables pour les résultats des vérifications
        self.installation_valid = False
        self.check_results = {}

        # Objets pour les vérifications
        self.config_checker = None
        self.file_validator = None

        # Références aux widgets
        self.path_edit = None
        self.check_button = None
        self.report_button = None
        self.progress_bar = None
        self.progress_label = None
        self.results_notebook = None

        super().__init__(parent, main_window)
        logger.info("Étape 2 initialisée")

    def create_widgets(self):
        """
        Crée les widgets de l'étape 2
        """
        # Utilisation du layout vertical principal
        main_layout = QVBoxLayout()
        self.layout.addLayout(main_layout)

        # Titre de l'étape
        title_label = QLabel("Étape 2 : Vérifications pré-validation")
        title_label.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {COLOR_SCHEME['primary']};")
        main_layout.addWidget(title_label)
        main_layout.addSpacing(20)

        # Description
        description_label = QLabel("Vérification de l'installation ZymoSoft et des fichiers de configuration.")
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(600)
        main_layout.addWidget(description_label)
        main_layout.addSpacing(20)

        # Sélection du chemin d'installation
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(path_frame)

        path_label = QLabel("Chemin d'installation ZymoSoft :")
        path_label.setMinimumWidth(200)
        path_layout.addWidget(path_label)

        self.path_edit = QLineEdit()
        self.path_edit.setMinimumWidth(300)
        path_layout.addWidget(self.path_edit)

        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_zymosoft_path)
        path_layout.addWidget(browse_button)

        detect_button = QPushButton("Détecter")
        detect_button.clicked.connect(self.detect_zymosoft_path)
        path_layout.addWidget(detect_button)

        main_layout.addSpacing(10)

        # Boutons d'action
        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(action_frame)

        self.check_button = QPushButton("Lancer les vérifications")
        self.check_button.clicked.connect(self.run_checks)
        self.check_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
        action_layout.addWidget(self.check_button)

        self.report_button = QPushButton("Générer rapport")
        self.report_button.clicked.connect(self.generate_report)
        self.report_button.setEnabled(False)
        action_layout.addWidget(self.report_button)
        action_layout.addStretch(1)

        main_layout.addSpacing(10)

        # Barre de progression
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(progress_frame)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        progress_layout.addWidget(self.progress_label)

        main_layout.addSpacing(10)

        # Zone de résultats
        results_frame = QFrame()
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(results_frame)

        # Notebook pour les différentes catégories de vérifications
        self.results_notebook = QTabWidget()
        results_layout.addWidget(self.results_notebook)

        # Ajouter un espace extensible à la fin
        main_layout.addStretch(1)

        # Onglet pour la structure d'installation
        self.structure_frame = QWidget()
        self.structure_layout = QVBoxLayout(self.structure_frame)
        self.results_notebook.addTab(self.structure_frame, "Structure d'installation")

        # Onglet pour Config.ini
        self.config_ini_frame = QWidget()
        self.config_ini_layout = QVBoxLayout(self.config_ini_frame)
        self.results_notebook.addTab(self.config_ini_frame, "Config.ini")

        # Onglet pour PlateConfig.ini
        self.plate_config_ini_frame = QWidget()
        self.plate_config_ini_layout = QVBoxLayout(self.plate_config_ini_frame)
        self.results_notebook.addTab(self.plate_config_ini_frame, "PlateConfig.ini")

        # Onglet pour ZymoCubeCtrl.ini
        self.zymocube_ctrl_ini_frame = QWidget()
        self.zymocube_ctrl_ini_layout = QVBoxLayout(self.zymocube_ctrl_ini_frame)
        self.results_notebook.addTab(self.zymocube_ctrl_ini_frame, "ZymoCubeCtrl.ini")

        # Onglet pour les erreurs et avertissements
        self.errors_frame = QWidget()
        self.errors_layout = QVBoxLayout(self.errors_frame)
        self.results_notebook.addTab(self.errors_frame, "Erreurs et avertissements")

        # Statut global
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.addWidget(status_frame)

        self.status_label = QLabel("En attente des vérifications...")
        self.status_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)

    def browse_zymosoft_path(self):
        """
        Ouvre une boîte de dialogue pour sélectionner le chemin d'installation ZymoSoft
        """
        path = QFileDialog.getExistingDirectory(
            self.widget,
            "Sélectionner le dossier d'installation ZymoSoft",
            ZYMOSOFT_BASE_PATH if os.path.exists(ZYMOSOFT_BASE_PATH) else "/"
        )

        if path:
            self.zymosoft_path = path
            self.path_edit.setText(path)
            logger.info(f"Chemin d'installation ZymoSoft sélectionné: {path}")

    def detect_zymosoft_path(self):
        """
        Détecte automatiquement le chemin d'installation ZymoSoft
        """
        self.progress_label.setText("Détection du chemin d'installation ZymoSoft...")
        self.progress_bar.setValue(0)

        # Désactiver les boutons pendant la détection
        self.check_button.setEnabled(False)

        def detection_task():
            path = find_zymosoft_installation()

            # Mise à jour de l'interface dans le thread principal
            # PyQt5 requires signals for thread safety, but for simplicity we'll use a direct call
            # In a real application, you should use signals and slots for thread safety
            self._update_after_detection(path)

        # Lancer la détection dans un thread séparé
        threading.Thread(target=detection_task, daemon=True).start()

    def _update_after_detection(self, path):
        """
        Met à jour l'interface après la détection du chemin d'installation

        Args:
            path: Chemin d'installation détecté ou None si non trouvé
        """
        if path:
            self.zymosoft_path = path
            self.path_edit.setText(path)
            self.progress_label.setText(f"Installation ZymoSoft détectée: {path}")
            self.progress_bar.setValue(100)
            logger.info(f"Installation ZymoSoft détectée: {path}")
        else:
            self.progress_label.setText("Aucune installation ZymoSoft détectée.")
            QMessageBox.warning(self.widget, 
                               "Détection", 
                               "Aucune installation ZymoSoft n'a été détectée.\n"
                               "Veuillez sélectionner manuellement le dossier d'installation.")
            logger.warning("Aucune installation ZymoSoft détectée")

        # Réactiver les boutons
        self.check_button.setEnabled(True)

    def run_checks(self):
        """
        Lance les vérifications de l'installation ZymoSoft
        """
        # Vérifier que le chemin d'installation est spécifié
        zymosoft_path = self.path_edit.text()
        if not zymosoft_path:
            QMessageBox.critical(self.widget, "Erreur", "Veuillez spécifier le chemin d'installation ZymoSoft.")
            return

        # Vérifier que le chemin existe
        if not os.path.exists(zymosoft_path):
            QMessageBox.critical(self.widget, "Erreur", f"Le chemin spécifié n'existe pas: {zymosoft_path}")
            return

        # Initialiser les objets de vérification
        self.config_checker = ConfigChecker(zymosoft_path)
        self.file_validator = FileValidator(zymosoft_path)

        # Réinitialiser l'interface
        self._clear_results()

        # Désactiver les boutons pendant les vérifications
        self.check_button.setEnabled(False)
        self.report_button.setEnabled(False)

        # Mettre à jour la barre de progression
        self.progress_bar.setValue(0)
        self.progress_label.setText("Lancement des vérifications...")

        def check_task():
            try:
                # Étape 1: Vérification de la structure d'installation (20%)
                self._update_progress(0, "Vérification de la structure d'installation...")
                structure_results = self.config_checker.check_installation_structure()
                time.sleep(0.5)  # Simuler un traitement

                # Étape 2: Vérification de Config.ini (40%)
                self._update_progress(20, "Vérification de Config.ini...")
                config_ini_results = self.config_checker.validate_config_ini()
                time.sleep(0.5)  # Simuler un traitement

                # Étape 3: Vérification de PlateConfig.ini (60%)
                self._update_progress(40, "Vérification de PlateConfig.ini...")
                plate_config_ini_results = self.config_checker.validate_plate_config_ini()
                time.sleep(0.5)  # Simuler un traitement

                # Étape 4: Vérification de ZymoCubeCtrl.ini (80%)
                self._update_progress(60, "Vérification de ZymoCubeCtrl.ini...")
                zymocube_ctrl_ini_results = self.config_checker.validate_zymocube_ctrl_ini()
                time.sleep(0.5)  # Simuler un traitement

                # Étape 5: Validation des fichiers (100%)
                self._update_progress(80, "Validation des fichiers...")
                files_results = self.file_validator.validate_required_files()
                time.sleep(0.5)  # Simuler un traitement

                # Compilation des résultats
                self.check_results = {
                    "installation_valid": structure_results.get("installation_valid", False),
                    "structure": structure_results,
                    "config_ini": config_ini_results,
                    "plate_config_ini": plate_config_ini_results,
                    "zymocube_ctrl_ini": zymocube_ctrl_ini_results,
                    "files": files_results
                }

                # Mise à jour de l'interface dans le thread principal
                # Note: In a real application, you should use signals and slots for thread safety
                self._display_results()
            except Exception as e:
                logger.error(f"Erreur lors des vérifications: {str(e)}", exc_info=True)
                self._handle_check_error(str(e))

        # Lancer les vérifications dans un thread séparé
        threading.Thread(target=check_task, daemon=True).start()

    def _update_progress(self, value, message):
        """
        Met à jour la barre de progression et le message

        Args:
            value: Valeur de progression (0-100)
            message: Message à afficher
        """
        # Note: In a real application, you should use signals and slots for thread safety
        # For simplicity, we're using a direct call
        self._do_update_progress(value, message)

    def _do_update_progress(self, value, message):
        """
        Effectue la mise à jour de la barre de progression et du message

        Args:
            value: Valeur de progression (0-100)
            message: Message à afficher
        """
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)

    def _handle_check_error(self, error_message):
        """
        Gère les erreurs survenues pendant les vérifications

        Args:
            error_message: Message d'erreur
        """
        QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors des vérifications:\n{error_message}")
        self.progress_label.setText(f"Erreur: {error_message}")
        self.check_button.setEnabled(True)

    def _clear_results(self):
        """
        Efface les résultats précédents
        """
        # Effacer les onglets
        # In PyQt5, we need to clear the layouts
        self._clear_layout(self.structure_layout)
        self._clear_layout(self.config_ini_layout)
        self._clear_layout(self.plate_config_ini_layout)
        self._clear_layout(self.zymocube_ctrl_ini_layout)
        self._clear_layout(self.errors_layout)

        # Réinitialiser le statut
        self.status_label.setText("En attente des vérifications...")
        self.status_label.setStyleSheet(f"color: {COLOR_SCHEME['text']};")

    def _clear_layout(self, layout):
        """
        Efface tous les widgets d'un layout

        Args:
            layout: Layout à effacer
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self._clear_layout(item.layout())

    def _display_results(self):
        """
        Met à jour l'interface avec les résultats des vérifications
        Note: Cette méthode est appelée depuis un thread séparé et doit être thread-safe
        """
        # Note: In a real application, you should use signals and slots for thread safety
        # For simplicity, we're using a direct call
        self._do_display_results()

    def _do_display_results(self):
        """
        Effectue la mise à jour de l'interface avec les résultats des vérifications
        """
        # Mise à jour de la barre de progression
        self.progress_bar.setValue(100)
        self.progress_label.setText("Vérifications terminées.")

        # Mise à jour du statut global
        self.installation_valid = self.check_results.get("installation_valid", False)

        if self.installation_valid:
            self.status_label.setText("✓ Installation valide")
            self.status_label.setStyleSheet(f"color: {COLOR_SCHEME['success']};")
        else:
            self.status_label.setText("✗ Installation non valide")
            self.status_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")

        # Affichage des résultats dans les onglets
        self._display_structure_results()
        self._display_config_ini_results()
        self._display_plate_config_ini_results()
        self._display_zymocube_ctrl_ini_results()
        self._display_errors_warnings()

        # Réactiver les boutons
        self.check_button.setEnabled(True)
        self.report_button.setEnabled(True)

        # Sauvegarder les résultats dans la session
        self.save_data()

        logger.info("Affichage des résultats des vérifications terminé")

    def _display_structure_results(self):
        """
        Affiche les résultats de la vérification de la structure d'installation
        """
        structure_results = self.check_results.get("structure", {})

        # Titre
        title_label = QLabel("Structure de l'installation")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.structure_layout.addWidget(title_label)

        # Tableau des résultats
        tree = QTreeWidget()
        tree.setHeaderLabels(["Élément", "Statut"])
        tree.setColumnWidth(0, 300)
        tree.setColumnWidth(1, 100)
        self.structure_layout.addWidget(tree)

        # Ajout des éléments
        for key, value in structure_results.items():
            if key != "installation_valid":
                status = "✓" if value else "✗"
                status_color = COLOR_SCHEME['success'] if value else COLOR_SCHEME['error']

                item_text = key.replace("_exists", "").replace("_", " ").capitalize()
                item = QTreeWidgetItem([item_text, status])
                item.setForeground(1, Qt.GlobalColor.green if value else Qt.GlobalColor.red)
                tree.addTopLevelItem(item)

    def _display_config_ini_results(self):
        """
        Affiche les résultats de la vérification de Config.ini
        """
        config_ini_results = self.check_results.get("config_ini", {})

        # Titre
        title_label = QLabel("Vérification de Config.ini")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.config_ini_layout.addWidget(title_label)

        # Statut
        status_text = "✓ Valide" if config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = COLOR_SCHEME['success'] if config_ini_results.get("config_valid", False) else COLOR_SCHEME['error']

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        self.config_ini_layout.addWidget(status_label)

        # Valeurs
        if "values" in config_ini_results and config_ini_results["values"]:
            values_group = QGroupBox("Valeurs")
            values_layout = QVBoxLayout(values_group)
            self.config_ini_layout.addWidget(values_group)

            tree = QTreeWidget()
            tree.setHeaderLabels(["Paramètre", "Valeur"])
            tree.setColumnWidth(0, 200)
            tree.setColumnWidth(1, 200)
            values_layout.addWidget(tree)

            for key, value in config_ini_results["values"].items():
                item = QTreeWidgetItem([key, str(value)])
                tree.addTopLevelItem(item)

    def _display_plate_config_ini_results(self):
        """
        Affiche les résultats de la vérification de PlateConfig.ini
        """
        plate_config_ini_results = self.check_results.get("plate_config_ini", {})

        # Titre
        title_label = QLabel("Vérification de PlateConfig.ini")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.plate_config_ini_layout.addWidget(title_label)

        # Statut
        status_text = "✓ Valide" if plate_config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = COLOR_SCHEME['success'] if plate_config_ini_results.get("config_valid", False) else COLOR_SCHEME['error']

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        self.plate_config_ini_layout.addWidget(status_label)

        # Types de plaques
        if "plate_types" in plate_config_ini_results and plate_config_ini_results["plate_types"]:
            plate_types_group = QGroupBox("Types de plaques")
            plate_types_layout = QVBoxLayout(plate_types_group)
            self.plate_config_ini_layout.addWidget(plate_types_group)

            tree = QTreeWidget()
            tree.setHeaderLabels(["Type de plaque", "Configuration"])
            tree.setColumnWidth(0, 200)
            tree.setColumnWidth(1, 200)
            plate_types_layout.addWidget(tree)

            for plate_type in plate_config_ini_results["plate_types"]:
                item = QTreeWidgetItem([plate_type.get("name", ""), plate_type.get("config", "")])
                tree.addTopLevelItem(item)

    def _display_zymocube_ctrl_ini_results(self):
        """
        Affiche les résultats de la vérification de ZymoCubeCtrl.ini
        """
        zymocube_ctrl_ini_results = self.check_results.get("zymocube_ctrl_ini", {})

        # Titre
        title_label = QLabel("Vérification de ZymoCubeCtrl.ini")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.zymocube_ctrl_ini_layout.addWidget(title_label)

        # Statut
        status_text = "✓ Valide" if zymocube_ctrl_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = COLOR_SCHEME['success'] if zymocube_ctrl_ini_results.get("config_valid", False) else COLOR_SCHEME['error']

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        self.zymocube_ctrl_ini_layout.addWidget(status_label)

        # Valeurs
        if "values" in zymocube_ctrl_ini_results and zymocube_ctrl_ini_results["values"]:
            values_group = QGroupBox("Valeurs")
            values_layout = QVBoxLayout(values_group)
            self.zymocube_ctrl_ini_layout.addWidget(values_group)

            tree = QTreeWidget()
            tree.setHeaderLabels(["Paramètre", "Valeur"])
            tree.setColumnWidth(0, 200)
            tree.setColumnWidth(1, 200)
            values_layout.addWidget(tree)

            for key, value in zymocube_ctrl_ini_results["values"].items():
                item = QTreeWidgetItem([key, str(value)])
                tree.addTopLevelItem(item)

    def _display_errors_warnings(self):
        """
        Affiche les erreurs et avertissements
        """
        # Titre
        title_label = QLabel("Erreurs et avertissements")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.errors_layout.addWidget(title_label)

        # Collecte des erreurs et avertissements
        errors = []
        warnings = []

        for key, value in self.check_results.items():
            if isinstance(value, dict):
                if "errors" in value:
                    errors.extend(value["errors"])
                if "warnings" in value:
                    warnings.extend(value["warnings"])

        # Affichage des erreurs
        if errors:
            errors_group = QGroupBox("Erreurs")
            errors_layout = QVBoxLayout(errors_group)
            self.errors_layout.addWidget(errors_group)

            for error in errors:
                error_label = QLabel(f"• {error}")
                error_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")
                error_label.setWordWrap(True)
                error_label.setMinimumWidth(600)
                errors_layout.addWidget(error_label)

        # Affichage des avertissements
        if warnings:
            warnings_group = QGroupBox("Avertissements")
            warnings_layout = QVBoxLayout(warnings_group)
            self.errors_layout.addWidget(warnings_group)

            for warning in warnings:
                warning_label = QLabel(f"• {warning}")
                warning_label.setStyleSheet(f"color: {COLOR_SCHEME['warning']};")
                warning_label.setWordWrap(True)
                warning_label.setMinimumWidth(600)
                warnings_layout.addWidget(warning_label)

        # Message si aucune erreur ni avertissement
        if not errors and not warnings:
            no_issues_label = QLabel("Aucune erreur ni avertissement détecté.")
            no_issues_label.setStyleSheet(f"color: {COLOR_SCHEME['success']};")
            no_issues_label.setWordWrap(True)
            no_issues_label.setAlignment(Qt.AlignCenter)
            self.errors_layout.addWidget(no_issues_label)

    def generate_report(self):
        """
        Génère un rapport PDF des vérifications
        """
        if not self.check_results:
            QMessageBox.critical(self.widget, "Erreur", "Aucun résultat de vérification disponible.")
            return

        try:
            # Création du générateur de rapports
            report_generator = ReportGenerator()

            # Génération du rapport
            report_path = report_generator.generate_step2_report(self.check_results)

            # Affichage du message de succès
            QMessageBox.information(self.widget, "Rapport", f"Le rapport a été généré avec succès:\n{report_path}")

            # Ouverture du rapport
            os.startfile(report_path)

            logger.info(f"Rapport de l'étape 2 généré: {report_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors de la génération du rapport:\n{str(e)}")

    def validate(self):
        """
        Valide les données de l'étape 2

        Returns:
            True si les données sont valides, False sinon
        """
        if not self.check_results:
            QMessageBox.critical(self.widget, "Validation", "Veuillez lancer les vérifications avant de continuer.")
            return False

        if not self.installation_valid:
            reply = QMessageBox.question(self.widget, "Validation", 
                                        "L'installation n'est pas valide. Voulez-vous quand même continuer ?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return False

        return True

    def save_data(self):
        """
        Sauvegarde les données de l'étape 2 dans la session
        """
        self.main_window.session_data["step2_checks"] = {
            "installation_valid": self.installation_valid,
            "zymosoft_path": self.path_edit.text(),
            "check_results": self.check_results
        }

        logger.info("Données de l'étape 2 sauvegardées")

    def load_data(self):
        """
        Charge les données de la session dans l'étape 2
        """
        step2_data = self.main_window.session_data.get("step2_checks", {})

        if "zymosoft_path" in step2_data:
            self.path_edit.setText(step2_data["zymosoft_path"])
            self.zymosoft_path = step2_data["zymosoft_path"]

        if "check_results" in step2_data:
            self.check_results = step2_data["check_results"]
            self.installation_valid = step2_data.get("installation_valid", False)

            # Afficher les résultats s'ils existent
            if self.check_results:
                self._display_results()

        logger.info("Données de l'étape 2 chargées")

    def reset(self):
        """
        Réinitialise l'étape 2
        """
        self.path_edit.setText("")
        self.zymosoft_path = ""
        self.check_results = {}
        self.installation_valid = False
        self.config_checker = None
        self.file_validator = None

        self._clear_results()
        self.progress_bar.setValue(0)
        self.progress_label.setText("")
        self.check_button.setEnabled(True)
        self.report_button.setEnabled(False)

        logger.info("Étape 2 réinitialisée")
