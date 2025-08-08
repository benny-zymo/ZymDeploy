#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 2 de l'assistant d'installation ZymoSoft : Vérifications pré-validation
Version améliorée avec meilleure UX et tableaux détaillés
"""

import os
import logging
import threading
import time
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFrame, QFileDialog, QMessageBox,
                             QProgressBar, QTabWidget, QWidget, QScrollArea,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTreeWidget, QTreeWidgetItem, QGroupBox,
                             QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QObject
from PyQt5.QtGui import QFont, QIcon

from zymosoft_assistant.utils.constants import COLOR_SCHEME, ZYMOSOFT_BASE_PATH
from zymosoft_assistant.utils.helpers import find_zymosoft_installation
from zymosoft_assistant.core.config_checker import ConfigChecker
from zymosoft_assistant.core.file_validator import FileValidator
from zymosoft_assistant.core.report_generator import ReportGenerator
from .step_frame import StepFrame

logger = logging.getLogger(__name__)

class Step2Helper(QObject):
    """
    Classe d'aide pour la communication thread-safe
    """
    update_progress_signal = pyqtSignal(int, str)
    display_results_signal = pyqtSignal()
    handle_error_signal = pyqtSignal(str)

class VerticalTabWidget(QWidget):
    """
    Widget pour créer des tabs verticaux avec indicateur de statut
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = 0
        self.tabs = []
        self.tab_widgets = []
        self.tab_buttons = []
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Zone des boutons de tabs (à gauche)
        self.tab_buttons_frame = QFrame()
        self.tab_buttons_frame.setFixedWidth(200)
        self.tab_buttons_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_SCHEME.get('background_light', '#f5f5f5')};
                border-right: 1px solid {COLOR_SCHEME.get('border', '#ddd')};
            }}
        """)
        self.tab_buttons_layout = QVBoxLayout(self.tab_buttons_frame)
        self.tab_buttons_layout.setContentsMargins(5, 5, 5, 5)
        self.tab_buttons_layout.setSpacing(2)

        # Zone de contenu (à droite)
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(self.tab_buttons_frame)
        layout.addWidget(self.content_frame, 1)

    def add_tab(self, widget, title, status=None):
        """
        Ajoute une tab avec un statut (None, True pour vert, False pour rouge)
        """
        button = QPushButton(title)
        button.setCheckable(True)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setMinimumHeight(40)

        # Utiliser une closure pour capturer l'index correct
        tab_index = len(self.tabs)
        button.clicked.connect(lambda checked, idx=tab_index: self.set_current_index(idx))

        self.update_tab_style(button, status, len(self.tabs) == 0)

        self.tab_buttons.append(button)
        self.tabs.append(title)
        self.tab_widgets.append(widget)

        self.tab_buttons_layout.addWidget(button)

        # Masquer le widget initialement sauf le premier
        widget.setVisible(len(self.tabs) == 1)
        self.content_layout.addWidget(widget)

        if len(self.tabs) == 1:
            button.setChecked(True)

    def update_tab_style(self, button, status, is_current=False):
        """
        Met à jour le style du bouton selon le statut
        """
        base_style = """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin: 1px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """

        if status is True:  # Valide - vert
            color_style = f"""
                QPushButton {{
                    background-color: {COLOR_SCHEME.get('success_light', '#d4edda')};
                    border-left: 4px solid {COLOR_SCHEME.get('success', '#28a745')};
                    color: {COLOR_SCHEME.get('success_dark', '#155724')};
                }}
                QPushButton:checked {{
                    background-color: {COLOR_SCHEME.get('success', '#28a745')};
                    color: white;
                }}
            """
        elif status is False:  # Invalide - rouge
            color_style = f"""
                QPushButton {{
                    background-color: {COLOR_SCHEME.get('error_light', '#f8d7da')};
                    border-left: 4px solid {COLOR_SCHEME.get('error', '#dc3545')};
                    color: {COLOR_SCHEME.get('error_dark', '#721c24')};
                }}
                QPushButton:checked {{
                    background-color: {COLOR_SCHEME.get('error', '#dc3545')};
                    color: white;
                }}
            """
        else:  # Neutre - gris
            color_style = f"""
                QPushButton {{
                    background-color: {COLOR_SCHEME.get('background', '#ffffff')};
                    border-left: 4px solid {COLOR_SCHEME.get('border', '#ddd')};
                    color: {COLOR_SCHEME.get('text', '#333')};
                }}
                QPushButton:checked {{
                    background-color: {COLOR_SCHEME.get('primary', '#007bff')};
                    color: white;
                }}
            """

        button.setStyleSheet(base_style + color_style)

    def set_current_index(self, index):
        """
        Change l'onglet actuel
        """
        if 0 <= index < len(self.tabs):
            # Masquer l'onglet actuel
            if 0 <= self.current_index < len(self.tab_widgets):
                self.tab_widgets[self.current_index].setVisible(False)
                if self.current_index < len(self.tab_buttons):
                    self.tab_buttons[self.current_index].setChecked(False)

            # Afficher le nouvel onglet
            self.current_index = index
            self.tab_widgets[index].setVisible(True)
            self.tab_buttons[index].setChecked(True)

    def update_tab_status(self, index, status):
        """
        Met à jour le statut d'une tab
        """
        if 0 <= index < len(self.tab_buttons):
            self.update_tab_style(self.tab_buttons[index], status, index == self.current_index)

class Step2Checks(StepFrame):
    """
    Classe pour l'étape 2 : Vérifications pré-validation avec interface améliorée
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

        # États de l'interface
        self.analysis_done = False
        self.analysis_in_progress = False

        # Références aux widgets
        self.main_container = None
        self.initial_selection_frame = None
        self.analysis_frame = None
        self.results_frame = None

        # Widgets pour sélection initiale
        self.folder_display_label = None
        self.select_folder_button = None
        self.start_analysis_button = None

        # Widgets pour analyse
        self.progress_bar = None
        self.progress_label = None

        # Widgets pour résultats
        self.results_tabs = None
        self.status_label = None
        self.change_folder_button = None
        self.report_button = None

        # Helper pour la communication thread-safe
        self.helper = Step2Helper()
        self.helper.update_progress_signal.connect(self._do_update_progress)
        self.helper.display_results_signal.connect(self._do_display_results)
        self.helper.handle_error_signal.connect(self._do_handle_check_error)

        super().__init__(parent, main_window)
        logger.info("Étape 2 initialisée avec interface améliorée")

    def create_widgets(self):
        """
        Crée les widgets de l'étape 2 avec la nouvelle interface
        """
        # Container principal
        self.main_container = QVBoxLayout()
        self.layout.addLayout(self.main_container)

        # Créer les différentes frames
        self._create_initial_selection_frame()
        self._create_analysis_frame()
        self._create_results_frame()

        # Afficher l'état initial
        self._show_initial_state()

    def _create_initial_selection_frame(self):
        """
        Crée la frame pour la sélection initiale du dossier
        """
        self.initial_selection_frame = QFrame()
        initial_layout = QVBoxLayout(self.initial_selection_frame)
        initial_layout.setAlignment(Qt.AlignCenter)
        initial_layout.setSpacing(20)

        # Titre
        title_label = QLabel("Sélection du dossier d'installation ZymoSoft")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        initial_layout.addWidget(title_label)

        # Espace
        initial_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Affichage du dossier sélectionné
        self.folder_display_label = QLabel("Aucun dossier sélectionné")
        self.folder_display_label.setStyleSheet(f"""
            QLabel {{
                padding: 15px;
                border: 2px dashed {COLOR_SCHEME.get('border', '#ddd')};
                border-radius: 8px;
                background-color: {COLOR_SCHEME.get('background_light', '#f8f9fa')};
                color: {COLOR_SCHEME.get('text_secondary', '#666')};
                font-size: 12pt;
            }}
        """)
        self.folder_display_label.setAlignment(Qt.AlignCenter)
        self.folder_display_label.setMinimumHeight(80)
        initial_layout.addWidget(self.folder_display_label)

        # Bouton de sélection de dossier
        self.select_folder_button = QPushButton("Sélectionner le dossier d'installation")
        self.select_folder_button.setMinimumHeight(50)
        self.select_folder_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SCHEME.get('primary', '#007bff')};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SCHEME.get('primary_dark', '#0056b3')};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_SCHEME.get('primary_darker', '#004085')};
            }}
        """)
        self.select_folder_button.clicked.connect(self.browse_zymosoft_path)
        initial_layout.addWidget(self.select_folder_button)

        # Bouton de lancement d'analyse (masqué initialement)
        self.start_analysis_button = QPushButton("Lancer l'analyse")
        self.start_analysis_button.setMinimumHeight(50)
        self.start_analysis_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SCHEME.get('success', '#28a745')};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SCHEME.get('success_dark', '#218838')};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_SCHEME.get('success_darker', '#1e7e34')};
            }}
        """)
        self.start_analysis_button.clicked.connect(self.run_checks)
        self.start_analysis_button.setVisible(False)
        initial_layout.addWidget(self.start_analysis_button)

        # Espace
        initial_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.main_container.addWidget(self.initial_selection_frame)

    def _create_analysis_frame(self):
        """
        Crée la frame pour l'affichage du progrès de l'analyse
        """
        self.analysis_frame = QFrame()
        analysis_layout = QVBoxLayout(self.analysis_frame)
        analysis_layout.setAlignment(Qt.AlignCenter)
        analysis_layout.setSpacing(20)

        # Titre
        title_label = QLabel("Analyse en cours...")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        analysis_layout.addWidget(title_label)

        # Espace
        analysis_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {COLOR_SCHEME.get('border', '#ddd')};
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 12pt;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_SCHEME.get('primary', '#007bff')};
                border-radius: 6px;
            }}
        """)
        analysis_layout.addWidget(self.progress_bar)

        # Label de progression
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 12pt; color: #666;")
        analysis_layout.addWidget(self.progress_label)

        # Espace
        analysis_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.analysis_frame.setVisible(False)
        self.main_container.addWidget(self.analysis_frame)

    def _create_results_frame(self):
        """
        Crée la frame pour l'affichage des résultats avec tabs verticaux
        """
        self.results_frame = QFrame()
        results_layout = QVBoxLayout(self.results_frame)
        results_layout.setSpacing(10)

        # En-tête avec statut et boutons
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Statut global
        self.status_label = QLabel("En attente des vérifications...")
        self.status_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(self.status_label)

        header_layout.addStretch(1)

        # Bouton pour changer de dossier
        self.change_folder_button = QPushButton("Changer de dossier")
        self.change_folder_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SCHEME.get('secondary', '#6c757d')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SCHEME.get('secondary_dark', '#5a6268')};
            }}
        """)
        self.change_folder_button.clicked.connect(self._change_folder)
        header_layout.addWidget(self.change_folder_button)

        # Bouton de rapport
        self.report_button = QPushButton("Générer rapport")
        self.report_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SCHEME.get('info', '#17a2b8')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SCHEME.get('info_dark', '#138496')};
            }}
        """)
        self.report_button.clicked.connect(self.generate_report)
        header_layout.addWidget(self.report_button)

        results_layout.addWidget(header_frame)

        # Tabs verticaux pour les résultats
        self.results_tabs = VerticalTabWidget()
        results_layout.addWidget(self.results_tabs, 1)

        # Créer les onglets
        self._create_result_tabs()

        self.results_frame.setVisible(False)
        self.main_container.addWidget(self.results_frame)

    def _create_result_tabs(self):
        """
        Crée les onglets pour les résultats
        """
        # Onglet Résumé
        self.summary_widget = QWidget()
        self.summary_layout = QVBoxLayout(self.summary_widget)
        self.results_tabs.add_tab(self.summary_widget, "Résumé")

        # Onglet Structure
        self.structure_widget = QWidget()
        self.structure_layout = QVBoxLayout(self.structure_widget)
        self.results_tabs.add_tab(self.structure_widget, "Structure")

        # Onglet Config.ini
        self.config_ini_widget = QWidget()
        self.config_ini_layout = QVBoxLayout(self.config_ini_widget)
        self.results_tabs.add_tab(self.config_ini_widget, "Config.ini")

        # Onglet PlateConfig.ini
        self.plate_config_ini_widget = QWidget()
        self.plate_config_ini_layout = QVBoxLayout(self.plate_config_ini_widget)
        self.results_tabs.add_tab(self.plate_config_ini_widget, "PlateConfig.ini")

        # Onglet ZymoCubeCtrl.ini
        self.zymocube_ctrl_ini_widget = QWidget()
        self.zymocube_ctrl_ini_layout = QVBoxLayout(self.zymocube_ctrl_ini_widget)
        self.results_tabs.add_tab(self.zymocube_ctrl_ini_widget, "ZymoCubeCtrl.ini")

        # Onglet Erreurs
        self.errors_widget = QWidget()
        self.errors_layout = QVBoxLayout(self.errors_widget)
        self.results_tabs.add_tab(self.errors_widget, "Erreurs")

    def _show_initial_state(self):
        """
        Affiche l'état initial (sélection de dossier)
        """
        self.initial_selection_frame.setVisible(True)
        self.analysis_frame.setVisible(False)
        self.results_frame.setVisible(False)

    def _show_analysis_state(self):
        """
        Affiche l'état d'analyse en cours
        """
        self.initial_selection_frame.setVisible(False)
        self.analysis_frame.setVisible(True)
        self.results_frame.setVisible(False)
        self.analysis_in_progress = True

    def _show_results_state(self):
        """
        Affiche l'état des résultats
        """
        self.initial_selection_frame.setVisible(False)
        self.analysis_frame.setVisible(False)
        self.results_frame.setVisible(True)
        self.analysis_in_progress = False
        self.analysis_done = True

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
            self.folder_display_label.setText(f"{path}")
            self.folder_display_label.setStyleSheet(f"""
                QLabel {{
                    padding: 15px;
                    border: 2px solid {COLOR_SCHEME.get('success', '#28a745')};
                    border-radius: 8px;
                    background-color: {COLOR_SCHEME.get('success_light', '#d4edda')};
                    color: {COLOR_SCHEME.get('success_dark', '#155724')};
                    font-size: 12pt;
                    font-weight: bold;
                }}
            """)
            self.start_analysis_button.setVisible(True)
            logger.info(f"Chemin d'installation ZymoSoft sélectionné: {path}")

    def _change_folder(self):
        """
        Permet de changer de dossier et recommencer l'analyse
        """
        self.zymosoft_path = ""
        self.check_results = {}
        self.installation_valid = False
        self.analysis_done = False

        # Réinitialiser l'affichage du dossier
        self.folder_display_label.setText("Aucun dossier sélectionné")
        self.folder_display_label.setStyleSheet(f"""
            QLabel {{
                padding: 15px;
                border: 2px dashed {COLOR_SCHEME.get('border', '#ddd')};
                border-radius: 8px;
                background-color: {COLOR_SCHEME.get('background_light', '#f8f9fa')};
                color: {COLOR_SCHEME.get('text_secondary', '#666')};
                font-size: 12pt;
            }}
        """)
        self.start_analysis_button.setVisible(False)

        # Retourner à l'état initial
        self._show_initial_state()

    def run_checks(self):
        """
        Lance les vérifications de l'installation ZymoSoft
        """
        # Vérifier que le chemin d'installation est spécifié
        if not self.zymosoft_path:
            QMessageBox.critical(self.widget, "Erreur", "Veuillez spécifier le chemin d'installation ZymoSoft.")
            return

        # Vérifier que le chemin existe
        if not os.path.exists(self.zymosoft_path):
            QMessageBox.critical(self.widget, "Erreur", f"Le chemin spécifié n'existe pas: {self.zymosoft_path}")
            return

        # Passer à l'état d'analyse
        self._show_analysis_state()

        # Initialiser les objets de vérification
        self.config_checker = ConfigChecker(self.zymosoft_path)
        self.file_validator = FileValidator(self.zymosoft_path)

        # Mettre à jour la barre de progression
        self.progress_bar.setValue(0)
        self.progress_label.setText("Préparation de l'analyse...")

        def check_task():
            try:
                # Étape 1: Vérification de la structure d'installation (25%)
                self._update_progress(0, "Vérification de la structure d'installation...")
                structure_results = self.config_checker.check_installation_structure()
                time.sleep(0.5)

                # Étape 2: Vérification de Config.ini (50%)
                self._update_progress(25, "Vérification de Config.ini...")
                config_ini_results = self.config_checker.validate_config_ini()
                time.sleep(0.5)

                # Étape 3: Vérification de PlateConfig.ini (75%)
                self._update_progress(50, "Vérification de PlateConfig.ini...")
                plate_config_ini_results = self.config_checker.validate_plate_config_ini()
                time.sleep(0.5)

                # Étape 4: Vérification de ZymoCubeCtrl.ini (100%)
                self._update_progress(75, "Vérification de ZymoCubeCtrl.ini...")
                zymocube_ctrl_ini_results = self.config_checker.validate_zymocube_ctrl_ini()
                time.sleep(0.5)

                # Compilation des résultats
                self.check_results = {
                    "installation_valid": structure_results.get("installation_valid", False),
                    "structure": structure_results,
                    "config_ini": config_ini_results,
                    "plate_config_ini": plate_config_ini_results,
                    "zymocube_ctrl_ini": zymocube_ctrl_ini_results
                }

                # Finalisation
                self._update_progress(100, "Analyse terminée !")
                time.sleep(0.5)

                # Afficher les résultats
                self._display_results()

            except Exception as e:
                logger.error(f"Erreur lors des vérifications: {str(e)}", exc_info=True)
                self._handle_check_error(str(e))

        # Lancer les vérifications dans un thread séparé
        threading.Thread(target=check_task, daemon=True).start()

    def _update_progress(self, value, message):
        """
        Met à jour la barre de progression et le message
        """
        self.helper.update_progress_signal.emit(value, message)

    def _do_update_progress(self, value, message):
        """
        Effectue la mise à jour de la barre de progression et du message
        """
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)

    def _handle_check_error(self, error_message):
        """
        Gère les erreurs survenues pendant les vérifications
        """
        self.helper.handle_error_signal.emit(error_message)

    def _do_handle_check_error(self, error_message):
        """
        Effectue la gestion des erreurs dans le thread principal
        """
        QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors des vérifications:\n{error_message}")
        self._show_initial_state()

    def _display_results(self):
        """
        Affiche les résultats des vérifications
        """
        self.helper.display_results_signal.emit()

    def _do_display_results(self):
        """
        Effectue l'affichage des résultats dans le thread principal
        """
        # Passer à l'état des résultats
        self._show_results_state()

        # Déterminer si l'installation est valide (TOUS les checks doivent être valides)
        self.installation_valid = self._calculate_global_validity()

        # Activer l'option "Modifier config.ini" dans le menu Actions
        if hasattr(self.main_window, 'edit_config_action'):
            self.main_window.edit_config_action.setEnabled(True)
            logger.debug("Action 'Modifier config.ini' activée après analyse")

        if self.installation_valid:
            self.status_label.setText("Installation valide")
            self.status_label.setStyleSheet(
                f"color: {COLOR_SCHEME.get('success', '#28a745')}; font-size: 16pt; font-weight: bold;")
        else:
            self.status_label.setText("Installation non valide")
            self.status_label.setStyleSheet(
                f"color: {COLOR_SCHEME.get('error', '#dc3545')}; font-size: 16pt; font-weight: bold;")

        # Nettoyer les onglets
        self._clear_layout(self.summary_layout)
        self._clear_layout(self.structure_layout)
        self._clear_layout(self.config_ini_layout)
        self._clear_layout(self.plate_config_ini_layout)
        self._clear_layout(self.zymocube_ctrl_ini_layout)
        self._clear_layout(self.errors_layout)

        # Remplir les onglets
        self._display_summary_results()
        self._display_structure_results()
        self._display_config_ini_results()
        self._display_plate_config_ini_results()
        self._display_zymocube_ctrl_ini_results()
        self._display_errors_warnings()

        # Mettre à jour les statuts des tabs
        self._update_tab_statuses()

        # Sélectionner l'onglet résumé
        self.results_tabs.set_current_index(0)

        # Sauvegarder les résultats
        self.save_data()

        logger.info("Affichage des résultats des vérifications terminé")

    def _calculate_global_validity(self):
        """
        Calcule la validité globale - TOUS les checks doivent être valides

        Returns:
            bool: True si TOUS les checks sont valides, False sinon
        """
        # Vérifier la structure
        structure_valid = self.check_results.get("structure", {}).get("installation_valid", False)
        if not structure_valid:
            return False

        # Vérifier Config.ini
        config_ini_valid = self.check_results.get("config_ini", {}).get("config_valid", False)
        if not config_ini_valid:
            return False

        # Vérifier PlateConfig.ini
        plate_config_ini_valid = self.check_results.get("plate_config_ini", {}).get("config_valid", False)
        if not plate_config_ini_valid:
            return False

        # Vérifier ZymoCubeCtrl.ini
        zymocube_ctrl_ini_valid = self.check_results.get("zymocube_ctrl_ini", {}).get("config_valid", False)
        if not zymocube_ctrl_ini_valid:
            return False

        # Vérifier qu'il n'y a pas d'erreurs
        for result in self.check_results.values():
            if isinstance(result, dict) and result.get("errors", []):
                return False

        return True

    def _update_tab_statuses(self):
        """
        Met à jour les statuts des tabs selon les résultats
        """
        # Résumé - statut global
        self.results_tabs.update_tab_status(0, self.installation_valid)

        # Structure
        structure_valid = self.check_results.get("structure", {}).get("installation_valid", False)
        self.results_tabs.update_tab_status(1, structure_valid)

        # Config.ini
        config_ini_valid = self.check_results.get("config_ini", {}).get("config_valid", False)
        self.results_tabs.update_tab_status(2, config_ini_valid)

        # PlateConfig.ini
        plate_config_ini_valid = self.check_results.get("plate_config_ini", {}).get("config_valid", False)
        self.results_tabs.update_tab_status(3, plate_config_ini_valid)

        # ZymoCubeCtrl.ini
        zymocube_ctrl_ini_valid = self.check_results.get("zymocube_ctrl_ini", {}).get("config_valid", False)
        self.results_tabs.update_tab_status(4, zymocube_ctrl_ini_valid)

        # Erreurs - rouge s'il y a des erreurs
        has_errors = any(
            isinstance(result, dict) and result.get("errors", [])
            for result in self.check_results.values()
        )
        self.results_tabs.update_tab_status(5, not has_errors)

    def _clear_layout(self, layout):
        """
        Efface tous les widgets d'un layout
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self._clear_layout(item.layout())

    def _display_summary_results(self):
        """
        Affiche un résumé de tous les résultats des vérifications avec des indicateurs de statut
        """
        # Titre
        title_label = QLabel("Résumé des vérifications")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; margin-bottom: 10px;")
        self.summary_layout.addWidget(title_label)

        # Tableau des résultats
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Catégorie", "Statut", "Détails"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.summary_layout.addWidget(table)

        # Construction des détails pour chaque catégorie
        def build_details(result, keys_to_check=None, value_keys=None):
            details = []
            if isinstance(result, dict):
                if "errors" in result and result["errors"]:
                    details.extend([f"Erreur: {e}" for e in result["errors"]])
                if "warnings" in result and result["warnings"]:
                    details.extend([f"Avertissement: {w}" for w in result["warnings"]])
                if keys_to_check:
                    for k in keys_to_check:
                        if k in result:
                            val = result[k]
                            if isinstance(val, bool):
                                details.append(f"{k.replace('_', ' ')}: {'OK' if val else 'Non'}")
                if value_keys:
                    for k in value_keys:
                        if k in result.get("values", {}):
                            v = result["values"][k]
                            details.append(f"{k}: {v}")
            return "\n".join(details)

        # Détails pour la structure
        structure = self.check_results.get("structure", {})
        structure_details = build_details(
            structure,
            keys_to_check=[
                "bin_exists", "etc_exists", "resultats_exists",
                "zymocubectrl_exists", "zymosoft_exists", "workers_exists", "version_match"
            ]
        )

        # Détails pour Config.ini
        config_ini = self.check_results.get("config_ini", {})
        config_ini_details = build_details(
            config_ini,
            value_keys=list(config_ini.get("values", {}).keys()) if "values" in config_ini else []
        )

        # Détails pour PlateConfig.ini
        plate_config_ini = self.check_results.get("plate_config_ini", {})
        plate_config_ini_details = build_details(plate_config_ini)
        if "errors" in plate_config_ini and plate_config_ini["errors"]:
            for err in plate_config_ini["errors"]:
                plate_config_ini_details += f"\n{err}"
        if "plate_types" in plate_config_ini and plate_config_ini["plate_types"]:
            for pt in plate_config_ini["plate_types"]:
                plate_config_ini_details += f"\nType: {pt.get('name','')} Config: {pt.get('config','')}"

        # Détails pour ZymoCubeCtrl.ini
        zymocube_ctrl_ini = self.check_results.get("zymocube_ctrl_ini", {})
        zymocube_ctrl_ini_details = build_details(
            zymocube_ctrl_ini,
            value_keys=list(zymocube_ctrl_ini.get("values", {}).keys()) if "values" in zymocube_ctrl_ini else []
        )
        if "plate_types" in zymocube_ctrl_ini and zymocube_ctrl_ini["plate_types"]:
            zymocube_ctrl_ini_details += "\nTypes de plaques: " + ", ".join(zymocube_ctrl_ini["plate_types"])

        # Compter les erreurs et avertissements
        errors_count = 0
        warnings_count = 0
        for key, value in self.check_results.items():
            if isinstance(value, dict):
                if "errors" in value:
                    errors_count += len(value["errors"])
                if "warnings" in value:
                    warnings_count += len(value["warnings"])

        # Ajouter les résultats au tableau
        categories = [
            ("Structure d'installation", structure.get("installation_valid", False), structure_details),
            ("Config.ini", config_ini.get("config_valid", False), config_ini_details),
            ("PlateConfig.ini", plate_config_ini.get("config_valid", False), plate_config_ini_details),
            ("ZymoCubeCtrl.ini", zymocube_ctrl_ini.get("config_valid", False), zymocube_ctrl_ini_details),
            ("Erreurs et avertissements", errors_count == 0, f"{errors_count} erreur(s), {warnings_count} avertissement(s)")
        ]

        table.setRowCount(len(categories))

        # Remplir le tableau
        for i, (category, is_valid, details_text) in enumerate(categories):
            category_item = QTableWidgetItem(category)
            table.setItem(i, 0, category_item)

            status_text = "✓" if is_valid else "✗"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(Qt.green if is_valid else Qt.red)
            table.setItem(i, 1, status_item)

            details_item = QTableWidgetItem(details_text)
            details_item.setToolTip(details_text)
            table.setItem(i, 2, details_item)

        # Statut global
        global_status_label = QLabel(f"Statut global: {'✓ Valide' if self.installation_valid else '✗ Non valide'}")
        global_status_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLOR_SCHEME.get('success', '#28a745') if self.installation_valid else COLOR_SCHEME.get('error', '#dc3545')};")
        global_status_label.setAlignment(Qt.AlignCenter)
        self.summary_layout.addWidget(global_status_label)

    def _display_structure_results(self):
        """
        Affiche les résultats de la vérification de la structure d'installation
        """
        structure_results = self.check_results.get("structure", {})

        # Titre
        title_label = QLabel("Structure de l'installation")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; margin-bottom: 10px;")
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
                item_text = key.replace("_exists", "").replace("_", " ").capitalize()
                item = QTreeWidgetItem([item_text, status])
                item.setForeground(1, Qt.green if value else Qt.red)
                tree.addTopLevelItem(item)

    def _display_config_ini_results(self):
        """
        Affiche les résultats de la vérification de Config.ini
        """
        config_ini_results = self.check_results.get("config_ini", {})

        # Titre
        title_label = QLabel("Vérification de Config.ini")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; margin-bottom: 10px;")
        self.config_ini_layout.addWidget(title_label)

        # Statut global
        status_text = "✓ Valide" if config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(
            f"color: {COLOR_SCHEME.get('success', '#28a745') if config_ini_results.get('config_valid', False) else COLOR_SCHEME.get('error', '#dc3545')}; font-weight: bold; font-size: 12pt; margin-bottom: 10px;")
        self.config_ini_layout.addWidget(status_label)

        # Tableau détaillé des vérifications
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Paramètre", "Valeur", "Statut"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.config_ini_layout.addWidget(table)

        # Liste des vérifications à afficher
        checks = [
            ("Application.ExpertMode", "ExpertMode"),
            ("Application.ExportAcquisitionDetailResults", "ExportAcquisitionDetailResults"),
            ("Hardware.Controller", "Controller"),
            ("Interf.Worker", "Worker"),
        ]

        # Ajouter Reflecto.Worker uniquement si pertinent
        values = config_ini_results.get("values", {})
        errors = config_ini_results.get("errors", [])
        has_reflecto_worker_error = any("Reflecto.Worker" in err or "ConfigLayer" in err for err in errors)
        if values.get("Reflecto.Worker") or has_reflecto_worker_error:
            checks.append(("Reflecto.Worker", "Worker"))

        # Ajout dynamique des valeurs présentes
        row = 0
        for param, key in checks:
            value = values.get(param, "")
            statut = "✓"
            if "errors" in config_ini_results and any(param.split(".")[1] in e for e in config_ini_results["errors"]):
                statut = "✗"
            elif value == "" and param != "Reflecto.Worker":  # Ne pas marquer Reflecto.Worker comme erreur s'il est absent
                statut = "✗"
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(param))
            table.setItem(row, 1, QTableWidgetItem(str(value)))
            status_item = QTableWidgetItem(statut)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(Qt.green if statut == "✓" else Qt.red)
            table.setItem(row, 2, status_item)
            row += 1

        # Affichage des erreurs spécifiques
        if "errors" in config_ini_results:
            for err in config_ini_results["errors"]:
                if not any(k in err for _, k in checks):
                    table.insertRow(row)
                    table.setItem(row, 0, QTableWidgetItem("Erreur"))
                    table.setItem(row, 1, QTableWidgetItem(err))
                    status_item = QTableWidgetItem("✗")
                    status_item.setTextAlignment(Qt.AlignCenter)
                    status_item.setForeground(Qt.red)
                    table.setItem(row, 2, status_item)
                    row += 1

    def _display_plate_config_ini_results(self):
        """
        Affiche les résultats de la vérification de PlateConfig.ini
        """
        plate_config_ini_results = self.check_results.get("plate_config_ini", {})

        # Titre
        title_label = QLabel("Vérification de PlateConfig.ini")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; margin-bottom: 10px;")
        self.plate_config_ini_layout.addWidget(title_label)

        # Statut global
        status_text = "✓ Valide" if plate_config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {COLOR_SCHEME.get('success', '#28a745') if plate_config_ini_results.get('config_valid', False) else COLOR_SCHEME.get('error', '#dc3545')}; font-weight: bold; font-size: 12pt; margin-bottom: 10px;")
        self.plate_config_ini_layout.addWidget(status_label)

        # Tableau détaillé des vérifications
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Type/Paramètre", "Valeur", "Statut"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.plate_config_ini_layout.addWidget(table)

        row = 0
        # Affichage des types de plaques
        plate_types = plate_config_ini_results.get("plate_types", [])
        for pt in plate_types:
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(f"Type de plaque"))
            table.setItem(row, 1, QTableWidgetItem(f"{pt.get('name','')} ({pt.get('config','')})"))
            status_item = QTableWidgetItem("✓")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(Qt.green)
            table.setItem(row, 2, status_item)
            row += 1

        # Affichage des configs de plaques
        configs = plate_config_ini_results.get("configs", {})
        for config_name, config in configs.items():
            if config.get("interf_params"):
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(f"{config_name}.InterfParams"))
                table.setItem(row, 1, QTableWidgetItem(config["interf_params"]))
                statut = "✓"
                if "errors" in plate_config_ini_results and any(config["interf_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                status_item = QTableWidgetItem(statut)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.green if statut == "✓" else Qt.red)
                table.setItem(row, 2, status_item)
                row += 1
            if config.get("reflecto_params"):
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(f"{config_name}.ReflectoParams"))
                table.setItem(row, 1, QTableWidgetItem(config["reflecto_params"]))
                statut = "✓"
                if "errors" in plate_config_ini_results and any(config["reflecto_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                status_item = QTableWidgetItem(statut)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.green if statut == "✓" else Qt.red)
                table.setItem(row, 2, status_item)
                row += 1
            for temp in config.get("temperature_files", []):
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(f"{config_name}.{temp['key']}"))
                table.setItem(row, 1, QTableWidgetItem(temp['file']))
                statut = "✓"
                if "errors" in plate_config_ini_results and any(temp['file'] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                status_item = QTableWidgetItem(statut)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.green if statut == "✓" else Qt.red)
                table.setItem(row, 2, status_item)
                row += 1

        # Affichage des erreurs spécifiques
        if "errors" in plate_config_ini_results:
            for err in plate_config_ini_results["errors"]:
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem("Erreur"))
                table.setItem(row, 1, QTableWidgetItem(err))
                status_item = QTableWidgetItem("✗")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.red)
                table.setItem(row, 2, status_item)
                row += 1

    def _display_zymocube_ctrl_ini_results(self):
        """
        Affiche les résultats de la vérification de ZymoCubeCtrl.ini
        """
        zymocube_ctrl_ini_results = self.check_results.get("zymocube_ctrl_ini", {})

        # Titre
        title_label = QLabel("Vérification de ZymoCubeCtrl.ini")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; margin-bottom: 10px;")
        self.zymocube_ctrl_ini_layout.addWidget(title_label)

        # Statut global
        status_text = "✓ Valide" if zymocube_ctrl_ini_results.get("config_valid", False) else "✗ Non valide"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {COLOR_SCHEME.get('success', '#28a745') if zymocube_ctrl_ini_results.get('config_valid', False) else COLOR_SCHEME.get('error', '#dc3545')}; font-weight: bold; font-size: 12pt; margin-bottom: 10px;")
        self.zymocube_ctrl_ini_layout.addWidget(status_label)

        # Tableau détaillé des vérifications
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Paramètre", "Valeur", "Statut"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.zymocube_ctrl_ini_layout.addWidget(table)

        row = 0
        # Paramètres principaux
        values = zymocube_ctrl_ini_results.get("values", {})
        for param, value in values.items():
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(param))
            table.setItem(row, 1, QTableWidgetItem(str(value)))
            statut = "✓"
            if "errors" in zymocube_ctrl_ini_results and any(param in e for e in zymocube_ctrl_ini_results["errors"]):
                statut = "✗"
            status_item = QTableWidgetItem(statut)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(Qt.green if statut == "✓" else Qt.red)
            table.setItem(row, 2, status_item)
            row += 1

        # Types de plaques
        plate_types = zymocube_ctrl_ini_results.get("plate_types", [])
        for pt in plate_types:
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem("PlateType"))
            table.setItem(row, 1, QTableWidgetItem(pt))
            status_item = QTableWidgetItem("✓")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(Qt.green)
            table.setItem(row, 2, status_item)
            row += 1

        # Affichage des erreurs spécifiques
        if "errors" in zymocube_ctrl_ini_results:
            for err in zymocube_ctrl_ini_results["errors"]:
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem("Erreur"))
                table.setItem(row, 1, QTableWidgetItem(err))
                status_item = QTableWidgetItem("✗")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.red)
                table.setItem(row, 2, status_item)
                row += 1

    def _display_errors_warnings(self):
        """
        Affiche les erreurs et avertissements
        """
        title_label = QLabel("Erreurs et avertissements")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; margin-bottom: 10px;")
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
            errors_group.setStyleSheet(
                f"QGroupBox {{ color: {COLOR_SCHEME.get('error', '#dc3545')}; font-weight: bold; }}")
            errors_layout = QVBoxLayout(errors_group)
            self.errors_layout.addWidget(errors_group)

            for error in errors:
                error_label = QLabel(f"• {error}")
                error_label.setStyleSheet(f"color: {COLOR_SCHEME.get('error', '#dc3545')};")
                error_label.setWordWrap(True)
                errors_layout.addWidget(error_label)

        # Affichage des avertissements
        if warnings:
            warnings_group = QGroupBox("Avertissements")
            warnings_group.setStyleSheet(
                f"QGroupBox {{ color: {COLOR_SCHEME.get('warning', '#ffc107')}; font-weight: bold; }}")
            warnings_layout = QVBoxLayout(warnings_group)
            self.errors_layout.addWidget(warnings_group)

            for warning in warnings:
                warning_label = QLabel(f"• {warning}")
                warning_label.setStyleSheet(f"color: {COLOR_SCHEME.get('warning', '#ffc107')};")
                warning_label.setWordWrap(True)
                warnings_layout.addWidget(warning_label)

        # Message si aucune erreur ni avertissement
        if not errors and not warnings:
            no_issues_label = QLabel("Aucune erreur ni avertissement détecté.")
            no_issues_label.setStyleSheet(f"color: {COLOR_SCHEME.get('success', '#28a745')}; font-weight: bold;")
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


            # ajouter valid au dic à envoyer au report generator
            self.check_results["installation_valid"] = self.installation_valid
            step1_results = self.main_window.session_data.get("client_info", {})
            installation_id = self.main_window.session_data.get("installation_id", "")

            # append installation_id to step1_results
            step1_results["installation_id"] = installation_id

            report_path = report_generator.generate_step2_report(self.check_results, step1_results)

            # Sauvegarder le chemin du rapport dans la session
            self.main_window.session_data["step2_report_path"] = report_path
            logger.info(f"Chemin du rapport de l'étape 2 sauvegardé dans la session: {report_path}")

            # Affichage du message de succès
            QMessageBox.information(self.widget, "Rapport", f"Le rapport a été généré avec succès:\n{report_path}")

            # Ouverture du rapport
            os.startfile(report_path)

            logger.info(f"Rapport de l'étape 2 généré: {report_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur",
                                 f"Une erreur est survenue lors de la génération du rapport:\n{str(e)}")

    def validate(self, generate_report=False):
        """
        Valide les données de l'étape 2
        """
        if not self.analysis_done:
            QMessageBox.critical(self.widget, "Validation", "Veuillez effectuer l'analyse avant de continuer.")
            return False



        if not self.installation_valid:
            reply = QMessageBox.question(self.widget, "Validation",
                                         "L'installation n'est pas valide. Voulez-vous quand même continuer ?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return False

        if generate_report:
            generate_report_reply = QMessageBox.question(self.widget, "Générer le rapport",
                                                         "Voulez-vous générer un rapport des vérifications ?",
                                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if generate_report_reply == QMessageBox.Yes:
                self.generate_report()


        return True

    def save_data(self):
        """
        Sauvegarde les données de l'étape 2 dans la session
        """
        self.main_window.session_data["step2_checks"] = {
            "installation_valid": self.installation_valid,
            "zymosoft_path": self.zymosoft_path,
            "check_results": self.check_results,
            "analysis_done": self.analysis_done
        }
        logger.info("Données de l'étape 2 sauvegardées")

    def load_data(self):
        """
        Charge les données de la session dans l'étape 2
        """
        step2_data = self.main_window.session_data.get("step2_checks", {})

        if "zymosoft_path" in step2_data:
            self.zymosoft_path = step2_data["zymosoft_path"]

        if "check_results" in step2_data:
            self.check_results = step2_data["check_results"]
            self.installation_valid = step2_data.get("installation_valid", False)
            self.analysis_done = step2_data.get("analysis_done", False)

            # Afficher les résultats s'ils existent
            if self.analysis_done and self.check_results:
                # Mettre à jour l'affichage du dossier
                if self.zymosoft_path:
                    self.folder_display_label.setText(f"{self.zymosoft_path}")
                    self.folder_display_label.setStyleSheet(f"""
                        QLabel {{
                            padding: 15px;
                            border: 2px solid {COLOR_SCHEME.get('success', '#28a745')};
                            border-radius: 8px;
                            background-color: {COLOR_SCHEME.get('success_light', '#d4edda')};
                            color: {COLOR_SCHEME.get('success_dark', '#155724')};
                            font-size: 12pt;
                            font-weight: bold;
                        }}
                    """)
                    self.start_analysis_button.setVisible(True)

                self._do_display_results()

        logger.info("Données de l'étape 2 chargées")

    def reset(self):
        """
        Réinitialise l'étape 2
        """
        self.zymosoft_path = ""
        self.check_results = {}
        self.installation_valid = False
        self.analysis_done = False
        self.analysis_in_progress = False
        self.config_checker = None
        self.file_validator = None

        # Réinitialiser l'interface
        self.folder_display_label.setText("Aucun dossier sélectionné")
        self.folder_display_label.setStyleSheet(f"""
            QLabel {{
                padding: 15px;
                border: 2px dashed {COLOR_SCHEME.get('border', '#ddd')};
                border-radius: 8px;
                background-color: {COLOR_SCHEME.get('background_light', '#f8f9fa')};
                color: {COLOR_SCHEME.get('text_secondary', '#666')};
                font-size: 12pt;
            }}
        """)
        self.start_analysis_button.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("")

        # Retourner à l'état initial
        self._show_initial_state()

        # Désactiver l'option "Modifier config.ini" dans le menu Actions
        if hasattr(self.main_window, 'edit_config_action'):
            self.main_window.edit_config_action.setEnabled(False)
            logger.debug("Action 'Modifier config.ini' désactivée après réinitialisation")

        logger.info("Étape 2 réinitialisée")
