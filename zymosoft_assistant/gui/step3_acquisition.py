#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 3 de l'assistant d'installation ZymoSoft : Validation par acquisitions
"""

import os
import logging
import threading
import time
from PIL import Image, ImageQt
import uuid
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFrame, QFileDialog, QMessageBox,
                             QProgressBar, QTabWidget, QWidget, QScrollArea,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QCheckBox, QRadioButton, QGroupBox, QTextEdit,
                             QTreeWidget, QTreeWidgetItem, QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal, QVariant
from PyQt5.QtGui import QPixmap

from zymosoft_assistant.utils.constants import COLOR_SCHEME, PLATE_TYPES, ACQUISITION_MODES
from zymosoft_assistant.core.acquisition_analyzer import AcquisitionAnalyzer
from zymosoft_assistant.core.report_generator import ReportGenerator
from .step_frame import StepFrame

logger = logging.getLogger(__name__)

class Step3Acquisition(StepFrame):
    """
    Classe pour l'étape 3 : Validation par acquisitions
    """

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
        self.comments_var = ""

        # Initialisation des valeurs par défaut
        self.plate_type_var = PLATE_TYPES[0]['id'] if PLATE_TYPES else ""
        self.acquisition_mode_var = ACQUISITION_MODES[0]['id'] if ACQUISITION_MODES else ""
        self.results_folder_var = ""

        super().__init__(parent, main_window)

        # Variables pour les résultats d'analyse
        self.analysis_results = None
        self.current_acquisition_id = 0
        self.acquisitions = []

        # Objets pour l'analyse
        self.analyzer = None

        # Images pour les graphiques
        self.graph_images = []

        # Références aux widgets
        self.notebook = None
        self.folder_info_var = ""
        self.progress_bar = None
        self.progress_label = None
        self.analyze_button = None
        self.info_text = None
        self.stats_tree = None
        self.comments_text = None
        self.graphs_canvas = None
        self.history_tree = None

        logger.info("Étape 3 initialisée")

    def create_widgets(self):
        """
        Crée les widgets de l'étape 3
        """
        # Utilisation du layout vertical principal
        main_layout = QVBoxLayout()
        self.layout.addLayout(main_layout)

        # Titre de l'étape
        title_label = QLabel("Étape 3 : Validation par acquisitions")
        title_label.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {COLOR_SCHEME['primary']};")
        main_layout.addWidget(title_label)
        main_layout.addSpacing(20)

        # Notebook pour les sous-étapes
        self.notebook = QTabWidget()
        main_layout.addWidget(self.notebook)

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
        main_layout.addWidget(self.history_frame)

        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["#", "Type de plaque", "Mode", "Statut"])
        self.history_tree.setColumnWidth(0, 50)
        self.history_tree.setColumnWidth(1, 150)
        self.history_tree.setColumnWidth(2, 150)
        self.history_tree.setColumnWidth(3, 100)
        self.history_tree.setMaximumHeight(100)
        history_layout.addWidget(self.history_tree)

        # Barre de navigation spécifique à l'étape 3
        self.nav_frame = QFrame()
        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.nav_frame)

        self.prev_substep_button = QPushButton("Étape précédente")
        self.prev_substep_button.clicked.connect(self._previous_substep)
        nav_layout.addWidget(self.prev_substep_button, 0, Qt.AlignLeft)

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

        # Formulaire
        form_frame = QWidget()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 0, 20, 0)
        self.config_layout.addWidget(form_frame)
        self.config_layout.addStretch(1)

        # Type de plaque
        plate_type_frame = QGroupBox("Type de plaque")
        plate_type_layout = QVBoxLayout(plate_type_frame)
        form_layout.addWidget(plate_type_frame)
        form_layout.addSpacing(10)

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
                plate_type_layout.addWidget(desc_label)

        # Mode d'acquisition
        mode_frame = QGroupBox("Mode d'acquisition")
        mode_layout = QVBoxLayout(mode_frame)
        form_layout.addWidget(mode_frame)
        form_layout.addSpacing(10)

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
                mode_layout.addWidget(desc_label)

        # Instructions
        instructions_frame = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout(instructions_frame)
        form_layout.addWidget(instructions_frame)
        form_layout.addSpacing(10)

        instructions_text = (
            "1. Sélectionnez le type de plaque et le mode d'acquisition.\n"
            "2. Lancez ZymoSoft et réalisez une acquisition avec les paramètres sélectionnés.\n"
            "3. Une fois l'acquisition terminée, cliquez sur \"Acquisition réalisée\"."
        )

        instructions_label = QLabel(instructions_text)
        instructions_label.setWordWrap(True)
        instructions_label.setAlignment(Qt.AlignLeft)
        instructions_layout.addWidget(instructions_label)

        # Bouton pour passer à l'étape suivante
        acquisition_done_button = QPushButton("Acquisition réalisée")
        acquisition_done_button.clicked.connect(self._acquisition_done)
        acquisition_done_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
        form_layout.addWidget(acquisition_done_button, 0, Qt.AlignCenter)
        form_layout.addSpacing(20)

    def _on_plate_type_changed(self, checked):
        """
        Appelé lorsque le type de plaque est modifié

        Args:
            checked: True si le bouton est coché, False sinon
        """
        if checked:
            sender = self.sender()
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
            sender = self.sender()
            if sender:
                self.acquisition_mode_var = sender.property("acquisition_mode_id")
                logger.info(f"Mode d'acquisition sélectionné: {self.acquisition_mode_var}")

    def _create_selection_widgets(self):
        """
        Crée les widgets pour la sélection des résultats
        """
        # Description
        description_label = QLabel("Sélectionnez le dossier contenant les résultats de l'acquisition.")
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(600)
        self.selection_layout.addWidget(description_label)
        self.selection_layout.addSpacing(20)

        # Sélection du dossier
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

        # Bouton pour analyser les résultats
        self.analyze_button = QPushButton("Analyser les résultats")
        self.analyze_button.clicked.connect(self._analyze_results)
        self.analyze_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
        self.selection_layout.addWidget(self.analyze_button, 0, Qt.AlignCenter)
        self.selection_layout.addSpacing(20)
        self.analyze_button.setEnabled(False)

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

        # Conteneur principal
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(20, 0, 20, 0)
        self.analysis_layout.addWidget(main_container)

        # Panneau gauche: Statistiques et informations
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel)

        # Informations sur l'acquisition
        info_frame = QGroupBox("Informations")
        info_layout = QVBoxLayout(info_frame)
        left_layout.addWidget(info_frame)

        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(120)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        # Statistiques
        stats_frame = QGroupBox("Statistiques")
        stats_layout = QVBoxLayout(stats_frame)
        left_layout.addWidget(stats_frame)

        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stats_table.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_table)

        # Commentaires
        comments_frame = QGroupBox("Commentaires")
        comments_layout = QVBoxLayout(comments_frame)
        left_layout.addWidget(comments_frame)

        self.comments_text = QTextEdit()
        self.comments_text.setMaximumHeight(100)
        comments_layout.addWidget(self.comments_text)

        # Panneau droit: Graphiques
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel)

        # Graphiques
        graphs_frame = QGroupBox("Graphiques")
        graphs_layout = QVBoxLayout(graphs_frame)
        right_layout.addWidget(graphs_frame)

        # Widget pour les graphiques
        self.graphs_widget = QLabel()
        self.graphs_widget.setStyleSheet(f"background-color: {COLOR_SCHEME['background']};")
        self.graphs_widget.setAlignment(Qt.AlignCenter)
        graphs_layout.addWidget(self.graphs_widget)

        # Boutons d'action
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 10, 0, 0)
        self.analysis_layout.addWidget(actions_frame)

        self.validate_continue_button = QPushButton("Valider cette acquisition et recommencer")
        self.validate_continue_button.clicked.connect(lambda: self._finalize_acquisition(True, True))
        actions_layout.addWidget(self.validate_continue_button)

        self.invalidate_button = QPushButton("Invalider et refaire")
        self.invalidate_button.clicked.connect(lambda: self._finalize_acquisition(False, True))
        actions_layout.addWidget(self.invalidate_button)

        actions_layout.addStretch(1)

        self.validate_next_button = QPushButton("Valider et étape suivante")
        self.validate_next_button.clicked.connect(lambda: self._finalize_acquisition(True, False))
        self.validate_next_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
        actions_layout.addWidget(self.validate_next_button)

        # Rapport
        report_frame = QFrame()
        report_layout = QHBoxLayout(report_frame)
        report_layout.setContentsMargins(0, 10, 0, 0)
        self.analysis_layout.addWidget(report_frame)

        self.report_button = QPushButton("Générer rapport d'acquisition")
        self.report_button.clicked.connect(self._generate_acquisition_report)
        report_layout.addWidget(self.report_button)
        report_layout.addStretch(1)

    def _acquisition_done(self):
        """
        Appelé lorsque l'utilisateur a terminé l'acquisition
        """
        # Activer l'onglet de sélection des résultats
        self.notebook.setTabEnabled(1, True)

        # Passer à l'onglet suivant
        self.notebook.setCurrentIndex(1)

    def _browse_results_folder(self):
        """
        Ouvre une boîte de dialogue pour sélectionner le dossier de résultats
        """
        folder = QFileDialog.getExistingDirectory(
            self.widget,
            "Sélectionner le dossier de résultats d'acquisition"
        )

        if folder:
            self.results_folder_var = folder
            self.folder_entry.setText(folder)
            self._check_results_folder(folder)

    def _check_results_folder(self, folder):
        """
        Vérifie le contenu du dossier de résultats

        Args:
            folder: Chemin du dossier à vérifier
        """
        if not folder or not os.path.exists(folder):
            self.folder_info_label.setText("Dossier non valide ou inexistant.")
            self.analyze_button.setEnabled(False)
            return

        # Vérifier le contenu du dossier
        try:
            files = os.listdir(folder)
            csv_files = [f for f in files if f.lower().endswith('.csv')]

            if not csv_files:
                self.folder_info_label.setText("Aucun fichier CSV trouvé dans le dossier.")
                self.analyze_button.setEnabled(False)
                return

            self.folder_info_label.setText(f"Dossier valide. {len(csv_files)} fichiers CSV trouvés.")
            self.analyze_button.setEnabled(True)
        except Exception as e:
            self.folder_info_label.setText(f"Erreur lors de la vérification du dossier: {str(e)}")
            self.analyze_button.setEnabled(False)

    def _analyze_results(self):
        """
        Lance l'analyse des résultats d'acquisition
        """
        results_folder = self.folder_entry.text()
        self.results_folder_var = results_folder

        if not results_folder or not os.path.exists(results_folder):
            QMessageBox.critical(self.widget, "Erreur", "Veuillez sélectionner un dossier de résultats valide.")
            return

        # Initialiser l'analyseur
        self.analyzer = AcquisitionAnalyzer()

        # Désactiver le bouton pendant l'analyse
        self.analyze_button.setEnabled(False)

        # Mettre à jour la barre de progression
        self.progress_bar.setValue(0)
        self.progress_label.setText("Lancement de l'analyse...")

        def analyze_task():
            try:
                # Mise à jour de la progression
                self._update_progress(10, "Chargement des données...")
                time.sleep(0.5)  # Simuler un traitement

                # Analyse des résultats
                self._update_progress(30, "Analyse des résultats...")
                analysis_results = self.analyzer.analyze_results(results_folder)
                time.sleep(0.5)  # Simuler un traitement

                # Calcul des statistiques
                self._update_progress(60, "Calcul des statistiques...")
                time.sleep(0.5)  # Simuler un traitement

                # Génération des graphiques
                self._update_progress(80, "Génération des graphiques...")
                time.sleep(0.5)  # Simuler un traitement

                # Finalisation
                self._update_progress(100, "Analyse terminée.")

                # Stockage des résultats
                self.analysis_results = analysis_results

                # Mise à jour de l'interface dans le thread principal
                # Note: In a real application, you should use signals and slots for thread safety
                self._display_analysis_results()
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse des résultats: {str(e)}", exc_info=True)
                self._handle_analysis_error(str(e))

        # Lancer l'analyse dans un thread séparé
        threading.Thread(target=analyze_task, daemon=True).start()

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

    def _handle_analysis_error(self, error_message):
        """
        Gère les erreurs survenues pendant l'analyse

        Args:
            error_message: Message d'erreur
        """
        QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors de l'analyse:\n{error_message}")
        self.progress_label.setText(f"Erreur: {error_message}")
        self.analyze_button.setEnabled(True)

    def _display_analysis_results(self):
        """
        Affiche les résultats de l'analyse
        """
        if not self.analysis_results:
            QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
            self.analyze_button.setEnabled(True)
            return

        # Activer l'onglet d'analyse
        self.notebook.setTabEnabled(2, True)

        # Passer à l'onglet d'analyse
        self.notebook.setCurrentIndex(2)

        # Afficher les informations
        self._display_acquisition_info()

        # Afficher les statistiques
        self._display_statistics()

        # Afficher les graphiques
        self._display_graphs()

        # Réactiver le bouton d'analyse
        self.analyze_button.setEnabled(True)

        logger.info("Affichage des résultats d'analyse terminé")

    def _display_acquisition_info(self):
        """
        Affiche les informations sur l'acquisition
        """
        # Effacer le contenu précédent
        self.info_text.clear()

        # Ajouter les informations
        plate_type_name = next((pt['name'] for pt in PLATE_TYPES if pt['id'] == self.plate_type_var), "Inconnu")
        mode_name = next((m['name'] for m in ACQUISITION_MODES if m['id'] == self.acquisition_mode_var), "Inconnu")

        info_text = (
            f"Type de plaque: {plate_type_name}\n"
            f"Mode d'acquisition: {mode_name}\n"
            f"Dossier de résultats: {self.results_folder_var}\n"
            f"Statut: {'Valide' if self.analysis_results.get('valid', False) else 'Non valide'}\n"
        )

        self.info_text.setText(info_text)
        self.info_text.setReadOnly(True)

    def _display_statistics(self):
        """
        Affiche les statistiques de l'analyse
        """
        # Effacer les statistiques précédentes
        self.stats_table.setRowCount(0)

        # Ajouter les nouvelles statistiques
        statistics = self.analysis_results.get("statistics", {})

        if statistics:
            # Pente
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem("Pente"))
            self.stats_table.setItem(row, 1, QTableWidgetItem(f"{statistics.get('slope', 0):.4f}"))

            # Ordonnée à l'origine
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem("Ordonnée à l'origine"))
            self.stats_table.setItem(row, 1, QTableWidgetItem(f"{statistics.get('intercept', 0):.4f}"))

            # Coefficient de détermination (R²)
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem("R²"))
            self.stats_table.setItem(row, 1, QTableWidgetItem(f"{statistics.get('r2', 0):.4f}"))

            # Nombre de valeurs aberrantes
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem("Valeurs aberrantes"))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(statistics.get('outliers_count', 0))))

            # Pourcentage de valeurs aberrantes
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem("% valeurs aberrantes"))
            self.stats_table.setItem(row, 1, QTableWidgetItem(f"{statistics.get('outliers_percentage', 0):.2f}%"))

    def _display_graphs(self):
        """
        Affiche les graphiques générés par l'analyse
        """
        # Effacer les graphiques précédents
        self.graphs_widget.clear()
        self.graph_images = []

        # Récupérer les chemins des graphiques
        graph_paths = self.analysis_results.get("graphs", [])

        if not graph_paths:
            self.graphs_widget.setText("Aucun graphique disponible")
            self.graphs_widget.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']}; background-color: {COLOR_SCHEME['background']};")
            return

        # Charger et afficher les graphiques
        try:
            # Utiliser le premier graphique pour l'instant (simplification)
            if graph_paths:
                image = QPixmap(graph_paths[0])
                if not image.isNull():
                    self.graphs_widget.setPixmap(image.scaled(
                        self.graphs_widget.width(), 
                        self.graphs_widget.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    ))
                    # Stocker la référence à l'image
                    self.graph_images.append(image)
                else:
                    self.graphs_widget.setText(f"Impossible de charger l'image: {graph_paths[0]}")
                    self.graphs_widget.setStyleSheet(f"color: {COLOR_SCHEME['error']}; background-color: {COLOR_SCHEME['background']};")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des graphiques: {str(e)}", exc_info=True)
            self.graphs_widget.setText(f"Erreur lors de l'affichage des graphiques: {str(e)}")
            self.graphs_widget.setStyleSheet(f"color: {COLOR_SCHEME['error']}; background-color: {COLOR_SCHEME['background']};")

    # La méthode _display_single_graph n'est plus nécessaire car nous utilisons un QLabel pour afficher les graphiques

    def _finalize_acquisition(self, validated, continue_acquisitions):
        """
        Finalise l'acquisition actuelle

        Args:
            validated: True si l'acquisition est validée, False sinon
            continue_acquisitions: True pour continuer avec une nouvelle acquisition, False pour passer à l'étape suivante
        """
        if not self.analysis_results:
            QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
            return

        # Récupérer les commentaires
        comments = self.comments_text.toPlainText().strip()

        # Incrémenter l'ID d'acquisition
        self.current_acquisition_id += 1

        # Créer l'objet acquisition
        acquisition = {
            "id": self.current_acquisition_id,
            "plate_type": self.plate_type_var.get(),
            "mode": self.acquisition_mode_var.get(),
            "results_folder": self.results_folder_var.get(),
            "analysis": self.analysis_results,
            "comments": comments,
            "validated": validated,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Ajouter à la liste des acquisitions
        self.acquisitions.append(acquisition)

        # Mettre à jour l'historique
        self._update_history()

        # Sauvegarder les données
        self.save_data()

        # Générer un rapport si l'acquisition est validée
        if validated:
            self._generate_acquisition_report()

        # Continuer ou passer à l'étape suivante
        if continue_acquisitions:
            # Réinitialiser pour une nouvelle acquisition
            self._reset_acquisition()

            # Revenir à l'onglet de configuration
            self.notebook.select(0)

            # Désactiver les onglets 2 et 3
            self.notebook.tab(1, state="disabled")
            self.notebook.tab(2, state="disabled")
        else:
            # Passer à l'étape suivante
            self.main_window.next_step()

    def _reset_acquisition(self):
        """
        Réinitialise les champs pour une nouvelle acquisition
        """
        # Réinitialiser le dossier de résultats
        self.results_folder_var = ""
        self.folder_entry.setText("")
        self.folder_info_label.setText("")

        # Réinitialiser les commentaires
        self.comments_text.clear()

        # Réinitialiser les résultats d'analyse
        self.analysis_results = None

        # Réinitialiser les graphiques
        self.graphs_widget.clear()
        self.graph_images = []

        # Réinitialiser les statistiques
        self.stats_table.setRowCount(0)

        # Réinitialiser les informations
        self.info_text.clear()
        self.info_text.setReadOnly(True)

        # Réactiver le bouton d'analyse
        self.analyze_button.setEnabled(False)

    def _update_history(self):
        """
        Met à jour l'historique des acquisitions
        """
        # Effacer l'historique précédent
        self.history_tree.clear()

        # Ajouter les acquisitions à l'historique
        for acquisition in self.acquisitions:
            # Récupérer les noms lisibles
            plate_type_name = next((pt['name'] for pt in PLATE_TYPES if pt['id'] == acquisition['plate_type']), "Inconnu")
            mode_name = next((m['name'] for m in ACQUISITION_MODES if m['id'] == acquisition['mode']), "Inconnu")

            # Statut
            status = "✓ Validée" if acquisition['validated'] else "✗ Invalidée"

            # Créer l'élément
            item = QTreeWidgetItem([str(acquisition['id']), plate_type_name, mode_name, status])

            # Définir la couleur en fonction du statut
            if acquisition['validated']:
                item.setForeground(3, Qt.green)
            else:
                item.setForeground(3, Qt.red)

            # Ajouter à l'arbre
            self.history_tree.addTopLevelItem(item)

    def _generate_acquisition_report(self):
        """
        Génère un rapport PDF pour l'acquisition actuelle
        """
        if not self.analysis_results:
            QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
            return

        try:
            # Création du générateur de rapports
            report_generator = ReportGenerator()

            # Ajout des commentaires aux résultats d'analyse
            analysis_results = dict(self.analysis_results)
            analysis_results["comments"] = self.comments_text.toPlainText().strip()

            # Génération du rapport
            report_path = report_generator.generate_acquisition_report(analysis_results)

            # Affichage du message de succès
            QMessageBox.information(self.widget, "Rapport", f"Le rapport d'acquisition a été généré avec succès:\n{report_path}")

            # Ouverture du rapport
            os.startfile(report_path)

            logger.info(f"Rapport d'acquisition généré: {report_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors de la génération du rapport:\n{str(e)}")

    def _previous_substep(self):
        """
        Passe à la sous-étape précédente
        """
        current_tab = self.notebook.index(self.notebook.select())

        if current_tab > 0:
            self.notebook.select(current_tab - 1)

    def _next_substep(self):
        """
        Passe à la sous-étape suivante
        """
        current_tab = self.notebook.index(self.notebook.select())

        if current_tab == 0:
            # De la configuration à la sélection
            self._acquisition_done()
        elif current_tab == 1:
            # De la sélection à l'analyse
            self._analyze_results()

    def _on_tab_changed(self, event):
        """
        Appelé lorsque l'onglet actif change
        """
        self._update_nav_buttons()

    def _update_nav_buttons(self):
        """
        Met à jour l'état des boutons de navigation
        """
        current_tab = self.notebook.currentIndex()

        # Bouton précédent
        if current_tab == 0:
            self.prev_substep_button.setEnabled(False)
        else:
            self.prev_substep_button.setEnabled(True)

        # Bouton suivant
        if current_tab == 0:
            self.next_substep_button.setText("Acquisition réalisée")
        elif current_tab == 1:
            self.next_substep_button.setText("Analyser les résultats")

            # Désactiver si aucun dossier valide n'est sélectionné
            if not self.results_folder_var or not os.path.exists(self.results_folder_var):
                self.next_substep_button.setEnabled(False)
            else:
                self.next_substep_button.setEnabled(True)
        else:
            self.next_substep_button.setEnabled(False)

    def validate(self):
        """
        Valide les données de l'étape 3

        Returns:
            True si les données sont valides, False sinon
        """
        if not self.acquisitions:
            QMessageBox.critical(self.widget, "Validation", "Veuillez réaliser au moins une acquisition validée avant de continuer.")
            return False

        # Vérifier qu'au moins une acquisition est validée
        valid_acquisitions = [acq for acq in self.acquisitions if acq['validated']]
        if not valid_acquisitions:
            QMessageBox.critical(self.widget, "Validation", "Veuillez valider au moins une acquisition avant de continuer.")
            return False

        return True

    def save_data(self):
        """
        Sauvegarde les données de l'étape 3 dans la session
        """
        self.main_window.session_data["acquisitions"] = self.acquisitions

        logger.info("Données de l'étape 3 sauvegardées")

    def load_data(self):
        """
        Charge les données de la session dans l'étape 3
        """
        acquisitions = self.main_window.session_data.get("acquisitions", [])

        if acquisitions:
            self.acquisitions = acquisitions

            # Mettre à jour l'ID d'acquisition
            if self.acquisitions:
                self.current_acquisition_id = max(acq['id'] for acq in self.acquisitions)

            # Mettre à jour l'historique
            self._update_history()

        logger.info("Données de l'étape 3 chargées")

    def reset(self):
        """
        Réinitialise l'étape 3
        """
        # Réinitialiser les sélections
        self.plate_type_var.set(PLATE_TYPES[0]['id'] if PLATE_TYPES else "")
        self.acquisition_mode_var.set(ACQUISITION_MODES[0]['id'] if ACQUISITION_MODES else "")
        self.results_folder_var.set("")

        # Réinitialiser les résultats
        self._reset_acquisition()

        # Réinitialiser les acquisitions
        self.acquisitions = []
        self.current_acquisition_id = 0

        # Mettre à jour l'historique
        self._update_history()

        # Désactiver les onglets 2 et 3
        self.notebook.tab(1, state="disabled")
        self.notebook.tab(2, state="disabled")

        # Sélectionner le premier onglet
        self.notebook.select(0)

        logger.info("Étape 3 réinitialisée")
