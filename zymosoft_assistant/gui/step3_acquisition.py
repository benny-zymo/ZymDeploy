#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 3 de l'assistant d'installation ZymoSoft : Validation par acquisitions
"""

import os
import logging
import threading
import time
import sys
from PIL import Image, ImageQt
import uuid
import pandas
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
from zymosoft_assistant.scripts.Routine_VALIDATION_ZC_18022025 import compare_enzymo_2_ref, comparaison_ZC_to_ref_v1, comparaison_ZC_to_ref_v1_nanofilm
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
        self.do_compare_to_ref = False   # =1 si mode expert, =0 si mode client
        self.do_compare_enzymo_to_ref = True  # Toujours activé

        # Initialisation des valeurs par défaut
        self.plate_type_var = PLATE_TYPES[0]['id'] if PLATE_TYPES else ""
        self.acquisition_mode_var = ACQUISITION_MODES[0]['id'] if ACQUISITION_MODES else ""
        self.results_folder_var = ""
        self.reference_folder_var = ""

        super().__init__(parent, main_window)

        # Variables pour les résultats d'analyse
        self.analysis_results = None
        self.current_acquisition_id = 0
        self.acquisitions = []

        # Objets pour l'analyse
        self.analyzer = None

        # Images pour les graphiques
        self.graph_images = []

        # Connect signals to slots
        self.progress_updated.connect(self._update_progress)
        self.analysis_completed.connect(self._display_analysis_results)
        self.analysis_error.connect(self._handle_analysis_error)

        # Références aux widgets
        self.notebook = None
        self.folder_info_var = ""
        self.progress_bar = None
        self.progress_label = None
        self.info_text = None
        self.stats_table = None
        self.comments_text = None
        self.graphs_widget = None
        self.history_tree = None

        logger.info("Étape 3 initialisée")

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
        # Supprimer la hauteur maximale pour permettre le redimensionnement
        # self.history_tree.setMaximumHeight(120)
        history_layout.addWidget(self.history_tree)

        # Barre de navigation spécifique à l'étape 3
        self.nav_frame = QFrame()
        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        # Ajouter la barre de navigation après le splitter
        main_layout.addWidget(self.nav_frame)

        self.prev_substep_button = QPushButton("Étape précédente")
        self.prev_substep_button.clicked.connect(self._previous_substep)
        nav_layout.addWidget(self.prev_substep_button, 0, Qt.AlignLeft)

        # Boutons d'action supplémentaires pour l'onglet d'analyse
        self.validate_continue_button = QPushButton("Valider cette acquisition et recommencer")
        self.validate_continue_button.clicked.connect(lambda: self._finalize_acquisition(True, True))
        self.validate_continue_button.setVisible(False)
        nav_layout.addWidget(self.validate_continue_button)

        self.invalidate_button = QPushButton("Invalider et refaire")
        self.invalidate_button.clicked.connect(lambda: self._finalize_acquisition(False, True))
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

        # Désactiver les onglets 2 et 3 au départ
        self.notebook.setTabEnabled(1, False)
        self.notebook.setTabEnabled(2, False)

        # Mise à jour de l'état des boutons de navigation
        self._update_nav_buttons()

        # Liaison des événements
        self.notebook.currentChanged.connect(self._on_tab_changed)

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

            # Description
            if 'description' in plate_type and plate_type['description']:
                desc_label = QLabel(plate_type['description'])
                desc_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
                desc_label.setWordWrap(True)
                desc_label.setContentsMargins(40, 0, 0, 5)
                # plate_type_layout.addWidget(desc_label)

        # Ajouter le cadre de type de plaque au splitter
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

            # Description
            if 'description' in mode and mode['description']:
                desc_label = QLabel(mode['description'])
                desc_label.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
                desc_label.setWordWrap(True)
                desc_label.setContentsMargins(40, 0, 0, 5)
                #mode_layout.addWidget(desc_label)

        # Ajouter le cadre de mode d'acquisition au splitter
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

        # Ajouter le cadre d'instructions au splitter
        config_splitter.addWidget(instructions_frame)

        # Définir les tailles initiales des sections
        config_splitter.setSizes([200, 200, 100])

        # Note: Suppression du bouton "Acquisition réalisée" dupliqué
        # La fonctionnalité est gérée par le bouton de navigation en bas

    def _on_plate_type_changed(self, checked):
        """
        Appelé lorsque le type de plaque est modifié

        Args:
            checked: True si le bouton est coché, False sinon
        """
        if checked:
            sender = self.widget.sender()
            if sender:
                self.plate_type_var = sender.property("plate_type_id")
                logger.info(f"Type de plaque sélectionné: {self.plate_type_var}")

    def _on_acquisition_mode_changed(self, checked):
        """
        Appelé lorsque le mode d'acquisition est modifié

        Args:
            checked: True si le bouton est coché, False sinon
        """
        if checked:
            sender = self.widget.sender()
            if sender:
                self.acquisition_mode_var = sender.property("acquisition_mode_id")
                logger.info(f"Mode d'acquisition sélectionné: {self.acquisition_mode_var}")

    def _on_folder_entry_changed(self, text):
        """
        Appelé lorsque le texte du champ de dossier est modifié

        Args:
            text: Le nouveau texte du champ
        """
        try:
            self.results_folder_var = text
            if text:
                self._check_results_folder(text)
            else:
                self.folder_info_label.setText("")
            # Mise à jour des boutons de navigation
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _on_folder_entry_changed: {str(e)}", exc_info=True)
            self.folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")

    def _on_ref_folder_entry_changed(self, text):
        """
        Appelé lorsque le texte du champ de dossier de référence est modifié

        Args:
            text: Le nouveau texte du champ
        """
        try:
            self.reference_folder_var = text
            if text:
                self._check_reference_folder(text)
            else:
                self.ref_folder_info_label.setText("")
            # Mise à jour des boutons de navigation
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _on_ref_folder_entry_changed: {str(e)}", exc_info=True)
            self.ref_folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")

    def _on_compare_to_ref_toggled(self, checked):
        """
        Appelé lorsque la case à cocher pour comparer aux références est modifiée

        Args:
            checked: True si la case est cochée, False sinon
        """
        try:
            self.do_compare_to_ref = checked
            logger.info(f"Option de comparaison aux références: {checked}")
        except Exception as e:
            logger.error(f"Erreur dans _on_compare_to_ref_toggled: {str(e)}", exc_info=True)

    def _on_compare_enzymo_to_ref_toggled(self, checked):
        """
        Appelé lorsque la case à cocher pour comparer les données enzymatiques est modifiée

        Args:
            checked: True si la case est cochée, False sinon
        """
        try:
            self.do_compare_enzymo_to_ref = checked
            logger.info(f"Option de comparaison des données enzymatiques: {checked}")
        except Exception as e:
            logger.error(f"Erreur dans _on_compare_enzymo_to_ref_toggled: {str(e)}", exc_info=True)

    def _create_selection_widgets(self):
        """
        Crée les widgets pour la sélection des résultats
        """
        # Description
        description_label = QLabel("Sélectionnez les dossiers contenant les résultats de l'acquisition et de référence.")
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

        # Note: Suppression du bouton "Analyser les résultats" dupliqué
        # La fonctionnalité est gérée par le bouton de navigation en bas

    def _create_analysis_widgets(self):
        """
        Crée les widgets pour l'analyse des résultats
        """
        # Description
        description_label = QLabel("Résultats de l'analyse de l'acquisition.")
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(600)
        self.analysis_layout.addWidget(description_label)
        self.analysis_layout.addSpacing(20)

        # Conteneur principal avec splitter pour permettre le redimensionnement
        from PyQt5.QtWidgets import QTabWidget
        main_splitter = QSplitter(Qt.Horizontal)
        self.analysis_layout.addWidget(main_splitter)

        # Panneau gauche: Statistiques et informations
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 0, 10, 0)

        # Utiliser des onglets pour les informations et statistiques
        info_stats_tabs = QTabWidget()
        left_layout.addWidget(info_stats_tabs)

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

        # Commentaires (reste en dehors des onglets comme demandé)
        comments_frame = QGroupBox("Commentaires")
        comments_layout = QVBoxLayout(comments_frame)
        left_layout.addWidget(comments_frame)

        self.comments_text = QTextEdit()
        self.comments_text.setMaximumHeight(100)
        self.comments_text.textChanged.connect(self._on_comments_changed)
        comments_layout.addWidget(self.comments_text)

        # Ajouter le panneau gauche au splitter
        main_splitter.addWidget(left_panel)

        # Panneau droit: Images
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 20, 0)

        # Images
        images_frame = QGroupBox("Images")
        images_layout = QVBoxLayout(images_frame)
        right_layout.addWidget(images_frame)

        # Container pour l'image et les contrôles
        image_container = QWidget()
        image_container_layout = QVBoxLayout(image_container)
        images_layout.addWidget(image_container)

        # Widget pour afficher l'image
        self.graphs_widget = QLabel()
        self.graphs_widget.setStyleSheet(f"background-color: {COLOR_SCHEME['background']};")
        self.graphs_widget.setAlignment(Qt.AlignCenter)
        self.graphs_widget.setMinimumHeight(300)  # Hauteur minimale pour rendre plus carré
        self.graphs_widget.mousePressEvent = self._on_image_clicked
        image_container_layout.addWidget(self.graphs_widget)

        # Titre de l'image
        self.image_title_label = QLabel()
        self.image_title_label.setAlignment(Qt.AlignCenter)
        self.image_title_label.setStyleSheet(f"color: {COLOR_SCHEME['text']}; font-weight: bold;")
        image_container_layout.addWidget(self.image_title_label)

        # Boutons de navigation
        nav_buttons_container = QWidget()
        nav_buttons_layout = QHBoxLayout(nav_buttons_container)
        nav_buttons_layout.setContentsMargins(0, 10, 0, 0)
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

        # Ajouter le panneau droit au splitter
        main_splitter.addWidget(right_panel)

        # Définir les tailles initiales des panneaux (1:2)
        main_splitter.setSizes([100, 200])

        # Initialiser les variables pour la navigation des images
        self.current_image_index = 0
        self.graph_images = []
        self.graph_titles = []

    def _on_comments_changed(self):
        """
        Appelé lorsque le texte des commentaires est modifié
        """
        try:
            if self.comments_text:
                self.comments_var = self.comments_text.toPlainText().strip()
        except Exception as e:
            logger.error(f"Erreur dans _on_comments_changed: {str(e)}", exc_info=True)

    def _display_current_image(self):
        """
        Affiche l'image courante
        """
        try:
            if 0 <= self.current_image_index < len(self.graph_images):
                image = self.graph_images[self.current_image_index]
                self.graphs_widget.setPixmap(image.scaled(
                    self.graphs_widget.width(),
                    self.graphs_widget.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

                # Afficher le titre de l'image
                if self.current_image_index < len(self.graph_titles):
                    self.image_title_label.setText(self.graph_titles[self.current_image_index])
                else:
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
                self.image_counter_label.setText(f"{self.current_image_index + 1}/{total_images}")
                self.prev_image_button.setEnabled(self.current_image_index > 0)
                self.next_image_button.setEnabled(self.current_image_index < total_images - 1)
            else:
                self.image_counter_label.setText("0/0")
                self.prev_image_button.setEnabled(False)
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

            # Créer une boîte de dialogue pour afficher l'image en grand
            dialog = QDialog(self.widget)
            dialog.setWindowTitle(self.graph_titles[self.current_image_index] if self.current_image_index < len(self.graph_titles) else "Image")
            dialog.setMinimumSize(800, 600)

            # Layout pour la boîte de dialogue
            layout = QVBoxLayout(dialog)

            # Label pour afficher l'image
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(image_label)

            # Classe pour stocker l'index de l'image actuellement affichée dans le dialogue
            class ImageIndex:
                def __init__(self, value):
                    self.value = value

            current_dialog_image = ImageIndex(self.current_image_index)

            # Boutons de navigation
            nav_layout = QHBoxLayout()

            # Bouton précédent
            prev_button = QPushButton("< Précédent")
            prev_button.setEnabled(current_dialog_image.value > 0)
            nav_layout.addWidget(prev_button)

            # Compteur d'images
            image_counter = QLabel(f"{current_dialog_image.value + 1}/{len(self.graph_images)}")
            image_counter.setAlignment(Qt.AlignCenter)
            nav_layout.addWidget(image_counter)

            # Bouton suivant
            next_button = QPushButton("Suivant >")
            next_button.setEnabled(current_dialog_image.value < len(self.graph_images) - 1)
            nav_layout.addWidget(next_button)

            # Fonction pour mettre à jour l'image affichée dans le dialogue
            def update_dialog_image():
                if 0 <= current_dialog_image.value < len(self.graph_images):
                    image = self.graph_images[current_dialog_image.value]
                    image_label.setPixmap(image)
                    dialog.setWindowTitle(self.graph_titles[current_dialog_image.value] if current_dialog_image.value < len(self.graph_titles) else "Image")
                    prev_button.setEnabled(current_dialog_image.value > 0)
                    next_button.setEnabled(current_dialog_image.value < len(self.graph_images) - 1)
                    image_counter.setText(f"{current_dialog_image.value + 1}/{len(self.graph_images)}")

            # Fonction pour passer à l'image précédente
            def show_previous_image():
                if current_dialog_image.value > 0:
                    current_dialog_image.value -= 1
                    update_dialog_image()

            # Fonction pour passer à l'image suivante
            def show_next_image():
                if current_dialog_image.value < len(self.graph_images) - 1:
                    current_dialog_image.value += 1
                    update_dialog_image()

            # Connect button signals
            prev_button.clicked.connect(show_previous_image)
            next_button.clicked.connect(show_next_image)

            # Afficher l'image initiale
            update_dialog_image()

            layout.addLayout(nav_layout)

            # Bouton pour fermer la boîte de dialogue
            close_button = QPushButton("Fermer")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            # Afficher la boîte de dialogue
            dialog.exec_()
        except Exception as e:
            logger.error(f"Erreur dans _on_image_clicked: {str(e)}", exc_info=True)

    def _acquisition_done(self):
        """
        Appelé lorsque l'utilisateur a terminé l'acquisition
        """
        try:
            if self.notebook is None:
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
                self.ref_folder_entry.setText(folder)
                self._check_reference_folder(folder)
        except Exception as e:
            logger.error(f"Erreur dans _browse_reference_folder: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _check_results_folder(self, folder):
        """
        Vérifie le contenu du dossier de résultats
        """
        try:
            if not folder or not os.path.exists(folder):
                self.folder_info_label.setText("Dossier non valide ou inexistant.")
                return

            files = os.listdir(folder)
            csv_files = [f for f in files if f.lower().endswith('.csv')]

            if not csv_files:
                self.folder_info_label.setText("Aucun fichier CSV trouvé dans le dossier.")
                return

            self.folder_info_label.setText(f"Dossier valide. {len(csv_files)} fichiers CSV trouvés.")
            logger.info(f"Dossier valide: {folder}, {len(csv_files)} fichiers CSV trouvés")

            # Mise à jour des boutons de navigation
            self._update_nav_buttons()
        except Exception as e:
            self.folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")
            logger.error(f"Erreur dans _check_results_folder: {str(e)}", exc_info=True)

    def _check_reference_folder(self, folder):
        """
        Vérifie le contenu du dossier de référence
        """
        try:
            if not folder or not os.path.exists(folder):
                self.ref_folder_info_label.setText("Dossier non valide ou inexistant.")
                return

            files = os.listdir(folder)
            csv_files = [f for f in files if f.lower().endswith('.csv')]
            excel_files = [f for f in files if f.lower().endswith('.xlsx')]

            if not csv_files and not excel_files:
                self.ref_folder_info_label.setText("Aucun fichier CSV ou Excel trouvé dans le dossier.")
                return

            self.ref_folder_info_label.setText(f"Dossier valide. {len(csv_files)} fichiers CSV et {len(excel_files)} fichiers Excel trouvés.")
            logger.info(f"Dossier de référence valide: {folder}, {len(csv_files)} fichiers CSV et {len(excel_files)} fichiers Excel trouvés")

            # Mise à jour des boutons de navigation
            self._update_nav_buttons()
        except Exception as e:
            self.ref_folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")
            logger.error(f"Erreur dans _check_reference_folder: {str(e)}", exc_info=True)

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
                QMessageBox.critical(self.widget, "Erreur", "Veuillez sélectionner un dossier de référence valide pour les options de validation sélectionnées.")
                return

            self.analyzer = AcquisitionAnalyzer()

            # Désactiver le bouton pendant l'analyse
            self.next_substep_button.setEnabled(False)
            self.next_substep_button.setText("Analyse en cours...")
            self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['disabled']}; color: white;")

            if self.progress_bar is not None:
                self.progress_bar.setValue(0)
                self.progress_bar.setStyleSheet(
                    f"QProgressBar::chunk {{ background-color: {COLOR_SCHEME['primary']}; }}")
            if self.progress_label is not None:
                self.progress_label.setText("Lancement de l'analyse...")
                self.progress_label.setStyleSheet(f"color: {COLOR_SCHEME['primary']}; font-weight: bold;")

            def analyze_task():
                try:
                    self.progress_updated.emit(10, "Chargement des données...")
                    time.sleep(0.5)

                    # Analyse standard des résultats
                    self.progress_updated.emit(30, "Analyse des résultats...")
                    analysis_results = self.analyzer.analyze_results(
                        results_folder,  # dossier des résultats
                        plate_type=self.plate_type_var,  # type de plaque ( nanofilm ou microdepot )
                        acquisition_mode=self.acquisition_mode_var # mode d'acquisition ( expo ou client )
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



                    if self.do_compare_to_ref:   # comparaison volumes et épaissseurs
                        self.progress_updated.emit(50, "Comparaison aux références...")
                        try:
                            # Déterminer si c'est un nanofilm ou non en fonction du type de plaque
                            is_nanofilm = "nanofilm" in self.plate_type_var.lower() if self.plate_type_var else False

                            if is_nanofilm:
                                # Utiliser la fonction pour nanofilm
                                name_dossier, slope, intercept, r_value, nb_puits_loin_fit, diff_mean, diff_cv, vect1, vect2 = comparaison_ZC_to_ref_v1_nanofilm(
                                    "SC", results_folder, machine_to_validate, reference_folder, reference_machine,
                                    validation_output_dir, "validation_comparison", 10
                                )
                            else:
                                # Utiliser la fonction pour microdepot
                                name_dossier, slope, intercept, r_value, nb_puits_loin_fit, diff_mean, diff_cv, diam_diff_mean, diam_diff_cv, vect1, vect2 = comparaison_ZC_to_ref_v1(
                                    "GP", results_folder, machine_to_validate, reference_folder, reference_machine, 
                                    validation_output_dir, "validation_comparison", 10
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

                    if self.do_compare_enzymo_to_ref:
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
                                excel_path = os.path.join(reference_parent_folder, acquisition_name_instrument_1, 'WellResults.xlsx')
                                all_results = []

                                if os.path.exists(excel_path):
                                    excel_file = pandas.ExcelFile(excel_path)
                                    sheet_names = excel_file.sheet_names

                                    # Itérer sur tous les onglets
                                    for sheet_name in sheet_names:
                                        try:
                                            ref_data, validation_data = compare_enzymo_2_ref(
                                                reference_parent_folder, reference_machine, acquisition_name_instrument_1, sheet_name,
                                                results_parent_folder, machine_to_validate, acquisition_name_instrument_2,
                                                comparison_dir
                                            )

                                            all_results.append(ref_data)
                                            all_results.append(validation_data)

                                            print(f"Onglet {sheet_name} - Référence: {ref_data}, Validation: {validation_data}")
                                        except Exception as e:
                                            logger.error(f"Erreur lors de la comparaison pour l'onglet {sheet_name}: {str(e)}", exc_info=True)

                                    # Créer le fichier CSV de résultats
                                    if all_results:
                                        find_len_max = 0
                                        for result in all_results:
                                            if len(result) > find_len_max:
                                                find_len_max = len(result)

                                        csv_path = os.path.join(comparison_dir, 'data_compar_enzymo_2_ref.csv')
                                        try:
                                            with open(csv_path, 'w') as csv_out:
                                                # Écrire l'en-tête
                                                csv_out.write('Nom de l Acquisitions;Machine;Zone;LOD;LOQ;Sensibilite (en U/mL);CV % deg a 30%;CV % deg a 50%;CV % deg a 70%;')

                                                # Calculer le nombre d'échantillons
                                                nb_echantillons = max(0, int((find_len_max-14)/4))

                                                # Ajouter les colonnes pour chaque échantillon
                                                for i in range(nb_echantillons):
                                                    csv_out.write('Activite Ech_' + str(i+1) + ' (U/mL);RSD Ech_' + str(i+1) + ' (%);')

                                                # Ajouter les colonnes de différence
                                                csv_out.write('diff % LOD;diff % LOQ;diff % Sensibilite (en U/mL);diff % CV % deg a 30%;diff % CV % deg a 50%;diff % CV % deg a 70%;')

                                                for i in range(nb_echantillons):
                                                    csv_out.write('diff % Activite Ech_' + str(i+1) + ' (U/mL);diff % RSD Ech_' + str(i+1) + ' (%);')

                                                csv_out.write('\n')

                                                # Écrire les données
                                                for result in all_results:
                                                    for value in result:
                                                        csv_out.write(str(value) + ';')
                                                    csv_out.write('\n')

                                            logger.info(f"Résultats écrits dans {csv_path}")
                                        except Exception as e:
                                            logger.error(f"Erreur lors de l'écriture des résultats dans {csv_path}: {str(e)}", exc_info=True)
                                else:
                                    logger.error(f"Le fichier WellResults.xlsx n'existe pas dans {os.path.dirname(excel_path)}")

                                # Stocker les résultats pour l'affichage
                                if all_results and len(all_results) >= 2:
                                    # Utiliser les premiers résultats pour l'affichage
                                    validation_results["enzymo_comparison"] = {
                                        "reference_data": all_results[0],
                                        "validation_data": all_results[1],
                                        "all_results": all_results
                                    }
                                else:
                                    validation_results["enzymo_comparison_error"] = "Aucun résultat obtenu pour la comparaison enzymatique"
                            else:
                                validation_results[
                                    "enzymo_comparison_error"] = "Sous-dossiers d'acquisition non trouvés"

                        except Exception as e:
                            logger.error(f"Erreur lors de la comparaison des données enzymatiques: {str(e)}",
                                         exc_info=True)
                            validation_results["enzymo_comparison_error"] = str(e)

                    # Ajouter les résultats de validation aux résultats d'analyse
                    if validation_results:
                        analysis_results["validation"] = validation_results

                    self.progress_updated.emit(90, "Finalisation de l'analyse...")
                    time.sleep(0.5)
                    self.progress_updated.emit(100, "Analyse terminée.")
                    self.analysis_results = analysis_results
                    self.analysis_completed.emit()
                except Exception as e:
                    logger.error(f"Erreur lors de l'analyse des résultats: {str(e)}", exc_info=True)
                    self.analysis_error.emit(str(e))

            threading.Thread(target=analyze_task, daemon=True).start()
        except Exception as e:
            logger.error(f"Erreur dans _analyze_results: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

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

            if self.notebook is None:
                logger.error("Erreur dans _display_analysis_results: self.notebook est None")
                QMessageBox.critical(self.widget, "Erreur",
                                     "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                self._reset_analysis_button()
                return

            self.notebook.setTabEnabled(2, True)
            self.notebook.setCurrentIndex(2)
            self._display_acquisition_info()
            self._display_statistics()
            self._display_graphs()

            # Réactiver le bouton et mettre à jour la navigation
            self._reset_analysis_button()
            self._update_nav_buttons()

            if self.progress_label is not None:
                self.progress_label.setStyleSheet("")
                self.progress_label.setText("Analyse terminée avec succès.")
            logger.info("Affichage des résultats d'analyse terminé")
        except Exception as e:
            logger.error(f"Erreur dans _display_analysis_results: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur",
                                 f"Une erreur est survenue lors de l'affichage des résultats :\n{str(e)}")
            self._reset_analysis_button()

    def _reset_analysis_button(self):
        """
        Réinitialise le bouton d'analyse à son état normal
        """
        try:
            self.next_substep_button.setEnabled(True)
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _reset_analysis_button: {str(e)}", exc_info=True)

    def _display_acquisition_info(self):
        """
        Affiche les informations sur l'acquisition
        """
        try:
            if self.info_text is None:
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
            if self.info_text is not None:
                self.info_text.setText(f"Erreur lors de l'affichage des infos : {str(e)}")

    def _display_statistics(self):
        """
        Affiche les statistiques de l'analyse
        """
        try:
            if self.stats_table is None:
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

            # Statistiques de validation
            validation = self.analysis_results.get("validation", {})
            if validation:
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
                                    # Pour R², on utilise r_value
                                    val = float(comp.get('r_value', 0))
                                    is_valid = val >= criteria['min'] and val <= criteria['max']
                                elif criteria_key == 'nb_puits_loin_fit':
                                    # Pour les points hors tolérance
                                    val = int(comp.get('nb_puits_loin_fit', 0))
                                    is_valid = val >= criteria['min'] and val <= criteria['max']
                                elif criteria_key == 'slope':
                                    # Pour la pente
                                    val = float(comp.get('slope', 0))
                                    is_valid = val >= criteria['min'] and val <= criteria['max']
                                elif criteria_key == 'intercept':
                                    # Pour l'ordonnée à l'origine
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

                # Statistiques de comparaison enzymatique
                if 'enzymo_comparison' in validation:
                    enzymo = validation['enzymo_comparison']

                    # Ajouter un séparateur pour les données enzymatiques
                    row = self.stats_table.rowCount()
                    self.stats_table.insertRow(row)
                    self.stats_table.setItem(row, 0, QTableWidgetItem("--- Comparaison enzymatique ---"))
                    self.stats_table.setItem(row, 1, QTableWidgetItem(""))
                    self.stats_table.setItem(row, 2, QTableWidgetItem(""))

                    # Extraire et afficher quelques statistiques enzymatiques clés si disponibles
                    if isinstance(enzymo.get('validation_data'), list) and len(enzymo.get('validation_data', [])) > 0:
                        validation_data = enzymo['validation_data'][0]
                        if isinstance(validation_data, str):
                            # Essayer de parser les données CSV
                            try:
                                parts = validation_data.split(';')
                                if len(parts) >= 7:
                                    enzymo_items = [
                                        ("LOD", parts[2] if len(parts) > 2 else "N/A"),
                                        ("LOQ", parts[3] if len(parts) > 3 else "N/A"),
                                        ("Sensibilité", parts[4] if len(parts) > 4 else "N/A"),
                                        ("CV à 30%", parts[5] if len(parts) > 5 else "N/A"),
                                        ("CV à 50%", parts[6] if len(parts) > 6 else "N/A"),
                                        ("CV à 70%", parts[7] if len(parts) > 7 else "N/A")
                                    ]

                                    for param, value in enzymo_items:
                                        row = self.stats_table.rowCount()
                                        self.stats_table.insertRow(row)
                                        self.stats_table.setItem(row, 0, QTableWidgetItem(param))
                                        self.stats_table.setItem(row, 1, QTableWidgetItem(value))
                                        self.stats_table.setItem(row, 2, QTableWidgetItem(""))
                            except Exception as e:
                                logger.error(f"Erreur lors du parsing des données enzymatiques: {str(e)}", exc_info=True)
                                row = self.stats_table.rowCount()
                                self.stats_table.insertRow(row)
                                self.stats_table.setItem(row, 0, QTableWidgetItem("Données enzymatiques"))
                                self.stats_table.setItem(row, 1, QTableWidgetItem("Disponibles mais format non reconnu"))
                                self.stats_table.setItem(row, 2, QTableWidgetItem(""))

                # Erreurs de validation
                if 'comparison_error' in validation or 'enzymo_comparison_error' in validation:
                    row = self.stats_table.rowCount()
                    self.stats_table.insertRow(row)
                    self.stats_table.setItem(row, 0, QTableWidgetItem("--- Erreurs de validation ---"))
                    self.stats_table.setItem(row, 1, QTableWidgetItem(""))
                    self.stats_table.setItem(row, 2, QTableWidgetItem(""))

                    if 'comparison_error' in validation:
                        row = self.stats_table.rowCount()
                        self.stats_table.insertRow(row)
                        self.stats_table.setItem(row, 0, QTableWidgetItem("Erreur de comparaison"))
                        self.stats_table.setItem(row, 1, QTableWidgetItem(validation['comparison_error']))
                        self.stats_table.setItem(row, 2, QTableWidgetItem(""))

                    if 'enzymo_comparison_error' in validation:
                        row = self.stats_table.rowCount()
                        self.stats_table.insertRow(row)
                        self.stats_table.setItem(row, 0, QTableWidgetItem("Erreur de comparaison enzymatique"))
                        self.stats_table.setItem(row, 1, QTableWidgetItem(validation['enzymo_comparison_error']))
                        self.stats_table.setItem(row, 2, QTableWidgetItem(""))

        except Exception as e:
            logger.error(f"Erreur dans _display_statistics: {str(e)}", exc_info=True)

    @pyqtSlot(int, str)
    def _update_progress(self, value, message):
        """
        Met à jour la barre de progression et le message associé

        Args:
            value: Valeur de progression (0-100)
            message: Message à afficher
        """
        try:
            if self.progress_bar is not None:
                self.progress_bar.setValue(value)
            if self.progress_label is not None:
                self.progress_label.setText(message)
            logger.debug(f"Progression: {value}% - {message}")
        except Exception as e:
            logger.error(f"Erreur dans _update_progress: {str(e)}", exc_info=True)

    @pyqtSlot(str)
    def _handle_analysis_error(self, error_message):
        """
        Gère les erreurs d'analyse

        Args:
            error_message: Message d'erreur
        """
        try:
            if self.progress_label is not None:
                self.progress_label.setText(f"Erreur: {error_message}")
                self.progress_label.setStyleSheet(f"color: {COLOR_SCHEME['error']}; font-weight: bold;")
            if self.progress_bar is not None:
                self.progress_bar.setValue(0)
                self.progress_bar.setStyleSheet("")

            # Réactiver le bouton d'analyse
            self._reset_analysis_button()

            QMessageBox.critical(self.widget, "Erreur d'analyse",
                                 f"Une erreur est survenue lors de l'analyse :\n{error_message}")
            logger.error(f"Erreur d'analyse: {error_message}")
        except Exception as e:
            logger.error(f"Erreur dans _handle_analysis_error: {str(e)}", exc_info=True)

    def _display_graphs(self):
        """
        Affiche les graphiques générés par l'analyse
        """
        try:
            if self.graphs_widget is None:
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

                    # Ajouter les images du dossier validation_comparison si elles existent
                    validation_comparison_dir = os.path.join(validation_dir, "validation_comparison")
                    if os.path.exists(validation_comparison_dir):
                        for file in os.listdir(validation_comparison_dir):
                            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                graph_paths.append(os.path.join(validation_comparison_dir, file))

                    # Ajouter les images du dossier comparaison_enzymo_routine si elles existent
                    enzymo_comparison_dir = os.path.join(validation_dir, "comparaison_enzymo_routine")
                    if os.path.exists(enzymo_comparison_dir):
                        for file in os.listdir(enzymo_comparison_dir):
                            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                graph_paths.append(os.path.join(enzymo_comparison_dir, file))

            if not graph_paths:
                self.graphs_widget.setText("Aucune image disponible")
                self.graphs_widget.setStyleSheet(
                    f"color: {COLOR_SCHEME['text_secondary']}; background-color: {COLOR_SCHEME['background']};")
                self.image_title_label.setText("")
                self.image_counter_label.setText("0/0")
                self.prev_image_button.setEnabled(False)
                self.next_image_button.setEnabled(False)
                return

            # Charger toutes les images
            for path in graph_paths:
                image = QPixmap(path)
                if not image.isNull():
                    self.graph_images.append(image)
                    # Extraire le nom du fichier comme titre
                    title = os.path.basename(path)
                    # Enlever l'extension
                    title = os.path.splitext(title)[0]
                    # Remplacer les underscores par des espaces
                    title = title.replace('_', ' ')
                    self.graph_titles.append(title)

            # Afficher la première image si disponible
            if self.graph_images:
                self.current_image_index = 0
                self._display_current_image()

                # Mettre à jour les contrôles de navigation
                self._update_image_navigation()
            else:
                self.graphs_widget.setText("Impossible de charger les images")
                self.graphs_widget.setStyleSheet(
                    f"color: {COLOR_SCHEME['error']}; background-color: {COLOR_SCHEME['background']};")
                self.image_title_label.setText("")
                self.image_counter_label.setText("0/0")
                self.prev_image_button.setEnabled(False)
                self.next_image_button.setEnabled(False)
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des graphiques: {str(e)}", exc_info=True)
            if self.graphs_widget is not None:
                self.graphs_widget.setText(f"Erreur lors de l'affichage des graphiques: {str(e)}")
                self.graphs_widget.setStyleSheet(
                    f"color: {COLOR_SCHEME['error']}; background-color: {COLOR_SCHEME['background']};")
                self.image_title_label.setText("")
                self.image_counter_label.setText("0/0")
                self.prev_image_button.setEnabled(False)
                self.next_image_button.setEnabled(False)

    def _finalize_acquisition(self, validated, continue_acquisitions):
        """
        Finalise l'acquisition actuelle
        """
        try:
            if not self.analysis_results:
                QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
                return

            comments = self.comments_var if hasattr(self, 'comments_var') else ""
            if self.comments_text:
                comments = self.comments_text.toPlainText().strip()

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
                if self.notebook is None:
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
            if hasattr(self, 'ref_folder_entry') and self.ref_folder_entry:
                self.ref_folder_entry.setText("")
            if hasattr(self, 'ref_folder_info_label') and self.ref_folder_info_label:
                self.ref_folder_info_label.setText("")

            # Réinitialiser les autres champs
            if self.comments_text:
                self.comments_text.clear()
            self.comments_var = ""
            self.analysis_results = None
            if self.graphs_widget:
                self.graphs_widget.clear()
            self.graph_images = []
            if self.stats_table:
                self.stats_table.setRowCount(0)
            if self.info_text:
                self.info_text.clear()
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
            if self.history_tree is None:
                logger.error("Erreur dans _update_history: self.history_tree est None")
                return

            self.history_tree.clear()
            for acquisition in self.acquisitions:
                plate_type_name = next((pt['name'] for pt in PLATE_TYPES if pt['id'] == acquisition['plate_type']),
                                       "Inconnu")
                mode_name = next((m['name'] for m in ACQUISITION_MODES if m['id'] == acquisition['mode']), "Inconnu")
                status = "✓ Validée" if acquisition['validated'] else "✗ Invalidée"
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
            if self.comments_text:
                comments = self.comments_text.toPlainText().strip()
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

    def _previous_substep(self):
        """
        Passe à la sous-étape précédente
        """
        try:
            if self.notebook is None:
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
            if self.notebook is None:
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
                self._finalize_acquisition(True, False)
        except Exception as e:
            logger.error(f"Erreur dans _next_substep: {str(e)}", exc_info=True)
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
            if self.notebook is None:
                logger.error("Erreur dans _update_nav_buttons: self.notebook est None")
                return

            current_tab = self.notebook.currentIndex()

            # Gestion du bouton précédent
            self.prev_substep_button.setEnabled(current_tab > 0)

            # Gestion des boutons d'action supplémentaires
            if current_tab == 2:  # Onglet d'analyse
                self.validate_continue_button.setVisible(True)
                self.invalidate_button.setVisible(True)
                self.report_button.setVisible(True)
            else:
                self.validate_continue_button.setVisible(False)
                self.invalidate_button.setVisible(False)
                self.report_button.setVisible(False)

            # Gestion du bouton suivant
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

                # Afficher un message d'information si nécessaire
                if not results_folder_valid:
                    self.folder_info_label.setText("Veuillez sélectionner un dossier de résultats valide.")
                elif reference_folder_required and not reference_folder_valid:
                    self.ref_folder_info_label.setText("Dossier de référence requis pour les options de validation sélectionnées.")

            elif current_tab == 2:  # Onglet Analyse
                self.next_substep_button.setText("Valider et étape suivante")
                self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
                self.next_substep_button.setEnabled(True)
            else:
                self.next_substep_button.setEnabled(False)
        except Exception as e:
            logger.error(f"Erreur dans _update_nav_buttons: {str(e)}", exc_info=True)

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
                if hasattr(self, 'ref_folder_entry') and self.ref_folder_entry:
                    self.ref_folder_entry.setText(self.reference_folder_var)
                if hasattr(self, 'compare_to_ref_checkbox') and self.compare_to_ref_checkbox:
                    self.compare_to_ref_checkbox.setChecked(self.do_compare_to_ref)
                if hasattr(self, 'compare_enzymo_to_ref_checkbox') and self.compare_enzymo_to_ref_checkbox:
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
            if hasattr(self, 'ref_folder_entry') and self.ref_folder_entry:
                self.ref_folder_entry.setText("")
            if hasattr(self, 'compare_to_ref_checkbox') and self.compare_to_ref_checkbox:
                self.compare_to_ref_checkbox.setChecked(self.do_compare_to_ref)
            if hasattr(self, 'compare_enzymo_to_ref_checkbox') and self.compare_enzymo_to_ref_checkbox:
                self.compare_enzymo_to_ref_checkbox.setChecked(self.do_compare_enzymo_to_ref)

            self._reset_acquisition()
            self.acquisitions = []
            self.current_acquisition_id = 0
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
            if self.notebook is None:
                logger.warning("self.notebook est None lors de l'affichage de l'étape 3, réinitialisation du notebook")
                self._reinitialize_notebook()

            # Mettre à jour l'historique au cas où des données auraient été chargées
            self._update_history()

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

            # Vérifier si le notebook existe déjà dans le layout
            notebook_exists = False
            notebook_widget = None

            # Trouver le main_layout (premier enfant de self.layout)
            main_layout = None
            for i in range(self.layout.count()):
                item = self.layout.itemAt(i)
                if item and item.layout():
                    main_layout = item.layout()
                    break

            if not main_layout:
                logger.error("Impossible de trouver le main_layout")
                return

            # Chercher le splitter dans le main_layout
            main_splitter = None
            for i in range(main_layout.count()):
                item = main_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QSplitter):
                    main_splitter = item.widget()
                    break

            if not main_splitter:
                logger.error("Impossible de trouver le main_splitter")
                return

            # Chercher si un QTabWidget existe déjà dans le main_splitter
            for i in range(main_splitter.count()):
                widget = main_splitter.widget(i)
                if isinstance(widget, QTabWidget):
                    notebook_exists = True
                    notebook_widget = widget
                    break

            if notebook_exists and notebook_widget:
                # Utiliser le notebook existant
                logger.info("Notebook existant trouvé, réutilisation")
                self.notebook = notebook_widget

                # Réinitialiser les références aux widgets dans les onglets
                self._reinitialize_widget_references()
            else:
                # Créer un nouveau notebook
                logger.info("Création d'un nouveau notebook")
                self.notebook = QTabWidget()

                # Insérer le notebook dans le main_splitter à l'index 0
                main_splitter.insertWidget(0, self.notebook)

                # Créer les onglets
                self._create_notebook_tabs()

            # Mise à jour de l'état des boutons de navigation
            self._update_nav_buttons()

            logger.info("Notebook réinitialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur dans _reinitialize_notebook: {str(e)}", exc_info=True)

    def _reinitialize_widget_references(self):
        """
        Réinitialise les références aux widgets dans les onglets existants
        """
        try:
            # Récupérer les références des widgets dans l'onglet de sélection
            selection_frame = self.notebook.widget(1)
            if selection_frame:
                # Parcourir les widgets pour trouver les références
                for widget in selection_frame.findChildren(QLineEdit):
                    if hasattr(widget, 'textChanged'):
                        self.folder_entry = widget
                        break

                for widget in selection_frame.findChildren(QLabel):
                    if widget.wordWrap():
                        self.folder_info_label = widget
                        break

                for widget in selection_frame.findChildren(QProgressBar):
                    self.progress_bar = widget
                    break

                for widget in selection_frame.findChildren(QLabel):
                    if widget.alignment() == Qt.AlignLeft:
                        self.progress_label = widget
                        break

            # Récupérer les références des widgets dans l'onglet d'analyse
            analysis_frame = self.notebook.widget(2)
            if analysis_frame:
                for widget in analysis_frame.findChildren(QTextEdit):
                    if widget.isReadOnly():
                        self.info_text = widget
                    else:
                        self.comments_text = widget

                for widget in analysis_frame.findChildren(QTableWidget):
                    self.stats_table = widget
                    break

                for widget in analysis_frame.findChildren(QLabel):
                    if widget.alignment() == Qt.AlignCenter:
                        self.graphs_widget = widget
                        break

            # Trouver le QTreeWidget pour l'historique des acquisitions
            main_layout = None
            for i in range(self.layout.count()):
                item = self.layout.itemAt(i)
                if item and item.layout():
                    main_layout = item.layout()
                    break

            if main_layout:
                # Chercher le splitter dans le main_layout
                main_splitter = None
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), QSplitter):
                        main_splitter = item.widget()
                        break

                if main_splitter:
                    # Chercher le QGroupBox dans le splitter
                    for i in range(main_splitter.count()):
                        widget = main_splitter.widget(i)
                        if isinstance(widget, QGroupBox) and widget.title() == "Historique des acquisitions":
                            history_frame = widget
                            for child in history_frame.findChildren(QTreeWidget):
                                self.history_tree = child
                                logger.info("Référence à l'historique des acquisitions réinitialisée")
                                break
                            break

            # Reconnecter les signaux
            if self.folder_entry:
                self.folder_entry.textChanged.connect(self._on_folder_entry_changed)
            if self.comments_text:
                self.comments_text.textChanged.connect(self._on_comments_changed)

            # Liaison des événements du notebook
            self.notebook.currentChanged.connect(self._on_tab_changed)

        except Exception as e:
            logger.error(f"Erreur dans _reinitialize_widget_references: {str(e)}", exc_info=True)

    def _create_notebook_tabs(self):
        """
        Crée les onglets du notebook
        """
        try:
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

            # Désactiver les onglets 2 et 3 au départ
            self.notebook.setTabEnabled(1, False)
            self.notebook.setTabEnabled(2, False)

            # Liaison des événements
            self.notebook.currentChanged.connect(self._on_tab_changed)
        except Exception as e:
            logger.error(f"Erreur dans _create_notebook_tabs: {str(e)}", exc_info=True)
