#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 3 de l'assistant d'installation ZymoSoft : Validation par acquisitions
Fixed version addressing widget initialization issues
"""

import os
import logging
import threading
import time
import sys

import pandas
from PIL import Image, ImageQt
import uuid
import pandas as pd
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFrame, QFileDialog, QMessageBox,
                             QProgressBar, QTabWidget, QWidget, QScrollArea,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QCheckBox, QRadioButton, QGroupBox, QTextEdit,
                             QTreeWidget, QTreeWidgetItem, QButtonGroup, QDialog,
                             QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, pyqtSlot
from PyQt5.QtGui import QPixmap

from zymosoft_assistant.utils.constants import COLOR_SCHEME, PLATE_TYPES, ACQUISITION_MODES
from zymosoft_assistant.core.acquisition_analyzer import AcquisitionAnalyzer
from zymosoft_assistant.core.report_generator import ReportGenerator
from zymosoft_assistant.scripts.Routine_VALIDATION_ZC_18022025 import compare_enzymo_2_ref, comparaison_ZC_to_ref_v1, \
    comparaison_ZC_to_ref_v1_nanofilm
from zymosoft_assistant.scripts.getDatasFromWellResults import processWellResults, calculateLODLOQComparison
from zymosoft_assistant.scripts.processAcquisitionLog import analyzeLogFile, generateLogAnalysisReport
from .step_frame import StepFrame

logger = logging.getLogger(__name__)


class Step3Acquisition(StepFrame):
    """
    Classe pour l'étape 3 : Validation par acquisitions
    """
    # Signals for thread communication
    progress_updated = pyqtSignal(int, str)
    analysis_completed = pyqtSignal()
    analysis_error = pyqtSignal(str)

    def __init__(self, parent, main_window):
        """
        Initialise l'étape 3

        Args:
            parent: Widget parent
            main_window: Référence vers la fenêtre principale
        """
        # Variables pour les sélections
        self.plate_type_var = ""
        self.acquisition_mode_var = ""
        self.results_folder_var = ""
        self.reference_folder_var = ""
        self.comments_var = ""

        # Variables pour la configuration de validation
        self.do_repeta_sans_ref = False  # Toujours désactivé pour un déploiement
        self.do_compare_to_ref = False  # =1 si mode expert, =0 si mode client
        self.do_compare_enzymo_to_ref = True  # Toujours activé

        # Initialisation des valeurs par défaut
        self.plate_type_var = PLATE_TYPES[0]['id'] if PLATE_TYPES else ""
        self.acquisition_mode_var = ACQUISITION_MODES[0]['id'] if ACQUISITION_MODES else ""
        self.results_folder_var = ""
        self.reference_folder_var = ""

        # Initialize all widget references to None first
        self._initialize_widget_references()

        super().__init__(parent, main_window)

        # Variables pour les résultats d'analyse
        self.analysis_results = None
        self.current_acquisition_id = 0
        self.acquisitions = []

        # Variables pour la comparaison WellResults
        self.well_results_comparison = None

        # Variables pour la comparaison LOD/LOQ
        self.lod_loq_comparison = None

        # Variables pour l'analyse des logs
        self.log_analysis_results = None

        # Objets pour l'analyse
        self.analyzer = None

        # Images pour les graphiques
        self.graph_images = []

        # Connect signals to slots
        self.progress_updated.connect(self._update_progress)
        self.analysis_completed.connect(self._display_analysis_results)
        self.analysis_error.connect(self._handle_analysis_error)

        logger.info("Étape 3 initialisée")

    def _initialize_widget_references(self):
        """
        Initialize all widget references to None to avoid AttributeError
        """
        # Main components
        self.notebook = None
        self.folder_info_var = ""
        self.progress_bar = None
        self.progress_label = None
        self.info_text = None
        self.stats_table = None
        self.graphs_widget = None
        self.history_tree = None

        # Input widgets
        self.folder_entry = None
        self.ref_folder_entry = None
        self.compare_to_ref_checkbox = None
        self.compare_enzymo_to_ref_checkbox = None

        # Info labels
        self.folder_info_label = None
        self.ref_folder_info_label = None
        self.well_results_info_label = None
        self.lod_loq_info_label = None
        self.log_info_label = None
        self.image_title_label = None
        self.image_counter_label = None

        # Tables
        self.well_results_table = None
        self.lod_loq_table = None
        self.log_analysis_table = None

        # Navigation buttons
        self.prev_image_button = None
        self.next_image_button = None
        self.validate_continue_button = None
        self.invalidate_button = None
        self.report_button = None
        self.prev_substep_button = None
        self.next_substep_button = None

        # Button groups
        self.plate_type_group = None
        self.acquisition_mode_group = None

        # Layout containers
        self.nav_frame = None
        self.config_frame = None
        self.selection_frame = None
        self.analysis_frame = None
        self.history_frame = None

        # Layouts
        self.config_layout = None
        self.selection_layout = None
        self.analysis_layout = None

        # Tabs widget and indexes for coloring
        self.info_stats_tabs = None
        self.well_results_tab_index = -1
        self.lod_loq_tab_index = -1
        self.log_analysis_tab_index = -1

        # Image navigation
        self.current_image_index = 0
        self.graph_titles = []

    def create_widgets(self):
        """
        Crée les widgets de l'étape 3
        """
        # Utilisation du layout vertical principal
        main_layout = QVBoxLayout()
        self.layout.addLayout(main_layout)

        # Utiliser un splitter pour permettre le redimensionnement entre le notebook et l'historique
        main_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(main_splitter)

        # Notebook pour les sous-étapes
        self.notebook = QTabWidget()
        main_splitter.addWidget(self.notebook)

        # Create tabs
        self._create_all_tabs()

        # Historique des acquisitions
        self.history_frame = QGroupBox("Historique des acquisitions")
        history_layout = QVBoxLayout(self.history_frame)
        main_splitter.addWidget(self.history_frame)

        # Définir les tailles initiales des sections (3:1)
        main_splitter.setSizes([300, 100])

        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["#", "Type de plaque", "Mode", "Statut", "Date"])
        self.history_tree.setColumnWidth(0, 50)
        self.history_tree.setColumnWidth(1, 150)
        self.history_tree.setColumnWidth(2, 150)
        self.history_tree.setColumnWidth(3, 100)
        self.history_tree.setColumnWidth(4, 150)
        history_layout.addWidget(self.history_tree)

        # Barre de navigation spécifique à l'étape 3
        self._create_navigation_bar(main_layout)

        # Désactiver les onglets 2 et 3 au départ
        self.notebook.setTabEnabled(1, False)
        self.notebook.setTabEnabled(2, False)

        # Mise à jour de l'état des boutons de navigation
        self._update_nav_buttons()

        # Liaison des événements
        self.notebook.currentChanged.connect(self._on_tab_changed)

    def _create_all_tabs(self):
        """
        Create all notebook tabs and ensure all widgets are properly initialized
        """
        # Sous-étape 1: Configuration de l'acquisition
        self.config_frame = QWidget()
        self.config_layout = QVBoxLayout(self.config_frame)
        self.notebook.addTab(self.config_frame, "1. Configuration")
        self._create_config_widgets()

        # Sous-étape 2: Sélection des résultats
        self.selection_frame = QWidget()
        self.selection_layout = QVBoxLayout(self.selection_frame)
        self.notebook.addTab(self.selection_frame, "2. Sélection des résultats")
        self._create_selection_widgets()

        # Sous-étape 3: Analyse des résultats
        self.analysis_frame = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_frame)
        self.notebook.addTab(self.analysis_frame, "3. Analyse des résultats")
        self._create_analysis_widgets()

    def _create_navigation_bar(self, main_layout):
        """
        Create the navigation bar with all buttons
        """
        self.nav_frame = QFrame()
        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.nav_frame)

        self.prev_substep_button = QPushButton("Étape précédente")
        self.prev_substep_button.clicked.connect(self._previous_substep)
        nav_layout.addWidget(self.prev_substep_button, 0, Qt.AlignLeft)

        # Boutons d'action supplémentaires pour l'onglet d'analyse
        self.validate_continue_button = QPushButton("Valider cette acquisition et recommencer")
        self.validate_continue_button.clicked.connect(
            lambda: self._show_comments_dialog("validate_continue", True, True))
        self.validate_continue_button.setVisible(False)
        nav_layout.addWidget(self.validate_continue_button)

        self.invalidate_button = QPushButton("Invalider et refaire")
        self.invalidate_button.clicked.connect(lambda: self._show_comments_dialog("invalidate", False, True))
        self.invalidate_button.setVisible(False)
        nav_layout.addWidget(self.invalidate_button)

        # Bouton de rapport
        self.report_button = QPushButton("Générer rapport d'acquisition")
        self.report_button.clicked.connect(self._generate_acquisition_report)
        self.report_button.setVisible(False)
        nav_layout.addWidget(self.report_button)

        nav_layout.addStretch(1)

        self.next_substep_button = QPushButton("Étape suivante")
        self.next_substep_button.clicked.connect(self._next_substep)
        self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
        nav_layout.addWidget(self.next_substep_button, 0, Qt.AlignRight)

    def _create_config_widgets(self):
        """
        Crée les widgets pour la configuration de l'acquisition
        """
        # Description
        description_label = QLabel("Configurez les paramètres de l'acquisition à réaliser.")
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(600)
        self.config_layout.addWidget(description_label)
        self.config_layout.addSpacing(20)

        # Utiliser un splitter pour permettre le redimensionnement
        config_splitter = QSplitter(Qt.Vertical)
        self.config_layout.addWidget(config_splitter)
        self.config_layout.addStretch(1)

        # Type de plaque
        plate_type_frame = QGroupBox("Type de plaque")
        plate_type_layout = QVBoxLayout(plate_type_frame)

        # Groupe de boutons radio pour le type de plaque
        self.plate_type_group = QButtonGroup()

        for plate_type in PLATE_TYPES:
            rb = QRadioButton(plate_type['name'])
            rb.setProperty("plate_type_id", plate_type['id'])
            if self.plate_type_var == plate_type['id']:
                rb.setChecked(True)
            rb.toggled.connect(self._on_plate_type_changed)
            plate_type_layout.addWidget(rb)
            self.plate_type_group.addButton(rb)

        config_splitter.addWidget(plate_type_frame)

        # Mode d'acquisition
        mode_frame = QGroupBox("Mode d'acquisition")
        mode_layout = QVBoxLayout(mode_frame)

        # Groupe de boutons radio pour le mode d'acquisition
        self.acquisition_mode_group = QButtonGroup()

        for mode in ACQUISITION_MODES:
            rb = QRadioButton(mode['name'])
            rb.setProperty("acquisition_mode_id", mode['id'])
            if self.acquisition_mode_var == mode['id']:
                rb.setChecked(True)
            rb.toggled.connect(self._on_acquisition_mode_changed)
            mode_layout.addWidget(rb)
            self.acquisition_mode_group.addButton(rb)

        config_splitter.addWidget(mode_frame)

        # Instructions
        instructions_frame = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout(instructions_frame)

        instructions_text = (
            "1. Sélectionnez le type de plaque et le mode d'acquisition.\n"
            "2. Lancez ZymoSoft et réalisez une acquisition avec les paramètres sélectionnés.\n"
            "3. Une fois l'acquisition terminée, cliquez sur le bouton \"Acquisition réalisée\" en bas de la fenêtre."
        )

        instructions_label = QLabel(instructions_text)
        instructions_label.setWordWrap(True)
        instructions_label.setAlignment(Qt.AlignLeft)
        instructions_layout.addWidget(instructions_label)

        config_splitter.addWidget(instructions_frame)
        config_splitter.setSizes([200, 200, 100])

    def _create_selection_widgets(self):
        """
        Crée les widgets pour la sélection des résultats
        """
        # Description
        description_label = QLabel(
            "Sélectionnez les dossiers contenant les résultats de l'acquisition et de référence.")
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(600)
        self.selection_layout.addWidget(description_label)
        self.selection_layout.addSpacing(20)

        # Sélection du dossier de résultats
        folder_frame = QFrame()
        folder_layout = QHBoxLayout(folder_frame)
        folder_layout.setContentsMargins(20, 0, 20, 0)
        self.selection_layout.addWidget(folder_frame)
        self.selection_layout.addSpacing(10)

        folder_label = QLabel("Dossier de résultats :")
        folder_label.setMinimumWidth(150)
        folder_layout.addWidget(folder_label)

        self.folder_entry = QLineEdit()
        self.folder_entry.setText(self.results_folder_var)
        self.folder_entry.setMinimumWidth(300)
        self.folder_entry.textChanged.connect(self._on_folder_entry_changed)
        folder_layout.addWidget(self.folder_entry)

        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self._browse_results_folder)
        folder_layout.addWidget(browse_button)

        # Informations sur le dossier
        self.folder_info_label = QLabel("")
        self.folder_info_label.setWordWrap(True)
        self.folder_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        self.selection_layout.addWidget(self.folder_info_label)
        self.selection_layout.addSpacing(10)

        # Sélection du dossier de référence
        ref_folder_frame = QFrame()
        ref_folder_layout = QHBoxLayout(ref_folder_frame)
        ref_folder_layout.setContentsMargins(20, 0, 20, 0)
        self.selection_layout.addWidget(ref_folder_frame)
        self.selection_layout.addSpacing(10)

        ref_folder_label = QLabel("Dossier de référence :")
        ref_folder_label.setMinimumWidth(150)
        ref_folder_layout.addWidget(ref_folder_label)

        self.ref_folder_entry = QLineEdit()
        self.ref_folder_entry.setText(self.reference_folder_var)
        self.ref_folder_entry.setMinimumWidth(300)
        self.ref_folder_entry.textChanged.connect(self._on_ref_folder_entry_changed)
        ref_folder_layout.addWidget(self.ref_folder_entry)

        ref_browse_button = QPushButton("Parcourir...")
        ref_browse_button.clicked.connect(self._browse_reference_folder)
        ref_folder_layout.addWidget(ref_browse_button)

        # Informations sur le dossier de référence
        self.ref_folder_info_label = QLabel("")
        self.ref_folder_info_label.setWordWrap(True)
        self.ref_folder_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        self.selection_layout.addWidget(self.ref_folder_info_label)
        self.selection_layout.addSpacing(10)

        # Options de validation
        validation_frame = QGroupBox("Options de validation")
        validation_layout = QVBoxLayout(validation_frame)
        self.selection_layout.addWidget(validation_frame)
        self.selection_layout.addSpacing(10)

        # Checkbox pour do_compare_to_ref
        self.compare_to_ref_checkbox = QCheckBox("Comparer aux références (mode expert)")
        self.compare_to_ref_checkbox.setChecked(self.do_compare_to_ref)
        self.compare_to_ref_checkbox.toggled.connect(self._on_compare_to_ref_toggled)
        validation_layout.addWidget(self.compare_to_ref_checkbox)

        # Checkbox pour do_compare_enzymo_to_ref
        self.compare_enzymo_to_ref_checkbox = QCheckBox("Comparer les données enzymatiques aux références")
        self.compare_enzymo_to_ref_checkbox.setChecked(self.do_compare_enzymo_to_ref)
        self.compare_enzymo_to_ref_checkbox.toggled.connect(self._on_compare_enzymo_to_ref_toggled)
        validation_layout.addWidget(self.compare_enzymo_to_ref_checkbox)

        # Barre de progression
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(20, 0, 20, 0)
        self.selection_layout.addWidget(progress_frame)
        self.selection_layout.addSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignLeft)
        progress_layout.addWidget(self.progress_label)

        # Instructions
        instructions_label = QLabel(
            "Une fois le dossier sélectionné, cliquez sur le bouton \"Analyser les résultats\" en bas de la fenêtre."
        )
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        self.selection_layout.addWidget(instructions_label)
        self.selection_layout.addStretch(1)

    def _create_analysis_widgets(self):
        """
        Crée les widgets pour l'analyse des résultats
        """
        # Description compacte en haut
        description_label = QLabel("Résultats de l'analyse de l'acquisition.")
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(600)
        # Réduire les marges pour économiser l'espace
        description_label.setContentsMargins(0, 0, 0, 5)
        self.analysis_layout.addWidget(description_label)

        # Réduire l'espacement après la description
        self.analysis_layout.addSpacing(5)

        # Conteneur principal avec splitter pour permettre le redimensionnement
        # Donner tout l'espace disponible à cette section
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setSizePolicy(QWidget().sizePolicy().Expanding, QWidget().sizePolicy().Expanding)
        self.analysis_layout.addWidget(main_splitter, 1)  # stretch factor = 1 pour prendre tout l'espace

        # Panneau gauche: Statistiques et informations
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 0, 5, 0)  # Réduire les marges

        # Utiliser des onglets pour les informations, statistiques et comparaisons
        self.info_stats_tabs = QTabWidget()
        left_layout.addWidget(self.info_stats_tabs, 1)  # stretch factor = 1 pour prendre tout l'espace

        # Create all tabs for the left panel
        self._create_info_tabs(self.info_stats_tabs)

        # Initialiser la variable de commentaires
        self.comments_var = ""

        # Ajouter le panneau gauche au splitter
        main_splitter.addWidget(left_panel)

        # Panneau droit: Images
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 0, 10, 0)  # Réduire les marges

        # Create image display widgets
        self._create_image_display_widgets(right_layout)

        # Ajouter le panneau droit au splitter
        main_splitter.addWidget(right_panel)

        # Définir les tailles initiales des panneaux (1:2)
        main_splitter.setSizes([100, 200])

        # Initialiser les variables pour la navigation des images
        self.current_image_index = 0
        self.graph_images = []
        self.graph_titles = []

    def _create_info_tabs(self, info_stats_tabs):
        """
        Create all information tabs in the left panel
        """
        # Onglet Informations
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        info_stats_tabs.addTab(info_tab, "Informations")

        # Onglet Statistiques
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        stats_layout.addWidget(self.stats_table)
        info_stats_tabs.addTab(stats_tab, "Statistiques")

        # Onglet Comparaison WellResults
        well_results_tab = QWidget()
        well_results_layout = QVBoxLayout(well_results_tab)

        # Informations sur la comparaison
        self.well_results_info_label = QLabel("")
        self.well_results_info_label.setWordWrap(True)
        self.well_results_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        well_results_layout.addWidget(self.well_results_info_label)

        # Tableau pour afficher les résultats de comparaison
        self.well_results_table = QTableWidget(0, 6)
        self.well_results_table.setHorizontalHeaderLabels(
            ["Activité", "Area", "Acquisition", "Référence", "Diff", "Valide"])
        self.well_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.well_results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.well_results_table.setAlternatingRowColors(True)
        well_results_layout.addWidget(self.well_results_table)
        self.well_results_tab_index = info_stats_tabs.addTab(well_results_tab, "Comparaison WellResults")

        # Onglet Comparaison LOD/LOQ
        lod_loq_tab = QWidget()
        lod_loq_layout = QVBoxLayout(lod_loq_tab)

        # Informations sur la comparaison LOD/LOQ
        self.lod_loq_info_label = QLabel("")
        self.lod_loq_info_label.setWordWrap(True)
        self.lod_loq_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        lod_loq_layout.addWidget(self.lod_loq_info_label)

        # Tableau pour afficher les résultats de comparaison LOD/LOQ
        self.lod_loq_table = QTableWidget(0, 9)
        self.lod_loq_table.setHorizontalHeaderLabels(
            ["Area", "LOD_Ref", "LOD_Acq", "LOQ_Ref", "LOQ_Acq", "Diff LOD", "Diff LOQ", "Valide LOD", "Valide LOQ"])
        self.lod_loq_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lod_loq_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.lod_loq_table.setAlternatingRowColors(True)
        lod_loq_layout.addWidget(self.lod_loq_table)
        self.lod_loq_tab_index = info_stats_tabs.addTab(lod_loq_tab, "Comparaison LOD/LOQ")

        # Onglet Analyse des logs
        log_analysis_tab = QWidget()
        log_analysis_layout = QVBoxLayout(log_analysis_tab)

        # Informations sur l'analyse des logs
        log_info_frame = QFrame()
        log_info_frame.setFrameShape(QFrame.StyledPanel)
        log_info_frame.setFrameShadow(QFrame.Raised)
        log_info_layout = QVBoxLayout(log_info_frame)

        self.log_info_label = QLabel("Aucune analyse de log disponible.")
        self.log_info_label.setWordWrap(True)
        log_info_layout.addWidget(self.log_info_label)
        log_analysis_layout.addWidget(log_info_frame)

        # Tableau des résultats d'analyse des logs
        log_table_frame = QFrame()
        log_table_frame.setFrameShape(QFrame.StyledPanel)
        log_table_frame.setFrameShadow(QFrame.Raised)
        log_table_layout = QVBoxLayout(log_table_frame)

        log_table_label = QLabel("Résultats de l'analyse des logs")
        log_table_label.setStyleSheet("font-weight: bold;")
        log_table_layout.addWidget(log_table_label)

        self.log_analysis_table = QTableWidget()
        self.log_analysis_table.setColumnCount(2)
        self.log_analysis_table.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
        self.log_analysis_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.log_analysis_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.log_analysis_table.setAlternatingRowColors(True)
        log_table_layout.addWidget(self.log_analysis_table)

        log_analysis_layout.addWidget(log_table_frame)
        self.log_analysis_tab_index = info_stats_tabs.addTab(log_analysis_tab, "Analyse des logs")

    def _update_tab_colors(self):
        """
        Met à jour les couleurs des onglets en fonction des résultats de validation
        """
        try:
            if not hasattr(self, 'info_stats_tabs') or not self.info_stats_tabs:
                return

            # Réinitialiser les couleurs des onglets
            self.info_stats_tabs.setStyleSheet("")

            # Vérifier les erreurs dans chaque onglet et colorer en orange si nécessaire
            tab_styles = []

            # Vérifier l'onglet Comparaison WellResults
            if hasattr(self, 'well_results_tab_index') and self._has_well_results_errors():
                tab_styles.append(
                    f"QTabWidget::tab:nth-child({self.well_results_tab_index + 1}) {{ background-color: orange; }}")

            # Vérifier l'onglet Comparaison LOD/LOQ
            if hasattr(self, 'lod_loq_tab_index') and self._has_lod_loq_errors():
                tab_styles.append(
                    f"QTabWidget::tab:nth-child({self.lod_loq_tab_index + 1}) {{ background-color: orange; }}")

            # Appliquer les styles si nécessaire
            if tab_styles:
                combined_style = "QTabWidget::pane { border: 1px solid #C0C0C0; } " + " ".join(tab_styles)
                self.info_stats_tabs.setStyleSheet(combined_style)

        except Exception as e:
            logger.error(f"Erreur dans _update_tab_colors: {str(e)}", exc_info=True)

    def _has_well_results_errors(self):
        """
        Vérifie si l'onglet WellResults contient des erreurs (éléments non valides)
        """
        try:
            validation = self.analysis_results.get("validation", {})

            # Vérifier s'il y a une erreur explicite
            if "well_results_error" in validation:
                return True

            # Vérifier s'il y a des résultats non valides
            if "well_results_comparison" in validation:
                well_results_df = validation["well_results_comparison"]
                if 'valid' in well_results_df.columns:
                    invalid_count = (~well_results_df['valid']).sum()
                    return invalid_count > 0

            return False
        except Exception:
            return False

    def _has_lod_loq_errors(self):
        """
        Vérifie si l'onglet LOD/LOQ contient des erreurs (éléments non valides)
        """
        try:
            validation = self.analysis_results.get("validation", {})

            # Vérifier s'il y a une erreur explicite
            if "lod_loq_error" in validation:
                return True

            # Vérifier s'il y a des résultats non valides
            if "lod_loq_comparison" in validation:
                lod_loq_df = validation["lod_loq_comparison"]

                # Vérifier les colonnes de validation
                has_lod_errors = False
                has_loq_errors = False

                # Vérifier Lod_Valid
                for col_name in ['Lod_Valid', 'Lod_valid']:
                    if col_name in lod_loq_df.columns:
                        has_lod_errors = (~lod_loq_df[col_name]).sum() > 0
                        break

                # Vérifier Loq_Valid
                for col_name in ['Loq_Valid', 'Loq_valid']:
                    if col_name in lod_loq_df.columns:
                        has_loq_errors = (~lod_loq_df[col_name]).sum() > 0
                        break

                return has_lod_errors or has_loq_errors

            return False
        except Exception:
            return False

    def _create_image_display_widgets(self, right_layout):
        """
        Create image display widgets for the right panel
        """
        # Images - maximiser l'utilisation de l'espace
        images_frame = QGroupBox("Images")
        images_layout = QVBoxLayout(images_frame)
        # Réduire les marges pour économiser l'espace
        images_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.addWidget(images_frame, 1)  # stretch factor = 1 pour prendre tout l'espace

        # Container pour l'image et les contrôles
        image_container = QWidget()
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(0, 0, 0, 0)
        image_container_layout.setSpacing(5)  # Réduire l'espacement
        images_layout.addWidget(image_container, 1)  # stretch factor = 1

        # Widget pour afficher l'image - donner plus d'espace à l'image
        self.graphs_widget = QLabel()
        self.graphs_widget.setStyleSheet(f"background-color: {COLOR_SCHEME['background']};")
        self.graphs_widget.setAlignment(Qt.AlignCenter)
        self.graphs_widget.setMinimumHeight(200)  # Réduire la hauteur minimale
        self.graphs_widget.setSizePolicy(QWidget().sizePolicy().Expanding, QWidget().sizePolicy().Expanding)
        self.graphs_widget.mousePressEvent = self._on_image_clicked
        image_container_layout.addWidget(self.graphs_widget, 1)  # stretch factor = 1 pour prendre l'espace disponible

        # Titre de l'image
        self.image_title_label = QLabel()
        self.image_title_label.setAlignment(Qt.AlignCenter)
        self.image_title_label.setStyleSheet(f"color: {COLOR_SCHEME['text']}; font-weight: bold;")
        self.image_title_label.setMaximumHeight(25)  # Limiter la hauteur du titre
        image_container_layout.addWidget(self.image_title_label)

        # Boutons de navigation - compacts
        nav_buttons_container = QWidget()
        nav_buttons_layout = QHBoxLayout(nav_buttons_container)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_buttons_layout.setSpacing(5)  # Réduire l'espacement
        nav_buttons_container.setMaximumHeight(35)  # Limiter la hauteur des boutons
        image_container_layout.addWidget(nav_buttons_container)

        self.prev_image_button = QPushButton("< Précédent")
        self.prev_image_button.clicked.connect(self._show_previous_image)
        self.prev_image_button.setEnabled(False)
        nav_buttons_layout.addWidget(self.prev_image_button)

        self.image_counter_label = QLabel("0/0")
        self.image_counter_label.setAlignment(Qt.AlignCenter)
        nav_buttons_layout.addWidget(self.image_counter_label)

        self.next_image_button = QPushButton("Suivant >")
        self.next_image_button.clicked.connect(self._show_next_image)
        self.next_image_button.setEnabled(False)
        nav_buttons_layout.addWidget(self.next_image_button)

    # Event handlers for widget interactions
    def _on_plate_type_changed(self, checked):
        """
        Appelé lorsque le type de plaque est modifié
        """
        if checked:
            sender = self.sender()
            if sender:
                self.plate_type_var = sender.property("plate_type_id")
                logger.info(f"Type de plaque sélectionné: {self.plate_type_var}")

    def _on_acquisition_mode_changed(self, checked):
        """
        Appelé lorsque le mode d'acquisition est modifié
        """
        if checked:
            sender = self.sender()
            if sender:
                self.acquisition_mode_var = sender.property("acquisition_mode_id")
                logger.info(f"Mode d'acquisition sélectionné: {self.acquisition_mode_var}")

    def _on_folder_entry_changed(self, text):
        """
        Appelé lorsque le texte du champ de dossier est modifié
        """
        try:
            self.results_folder_var = text
            if text:
                self._check_results_folder(text)
            else:
                if self.folder_info_label:
                    self.folder_info_label.setText("")
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _on_folder_entry_changed: {str(e)}", exc_info=True)
            if self.folder_info_label:
                self.folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")

    def _on_ref_folder_entry_changed(self, text):
        """
        Appelé lorsque le texte du champ de dossier de référence est modifié
        """
        try:
            self.reference_folder_var = text
            if text:
                self._check_reference_folder(text)
            else:
                if self.ref_folder_info_label:
                    self.ref_folder_info_label.setText("")
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _on_ref_folder_entry_changed: {str(e)}", exc_info=True)
            if self.ref_folder_info_label:
                self.ref_folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")

    def _on_compare_to_ref_toggled(self, checked):
        """
        Appelé lorsque la case à cocher pour comparer aux références est modifiée
        """
        try:
            self.do_compare_to_ref = checked
            logger.info(f"Option de comparaison aux références: {checked}")
        except Exception as e:
            logger.error(f"Erreur dans _on_compare_to_ref_toggled: {str(e)}", exc_info=True)

    def _on_compare_enzymo_to_ref_toggled(self, checked):
        """
        Appelé lorsque la case à cocher pour comparer les données enzymatiques est modifiée
        """
        try:
            self.do_compare_enzymo_to_ref = checked
            logger.info(f"Option de comparaison des données enzymatiques: {checked}")
        except Exception as e:
            logger.error(f"Erreur dans _on_compare_enzymo_to_ref_toggled: {str(e)}", exc_info=True)

    # Folder validation methods
    def _check_results_folder(self, folder):
        """
        Vérifie le contenu du dossier de résultats
        """
        try:
            if not folder or not os.path.exists(folder):
                if self.folder_info_label:
                    self.folder_info_label.setText("Dossier non valide ou inexistant.")
                return

            files = os.listdir(folder)
            csv_files = [f for f in files if f.lower().endswith('.csv')]

            if not csv_files:
                if self.folder_info_label:
                    self.folder_info_label.setText("Aucun fichier CSV trouvé dans le dossier.")
                return

            if self.folder_info_label:
                self.folder_info_label.setText(f"Dossier valide. {len(csv_files)} fichiers CSV trouvés.")
            logger.info(f"Dossier valide: {folder}, {len(csv_files)} fichiers CSV trouvés")

            self._update_nav_buttons()
        except Exception as e:
            if self.folder_info_label:
                self.folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")
            logger.error(f"Erreur dans _check_results_folder: {str(e)}", exc_info=True)

    def _check_reference_folder(self, folder):
        """
        Vérifie le contenu du dossier de référence
        """
        try:
            if not folder or not os.path.exists(folder):
                if self.ref_folder_info_label:
                    self.ref_folder_info_label.setText("Dossier non valide ou inexistant.")
                return

            files = os.listdir(folder)
            csv_files = [f for f in files if f.lower().endswith('.csv')]
            excel_files = [f for f in files if f.lower().endswith('.xlsx')]

            if not csv_files and not excel_files:
                if self.ref_folder_info_label:
                    self.ref_folder_info_label.setText("Aucun fichier CSV ou Excel trouvé dans le dossier.")
                return

            if self.ref_folder_info_label:
                self.ref_folder_info_label.setText(
                    f"Dossier valide. {len(csv_files)} fichiers CSV et {len(excel_files)} fichiers Excel trouvés.")
            logger.info(
                f"Dossier de référence valide: {folder}, {len(csv_files)} fichiers CSV et {len(excel_files)} fichiers Excel trouvés")

            self._update_nav_buttons()
        except Exception as e:
            if self.ref_folder_info_label:
                self.ref_folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")
            logger.error(f"Erreur dans _check_reference_folder: {str(e)}", exc_info=True)

    # Browse folder methods
    def _browse_results_folder(self):
        """
        Ouvre une boîte de dialogue pour sélectionner le dossier de résultats
        """
        try:
            folder = QFileDialog.getExistingDirectory(
                self.widget,
                "Sélectionner le dossier de résultats d'acquisition"
            )
            if folder:
                self.results_folder_var = folder
                if self.folder_entry:
                    self.folder_entry.setText(folder)
                self._check_results_folder(folder)
        except Exception as e:
            logger.error(f"Erreur dans _browse_results_folder: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _browse_reference_folder(self):
        """
        Ouvre une boîte de dialogue pour sélectionner le dossier de référence
        """
        try:
            folder = QFileDialog.getExistingDirectory(
                self.widget,
                "Sélectionner le dossier de référence"
            )
            if folder:
                self.reference_folder_var = folder
                if self.ref_folder_entry:
                    self.ref_folder_entry.setText(folder)
                self._check_reference_folder(folder)
        except Exception as e:
            logger.error(f"Erreur dans _browse_reference_folder: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    # Analysis methods
    def _analyze_results(self):
        """
        Lance l'analyse des résultats d'acquisition
        """
        try:
            results_folder = self.results_folder_var
            reference_folder = self.reference_folder_var

            if not results_folder or not os.path.exists(results_folder):
                QMessageBox.critical(self.widget, "Erreur", "Veuillez sélectionner un dossier de résultats valide.")
                return

            # Vérifier si un dossier de référence est requis
            reference_required = self.do_compare_to_ref or self.do_compare_enzymo_to_ref
            if reference_required and (not reference_folder or not os.path.exists(reference_folder)):
                QMessageBox.critical(self.widget, "Erreur",
                                     "Veuillez sélectionner un dossier de référence valide pour les options de validation sélectionnées.")
                return

            self.analyzer = AcquisitionAnalyzer()

            # Désactiver le bouton pendant l'analyse
            if self.next_substep_button:
                self.next_substep_button.setEnabled(False)
                self.next_substep_button.setText("Analyse en cours...")
                self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['disabled']}; color: white;")

            if self.progress_bar:
                self.progress_bar.setValue(0)
                self.progress_bar.setStyleSheet(
                    f"QProgressBar::chunk {{ background-color: {COLOR_SCHEME['primary']}; }}")

            if self.progress_label:
                self.progress_label.setText("Lancement de l'analyse...")
                self.progress_label.setStyleSheet(f"color: {COLOR_SCHEME['primary']}; font-weight: bold;")

            # Start analysis in separate thread
            def analyze_task():
                try:
                    self._perform_analysis(results_folder, reference_folder)
                except Exception as e:
                    logger.error(f"Erreur lors de l'analyse des résultats: {str(e)}", exc_info=True)
                    self.analysis_error.emit(str(e))

            threading.Thread(target=analyze_task, daemon=True).start()
        except Exception as e:
            logger.error(f"Erreur dans _analyze_results: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _perform_analysis(self, results_folder, reference_folder):
        """
        Perform the actual analysis in a separate thread
        """
        self.progress_updated.emit(10, "Chargement des données...")
        time.sleep(0.5)

        # Analyse standard des résultats
        self.progress_updated.emit(30, "Analyse des résultats...")
        analysis_results = self.analyzer.analyze_results(
            results_folder,
            plate_type=self.plate_type_var,
            acquisition_mode=self.acquisition_mode_var
        )

        # Créer un dossier pour les résultats de validation si nécessaire
        validation_output_dir = os.path.join(results_folder, "validation_results")
        if (self.do_compare_to_ref or self.do_compare_enzymo_to_ref) and not os.path.exists(validation_output_dir):
            os.makedirs(validation_output_dir)

        # Exécuter les scripts de validation selon les options sélectionnées
        validation_results = {}

        # Déterminer le type de machine à valider et la référence
        machine_to_validate = f"ZC_{self.plate_type_var}" if self.plate_type_var else "ZC"
        reference_machine = "REFERENCE ZYMOPTIQ"

        # Perform various validation comparisons
        self._perform_well_results_comparison(reference_folder, validation_output_dir, validation_results)
        self._perform_lod_loq_comparison(reference_folder, validation_output_dir, validation_results)

        if self.do_compare_to_ref:
            self._perform_reference_comparison(results_folder, reference_folder, validation_output_dir,
                                               validation_results, machine_to_validate, reference_machine)

        if self.do_compare_enzymo_to_ref:
            self._perform_enzymo_comparison(results_folder, reference_folder, validation_output_dir,
                                            validation_results, machine_to_validate, reference_machine)

        # Perform log analysis
        self._perform_log_analysis(results_folder, analysis_results)

        # Add validation results to analysis results
        if validation_results:
            analysis_results["validation"] = validation_results

        self.progress_updated.emit(100, "Analyse terminée.")
        self.analysis_results = analysis_results
        self.analysis_completed.emit()

    def _perform_well_results_comparison(self, reference_folder, validation_output_dir, validation_results):
        """
        Perform WellResults comparison
        """
        if reference_folder and os.path.exists(reference_folder):
            self.progress_updated.emit(40, "Comparaison des résultats WellResults...")
            try:
                # Exécuter la comparaison WellResults
                well_results_comparison = processWellResults(self.results_folder_var, reference_folder)

                # Sauvegarder les résultats dans le dossier de validation
                csv_path = os.path.join(validation_output_dir, "comparaison_resultats_puits.csv")
                well_results_comparison.to_csv(csv_path, index=False)

                # Stocker les résultats pour l'affichage
                validation_results["well_results_comparison"] = well_results_comparison

                logger.info(f"Comparaison WellResults terminée, résultats sauvegardés dans {csv_path}")

            except Exception as e:
                logger.error(f"Erreur lors de la comparaison WellResults: {str(e)}", exc_info=True)
                validation_results["well_results_error"] = str(e)

    def _perform_lod_loq_comparison(self, reference_folder, validation_output_dir, validation_results):
        """
        Perform LOD/LOQ comparison
        """
        if self.do_compare_enzymo_to_ref and reference_folder and os.path.exists(reference_folder):
            self.progress_updated.emit(60, "Comparaison des LOD et LOQ...")
            try:
                # Exécuter la comparaison LOD/LOQ
                lod_loq_comparison = calculateLODLOQComparison(self.results_folder_var, reference_folder)

                # Sauvegarder les résultats dans le dossier de validation
                csv_path = os.path.join(validation_output_dir, "comparaison_LOD_LOQ.csv")
                lod_loq_comparison.to_csv(csv_path, index=False)

                # Stocker les résultats pour l'affichage
                validation_results["lod_loq_comparison"] = lod_loq_comparison

                logger.info(f"Comparaison LOD/LOQ terminée, résultats sauvegardés dans {csv_path}")

            except Exception as e:
                logger.error(f"Erreur lors de la comparaison LOD/LOQ: {str(e)}", exc_info=True)
                validation_results["lod_loq_error"] = str(e)

    def _perform_reference_comparison(self, results_folder, reference_folder, validation_output_dir,
                                      validation_results, machine_to_validate, reference_machine):
        """
        Perform reference comparison (volumes and thicknesses)
        """
        self.progress_updated.emit(50, "Comparaison aux références...")
        try:
            # Déterminer si c'est un nanofilm ou non en fonction du type de plaque
            is_nanofilm = "nanofilm" in self.plate_type_var.lower() if self.plate_type_var else False

            # Normaliser les chemins pour s'assurer qu'ils utilisent les bons séparateurs
            results_folder_norm = os.path.normpath(results_folder)
            reference_folder_norm = os.path.normpath(reference_folder)
            validation_output_dir_norm = os.path.normpath(validation_output_dir)

            if is_nanofilm:
                # Utiliser la fonction pour nanofilm
                name_dossier, slope, intercept, r_value, nb_puits_loin_fit, diff_mean, diff_cv, vect1, vect2 = comparaison_ZC_to_ref_v1_nanofilm(
                    "SC", results_folder_norm, machine_to_validate, reference_folder_norm, reference_machine,
                    validation_output_dir_norm, "validation_comparison", 5
                )
            else:
                # Utiliser la fonction pour microdepot
                name_dossier, slope, intercept, r_value, nb_puits_loin_fit, diff_mean, diff_cv, diam_diff_mean, diam_diff_cv, vect1, vect2 = comparaison_ZC_to_ref_v1(
                    "GP", results_folder_norm, machine_to_validate, reference_folder_norm, reference_machine,
                    validation_output_dir_norm, "validation_comparison", 5
                )

            validation_results["comparison"] = {
                "name_dossier": name_dossier,
                "slope": slope,
                "intercept": intercept,
                "r_value": r_value,
                "nb_puits_loin_fit": nb_puits_loin_fit,
                "diff_mean": diff_mean,
                "diff_cv": diff_cv
            }

            # Ajouter les métriques de diamètre si disponibles (cas non-nanofilm)
            if not is_nanofilm:
                validation_results["comparison"].update({
                    "diam_diff_mean": diam_diff_mean,
                    "diam_diff_cv": diam_diff_cv
                })

        except Exception as e:
            logger.error(f"Erreur lors de la comparaison aux références: {str(e)}", exc_info=True)
            validation_results["comparison_error"] = str(e)

    def _perform_enzymo_comparison(self, results_folder, reference_folder, validation_output_dir,
                                   validation_results, machine_to_validate, reference_machine):
        """
        Perform enzymatic comparison
        """
        self.progress_updated.emit(70, "Comparaison des données enzymatiques...")

        try:
            # Obtenir les dossiers parents
            results_parent_folder = os.path.dirname(results_folder)
            reference_parent_folder = os.path.dirname(reference_folder)

            # Trouver les dossiers d'acquisition dans les dossiers parents
            results_subfolders = [f for f in os.listdir(results_parent_folder) if
                                  os.path.isdir(os.path.join(results_parent_folder, f))]
            reference_subfolders = [f for f in os.listdir(reference_parent_folder) if
                                    os.path.isdir(os.path.join(reference_parent_folder, f))]

            if results_subfolders and reference_subfolders:
                # Utiliser le premier sous-dossier trouvé pour chaque
                acquisition_name_instrument_1 = reference_subfolders[0]
                acquisition_name_instrument_2 = results_subfolders[0]

                # Exécuter la comparaison enzymatique avec les dossiers parents
                # Créer un dossier pour stocker les résultats de comparaison
                comparison_dir = os.path.join(validation_output_dir, "comparaison_enzymo_routine")
                if not os.path.exists(comparison_dir):
                    os.makedirs(comparison_dir)

                # Récupérer tous les onglets du fichier Excel
                excel_path = os.path.normpath(os.path.join(reference_parent_folder, acquisition_name_instrument_1,
                                                           'WellResults.xlsx'))
                all_results = []

                if os.path.exists(excel_path):
                    excel_file = pandas.ExcelFile(excel_path)
                    sheet_names = excel_file.sheet_names

                    # Paramètres pour les pourcentages de dégradation (utilisés dans l'en-tête CSV)
                    # La fonction compare_enzymo_2_ref utilise des pourcentages fixes: 30%, 50%, 70%
                    deg_percentages = [30, 50, 70]

                    # Itérer sur tous les onglets
                    for sheet_name in sheet_names:
                        try:
                            # Normaliser les chemins
                            reference_parent_folder_norm = os.path.normpath(reference_parent_folder)
                            results_parent_folder_norm = os.path.normpath(results_parent_folder)
                            comparison_dir_norm = os.path.normpath(comparison_dir)

                            try:
                                ref_data, validation_data = compare_enzymo_2_ref(
                                    reference_parent_folder_norm, reference_machine,
                                    acquisition_name_instrument_1, sheet_name,
                                    results_parent_folder_norm, machine_to_validate,
                                    acquisition_name_instrument_2,
                                    comparison_dir_norm
                                )
                            except FileNotFoundError as fnf_error:
                                logger.error(f"Fichier non trouvé lors de la comparaison enzymatique: {str(fnf_error)}",
                                             exc_info=True)
                                # Continuer avec le prochain onglet
                                continue

                            all_results.append(ref_data)
                            all_results.append(validation_data)

                            print(
                                f"Onglet {sheet_name} - Référence: {ref_data}, Validation: {validation_data}")
                        except Exception as e:
                            logger.error(
                                f"Erreur lors de la comparaison pour l'onglet {sheet_name}: {str(e)}",
                                exc_info=True)

                    # Créer le fichier CSV de résultats
                    if all_results:
                        find_len_max = 0
                        for result in all_results:
                            if len(result) > find_len_max:
                                find_len_max = len(result)

                        # Utiliser les mêmes paramètres de dégradation que ceux définis plus haut

                        csv_path = os.path.normpath(os.path.join(comparison_dir, 'data_compar_enzymo_2_ref.csv'))

                        # S'assurer que le répertoire existe
                        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

                        # Préparer le contenu du fichier
                        csv_content = ""

                        # Écrire l'en-tête
                        header = 'Nom de l Acquisitions;Machine;Zone;LOD;LOQ;Sensibilite (en U/mL);'

                        # Ajouter les CV pour 30%, 50%, 70%
                        for deg_percent in deg_percentages:
                            header += f'CV % deg a {deg_percent}%;'

                        csv_content += header

                        # Calculer le nombre d'échantillons basé sur la structure des données retournées
                        # data_R: 9 base + 2*samples (activité, RSD par échantillon)
                        # data_V: 9 base + 2*samples + 6 diff_base + 2*samples diff = 15 + 4*samples
                        # find_len_max correspond à la longueur de data_V
                        base_columns_with_diffs = 15  # 9 base + 6 différences de métriques de base
                        nb_echantillons = max(0, (find_len_max - base_columns_with_diffs) // 4)

                        # Ajouter les colonnes pour chaque échantillon
                        for i in range(nb_echantillons):
                            csv_content += 'Activite Ech_' + str(i + 1) + ' (U/mL);RSD Ech_' + str(
                                i + 1) + ' (%);'

                        # Ajouter les colonnes de différence
                        diff_header = 'diff % LOD;diff % LOQ;diff % Sensibilite (en U/mL);'

                        # Ajouter les différences de CV pour 30%, 50%, 70%
                        for deg_percent in deg_percentages:
                            diff_header += f'diff % CV % deg a {deg_percent}%;'

                        csv_content += diff_header

                        for i in range(nb_echantillons):
                            csv_content += 'diff % Activite Ech_' + str(
                                i + 1) + ' (U/mL);diff % RSD Ech_' + str(i + 1) + ' (%);'

                        csv_content += '\n'

                        # Écrire les données
                        for result in all_results:
                            for value in result:
                                csv_content += str(value) + ';'
                            csv_content += '\n'

                        # Essayer d'écrire dans le fichier avec plusieurs tentatives
                        max_attempts = 5
                        attempt = 0
                        success = False

                        while attempt < max_attempts and not success:
                            try:
                                # Essayer d'écrire directement dans le fichier
                                with open(csv_path, 'w') as csv_out:
                                    csv_out.write(csv_content)
                                success = True
                                logger.info(
                                    f"Résultats écrits dans {csv_path} (tentative {attempt + 1})")
                            except PermissionError as e:
                                attempt += 1
                                logger.warning(
                                    f"Tentative {attempt}/{max_attempts} - Erreur de permission lors de l'écriture dans {csv_path}: {str(e)}")
                                if attempt < max_attempts:
                                    # Attendre un peu avant de réessayer
                                    time.sleep(1)
                                else:
                                    # Dernière tentative: essayer avec un fichier temporaire
                                    try:
                                        import tempfile
                                        import shutil

                                        # Créer un fichier temporaire dans le même répertoire
                                        temp_dir = os.path.dirname(csv_path)
                                        fd, temp_path = tempfile.mkstemp(suffix='.csv', dir=temp_dir)

                                        # Écrire dans le fichier temporaire
                                        with os.fdopen(fd, 'w') as temp_file:
                                            temp_file.write(csv_content)

                                        # Essayer de remplacer le fichier original
                                        if os.path.exists(csv_path):
                                            os.remove(csv_path)
                                        shutil.move(temp_path, csv_path)

                                        success = True
                                        logger.info(
                                            f"Résultats écrits dans {csv_path} via fichier temporaire")
                                    except Exception as temp_e:
                                        logger.error(
                                            f"Échec de l'écriture via fichier temporaire: {str(temp_e)}",
                                            exc_info=True)
                                        raise
                            except Exception as e:
                                logger.error(
                                    f"Erreur lors de l'écriture des résultats dans {csv_path}: {str(e)}",
                                    exc_info=True)
                                break

                        if not success:
                            logger.error(
                                f"Impossible d'écrire dans {csv_path} après {max_attempts} tentatives")
                else:
                    logger.error(
                        f"Le fichier WellResults.xlsx n'existe pas dans {os.path.dirname(excel_path)}")

                # Stocker les résultats pour l'affichage
                if all_results and len(all_results) >= 2:
                    # Utiliser les premiers résultats pour l'affichage
                    validation_results["enzymo_comparison"] = {
                        "reference_data": all_results[0],
                        "validation_data": all_results[1],
                        "all_results": all_results
                    }
                else:
                    validation_results[
                        "enzymo_comparison_error"] = "Aucun résultat obtenu pour la comparaison enzymatique"
            else:
                validation_results[
                    "enzymo_comparison_error"] = "Sous-dossiers d'acquisition non trouvés"

        except Exception as e:
            logger.error(f"Erreur lors de la comparaison des données enzymatiques: {str(e)}", exc_info=True)
            validation_results["enzymo_comparison_error"] = str(e)

    def _perform_log_analysis(self, results_folder, analysis_results):
        """
        Perform log file analysis
        """
        self.progress_updated.emit(85, "Analyse des logs d'acquisition...")
        try:
            from zymosoft_assistant.scripts.processAcquisitionLog import getLogFile, analyzeLogFile

            try:
                log_file_path = getLogFile(results_folder)
            except FileNotFoundError:
                try:
                    log_file_path = getLogFile(os.path.dirname(results_folder))
                except FileNotFoundError:
                    default_log_path = os.path.normpath("C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/log/prior")
                    log_file_path = getLogFile(default_log_path)

            # Analyse du fichier de log
            log_analysis = analyzeLogFile(log_file_path)

            # Stocker les résultats d'analyse des logs
            self.log_analysis_results = log_analysis
            analysis_results["log_analysis"] = log_analysis

            logger.info(f"Analyse des logs terminée avec succès: {log_file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des logs: {str(e)}", exc_info=True)
            self.log_analysis_results = None
            analysis_results["log_analysis_error"] = str(e)

    # Display methods
    @pyqtSlot()
    def _display_analysis_results(self):
        """
        Affiche les résultats de l'analyse
        """
        try:
            if not self.analysis_results:
                QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
                self._reset_analysis_button()
                return

            if not self.notebook:
                logger.error("Erreur dans _display_analysis_results: self.notebook est None")
                QMessageBox.critical(self.widget, "Erreur",
                                     "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                self._reset_analysis_button()
                return

            self.notebook.setTabEnabled(2, True)
            self.notebook.setCurrentIndex(2)

            # Display all results with proper error handling
            self._display_acquisition_info()
            self._display_statistics()
            self._display_well_results_comparison()
            self._display_lod_loq_comparison()
            self._display_graphs()
            self._display_log_analysis()

            # Mettre à jour les couleurs des onglets après avoir affiché tous les résultats
            self._update_tab_colors()

            # Réactiver le bouton et mettre à jour la navigation
            self._reset_analysis_button()
            self._update_nav_buttons()

            if self.progress_label:
                self.progress_label.setStyleSheet("")
                self.progress_label.setText("Analyse terminée avec succès.")

            logger.info("Affichage des résultats d'analyse terminé")

        except Exception as e:
            logger.error(f"Erreur dans _display_analysis_results: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur",
                                 f"Une erreur est survenue lors de l'affichage des résultats :\n{str(e)}")
            self._reset_analysis_button()

    def _display_well_results_comparison(self):
        """
        Affiche les résultats de la comparaison WellResults
        """
        try:
            if not self.well_results_table:
                logger.error("Erreur dans _display_well_results_comparison: self.well_results_table est None")
                return

            # Vider le tableau
            self.well_results_table.setRowCount(0)

            # Récupérer les résultats de validation
            validation = self.analysis_results.get("validation", {})

            if "well_results_comparison" in validation:
                well_results_df = validation["well_results_comparison"]

                # Mettre à jour le label d'information
                total_tests = len(well_results_df)
                valid_tests = well_results_df['valid'].sum()
                validation_rate = (valid_tests / total_tests * 100) if total_tests > 0 else 0

                info_text = f"Comparaison WellResults terminée avec succès.\n"
                info_text += f"Total des tests: {total_tests}\n"
                info_text += f"Tests valides: {valid_tests}\n"
                info_text += f"Taux de validation: {validation_rate:.2f}%"

                if self.well_results_info_label:
                    self.well_results_info_label.setText(info_text)
                    self.well_results_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text']};")

                # Remplir le tableau avec les noms de colonnes exacts du fichier getDatasFromWellResults.py
                self.well_results_table.setRowCount(len(well_results_df))

                for row, (_, data) in enumerate(well_results_df.iterrows()):
                    # Activité (nom exact : 'activité')
                    self.well_results_table.setItem(row, 0, QTableWidgetItem(str(data['activité'])))

                    # Area (nom exact : 'area')
                    self.well_results_table.setItem(row, 1, QTableWidgetItem(str(data['area'])))

                    # Acquisition (nom exact : 'acquisition')
                    acquisition_val = self._safe_float_format(data['acquisition'], 4)
                    self.well_results_table.setItem(row, 2, QTableWidgetItem(str(acquisition_val)))

                    # Référence (nom exact : 'reference')
                    reference_val = self._safe_float_format(data['reference'], 4)
                    self.well_results_table.setItem(row, 3, QTableWidgetItem(str(reference_val)))

                    # CV (nom exact : 'CV' - c'est acquisition - reference dans getDatasFromWellResults.py)
                    cv_val = self._safe_float_format(data['CV'], 4)
                    self.well_results_table.setItem(row, 4, QTableWidgetItem(str(cv_val)))

                    # Valide (nom exact : 'valid') - utiliser des caractères ASCII pour éviter les problèmes d'encodage
                    valid_text = "Valide" if data['valid'] else "Non valide"
                    valid_item = QTableWidgetItem(valid_text)
                    if data['valid']:
                        valid_item.setBackground(Qt.green)
                    else:
                        valid_item.setBackground(Qt.red)
                    self.well_results_table.setItem(row, 5, valid_item)

                logger.info("Comparaison WellResults affichée avec succès")

            elif "well_results_error" in validation:
                # Afficher l'erreur
                error_msg = validation["well_results_error"]
                if self.well_results_info_label:
                    self.well_results_info_label.setText(f"Erreur lors de la comparaison WellResults:\n{error_msg}")
                    self.well_results_info_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")

                # Ajouter une ligne d'erreur dans le tableau
                self.well_results_table.setRowCount(1)
                self.well_results_table.setItem(0, 0, QTableWidgetItem("Erreur"))
                self.well_results_table.setItem(0, 5, QTableWidgetItem(error_msg))

                logger.error(f"Erreur lors de la comparaison WellResults: {error_msg}")

            else:
                # Aucune comparaison WellResults disponible
                if self.well_results_info_label:
                    self.well_results_info_label.setText(
                        "Aucune comparaison WellResults disponible. Vérifiez que les dossiers d'acquisition et de référence sont correctement sélectionnés.")
                    self.well_results_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")

                self.well_results_table.setRowCount(0)
                logger.info("Aucune comparaison WellResults disponible")

        except Exception as e:
            logger.error(f"Erreur dans _display_well_results_comparison: {str(e)}", exc_info=True)
            if self.well_results_info_label:
                self.well_results_info_label.setText(
                    f"Erreur lors de l'affichage de la comparaison WellResults: {str(e)}")
                self.well_results_info_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")

    def _display_lod_loq_comparison(self):
        """
        Affiche les résultats de la comparaison LOD/LOQ
        """
        try:
            if not self.lod_loq_table:
                logger.error("Erreur dans _display_lod_loq_comparison: self.lod_loq_table est None")
                return

            if not self.lod_loq_info_label:
                logger.error("Erreur dans _display_lod_loq_comparison: self.lod_loq_info_label est None")
                return

            if not self.analysis_results:
                logger.error("Erreur dans _display_lod_loq_comparison: self.analysis_results est None")
                self.lod_loq_info_label.setText("Aucun résultat d'analyse disponible.")
                return

            # Vider le tableau
            self.lod_loq_table.setRowCount(0)

            # Récupérer les résultats de validation
            validation = self.analysis_results.get("validation", {})

            if "lod_loq_comparison" in validation:
                lod_loq_df = validation["lod_loq_comparison"]

                # Mettre à jour le label d'information
                info_text = f"Comparaison LOD/LOQ terminée avec succès.\n"
                info_text += f"Total des tests: {len(lod_loq_df)}"

                self.lod_loq_info_label.setText(info_text)
                self.lod_loq_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text']};")

                # Vérifier les colonnes disponibles dans le DataFrame
                available_columns = list(lod_loq_df.columns)
                logger.info(f"Colonnes disponibles dans LOD/LOQ DataFrame: {available_columns}")

                # Remplir le tableau
                self.lod_loq_table.setRowCount(len(lod_loq_df))

                for row, (_, data) in enumerate(lod_loq_df.iterrows()):
                    try:
                        # Area (colonne exacte du fichier getDatasFromWellResults.py)
                        area_value = self._safe_float_format(data.get('Area', data.get('area', 'N/A')), 0)
                        self.lod_loq_table.setItem(row, 0, QTableWidgetItem(str(area_value)))

                        # LOD_Ref (nom exact du fichier getDatasFromWellResults.py)
                        lod_ref_value = self._safe_float_format(data.get('LOD_Ref', 'N/A'), 4)
                        self.lod_loq_table.setItem(row, 1, QTableWidgetItem(str(lod_ref_value)))

                        # LOD_Acq (nom exact du fichier getDatasFromWellResults.py)
                        lod_acq_value = self._safe_float_format(data.get('LOD_Acq', 'N/A'), 4)
                        self.lod_loq_table.setItem(row, 2, QTableWidgetItem(str(lod_acq_value)))

                        # LOQ_Ref (nom exact du fichier getDatasFromWellResults.py)
                        loq_ref_value = self._safe_float_format(data.get('LOQ_Ref', 'N/A'), 4)
                        self.lod_loq_table.setItem(row, 3, QTableWidgetItem(str(loq_ref_value)))

                        # LOQ_Acq (nom exact du fichier getDatasFromWellResults.py)
                        loq_acq_value = self._safe_float_format(data.get('LOQ_Acq', 'N/A'), 4)
                        self.lod_loq_table.setItem(row, 4, QTableWidgetItem(str(loq_acq_value)))

                        # Diff_LOD (nom exact du fichier getDatasFromWellResults.py)
                        diff_lod_value = self._safe_float_format(data.get('Diff_LOD', 'N/A'), 4)
                        self.lod_loq_table.setItem(row, 5, QTableWidgetItem(str(diff_lod_value)))

                        # Diff_LOQ (nom exact du fichier getDatasFromWellResults.py)
                        diff_loq_value = self._safe_float_format(data.get('Diff_LOQ', 'N/A'), 4)
                        self.lod_loq_table.setItem(row, 6, QTableWidgetItem(str(diff_loq_value)))

                        # Lod_Valid (nom exact du fichier getDatasFromWellResults.py)
                        lod_valid_value = self._safe_bool_check(data.get('Lod_Valid', data.get('Lod_valid', False)))
                        lod_valid_text = "Valide" if lod_valid_value else "Non valide"
                        lod_valid_item = QTableWidgetItem(lod_valid_text)
                        if lod_valid_value:
                            lod_valid_item.setBackground(Qt.green)
                        else:
                            lod_valid_item.setBackground(Qt.red)
                        self.lod_loq_table.setItem(row, 7, lod_valid_item)

                        # Loq_Valid (nom exact du fichier getDatasFromWellResults.py)
                        loq_valid_value = self._safe_bool_check(data.get('Loq_Valid', data.get('Loq_valid', False)))
                        loq_valid_text = "Valide" if loq_valid_value else "Non valide"
                        loq_valid_item = QTableWidgetItem(loq_valid_text)
                        if loq_valid_value:
                            loq_valid_item.setBackground(Qt.green)
                        else:
                            loq_valid_item.setBackground(Qt.red)
                        self.lod_loq_table.setItem(row, 8, loq_valid_item)

                    except Exception as row_error:
                        logger.error(f"Erreur lors du traitement de la ligne {row}: {str(row_error)}")
                        # Remplir avec des valeurs par défaut en cas d'erreur
                        for col in range(9):
                            if not self.lod_loq_table.item(row, col):
                                self.lod_loq_table.setItem(row, col, QTableWidgetItem("Erreur"))

                logger.info("Comparaison LOD/LOQ affichée avec succès")

            elif "lod_loq_error" in validation:
                # Afficher l'erreur
                error_msg = validation["lod_loq_error"]
                self.lod_loq_info_label.setText(f"Erreur lors de la comparaison LOD/LOQ:\n{error_msg}")
                self.lod_loq_info_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")

                # Ajouter une ligne d'erreur dans le tableau
                self.lod_loq_table.setRowCount(1)
                self.lod_loq_table.setItem(0, 0, QTableWidgetItem("Erreur"))
                self.lod_loq_table.setItem(0, 5, QTableWidgetItem(error_msg))

                logger.error(f"Erreur lors de la comparaison LOD/LOQ: {error_msg}")
            else:
                # Aucune comparaison LOD/LOQ disponible
                self.lod_loq_info_label.setText(
                    "Aucune comparaison LOD/LOQ disponible. Vérifiez que les dossiers d'acquisition et de référence sont correctement sélectionnés.")
                self.lod_loq_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")

                self.lod_loq_table.setRowCount(0)
                logger.info("Aucune comparaison LOD/LOQ disponible")

        except Exception as e:
            logger.error(f"Erreur dans _display_lod_loq_comparison: {str(e)}", exc_info=True)
            if self.lod_loq_info_label:
                self.lod_loq_info_label.setText(
                    f"Erreur lors de l'affichage de la comparaison LOD/LOQ: {str(e)}")
                self.lod_loq_info_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")

    def _display_log_analysis(self):
        """
        Affiche les résultats de l'analyse des logs
        """
        try:
            if not self.log_analysis_table:
                logger.error("Erreur dans _display_log_analysis: self.log_analysis_table est None")
                return

            if not self.log_info_label:
                logger.error("Erreur dans _display_log_analysis: self.log_info_label est None")
                return

            if not self.analysis_results:
                logger.error("Erreur dans _display_log_analysis: self.analysis_results est None")
                self.log_info_label.setText("Aucun résultat d'analyse disponible.")
                return

            # Vérifier si des résultats d'analyse des logs sont disponibles
            if "log_analysis" not in self.analysis_results and "log_analysis_error" not in self.analysis_results:
                self.log_info_label.setText("Aucune analyse de log disponible.")
                return

            # Vérifier s'il y a eu une erreur lors de l'analyse des logs
            if "log_analysis_error" in self.analysis_results:
                error_msg = self.analysis_results["log_analysis_error"]
                self.log_info_label.setText(f"Erreur lors de l'analyse des logs:\n{error_msg}")
                self.log_info_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")
                return

            # Récupérer les résultats d'analyse des logs
            log_analysis = self.analysis_results["log_analysis"]

            # Simplifier le label d'information - juste indiquer que l'analyse est disponible
            self.log_info_label.setText("Analyse des logs d'acquisition terminée avec succès.")
            self.log_info_label.setStyleSheet(f"color: {COLOR_SCHEME['text']};")

            # Remplir le tableau des résultats
            self.log_analysis_table.setRowCount(0)  # Vider le tableau

            # Préparer les données pour le tableau
            table_data = []

            # Récupérer les informations de base
            acquisition_type = log_analysis.get("acquisition_type", "inconnu")
            acquisition_duration = log_analysis.get("acquisition_duration", {})
            duration_minutes = acquisition_duration.get("duration_minutes", 0)

            # Informations communes
            table_data.append(["Type d'acquisition", acquisition_type])
            table_data.append(["Durée d'acquisition (minutes)", f"{duration_minutes:.2f}"])
            table_data.append(["Nombre total de puits", str(log_analysis.get("total_wells", 0))])
            table_data.append(["Nombre de drift fixes", str(log_analysis.get("drift_fix_count", 0))])
            table_data.append(["Nombre de max retry", str(log_analysis.get("max_retry_count", 0))])

            # Informations spécifiques au type d'acquisition
            if acquisition_type == "prior":
                table_data.append(["Nombre moyen de loops", f"{log_analysis.get('average_value', 0):.2f}"])
                table_data.append(["Nombre total de mesures", str(log_analysis.get("total_measurements", 0))])
                table_data.append(["Mesures 'Done'", str(log_analysis.get("done_measurements", 0))])
                table_data.append(["Mesures 'Timeout'", str(log_analysis.get("timeout_measurements", 0))])
            else:  # custom_focus
                table_data.append(["Nombre moyen de moves", f"{log_analysis.get('average_value', 0):.2f}"])
                table_data.append(["Nombre total de mesures", str(log_analysis.get("total_measurements", 0))])

            # Remplir le tableau
            self.log_analysis_table.setRowCount(len(table_data))
            for row, (param, value) in enumerate(table_data):
                self.log_analysis_table.setItem(row, 0, QTableWidgetItem(param))
                self.log_analysis_table.setItem(row, 1, QTableWidgetItem(str(value)))

            logger.info("Affichage des résultats d'analyse des logs terminé")

        except Exception as e:
            logger.error(f"Erreur dans _display_log_analysis: {str(e)}", exc_info=True)
            if self.log_info_label:
                self.log_info_label.setText(f"Erreur lors de l'affichage des résultats d'analyse des logs:\n{str(e)}")
                self.log_info_label.setStyleSheet(f"color: {COLOR_SCHEME['error']};")

    def _display_acquisition_info(self):
        """
        Affiche les informations sur l'acquisition
        """
        try:
            if not self.info_text:
                logger.error("Erreur dans _display_acquisition_info: self.info_text est None")
                return

            self.info_text.clear()
            plate_type_name = next((pt['name'] for pt in PLATE_TYPES if pt['id'] == self.plate_type_var), "Inconnu")
            mode_name = next((m['name'] for m in ACQUISITION_MODES if m['id'] == self.acquisition_mode_var), "Inconnu")

            # Informations de base
            info_text = (
                f"Type de plaque: {plate_type_name}\n"
                f"Mode d'acquisition: {mode_name}\n"
                f"Dossier de résultats: {self.results_folder_var}\n"
            )

            # Ajouter les informations de validation si disponibles
            if self.analysis_results.get('validation'):
                validation = self.analysis_results['validation']

                # Informations de comparaison WellResults
                if 'well_results_comparison' in validation:
                    well_results_df = validation['well_results_comparison']
                    total_tests = len(well_results_df)
                    valid_tests = well_results_df['valid'].sum()
                    validation_rate = (valid_tests / total_tests * 100) if total_tests > 0 else 0
                    info_text += (
                        f"\nComparaison WellResults:\n"
                        f"- Total des tests: {total_tests}\n"
                        f"- Tests valides: {valid_tests}\n"
                        f"- Taux de validation: {validation_rate:.2f}%\n"
                    )
                elif 'well_results_error' in validation:
                    info_text += f"\nErreur comparaison WellResults: {validation['well_results_error']}\n"

                # Informations de comparaison aux références
                if 'comparison' in validation:
                    comp = validation['comparison']
                    info_text += (
                        f"\nComparaison aux références:\n"
                        f"- Pente: {comp.get('slope', 'N/A'):.4f}\n"
                        f"- R²: {comp.get('r_value', 'N/A'):.4f}\n"
                        f"- Points hors tolérance: {comp.get('nb_puits_loin_fit', 'N/A')}\n"
                    )
                elif 'comparison_error' in validation:
                    info_text += f"\nErreur de comparaison: {validation['comparison_error']}\n"

                # Informations de comparaison enzymatique
                if 'enzymo_comparison' in validation:
                    info_text += f"\nComparaison enzymatique: Réussie\n"
                elif 'enzymo_comparison_error' in validation:
                    info_text += f"\nErreur de comparaison enzymatique: {validation['enzymo_comparison_error']}\n"

            # Statut global
            info_text += f"\nStatut: {'Valide' if self.analysis_results.get('valid', False) else 'Non valide'}\n"

            self.info_text.setText(info_text)
            self.info_text.setReadOnly(True)
        except Exception as e:
            logger.error(f"Erreur dans _display_acquisition_info: {str(e)}", exc_info=True)
            if self.info_text:
                self.info_text.setText(f"Erreur lors de l'affichage des infos : {str(e)}")

    def _display_statistics(self):
        """
        Affiche les statistiques de l'analyse
        """
        try:
            if not self.stats_table:
                logger.error("Erreur dans _display_statistics: self.stats_table est None")
                return

            # Rendre la table non éditable
            self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)

            # Ajout d'une colonne pour les critères de référence
            self.stats_table.setColumnCount(3)
            self.stats_table.setHorizontalHeaderLabels(["Paramètre", "Valeur", "Critère de référence"])

            # Ajuster la largeur des colonnes
            header = self.stats_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)

            self.stats_table.setRowCount(0)

            # Statistiques standard
            statistics = self.analysis_results.get("statistics", {})
            if statistics:
                stats_items = [
                    ("Pente", f"{statistics.get('slope', 0):.4f}"),
                    ("Ordonnée à l'origine", f"{statistics.get('intercept', 0):.4f}"),
                    ("R²", f"{statistics.get('r2', 0):.4f}"),
                    ("Valeurs aberrantes", str(statistics.get('outliers_count', 0))),
                    ("% valeurs aberrantes", f"{statistics.get('outliers_percentage', 0):.2f}%")
                ]

                for param, value in stats_items:
                    row = self.stats_table.rowCount()
                    self.stats_table.insertRow(row)
                    self.stats_table.setItem(row, 0, QTableWidgetItem(param))
                    self.stats_table.setItem(row, 1, QTableWidgetItem(value))
                    self.stats_table.setItem(row, 2, QTableWidgetItem(""))

            # Continue with validation statistics...
            validation = self.analysis_results.get("validation", {})
            if validation:
                self._add_validation_statistics(validation)

        except Exception as e:
            logger.error(f"Erreur dans _display_statistics: {str(e)}", exc_info=True)

    def _add_validation_statistics(self, validation):
        """
        Add validation statistics to the stats table
        """
        # Ajouter un séparateur
        row = self.stats_table.rowCount()
        self.stats_table.insertRow(row)
        self.stats_table.setItem(row, 0, QTableWidgetItem("--- Résultats de validation ---"))
        self.stats_table.setItem(row, 1, QTableWidgetItem(""))
        self.stats_table.setItem(row, 2, QTableWidgetItem(""))

        # Statistiques de comparaison aux références
        if 'comparison' in validation:
            comp = validation['comparison']

            # Import des critères de validation
            from zymosoft_assistant.utils.constants import VALIDATION_CRITERIA

            # Création des items avec vérification des critères
            comp_items = [
                ("Pente (validation)", f"{comp.get('slope', 0):.4f}", 'slope'),
                ("Ordonnée à l'origine (validation)", f"{comp.get('intercept', 0):.4f}", 'intercept'),
                ("R² (validation)", f"{comp.get('r_value', 0):.4f}", 'r2'),
                ("Points hors tolérance", str(comp.get('nb_puits_loin_fit', 'N/A')), 'nb_puits_loin_fit'),
                ("Différence relative moyenne", f"{comp.get('diff_mean', 0):.2f}%", None),
                ("CV de la différence relative", f"{comp.get('diff_cv', 0):.2f}%", None)
            ]

            for param, value, criteria_key in comp_items:
                row = self.stats_table.rowCount()
                self.stats_table.insertRow(row)

                # Paramètre
                param_item = QTableWidgetItem(param)
                self.stats_table.setItem(row, 0, param_item)

                # Valeur
                value_item = QTableWidgetItem(value)
                self.stats_table.setItem(row, 1, value_item)

                # Critère de référence et coloration
                if criteria_key and criteria_key in VALIDATION_CRITERIA:
                    criteria = VALIDATION_CRITERIA[criteria_key]
                    criteria_text = f"{criteria['min']} - {criteria['max']}" if criteria_key != 'r2' else f"> {criteria['min']}"
                    criteria_item = QTableWidgetItem(criteria_text)
                    self.stats_table.setItem(row, 2, criteria_item)

                    # Vérification si la valeur respecte les critères
                    try:
                        if criteria_key == 'r2':
                            val = float(comp.get('r_value', 0))
                            is_valid = val >= criteria['min'] and val <= criteria['max']
                        elif criteria_key == 'nb_puits_loin_fit':
                            val = int(comp.get('nb_puits_loin_fit', 0))
                            is_valid = val >= criteria['min'] and val <= criteria['max']
                        elif criteria_key == 'slope':
                            val = float(comp.get('slope', 0))
                            is_valid = val >= criteria['min'] and val <= criteria['max']
                        elif criteria_key == 'intercept':
                            val = float(comp.get('intercept', 0))
                            is_valid = val >= criteria['min'] and val <= criteria['max']
                        else:
                            is_valid = True

                        # Coloration de la cellule
                        if is_valid:
                            value_item.setBackground(Qt.green)
                        else:
                            value_item.setBackground(Qt.red)
                    except (ValueError, TypeError):
                        # En cas d'erreur de conversion, on ne colore pas
                        pass
                else:
                    self.stats_table.setItem(row, 2, QTableWidgetItem(""))

    def _display_graphs(self):
        """
        Affiche les graphiques générés par l'analyse
        """
        try:
            if not self.graphs_widget:
                logger.error("Erreur dans _display_graphs: self.graphs_widget est None")
                return

            self.graphs_widget.clear()
            self.graph_images = []
            self.graph_titles = []

            # Récupérer les chemins des graphiques générés par l'analyse
            graph_paths = self.analysis_results.get("graphs", [])

            # Ajouter les images de validation si elles existent
            validation_dir = ""
            if self.results_folder_var:
                validation_dir = os.path.join(self.results_folder_var, "validation_results")
                if os.path.exists(validation_dir):
                    for file in os.listdir(validation_dir):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            graph_paths.append(os.path.join(validation_dir, file))

                    # Ajouter les images des sous-dossiers de validation
                    for subdir in ["validation_comparison", "comparaison_enzymo_routine"]:
                        subdir_path = os.path.join(validation_dir, subdir)
                        if os.path.exists(subdir_path):
                            for file in os.listdir(subdir_path):
                                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    graph_paths.append(os.path.join(subdir_path, file))

            if not graph_paths:
                self.graphs_widget.setText("Aucune image disponible")
                self.graphs_widget.setStyleSheet(
                    f"color: {COLOR_SCHEME['text_secondary']}; background-color: {COLOR_SCHEME['background']};")
                if self.image_title_label:
                    self.image_title_label.setText("")
                if self.image_counter_label:
                    self.image_counter_label.setText("0/0")
                if self.prev_image_button:
                    self.prev_image_button.setEnabled(False)
                if self.next_image_button:
                    self.next_image_button.setEnabled(False)
                return

            # Charger toutes les images
            for path in graph_paths:
                image = QPixmap(path)
                if not image.isNull():
                    self.graph_images.append(image)
                    # Extraire le nom du fichier comme titre
                    title = os.path.basename(path)
                    title = os.path.splitext(title)[0]
                    title = title.replace('_', ' ')
                    self.graph_titles.append(title)

            # Afficher la première image si disponible
            if self.graph_images:
                self.current_image_index = 0
                self._display_current_image()
                self._update_image_navigation()
            else:
                self.graphs_widget.setText("Impossible de charger les images")
                self.graphs_widget.setStyleSheet(
                    f"color: {COLOR_SCHEME['error']}; background-color: {COLOR_SCHEME['background']};")

        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des graphiques: {str(e)}", exc_info=True)
            if self.graphs_widget:
                self.graphs_widget.setText(f"Erreur lors de l'affichage des graphiques: {str(e)}")
                self.graphs_widget.setStyleSheet(
                    f"color: {COLOR_SCHEME['error']}; background-color: {COLOR_SCHEME['background']};")

    # Image navigation methods
    def _display_current_image(self):
        """
        Affiche l'image courante
        """
        try:
            if 0 <= self.current_image_index < len(self.graph_images) and self.graphs_widget:
                image = self.graph_images[self.current_image_index]
                self.graphs_widget.setPixmap(image.scaled(
                    self.graphs_widget.width(),
                    self.graphs_widget.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

                # Afficher le titre de l'image
                if self.image_title_label and self.current_image_index < len(self.graph_titles):
                    self.image_title_label.setText(self.graph_titles[self.current_image_index])
                elif self.image_title_label:
                    self.image_title_label.setText("")
        except Exception as e:
            logger.error(f"Erreur dans _display_current_image: {str(e)}", exc_info=True)

    def _update_image_navigation(self):
        """
        Met à jour les contrôles de navigation des images
        """
        try:
            total_images = len(self.graph_images)
            if total_images > 0:
                if self.image_counter_label:
                    self.image_counter_label.setText(f"{self.current_image_index + 1}/{total_images}")
                if self.prev_image_button:
                    self.prev_image_button.setEnabled(self.current_image_index > 0)
                if self.next_image_button:
                    self.next_image_button.setEnabled(self.current_image_index < total_images - 1)
            else:
                if self.image_counter_label:
                    self.image_counter_label.setText("0/0")
                if self.prev_image_button:
                    self.prev_image_button.setEnabled(False)
                if self.next_image_button:
                    self.next_image_button.setEnabled(False)
        except Exception as e:
            logger.error(f"Erreur dans _update_image_navigation: {str(e)}", exc_info=True)

    def _show_previous_image(self):
        """
        Affiche l'image précédente
        """
        try:
            if self.current_image_index > 0:
                self.current_image_index -= 1
                self._display_current_image()
                self._update_image_navigation()
        except Exception as e:
            logger.error(f"Erreur dans _show_previous_image: {str(e)}", exc_info=True)

    def _show_next_image(self):
        """
        Affiche l'image suivante
        """
        try:
            if self.current_image_index < len(self.graph_images) - 1:
                self.current_image_index += 1
                self._display_current_image()
                self._update_image_navigation()
        except Exception as e:
            logger.error(f"Erreur dans _show_next_image: {str(e)}", exc_info=True)

    def _on_image_clicked(self, event):
        """
        Gère le clic sur une image pour l'afficher en grand
        """
        try:
            if not self.graph_images or self.current_image_index >= len(self.graph_images):
                return

            # Create a dialog to display the enlarged image
            dialog = QDialog(self.widget)
            dialog.setWindowTitle(self.graph_titles[self.current_image_index] if self.current_image_index < len(
                self.graph_titles) else "Image")
            dialog.setMinimumSize(800, 600)

            layout = QVBoxLayout(dialog)

            # Image label
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(image_label)

            # Navigation buttons for dialog
            nav_layout = QHBoxLayout()

            class ImageIndex:
                def __init__(self, value):
                    self.value = value

            current_dialog_image = ImageIndex(self.current_image_index)

            prev_button = QPushButton("< Précédent")
            prev_button.setEnabled(current_dialog_image.value > 0)
            nav_layout.addWidget(prev_button)

            image_counter = QLabel(f"{current_dialog_image.value + 1}/{len(self.graph_images)}")
            image_counter.setAlignment(Qt.AlignCenter)
            nav_layout.addWidget(image_counter)

            next_button = QPushButton("Suivant >")
            next_button.setEnabled(current_dialog_image.value < len(self.graph_images) - 1)
            nav_layout.addWidget(next_button)

            def update_dialog_image():
                if 0 <= current_dialog_image.value < len(self.graph_images):
                    image = self.graph_images[current_dialog_image.value]
                    image_label.setPixmap(image)
                    dialog.setWindowTitle(
                        self.graph_titles[current_dialog_image.value] if current_dialog_image.value < len(
                            self.graph_titles) else "Image")
                    prev_button.setEnabled(current_dialog_image.value > 0)
                    next_button.setEnabled(current_dialog_image.value < len(self.graph_images) - 1)
                    image_counter.setText(f"{current_dialog_image.value + 1}/{len(self.graph_images)}")

            def show_previous_image():
                if current_dialog_image.value > 0:
                    current_dialog_image.value -= 1
                    update_dialog_image()

            def show_next_image():
                if current_dialog_image.value < len(self.graph_images) - 1:
                    current_dialog_image.value += 1
                    update_dialog_image()

            prev_button.clicked.connect(show_previous_image)
            next_button.clicked.connect(show_next_image)

            update_dialog_image()

            layout.addLayout(nav_layout)

            close_button = QPushButton("Fermer")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.exec_()
        except Exception as e:
            logger.error(f"Erreur dans _on_image_clicked: {str(e)}", exc_info=True)

    # Progress and error handling methods
    @pyqtSlot(int, str)
    def _update_progress(self, value, message):
        """
        Met à jour la barre de progression et le message associé
        """
        try:
            if self.progress_bar:
                self.progress_bar.setValue(value)
            if self.progress_label:
                self.progress_label.setText(message)
            logger.debug(f"Progression: {value}% - {message}")
        except Exception as e:
            logger.error(f"Erreur dans _update_progress: {str(e)}", exc_info=True)

    @pyqtSlot(str)
    def _handle_analysis_error(self, error_message):
        """
        Gère les erreurs d'analyse
        """
        try:
            if self.progress_label:
                self.progress_label.setText(f"Erreur: {error_message}")
                self.progress_label.setStyleSheet(f"color: {COLOR_SCHEME['error']}; font-weight: bold;")
            if self.progress_bar:
                self.progress_bar.setValue(0)
                self.progress_bar.setStyleSheet("")

            self._reset_analysis_button()

            QMessageBox.critical(self.widget, "Erreur d'analyse",
                                 f"Une erreur est survenue lors de l'analyse :\n{error_message}")
            logger.error(f"Erreur d'analyse: {error_message}")
        except Exception as e:
            logger.error(f"Erreur dans _handle_analysis_error: {str(e)}", exc_info=True)

    def _reset_analysis_button(self):
        """
        Réinitialise le bouton d'analyse à son état normal
        """
        try:
            if self.next_substep_button:
                self.next_substep_button.setEnabled(True)
                self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _reset_analysis_button: {str(e)}", exc_info=True)

    # Navigation methods
    def _previous_substep(self):
        """
        Passe à la sous-étape précédente
        """
        try:
            if not self.notebook:
                logger.error("Erreur dans _previous_substep: self.notebook est None")
                QMessageBox.critical(self.widget, "Erreur",
                                     "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                return
            current_tab = self.notebook.currentIndex()
            if current_tab > 0:
                self.notebook.setCurrentIndex(current_tab - 1)
                self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _previous_substep: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _next_substep(self):
        """
        Passe à la sous-étape suivante ou exécute l'action appropriée selon l'onglet actif
        """
        try:
            if not self.notebook:
                logger.error("Erreur dans _next_substep: self.notebook est None")
                QMessageBox.critical(self.widget, "Erreur",
                                     "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                return

            current_tab = self.notebook.currentIndex()

            if current_tab == 0:  # Onglet Configuration
                self._acquisition_done()
            elif current_tab == 1:  # Onglet Sélection des résultats
                # Vérifier si un dossier valide est sélectionné
                if not self.results_folder_var or not os.path.exists(self.results_folder_var):
                    QMessageBox.warning(self.widget, "Attention",
                                        "Veuillez d'abord sélectionner un dossier de résultats valide.")
                    return
                self._analyze_results()
            elif current_tab == 2:  # Onglet Analyse
                # Valider l'acquisition et passer à l'étape suivante
                self._show_comments_dialog("validate_next", True, False)
        except Exception as e:
            logger.error(f"Erreur dans _next_substep: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _acquisition_done(self):
        """
        Appelé lorsque l'utilisateur a terminé l'acquisition
        """
        try:
            if not self.notebook:
                logger.error("Erreur dans _acquisition_done: self.notebook est None")
                QMessageBox.critical(self.widget, "Erreur",
                                     "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                return
            self.notebook.setTabEnabled(1, True)
            self.notebook.setCurrentIndex(1)
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _acquisition_done: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _on_tab_changed(self, index):
        """
        Appelé lorsque l'onglet actif change
        """
        try:
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _on_tab_changed: {str(e)}", exc_info=True)

    def _update_nav_buttons(self):
        """
        Met à jour l'état des boutons de navigation
        """
        try:
            if not self.notebook:
                logger.error("Erreur dans _update_nav_buttons: self.notebook est None")
                return

            current_tab = self.notebook.currentIndex()

            # Gestion du bouton précédent
            if self.prev_substep_button:
                self.prev_substep_button.setEnabled(current_tab > 0)

            # Gestion des boutons d'action supplémentaires
            if current_tab == 2:  # Onglet d'analyse
                if self.validate_continue_button:
                    self.validate_continue_button.setVisible(True)
                if self.invalidate_button:
                    self.invalidate_button.setVisible(True)
                if self.report_button:
                    self.report_button.setVisible(True)
            else:
                if self.validate_continue_button:
                    self.validate_continue_button.setVisible(False)
                if self.invalidate_button:
                    self.invalidate_button.setVisible(False)
                if self.report_button:
                    self.report_button.setVisible(False)

            # Gestion du bouton suivant
            if not self.next_substep_button:
                return

            if current_tab == 0:  # Onglet Configuration
                self.next_substep_button.setText("Acquisition réalisée")
                self.next_substep_button.setEnabled(True)
                self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
            elif current_tab == 1:  # Onglet Sélection des résultats
                self.next_substep_button.setText("Analyser les résultats")

                # Vérifier si un dossier de résultats valide est sélectionné
                results_folder_valid = bool(self.results_folder_var and os.path.exists(self.results_folder_var))

                # Vérifier si un dossier de référence valide est sélectionné (requis si options de comparaison activées)
                reference_folder_required = bool(self.do_compare_to_ref or self.do_compare_enzymo_to_ref)
                reference_folder_valid = bool(self.reference_folder_var and os.path.exists(self.reference_folder_var))

                # Déterminer si l'analyse peut procéder
                can_analyze = bool(results_folder_valid and (not reference_folder_required or reference_folder_valid))

                self.next_substep_button.setEnabled(can_analyze)

                if can_analyze:
                    self.next_substep_button.setStyleSheet(
                        f"background-color: {COLOR_SCHEME['primary']}; color: white;")
                else:
                    self.next_substep_button.setStyleSheet(
                        f"background-color: {COLOR_SCHEME['disabled']}; color: white;")

            elif current_tab == 2:  # Onglet Analyse
                self.next_substep_button.setText("Valider et étape suivante")
                self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
                self.next_substep_button.setEnabled(True)
            else:
                self.next_substep_button.setEnabled(False)
        except Exception as e:
            logger.error(f"Erreur dans _update_nav_buttons: {str(e)}", exc_info=True)

    # Dialog and action methods
    def _show_comments_dialog(self, action_type, validated, continue_acquisitions):
        """
        Affiche une boîte de dialogue pour saisir des commentaires avant de finaliser l'acquisition
        """
        try:
            dialog = QDialog(self.widget)

            if action_type == "validate_continue":
                dialog.setWindowTitle("Valider cette acquisition et recommencer")
            elif action_type == "invalidate":
                dialog.setWindowTitle("Invalider et refaire")
            else:  # validate_next
                dialog.setWindowTitle("Valider et étape suivante")

            dialog.setMinimumWidth(500)

            layout = QVBoxLayout(dialog)

            # Message explicatif
            message = ""
            if action_type == "validate_continue":
                message = "Vous allez valider cette acquisition et recommencer une nouvelle acquisition."
            elif action_type == "invalidate":
                message = "Vous allez invalider cette acquisition et recommencer."
            else:  # validate_next
                message = "Vous allez valider cette acquisition et passer à l'étape suivante."

            message_label = QLabel(message)
            message_label.setWordWrap(True)
            layout.addWidget(message_label)

            # Champ de commentaires
            comments_label = QLabel("Commentaires (optionnel):")
            layout.addWidget(comments_label)

            comments_text = QTextEdit()
            comments_text.setPlainText(self.comments_var)  # Pré-remplir avec les commentaires existants
            layout.addWidget(comments_text)

            # Boutons
            buttons_layout = QHBoxLayout()
            cancel_button = QPushButton("Annuler")
            cancel_button.clicked.connect(dialog.reject)
            buttons_layout.addWidget(cancel_button)

            confirm_button = QPushButton("Confirmer")
            confirm_button.clicked.connect(dialog.accept)
            confirm_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
            buttons_layout.addWidget(confirm_button)

            layout.addLayout(buttons_layout)

            # Afficher la boîte de dialogue
            result = dialog.exec_()

            if result == QDialog.Accepted:
                # Récupérer les commentaires
                self.comments_var = comments_text.toPlainText().strip()
                # Finaliser l'acquisition
                self._finalize_acquisition(validated, continue_acquisitions)
                return True

            return False

        except Exception as e:
            logger.error(f"Erreur dans _show_comments_dialog: {str(e)}", exc_info=True)
            return False

    def _finalize_acquisition(self, validated, continue_acquisitions):
        """
        Finalise l'acquisition actuelle
        """
        try:
            if not self.analysis_results:
                QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
                return

            comments = self.comments_var if hasattr(self, 'comments_var') else ""

            self.current_acquisition_id += 1
            acquisition = {
                "id": self.current_acquisition_id,
                "plate_type": self.plate_type_var,
                "mode": self.acquisition_mode_var,
                "results_folder": self.results_folder_var,
                "analysis": self.analysis_results,
                "comments": comments,
                "validated": validated,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.acquisitions.append(acquisition)
            self._update_history()
            self.save_data()

            if validated:
                self._generate_acquisition_report()

            if continue_acquisitions:
                self._reset_acquisition()
                if not self.notebook:
                    logger.error("Erreur dans _finalize_acquisition: self.notebook est None")
                    QMessageBox.critical(self.widget, "Erreur",
                                         "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                    return
                self.notebook.setCurrentIndex(0)
                self.notebook.setTabEnabled(1, False)
                self.notebook.setTabEnabled(2, False)
                self._update_nav_buttons()
            else:
                self.main_window.next_step()
        except Exception as e:
            logger.error(f"Erreur dans _finalize_acquisition: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors de la finalisation :\n{str(e)}")

    def _reset_acquisition(self):
        """
        Réinitialise les champs pour une nouvelle acquisition
        """
        try:
            # Réinitialiser le dossier de résultats
            self.results_folder_var = ""
            if self.folder_entry:
                self.folder_entry.setText("")
            if self.folder_info_label:
                self.folder_info_label.setText("")

            # Réinitialiser le dossier de référence
            self.reference_folder_var = ""
            if self.ref_folder_entry:
                self.ref_folder_entry.setText("")
            if self.ref_folder_info_label:
                self.ref_folder_info_label.setText("")

            # Réinitialiser les autres champs
            self.comments_var = ""
            self.analysis_results = None
            self.well_results_comparison = None
            if self.graphs_widget:
                self.graphs_widget.clear()
            self.graph_images = []
            if self.stats_table:
                self.stats_table.setRowCount(0)
            if self.info_text:
                self.info_text.clear()
            if self.well_results_table:
                self.well_results_table.setRowCount(0)
            if self.well_results_info_label:
                self.well_results_info_label.setText("")
            if self.lod_loq_table:
                self.lod_loq_table.setRowCount(0)
            if self.lod_loq_info_label:
                self.lod_loq_info_label.setText("")
            if self.progress_bar:
                self.progress_bar.setValue(0)
            if self.progress_label:
                self.progress_label.setText("")
        except Exception as e:
            logger.error(f"Erreur dans _reset_acquisition: {str(e)}", exc_info=True)

    def _update_history(self):
        """
        Met à jour l'historique des acquisitions
        """
        try:
            if not self.history_tree:
                logger.error("Erreur dans _update_history: self.history_tree est None")
                return

            self.history_tree.clear()
            for acquisition in self.acquisitions:
                plate_type_name = next((pt['name'] for pt in PLATE_TYPES if pt['id'] == acquisition['plate_type']),
                                       "Inconnu")
                mode_name = next((m['name'] for m in ACQUISITION_MODES if m['id'] == acquisition['mode']), "Inconnu")
                # Utiliser des caractères ASCII pour éviter les problèmes d'encodage
                status = "Validee" if acquisition['validated'] else "Invalidee"
                timestamp = acquisition.get('timestamp', 'N/A')

                item = QTreeWidgetItem([
                    str(acquisition['id']),
                    plate_type_name,
                    mode_name,
                    status,
                    timestamp
                ])

                # Coloration selon le statut
                if acquisition['validated']:
                    item.setForeground(3, Qt.green)
                else:
                    item.setForeground(3, Qt.red)

                self.history_tree.addTopLevelItem(item)

            # Ajuster la taille des colonnes
            for i in range(self.history_tree.columnCount()):
                self.history_tree.resizeColumnToContents(i)

            logger.info(f"Historique mis à jour avec {len(self.acquisitions)} acquisitions")
        except Exception as e:
            logger.error(f"Erreur dans _update_history: {str(e)}", exc_info=True)

    def _generate_acquisition_report(self):
        """
        Génère un rapport PDF pour l'acquisition actuelle
        """
        try:
            if not self.analysis_results:
                QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
                return

            report_generator = ReportGenerator()
            analysis_results = dict(self.analysis_results)

            # Ajouter les commentaires
            comments = self.comments_var if hasattr(self, 'comments_var') else ""
            analysis_results["comments"] = comments

            report_path = report_generator.generate_acquisition_report(analysis_results)
            QMessageBox.information(self.widget, "Rapport",
                                    f"Le rapport d'acquisition a été généré avec succès:\n{report_path}")

            try:
                os.startfile(report_path)
            except Exception as e:
                logger.warning(f"Impossible d'ouvrir le rapport automatiquement: {str(e)}")

            logger.info(f"Rapport d'acquisition généré: {report_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur",
                                 f"Une erreur est survenue lors de la génération du rapport:\n{str(e)}")

    # Data management methods
    def validate(self):
        """
        Valide les données de l'étape 3
        """
        try:
            if not self.acquisitions:
                QMessageBox.critical(self.widget, "Validation",
                                     "Veuillez réaliser au moins une acquisition validée avant de continuer.")
                return False

            valid_acquisitions = [acq for acq in self.acquisitions if acq['validated']]
            if not valid_acquisitions:
                QMessageBox.critical(self.widget, "Validation",
                                     "Veuillez valider au moins une acquisition avant de continuer.")
                return False

            return True
        except Exception as e:
            logger.error(f"Erreur dans validate: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors de la validation :\n{str(e)}")
            return False

    def save_data(self):
        """
        Sauvegarde les données de l'étape 3 dans la session
        """
        try:
            self.main_window.session_data["acquisitions"] = self.acquisitions

            # Sauvegarder les configurations de validation
            validation_config = {
                "reference_folder": self.reference_folder_var,
                "do_compare_to_ref": self.do_compare_to_ref,
                "do_compare_enzymo_to_ref": self.do_compare_enzymo_to_ref
            }
            self.main_window.session_data["validation_config"] = validation_config

            logger.info("Données de l'étape 3 sauvegardées")
        except Exception as e:
            logger.error(f"Erreur dans save_data: {str(e)}", exc_info=True)

    def load_data(self):
        """
        Charge les données de la session dans l'étape 3
        """
        try:
            # Charger les acquisitions
            acquisitions = self.main_window.session_data.get("acquisitions", [])
            if acquisitions:
                self.acquisitions = acquisitions
                if self.acquisitions:
                    self.current_acquisition_id = max(acq['id'] for acq in self.acquisitions)
                self._update_history()

            # Charger les configurations de validation
            validation_config = self.main_window.session_data.get("validation_config", {})
            if validation_config:
                self.reference_folder_var = validation_config.get("reference_folder", "")
                self.do_compare_to_ref = validation_config.get("do_compare_to_ref", False)
                self.do_compare_enzymo_to_ref = validation_config.get("do_compare_enzymo_to_ref", True)

                # Mettre à jour l'interface si elle est déjà créée
                if self.ref_folder_entry:
                    self.ref_folder_entry.setText(self.reference_folder_var)
                if self.compare_to_ref_checkbox:
                    self.compare_to_ref_checkbox.setChecked(self.do_compare_to_ref)
                if self.compare_enzymo_to_ref_checkbox:
                    self.compare_enzymo_to_ref_checkbox.setChecked(self.do_compare_enzymo_to_ref)

            logger.info("Données de l'étape 3 chargées")
        except Exception as e:
            logger.error(f"Erreur dans load_data: {str(e)}", exc_info=True)

    def reset(self):
        """
        Réinitialise l'étape 3
        """
        try:
            self.plate_type_var = PLATE_TYPES[0]['id'] if PLATE_TYPES else ""
            self.acquisition_mode_var = ACQUISITION_MODES[0]['id'] if ACQUISITION_MODES else ""
            self.results_folder_var = ""
            self.reference_folder_var = ""
            self.comments_var = ""

            # Réinitialiser les options de validation
            self.do_repeta_sans_ref = False
            self.do_compare_to_ref = False
            self.do_compare_enzymo_to_ref = True

            # Mettre à jour l'interface si elle est déjà créée
            if self.ref_folder_entry:
                self.ref_folder_entry.setText("")
            if self.compare_to_ref_checkbox:
                self.compare_to_ref_checkbox.setChecked(self.do_compare_to_ref)
            if self.compare_enzymo_to_ref_checkbox:
                self.compare_enzymo_to_ref_checkbox.setChecked(self.do_compare_enzymo_to_ref)

            self._reset_acquisition()
            self.acquisitions = []
            self.current_acquisition_id = 0
            self.well_results_comparison = None
            self.lod_loq_comparison = None
            self._update_history()

            if self.notebook:
                self.notebook.setTabEnabled(1, False)
                self.notebook.setTabEnabled(2, False)
                self.notebook.setCurrentIndex(0)
                self._update_nav_buttons()

            logger.info("Étape 3 réinitialisée")
        except Exception as e:
            logger.error(f"Erreur dans reset: {str(e)}", exc_info=True)

    def on_show(self):
        """
        Appelé lorsque l'étape est affichée
        """
        try:
            logger.debug("Affichage de l'étape 3 (Step3Acquisition)")

            # Vérifier si self.notebook est None et le réinitialiser si nécessaire
            if not self.notebook:
                logger.warning("self.notebook est None lors de l'affichage de l'étape 3, réinitialisation du notebook")
                self._reinitialize_notebook()

            # Mettre à jour l'historique au cas où des données auraient été chargées
            self._update_history()

            # Mettre à jour les couleurs des onglets si des résultats d'analyse sont disponibles
            if hasattr(self, 'analysis_results') and self.analysis_results:
                self._update_tab_colors()

            # Mettre à jour les boutons de navigation
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans on_show: {str(e)}", exc_info=True)

    def _reinitialize_notebook(self):
        """
        Réinitialise uniquement le notebook sans recréer tous les widgets
        Cette méthode est appelée uniquement si self.notebook est None
        """
        try:
            logger.debug("Réinitialisation du notebook")

            # Find the main_layout (first child of self.layout)
            main_layout = None
            for i in range(self.layout.count()):
                item = self.layout.itemAt(i)
                if item and item.layout():
                    main_layout = item.layout()
                    break

            if not main_layout:
                logger.error("Impossible de trouver le main_layout")
                return

            # Find the splitter in main_layout
            main_splitter = None
            for i in range(main_layout.count()):
                item = main_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QSplitter):
                    main_splitter = item.widget()
                    break

            if not main_splitter:
                logger.error("Impossible de trouver le main_splitter")
                return

            # Check if a QTabWidget already exists in the main_splitter
            notebook_exists = False
            notebook_widget = None
            for i in range(main_splitter.count()):
                widget = main_splitter.widget(i)
                if isinstance(widget, QTabWidget):
                    notebook_exists = True
                    notebook_widget = widget
                    break

            if notebook_exists and notebook_widget:
                # Use existing notebook
                logger.info("Notebook existant trouvé, réutilisation")
                self.notebook = notebook_widget
                self._reinitialize_widget_references()
            else:
                # Create new notebook
                logger.info("Création d'un nouveau notebook")
                self.notebook = QTabWidget()
                main_splitter.insertWidget(0, self.notebook)
                self._create_all_tabs()

            # Update navigation buttons state
            self._update_nav_buttons()

            logger.info("Notebook réinitialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur dans _reinitialize_notebook: {str(e)}", exc_info=True)

    def _reinitialize_widget_references(self):
        """
        Réinitialise les références aux widgets dans les onglets existants
        """
        try:
            # Réinitialiser les index d'onglets
            self.well_results_tab_index = -1
            self.lod_loq_tab_index = -1
            self.log_analysis_tab_index = -1

            # Get widget references from the selection tab
            selection_frame = self.notebook.widget(1)
            if selection_frame:
                # Find folder entry widget
                for widget in selection_frame.findChildren(QLineEdit):
                    if hasattr(widget, 'textChanged'):
                        self.folder_entry = widget
                        break

                # Find info labels
                for widget in selection_frame.findChildren(QLabel):
                    if widget.wordWrap() and "dossier" in widget.text().lower():
                        if not self.folder_info_label:
                            self.folder_info_label = widget
                        elif not self.ref_folder_info_label:
                            self.ref_folder_info_label = widget

                # Find progress widgets
                for widget in selection_frame.findChildren(QProgressBar):
                    self.progress_bar = widget
                    break

                for widget in selection_frame.findChildren(QLabel):
                    if widget.alignment() == Qt.AlignLeft and not widget.wordWrap():
                        self.progress_label = widget
                        break

            # Get widget references from the analysis tab
            analysis_frame = self.notebook.widget(2)
            if analysis_frame:
                # Find the info_stats_tabs (QTabWidget)
                for widget in analysis_frame.findChildren(QTabWidget):
                    self.info_stats_tabs = widget

                    # Retrouver les index des onglets par leur titre
                    for i in range(widget.count()):
                        tab_text = widget.tabText(i)
                        if "WellResults" in tab_text:
                            self.well_results_tab_index = i
                        elif "LOD/LOQ" in tab_text:
                            self.lod_loq_tab_index = i
                        elif "logs" in tab_text:
                            self.log_analysis_tab_index = i
                    break

                for widget in analysis_frame.findChildren(QTextEdit):
                    if widget.isReadOnly():
                        self.info_text = widget
                        break

                # Find tables
                for widget in analysis_frame.findChildren(QTableWidget):
                    if widget.columnCount() == 2 and "Paramètre" in [widget.horizontalHeaderItem(i).text() for i in
                                                                     range(widget.columnCount()) if
                                                                     widget.horizontalHeaderItem(i)]:
                        # Distinguer entre stats_table et log_analysis_table
                        parent_widget = widget.parent()
                        while parent_widget:
                            if isinstance(parent_widget, QGroupBox) or isinstance(parent_widget, QFrame):
                                break
                            parent_widget = parent_widget.parent()

                        # Si le parent contient "log" dans son contexte, c'est le log_analysis_table
                        is_log_table = False
                        if parent_widget:
                            for child in parent_widget.findChildren(QLabel):
                                if "log" in child.text().lower():
                                    is_log_table = True
                                    break

                        if is_log_table:
                            self.log_analysis_table = widget
                        else:
                            self.stats_table = widget
                    elif widget.columnCount() == 6:
                        self.well_results_table = widget
                    elif widget.columnCount() == 9:
                        self.lod_loq_table = widget

                # Find image display widget - chercher par d'autres critères car minimumHeight a changé
                for widget in analysis_frame.findChildren(QLabel):
                    if (widget.alignment() == Qt.AlignCenter and
                            hasattr(widget, 'mousePressEvent') and
                            f"background-color: {COLOR_SCHEME['background']}" in widget.styleSheet()):
                        self.graphs_widget = widget
                        break

                # Find info labels in the analysis tab
                for widget in analysis_frame.findChildren(QLabel):
                    if widget.wordWrap():
                        widget_text = widget.text().lower()
                        if "wellresults" in widget_text and not self.well_results_info_label:
                            self.well_results_info_label = widget
                        elif "lod" in widget_text and "loq" in widget_text and not self.lod_loq_info_label:
                            self.lod_loq_info_label = widget
                        elif "log" in widget_text and not self.log_info_label:
                            self.log_info_label = widget

            # Find history tree widget
            main_layout = None
            for i in range(self.layout.count()):
                item = self.layout.itemAt(i)
                if item and item.layout():
                    main_layout = item.layout()
                    break

            if main_layout:
                # Find splitter in main_layout
                main_splitter = None
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), QSplitter):
                        main_splitter = item.widget()
                        break

                if main_splitter:
                    # Find QGroupBox in splitter
                    for i in range(main_splitter.count()):
                        widget = main_splitter.widget(i)
                        if isinstance(widget, QGroupBox) and widget.title() == "Historique des acquisitions":
                            history_frame = widget
                            for child in history_frame.findChildren(QTreeWidget):
                                self.history_tree = child
                                logger.info("Référence à l'historique des acquisitions réinitialisée")
                                break
                            break

            # Reconnect signals if widgets are found
            if self.folder_entry:
                self.folder_entry.textChanged.connect(self._on_folder_entry_changed)

            if self.notebook:
                self.notebook.currentChanged.connect(self._on_tab_changed)

        except Exception as e:
            logger.error(f"Erreur dans _reinitialize_widget_references: {str(e)}", exc_info=True)

    # Additional utility methods for robust data handling
    def _safe_float_format(self, value, decimals=4):
        """
        Safely format a value as a float string with error handling
        """
        try:
            if pd.notna(value):
                return f"{float(value):.{decimals}f}"
            else:
                return "N/A"
        except (ValueError, TypeError):
            return str(value) if value is not None else "N/A"

    def _safe_bool_check(self, value):
        """
        Safely check if a value represents a boolean True
        """
        try:
            if pd.notna(value):
                return bool(value)
            else:
                return False
        except (ValueError, TypeError):
            return False

    def _find_column_by_names(self, data, possible_names):
        """
        Find a column in data by checking multiple possible column names
        """
        for name in possible_names:
            if name in data.index:
                return name
        return None

