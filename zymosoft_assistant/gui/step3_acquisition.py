#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 3 de l'assistant d'installation ZymoSoft : Validation par acquisitions
Fixed version addressing widget initialization issues
"""

import os
import logging
import shutil
import threading
import time
import sys

import pandas
from PIL import Image, ImageQt
import uuid
import pandas as pd
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFrame, QFileDialog, QMessageBox,
                             QProgressBar, QStackedWidget, QWidget, QScrollArea,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QCheckBox, QRadioButton, QGroupBox, QTextEdit,
                             QTreeWidget, QTreeWidgetItem, QButtonGroup, QDialog,
                             QSplitter, QSizePolicy, QSpacerItem, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, pyqtSlot
from PyQt5.QtGui import QPixmap, QFont

from zymosoft_assistant.utils.constants import COLOR_SCHEME, PLATE_TYPES, ACQUISITION_MODES, VALIDATION_CRITERIA
from zymosoft_assistant.core.acquisition_analyzer import AcquisitionAnalyzer
from zymosoft_assistant.core.report_generator import ReportGenerator
from zymosoft_assistant.scripts.Routine_VALIDATION_ZC_18022025 import compare_enzymo_2_ref, comparaison_ZC_to_ref_v1, \
    comparaison_ZC_to_ref_v1_nanofilm
from zymosoft_assistant.scripts.getDatasFromWellResults import processWellResults, calculateLODLOQComparison
from zymosoft_assistant.core.file_validator import FileValidator
from zymosoft_assistant.scripts.processAcquisitionLog import analyzeLogFile, generateLogAnalysisReport
from .step_frame import StepFrame

logger = logging.getLogger(__name__)


class SelectionBox(QPushButton):
    """
    A custom clickable box widget that acts like a radio button.
    """
    def __init__(self, text, option_id, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.option_id = option_id
        self.setMinimumHeight(60)
        # give a special background color opacity when hovered
        self.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {COLOR_SCHEME.get('border', '#ddd')};
                border-radius: 8px;
                padding: 15px;
                background-color: white;
                color: transparent;
                text-align: center;
                font-weight: bold;
                font-size: 11pt;
            }}
            QPushButton {{
                border-color: {COLOR_SCHEME.get('primary_hover', '#0056b3')};
                color: {COLOR_SCHEME.get('primary_hover', '#0056b3')};
            }}
            QPushButton:hover {{
                background-color: rgba(0, 255, 0, 0.1);

            }}
            QPushButton:checked {{
                background-color: {COLOR_SCHEME.get('primary', '#007bff')};
                color: white;
                border-color: {COLOR_SCHEME.get('primary_dark', '#0056b3')};
            }}
        """)

    def get_id(self):
        return self.option_id


class ToggleSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(60)
        self.setMinimumHeight(30)
        self.toggled.connect(self.update_style)
        self.update_style(self.isChecked())

    def update_style(self, checked):
        if checked:
            self.setText("ON")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_SCHEME.get('success', '#28a745')};
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setText("OFF")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_SCHEME.get('secondary', '#6c757d')};
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                }}
            """)

class FolderSelectionWidget(QFrame):
    path_selected = pyqtSignal(str)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.path = ""
        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)

        errors = []

        self.path_label = QLabel("Aucun dossier sélectionné")
        self.path_label.setStyleSheet(f"""
            QLabel {{
                padding: 15px;
                border: 2px dashed {COLOR_SCHEME.get('border', '#ddd')};
                border-radius: 8px;
                background-color: {COLOR_SCHEME.get('background_light', '#f8f9fa')};
                color: {COLOR_SCHEME.get('text_secondary', '#666')};
                font-size: 11pt;
            }}
        """)
        self.path_label.setAlignment(Qt.AlignCenter)
        self.path_label.setMinimumHeight(80)
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        # Ajout d'un label pour afficher les erreurs
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_SCHEME.get('error_dark', '#721c24')};
                font-size: 10pt;
                margin-top: 5px;
            }}
        """)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        self.browse_button = QPushButton("Parcourir...")
        self.browse_button.clicked.connect(self.browse_folder)
        layout.addWidget(self.browse_button, 0, Qt.AlignRight)

    def browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier", "/")
        if path:
            self.set_path(path)
            self.path_selected.emit(path)

    def set_path(self, path):
        self.path = path
        self.path_label.setText(path)
        # The validation will set the color, so we just reset to a neutral state here
        self.path_label.setStyleSheet(f"""
            QLabel {{
                padding: 15px;
                border: 2px dashed {COLOR_SCHEME.get('border', '#ddd')};
                border-radius: 8px;
                background-color: {COLOR_SCHEME.get('background_light', '#f8f9fa')};
                color: {COLOR_SCHEME.get('text_secondary', '#666')};
                font-size: 11pt;
            }}
        """)
        # Reset error label when a new path is set
        self.error_label.setVisible(False)
        self.error_label.setText("")

    def get_path(self):
        return self.path

    def set_validity(self, is_valid, errors=None):
        if is_valid:
            self.path_label.setStyleSheet(f"""
                QLabel {{
                    padding: 15px;
                    border: 2px solid {COLOR_SCHEME.get('success', '#28a745')};
                    border-radius: 8px;
                    background-color: {COLOR_SCHEME.get('success_light', '#d4edda')};
                    color: {COLOR_SCHEME.get('success_dark', '#155724')};
                    font-size: 11pt;
                    font-weight: bold;
                }}
            """)
            self.path_label.setToolTip("")
            # Cacher le label d'erreur quand tout est valide
            self.error_label.setVisible(False)
            self.error_label.setText("")
        else:
            self.path_label.setStyleSheet(f"""
                QLabel {{
                    padding: 15px;
                    border: 2px solid {COLOR_SCHEME.get('error', '#dc3545')};
                    border-radius: 8px;
                    background-color: {COLOR_SCHEME.get('error_light', '#f8d7da')};
                    color: {COLOR_SCHEME.get('error_dark', '#721c24')};
                    font-size: 11pt;
                    font-weight: bold;
                }}
            """)
            # Mettre à jour le tooltip et le label d'erreur
            if errors:
                error_text = "\n".join(errors)
                self.path_label.setToolTip(error_text)
                self.error_label.setText(error_text)
                self.error_label.setVisible(True)
            else:
                self.path_label.setToolTip("Dossier invalide.")
                self.error_label.setText("Dossier invalide.")
                self.error_label.setVisible(True)


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

        return tab_index

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


class AcquisitionDetailsDialog(QDialog):
    """
    A dialog to show the detailed results of a past acquisition.
    """
    def __init__(self, acquisition_data, parent=None):
        super().__init__(parent)
        self.acquisition_data = acquisition_data
        self.setWindowTitle(f"Détails de l'Acquisition #{acquisition_data['id']}")
        self.setMinimumSize(1000, 700)

        # Initialize widget references
        self._initialize_widget_references()

        # Setup UI
        self.setup_ui()
        self.populate_data()

    def _initialize_widget_references(self):
        self.info_stats_tabs = None
        self.info_text = None
        self.stats_table = None
        self.well_results_table = None
        self.lod_loq_table = None
        self.log_analysis_table = None
        self.graphs_widget = None
        self.image_title_label = None
        self.image_counter_label = None
        self.prev_image_button = None
        self.next_image_button = None
        self.graph_images = []
        self.graph_titles = []
        self.current_image_index = 0

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Create analysis widgets (reusing logic from Step3Acquisition)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.info_stats_tabs = VerticalTabWidget()
        left_layout.addWidget(self.info_stats_tabs)
        self._create_info_tabs()
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self._create_image_display_widgets(right_layout)
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 600])

        # Add buttons
        button_layout = QHBoxLayout()
        self.report_button = QPushButton("Générer le rapport")
        self.report_button.clicked.connect(self._generate_report)
        button_layout.addWidget(self.report_button)
        button_layout.addStretch()
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

    def populate_data(self):
        # This method will call display methods similar to Step3Acquisition
        self._display_acquisition_info()
        self._display_statistics()
        self._display_well_results_comparison()
        self._display_lod_loq_comparison()
        self._display_log_analysis()
        self._display_graphs()
        # No need to update tab colors here as it's a static view

    # --- Copied and adapted methods from Step3Acquisition ---

    def _create_info_tabs(self):
        # This is a simplified version of _create_info_tabs from the main class
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        self.info_stats_tabs.add_tab(info_tab, "Informations")

        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
        stats_layout.addWidget(self.stats_table)
        self.info_stats_tabs.add_tab(stats_tab, "Statistiques")

        well_results_tab = QWidget()
        well_results_layout = QVBoxLayout(well_results_tab)
        self.well_results_table = QTableWidget(0, 6)
        self.well_results_table.setHorizontalHeaderLabels(["Activité (U/mL)", "Zone", "CV déploiement", "CV référence", "Différence (point de %)", "Validité"])
        well_results_layout.addWidget(self.well_results_table)
        self.info_stats_tabs.add_tab(well_results_tab, "Comparaison des gammes de calibration")

        lod_loq_tab = QWidget()
        lod_loq_layout = QVBoxLayout(lod_loq_tab)
        self.lod_loq_table = QTableWidget(0, 9)
        self.lod_loq_table.setHorizontalHeaderLabels(["Zone", "LOD Ref (ZU)", "LOD déploiement (ZU)", "LOQ Ref (ZU)", "LOQ déploiement (ZU)", "Diff LOD (point de %)", "Diff LOQ (point de %)", "Valide LOD", "Valide LOQ"])
        lod_loq_layout.addWidget(self.lod_loq_table)
        self.info_stats_tabs.add_tab(lod_loq_tab, "Comparaison LOD/LOQ")

        log_analysis_tab = QWidget()
        log_analysis_layout = QVBoxLayout(log_analysis_tab)
        self.log_analysis_table = QTableWidget(0, 2)
        self.log_analysis_table.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
        log_analysis_layout.addWidget(self.log_analysis_table)
        self.info_stats_tabs.add_tab(log_analysis_tab, "Analyse des logs")

    def _create_image_display_widgets(self, right_layout):
        images_frame = QGroupBox("Images")
        images_layout = QVBoxLayout(images_frame)
        right_layout.addWidget(images_frame)

        self.graphs_widget = QLabel()
        self.graphs_widget.setAlignment(Qt.AlignCenter)
        images_layout.addWidget(self.graphs_widget)

        self.image_title_label = QLabel()
        self.image_title_label.setAlignment(Qt.AlignCenter)
        images_layout.addWidget(self.image_title_label)

        nav_buttons_container = QWidget()
        nav_buttons_layout = QHBoxLayout(nav_buttons_container)
        images_layout.addWidget(nav_buttons_container)

        self.prev_image_button = QPushButton("< Précédent")
        self.prev_image_button.clicked.connect(self._show_previous_image)
        nav_buttons_layout.addWidget(self.prev_image_button)

        self.image_counter_label = QLabel("0/0")
        self.image_counter_label.setAlignment(Qt.AlignCenter)
        nav_buttons_layout.addWidget(self.image_counter_label)

        self.next_image_button = QPushButton("Suivant >")
        self.next_image_button.clicked.connect(self._show_next_image)
        nav_buttons_layout.addWidget(self.next_image_button)

    def _display_acquisition_info(self):
        plate_type_name = next((pt['name'] for pt in PLATE_TYPES if pt['id'] == self.acquisition_data['plate_type']), "Inconnu")
        mode_name = next((m['name'] for m in ACQUISITION_MODES if m['id'] == self.acquisition_data['mode']), "Inconnu")
        info_text = (
            f"ID: {self.acquisition_data['id']}\n"
            f"Date: {self.acquisition_data['timestamp']}\n"
            f"Type de plaque: {plate_type_name}\n"
            f"Mode: {mode_name}\n"
            f"Dossier: {self.acquisition_data['results_folder']}\n"
            f"Statut: {'Validée' if self.acquisition_data['validated'] else 'Invalidée'}\n\n"
            f"Commentaires: {self.acquisition_data['comments']}"
        )
        self.info_text.setText(info_text)

    def _display_statistics(self):
        self.stats_table.setRowCount(0)
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["Paramètre", "Valeur", "Critère de référence"])
        header = self.stats_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        analysis = self.acquisition_data.get('analysis', {})
        statistics = analysis.get("statistics", {})
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

        validation = analysis.get("validation", {})
        if validation and 'comparison' in validation:
            self._add_validation_statistics(validation)

    def _add_validation_statistics(self, validation):
        row = self.stats_table.rowCount()
        self.stats_table.insertRow(row)
        self.stats_table.setItem(row, 0, QTableWidgetItem("--- Résultats de validation ---"))

        comp = validation['comparison']
        comp_items = [
            ("Pente", f"{comp.get('slope', 0):.4f}", 'slope'),
            ("R²", f"{comp.get('r_value', 0):.4f}", 'r2'),
        ]
        for param, value, criteria_key in comp_items:
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem(param))
            value_item = QTableWidgetItem(value)
            self.stats_table.setItem(row, 1, value_item)

            criteria = VALIDATION_CRITERIA.get(criteria_key, {})
            if criteria:
                criteria_text = f"> {criteria['min']}" if criteria_key == 'r2' else f"{criteria['min']} - {criteria['max']}"
                self.stats_table.setItem(row, 2, QTableWidgetItem(criteria_text))
                try:
                    val = float(value.split(' ')[0])
                    is_valid = (val >= criteria['min'] and val <= criteria['max']) if criteria_key != 'r2' else (val >= criteria['min'])
                    value_item.setBackground(Qt.green if is_valid else Qt.red)
                except (ValueError, TypeError):
                    pass

    def _display_well_results_comparison(self):
        # This is a simplified display logic
        self.well_results_table.setRowCount(0)
        validation = self.acquisition_data.get('analysis', {}).get("validation", {})
        if "well_results_comparison" in validation:
            df = validation["well_results_comparison"]
            self.well_results_table.setRowCount(len(df))
            for i, row in df.iterrows():
                for j, col in enumerate(df.columns):
                    self.well_results_table.setItem(i, j, QTableWidgetItem(str(row[col])))

    def _display_lod_loq_comparison(self):
        self.lod_loq_table.setRowCount(0)
        validation = self.acquisition_data.get('analysis', {}).get("validation", {})
        if "lod_loq_comparison" in validation:
            df = validation["lod_loq_comparison"]
            self.lod_loq_table.setRowCount(len(df))
            for i, row in df.iterrows():
                for j, col in enumerate(df.columns):
                    self.lod_loq_table.setItem(i, j, QTableWidgetItem(str(row[col])))

    def _display_log_analysis(self):
        self.log_analysis_table.setRowCount(0)
        log_analysis = self.acquisition_data.get('analysis', {}).get("log_analysis", {})
        if log_analysis:
            for key, value in log_analysis.items():
                row = self.log_analysis_table.rowCount()
                self.log_analysis_table.insertRow(row)
                self.log_analysis_table.setItem(row, 0, QTableWidgetItem(str(key)))
                self.log_analysis_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def _display_graphs(self):
        analysis = self.acquisition_data.get('analysis', {})
        graph_paths = analysis.get("graphs", [])

        # Also look for graphs in the validation_results subfolder
        validation_dir = os.path.join(self.acquisition_data['results_folder'], "validation_results")
        if os.path.exists(validation_dir):
            for file in os.listdir(validation_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    graph_paths.append(os.path.join(validation_dir, file))

        if not graph_paths:
            self.graphs_widget.setText("Aucune image disponible")
            return

        for path in graph_paths:
            if os.path.exists(path):
                image = QPixmap(path)
                if not image.isNull():
                    self.graph_images.append(image)
                    self.graph_titles.append(os.path.basename(path))

        if self.graph_images:
            self.current_image_index = 0
            self._display_current_image()
        self._update_image_navigation()

    def _display_current_image(self):
        if 0 <= self.current_image_index < len(self.graph_images):
            image = self.graph_images[self.current_image_index]
            self.graphs_widget.setPixmap(image.scaled(self.graphs_widget.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.image_title_label.setText(self.graph_titles[self.current_image_index])

    def _update_image_navigation(self):
        total = len(self.graph_images)
        self.prev_image_button.setEnabled(self.current_image_index > 0)
        self.next_image_button.setEnabled(self.current_image_index < total - 1)
        self.image_counter_label.setText(f"{self.current_image_index + 1}/{total}")

    def _show_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self._display_current_image()
            self._update_image_navigation()

    def _show_next_image(self):
        if self.current_image_index < len(self.graph_images) - 1:
            self.current_image_index += 1
            self._display_current_image()
            self._update_image_navigation()

    def _generate_report(self):
        try:
            report_generator = ReportGenerator()

            # Prepare data for the report, including the validation status
            report_data = {
                'analysis': self.acquisition_data.get('analysis', {}),
                'comments': self.acquisition_data.get('comments', ''),
                'validated': self.acquisition_data.get('validated', False)
            }

            report_path = report_generator.generate_acquisition_report(report_data)
            QMessageBox.information(self, "Rapport Généré", f"Le rapport a été généré avec succès:\n{report_path}")
            os.startfile(report_path)
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport depuis le modal: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la génération du rapport:\n{str(e)}")


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
        self.manual_validation = {
            "time" : False,
            "dift" : False,
            "blur" : False
        }

        # Variables pour la configuration de validation
        self.do_repeta_sans_ref = False  # Toujours désactivé pour un déploiement
        self.do_compare_to_ref = True  # =1 si mode expert, =0 si mode client
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
        self.substep_indicator_label = None
        self.substep_titles = []
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
        self.info_tab_index = -1
        self.stats_tab_index = -1
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

        # Utiliser un splitter pour permettre le redimensionnement entre la partie principale et l'historique
        main_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(main_splitter)

        # --- Partie principale (en haut) ---
        main_content_frame = QFrame()
        main_content_layout = QVBoxLayout(main_content_frame)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_splitter.addWidget(main_content_frame)

        # Indicateur de sous-étape
        self.substep_indicator_label = QLabel("Configuration")
        self.substep_indicator_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 10px;")
        self.substep_indicator_label.setAlignment(Qt.AlignCenter)
        main_content_layout.addWidget(self.substep_indicator_label)

        # QStackedWidget pour les sous-étapes
        self.notebook = QStackedWidget()
        main_content_layout.addWidget(self.notebook)

        # Créer les pages du QStackedWidget
        self._create_all_pages()

        # Historique des acquisitions (en bas)
        self.history_frame = QGroupBox("Historique des acquisitions")
        history_layout = QVBoxLayout(self.history_frame)
        main_splitter.addWidget(self.history_frame)

        # Définir les tailles initiales des sections (par exemple, 3:1)
        main_splitter.setSizes([400, 150])

        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["#", "Type de plaque", "Mode", "Statut", "Date"])
        self.history_tree.itemDoubleClicked.connect(self._show_acquisition_details_modal)
        self.history_tree.setColumnWidth(0, 50)
        self.history_tree.setColumnWidth(1, 150)
        self.history_tree.setColumnWidth(2, 150)
        self.history_tree.setColumnWidth(3, 100)
        self.history_tree.setColumnWidth(4, 150)
        history_layout.addWidget(self.history_tree)

        # Barre de navigation spécifique à l'étape 3
        self._create_navigation_bar(main_layout)

        # Mise à jour de l'état des boutons de navigation
        self._update_nav_buttons()

        # Liaison des événements
        self.notebook.currentChanged.connect(self._on_substep_changed)


    def _create_all_pages(self):
        """
        Crée toutes les pages du QStackedWidget et initialise les titres.
        """
        self.substep_titles = [
            "1. Configuration",
            "2. Sélection des résultats",
            "3. Analyse des résultats"
        ]

        # Page 1: Configuration de l'acquisition
        self.config_frame = QWidget()
        self.config_layout = QVBoxLayout(self.config_frame)
        self.notebook.addWidget(self.config_frame)
        self._create_config_widgets()

        # Page 2: Sélection des résultats
        self.selection_frame = QWidget()
        self.selection_layout = QVBoxLayout(self.selection_frame)
        self.notebook.addWidget(self.selection_frame)
        self._create_selection_widgets()

        # Page 3: Analyse des résultats
        self.analysis_frame = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_frame)
        self.notebook.addWidget(self.analysis_frame)
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
        # The report button is removed from here to avoid confusion.
        # Report is now generated automatically on finalization or from the details modal.
        # self.report_button = QPushButton("Générer rapport d'acquisition")
        # self.report_button.clicked.connect(self._generate_acquisition_report)
        # self.report_button.setVisible(False)
        # nav_layout.addWidget(self.report_button)

        nav_layout.addStretch(1)

        self.next_substep_button = QPushButton("Étape suivante")
        self.next_substep_button.clicked.connect(self._next_substep)
        self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
        nav_layout.addWidget(self.next_substep_button, 0, Qt.AlignRight)

    def _create_config_widgets(self):
        """
        Crée les widgets pour la configuration de l'acquisition avec un design amélioré.
        """
        # Description
        description_label = QLabel("Configurez les paramètres de l'acquisition à valider.")
        description_label.setWordWrap(True)
        self.config_layout.addWidget(description_label)
        self.config_layout.addSpacing(20)

        # Layout principal pour les boîtes de sélection
        options_layout = QHBoxLayout()
        options_layout.setSpacing(20)
        self.config_layout.addLayout(options_layout)

        # --- Groupe 1: Type de plaque ---
        plate_type_groupbox = QGroupBox("Type de plaque (Nano film ou Micro dépôt)")
        plate_type_layout = QVBoxLayout(plate_type_groupbox)
        self.plate_type_group = QButtonGroup(self)
        self.plate_type_group.setExclusive(True)

        for plate_type in PLATE_TYPES:
            box = SelectionBox(plate_type['name'], plate_type['id'])
            if self.plate_type_var == plate_type['id']:
                box.setChecked(True)
            box.toggled.connect(lambda checked, b=box: self._on_plate_type_changed(checked, b))
            plate_type_layout.addWidget(box)
            self.plate_type_group.addButton(box)
        options_layout.addWidget(plate_type_groupbox)

        # --- Groupe 2: Mode d'acquisition ---
        mode_groupbox = QGroupBox("Mode d'acquisition (Client ou Expert)")
        mode_layout = QVBoxLayout(mode_groupbox)
        self.acquisition_mode_group = QButtonGroup(self)
        self.acquisition_mode_group.setExclusive(True)

        for mode in ACQUISITION_MODES:
            box = SelectionBox(mode['name'], mode['id'])
            if self.acquisition_mode_var == mode['id']:
                box.setChecked(True)
            box.toggled.connect(lambda checked, b=box: self._on_acquisition_mode_changed(checked, b))
            mode_layout.addWidget(box)
            self.acquisition_mode_group.addButton(box)
        options_layout.addWidget(mode_groupbox)

        self.config_layout.addStretch(1)

        # --- Instructions ---
        instructions_frame = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout(instructions_frame)
        instructions_text = (
            "1. Sélectionnez le type de plaque et le mode d'acquisition ci-dessus.\n"
            "2. Lancez ZymoSoft et réalisez une acquisition en utilisant ces mêmes paramètres.\n"
            "3. Une fois l'acquisition terminée, cliquez sur 'Étape suivante' pour sélectionner les résultats."
        )
        instructions_label = QLabel(instructions_text)
        instructions_label.setWordWrap(True)
        instructions_layout.addWidget(instructions_label)
        self.config_layout.addWidget(instructions_frame)

    def _create_selection_widgets(self):
        """
        Crée les widgets pour la sélection des résultats, avec un design amélioré.
        """
        # Description
        description_label = QLabel("Sélectionnez les dossiers contenant les résultats de l'acquisition et  de référence.")
        description_label.setWordWrap(True)
        self.selection_layout.addWidget(description_label)
        self.selection_layout.addSpacing(10)

        # Layout pour les sélecteurs de dossier
        folder_selection_layout = QHBoxLayout()
        self.results_folder_widget = FolderSelectionWidget("Dossier de résultats d'acquisition")
        self.results_folder_widget.path_selected.connect(self._on_results_folder_selected)
        folder_selection_layout.addWidget(self.results_folder_widget)

        self.reference_folder_widget = FolderSelectionWidget("Dossier de référence")
        self.reference_folder_widget.path_selected.connect(self._on_reference_folder_selected)
        folder_selection_layout.addWidget(self.reference_folder_widget)
        self.selection_layout.addLayout(folder_selection_layout)

        # Options de validation
        validation_frame = QGroupBox("Options de validation")
        validation_layout = QGridLayout(validation_frame)
        self.selection_layout.addWidget(validation_frame)

        # Option 1
        validation_layout.addWidget(QLabel("Comparer aux références (mode expert)"), 0, 0)
        self.compare_to_ref_switch = ToggleSwitch()
        self.compare_to_ref_switch.setChecked(self.do_compare_to_ref)
        self.compare_to_ref_switch.toggled.connect(self._on_compare_to_ref_toggled)
        validation_layout.addWidget(self.compare_to_ref_switch, 0, 1, Qt.AlignLeft)

        # Option 2
        validation_layout.addWidget(QLabel("Comparer les données enzymatiques aux références"), 1, 0)
        self.compare_enzymo_to_ref_switch = ToggleSwitch()
        self.compare_enzymo_to_ref_switch.setChecked(self.do_compare_enzymo_to_ref)
        self.compare_enzymo_to_ref_switch.toggled.connect(self._on_compare_enzymo_to_ref_toggled)
        validation_layout.addWidget(self.compare_enzymo_to_ref_switch, 1, 1, Qt.AlignLeft)

        self.selection_layout.addStretch(1)

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

        # Utiliser des onglets verticaux pour les informations, statistiques et comparaisons
        self.info_stats_tabs = VerticalTabWidget()
        left_layout.addWidget(self.info_stats_tabs, 1)  # stretch factor = 1 pour prendre tout l'espace

        # Create all tabs for the left panel
        self._create_info_tabs()

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

    def _create_info_tabs(self):
        """
        Create all information tabs in the left panel using VerticalTabWidget.
        """
        # Onglet Informations
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        self.info_tab_index = self.info_stats_tabs.add_tab(info_tab, "Informations")

        # Onglet Statistiques
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        stats_layout.addWidget(self.stats_table)
        self.stats_tab_index = self.info_stats_tabs.add_tab(stats_tab, "Statistiques")

        # Onglet Comparaison WellResults
        well_results_tab = QWidget()
        well_results_layout = QVBoxLayout(well_results_tab)
        self.well_results_info_label = QLabel("")
        self.well_results_info_label.setWordWrap(True)
        well_results_layout.addWidget(self.well_results_info_label)
        self.well_results_table = QTableWidget(0, 6)
        self.well_results_table.setHorizontalHeaderLabels(["Activité (U/mL)", "Zone", "CV déploiement", "CV référence", "Différence (point de %)", "Validité"])
        self.well_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        well_results_layout.addWidget(self.well_results_table)
        self.well_results_tab_index = self.info_stats_tabs.add_tab(well_results_tab, "Comparaison des gammes de calibration")

        # Onglet Comparaison LOD/LOQ
        lod_loq_tab = QWidget()
        lod_loq_layout = QVBoxLayout(lod_loq_tab)
        self.lod_loq_info_label = QLabel("")
        self.lod_loq_info_label.setWordWrap(True)
        lod_loq_layout.addWidget(self.lod_loq_info_label)
        self.lod_loq_table = QTableWidget(0, 9)
        self.lod_loq_table.setHorizontalHeaderLabels(["Zone", "LOD Ref (ZU)", "LOD déploiement (ZU)", "LOQ Ref (ZU)", "LOQ déploiement (ZU)", "Diff LOD (point de %)", "Diff LOQ (point de %)", "Valide LOD", "Valide LOQ"])
        self.lod_loq_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lod_loq_layout.addWidget(self.lod_loq_table)
        self.lod_loq_tab_index = self.info_stats_tabs.add_tab(lod_loq_tab, "Comparaison LOD/LOQ")

        # Onglet Analyse des logs
        log_analysis_tab = QWidget()
        log_analysis_layout = QVBoxLayout(log_analysis_tab)
        self.log_info_label = QLabel("Aucune analyse de log disponible.")
        self.log_info_label.setWordWrap(True)
        log_analysis_layout.addWidget(self.log_info_label)
        self.log_analysis_table = QTableWidget(0, 2)
        self.log_analysis_table.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
        self.log_analysis_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        log_analysis_layout.addWidget(self.log_analysis_table)
        self.log_analysis_tab_index = self.info_stats_tabs.add_tab(log_analysis_tab, "Analyse des logs")

    def _update_tab_colors(self):
        """
        Met à jour les couleurs des onglets verticaux en fonction des résultats de validation.
        """
        try:
            if not hasattr(self, 'info_stats_tabs') or not self.info_stats_tabs:
                return

            # Statut général (par défaut: succès)
            general_status = True
            if self.analysis_results and self.analysis_results.get("validation", {}).get("global_status") is False:
                general_status = False

            self.info_stats_tabs.update_tab_status(self.info_tab_index, general_status)
            self.info_stats_tabs.update_tab_status(self.stats_tab_index, general_status)

            # Statut pour la comparaison WellResults
            well_results_status = not self._has_well_results_errors()
            self.info_stats_tabs.update_tab_status(self.well_results_tab_index, well_results_status)

            # Statut pour la comparaison LOD/LOQ
            lod_loq_status = not self._has_lod_loq_errors()
            self.info_stats_tabs.update_tab_status(self.lod_loq_tab_index, lod_loq_status)

            # Statut pour l'analyse des logs
            log_status = "log_analysis_error" not in self.analysis_results if self.analysis_results else None
            self.info_stats_tabs.update_tab_status(self.log_analysis_tab_index, log_status)

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
    def _on_plate_type_changed(self, checked, box):
        """
        Appelé lorsque le type de plaque est modifié.
        """
        if checked:
            self.plate_type_var = box.get_id()
            logger.info(f"Type de plaque sélectionné: {self.plate_type_var}")
            # Revalider les dossiers si un chemin a été sélectionné
            if self.results_folder_var or self.reference_folder_var:
                self._validate_folders()

    def _on_acquisition_mode_changed(self, checked, box):
        """
        Appelé lorsque le mode d'acquisition est modifié.
        """
        if checked:
            self.acquisition_mode_var = box.get_id()
            logger.info(f"Mode d'acquisition sélectionné: {self.acquisition_mode_var}")
            # Revalider les dossiers si un chemin a été sélectionné
            if self.results_folder_var or self.reference_folder_var:
                self._validate_folders()

    def _on_results_folder_selected(self, path):
        self.results_folder_var = path
        self._validate_folders()

    def _on_reference_folder_selected(self, path):
        self.reference_folder_var = path
        self._validate_folders()

    def _validate_folders(self):
        """
        Valide les dossiers de résultats et de référence et met à jour l'interface.
        """
        # Réinitialiser les erreurs
        results_errors = []
        ref_errors = []

        is_expert = self.acquisition_mode_var == 'expert'
        plate_type = self.plate_type_var

        # Validation du dossier de résultats
        if self.results_folder_var:
            results_validation = FileValidator.validate_acquisition_folder(self.results_folder_var, is_expert, plate_type)
            if not results_validation["is_valid"]:
                results_errors.extend(results_validation["errors"])

        # Validation du dossier de référence
        if self.reference_folder_var:
            ref_validation = FileValidator.validate_acquisition_folder(self.reference_folder_var, is_expert, plate_type)
            if not ref_validation["is_valid"]:
                ref_errors.extend(ref_validation["errors"])

        # Vérifier si les dossiers sont identiques
        if self.results_folder_var and self.reference_folder_var and \
           os.path.normpath(self.results_folder_var) == os.path.normpath(self.reference_folder_var):
            error_msg = "Le dossier d'acquisition et de référence ne peuvent pas être identiques."
            if error_msg not in results_errors:
                results_errors.append(error_msg)
            if error_msg not in ref_errors:
                ref_errors.append(error_msg)

        # Mettre à jour l'affichage
        if self.results_folder_var:
            self.results_folder_widget.set_validity(len(results_errors) == 0, results_errors)

        if self.reference_folder_var:
            self.reference_folder_widget.set_validity(len(ref_errors) == 0, ref_errors)

        self._update_nav_buttons()

    def _on_compare_to_ref_toggled(self, checked):
        """
        Appelé lorsque la case à cocher pour comparer aux références est modifiée
        """
        try:
            self.do_compare_to_ref = checked
            self._validate_folders()  # Re-valider les dossiers
            logger.info(f"Option de comparaison aux références: {checked}")
        except Exception as e:
            logger.error(f"Erreur dans _on_compare_to_ref_toggled: {str(e)}", exc_info=True)

    def _on_compare_enzymo_to_ref_toggled(self, checked):
        """
        Appelé lorsque la case à cocher pour comparer les données enzymatiques est modifiée
        """
        try:
            self.do_compare_enzymo_to_ref = checked
            self._validate_folders()  # Re-valider les dossiers
            logger.info(f"Option de comparaison des données enzymatiques: {checked}")
        except Exception as e:
            logger.error(f"Erreur dans _on_compare_enzymo_to_ref_toggled: {str(e)}", exc_info=True)

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

            step2_data = self.main_window.session_data.get("step2_checks", {})
            zymosoft_path = step2_data.get("zymosoft_path")
            if zymosoft_path and os.path.isdir(os.path.join(zymosoft_path, '..', 'Diag', 'Temp')):
                default_log_path = os.path.join(zymosoft_path, '..', 'Diag', 'Temp')
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
                ("Pente", f"{comp.get('slope', 0):.4f}", 'slope'),
                ("Ordonnée à l'origine", f"{comp.get('intercept', 0):.4f}", 'intercept'),
                ("R²", f"{comp.get('r_value', 0):.4f}", 'r2'),
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
            current_index = self.notebook.currentIndex()
            if current_index > 0:
                self.notebook.setCurrentIndex(current_index - 1)
        except Exception as e:
            logger.error(f"Erreur dans _previous_substep: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _next_substep(self):
        """
        Passe à la sous-étape suivante ou exécute l'action appropriée selon la page active.
        """
        try:
            if not self.notebook:
                logger.error("Erreur dans _next_substep: self.notebook est None")
                QMessageBox.critical(self.widget, "Erreur",
                                     "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                return

            current_index = self.notebook.currentIndex()

            if current_index == 0:  # Page de Configuration
                self.notebook.setCurrentIndex(1)
            elif current_index == 1:  # Page de Sélection des résultats
                if not self.results_folder_var or not os.path.exists(self.results_folder_var):
                    QMessageBox.warning(self.widget, "Attention",
                                        "Veuillez d'abord sélectionner un dossier de résultats valide.")
                    return
                self._analyze_results()
            elif current_index == 2:  # Page d'Analyse
                self._show_comments_dialog("validate_next", True, False)
        except Exception as e:
            logger.error(f"Erreur dans _next_substep: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _acquisition_done(self):
        """
        Appelé lorsque l'utilisateur a terminé l'acquisition (obsolète avec la nouvelle navigation,
        mais conservé pour la logique de _next_substep).
        """
        try:
            if not self.notebook:
                logger.error("Erreur dans _acquisition_done: self.notebook est None")
                return
            self.notebook.setCurrentIndex(1)
        except Exception as e:
            logger.error(f"Erreur dans _acquisition_done: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue :\n{str(e)}")

    def _on_substep_changed(self, index):
        """
        Appelé lorsque la page active du QStackedWidget change.
        """
        try:
            if self.substep_indicator_label and index < len(self.substep_titles):
                # Simplifier le titre pour ne montrer que le nom de l'étape
                title = self.substep_titles[index].split('. ')[-1]
                self.substep_indicator_label.setText(title)
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans _on_substep_changed: {str(e)}", exc_info=True)

    def _show_acquisition_details_modal(self, item, column):
        """
        Affiche une boîte de dialogue avec les détails d'une acquisition de l'historique.
        """
        try:
            acquisition_id = int(item.text(0))
            acquisition_data = next((acq for acq in self.acquisitions if acq['id'] == acquisition_id), None)

            if acquisition_data:
                dialog = AcquisitionDetailsDialog(acquisition_data, self.widget)
                dialog.exec_()
            else:
                QMessageBox.warning(self.widget, "Erreur", f"Impossible de trouver les données pour l'acquisition #{acquisition_id}.")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du modal de détails: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue: {e}")

    def _update_nav_buttons(self):
        """
        Met à jour l'état des boutons de navigation en fonction de la page active.
        """
        try:
            if not self.notebook:
                logger.error("Erreur dans _update_nav_buttons: self.notebook est None")
                return

            current_index = self.notebook.currentIndex()

            # Gestion du bouton précédent
            if self.prev_substep_button:
                self.prev_substep_button.setEnabled(current_index > 0)

            # Gestion des boutons d'action supplémentaires (visibles uniquement sur la page d'analyse)
            is_analysis_page = (current_index == 2)
            if self.validate_continue_button:
                self.validate_continue_button.setVisible(is_analysis_page)
            if self.invalidate_button:
                self.invalidate_button.setVisible(is_analysis_page)
            # The main report button is no longer used here.
            # if self.report_button:
            #     self.report_button.setVisible(is_analysis_page)

            # Gestion du bouton suivant
            if not self.next_substep_button:
                return

            if current_index == 0:  # Page de Configuration
                self.next_substep_button.setText("Étape suivante")
                self.next_substep_button.setEnabled(True)
                self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
            elif current_index == 1:  # Page de Sélection des résultats
                self.next_substep_button.setText("Analyser les résultats")
                results_folder_valid = bool(self.results_folder_var and self.results_folder_widget.path_label.toolTip() == "")
                reference_folder_required = self.do_compare_to_ref or self.do_compare_enzymo_to_ref

                can_analyze = results_folder_valid
                if reference_folder_required:
                    reference_folder_valid = bool(self.reference_folder_var and self.reference_folder_widget.path_label.toolTip() == "")
                    can_analyze = can_analyze and reference_folder_valid

                self.next_substep_button.setEnabled(can_analyze)
                if can_analyze:
                    self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
                else:
                    self.next_substep_button.setStyleSheet(f"background-color: {COLOR_SCHEME['disabled']}; color: white;")
            elif current_index == 2:  # Page d'Analyse
                self.next_substep_button.setText("Valider et terminer l'acquisition")
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

            options_layout = QVBoxLayout()
            options_layout.setAlignment(Qt.AlignLeft)
            self.check_acquisition_time = QCheckBox("Temps d'acquisition correct")
            self.check_acquisition_time.setChecked(False)
            options_layout.addWidget(self.check_acquisition_time)
            self.check_drift = QCheckBox("Drift acceptable")
            self.check_drift.setChecked(False)
            options_layout.addWidget(self.check_drift)
            self.check_blurriness = QCheckBox("Flou acceptable")
            self.check_blurriness.setChecked(False)
            options_layout.addWidget(self.check_blurriness)

            layout.addLayout(options_layout)

            # Champ de commentaires
            comments_label = QLabel("Commentaires:")
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
                # Vérifier les options supplémentaires , si l'utilisateur voulais valider l'acquisition il doit cocher toutes les options supplémentaires si il voulais invalider rien ne l'oblige à cocher les options
                if action_type == "validate_continue":
                    if not (self.check_acquisition_time.isChecked() and self.check_drift.isChecked() and self.check_blurriness.isChecked()):
                        QMessageBox.warning(self.widget, "Attention",
                                            "Veuillez vérifier que toutes les options sont cochées avant de valider l'acquisition.")
                        return False
                elif action_type == "validate_next":
                    if not (self.check_acquisition_time.isChecked() and self.check_drift.isChecked() and self.check_blurriness.isChecked()):
                        QMessageBox.warning(self.widget, "Attention",
                                            "Veuillez vérifier que toutes les options sont cochées avant de valider l'acquisition.")
                        return False

                # stocker les options supplémentaires dans l'analyse sous le nom "manuel_verfications"
                self.manual_validation = {
                    "time": self.check_acquisition_time.isChecked(),
                    "drift": self.check_drift.isChecked(),
                    "blur": self.check_blurriness.isChecked()
                }
                self.analysis_results['manual_validation'] = self.manual_validation


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
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "manual_validations": self.manual_validation
            }
            self.acquisitions.append(acquisition)
            self._update_history()
            self.save_data()

            # Generate the report automatically upon finalizing, with the correct status
            self._generate_acquisition_report(validated)

            # copie the analised log file to the results folder
            if self.results_folder_var:
                from zymosoft_assistant.scripts.processAcquisitionLog import getLogFile, analyzeLogFile

                step2_data = self.main_window.session_data.get("step2_checks", {})
                log_file_path = None
                zymosoft_path = step2_data.get("zymosoft_path")
                if zymosoft_path and os.path.isdir(os.path.join(zymosoft_path, '..', 'Diag', 'Temp')):
                    default_log_path = os.path.join(zymosoft_path, '..', 'Diag', 'Temp')
                    log_file_path = getLogFile(default_log_path)

                if log_file_path and os.path.exists(log_file_path):
                    try:
                        shutil.copy(log_file_path, self.results_folder_var)
                        logger.info(f"Fichier de log copié dans le dossier des résultats: {self.results_folder_var}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la copie du fichier de log: {str(e)}", exc_info=True)

            if continue_acquisitions:
                self._reset_acquisition()
                if not self.notebook:
                    logger.error("Erreur dans _finalize_acquisition: self.notebook est None")
                    QMessageBox.critical(self.widget, "Erreur",
                                         "Une erreur interne est survenue. Veuillez redémarrer l'application.")
                    return
                self.notebook.setCurrentIndex(0)
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

    def _generate_acquisition_report(self, validated_status):
        """
        Génère un rapport PDF pour l'acquisition actuelle, en utilisant le statut de validation fourni.
        """
        try:
            if not self.analysis_results:
                QMessageBox.critical(self.widget, "Erreur", "Aucun résultat d'analyse disponible.")
                return

            report_generator = ReportGenerator()

            # Construire le dictionnaire de données pour le rapport
            report_data = {
                'installation_id': self.main_window.session_data.get('installation_id', 'Inconnu'),
                'acquisition_id': self.current_acquisition_id,
                'plate_type': self.plate_type_var,
                'acquisition_mode': self.acquisition_mode_var,
                'folder' : self.results_folder_var,
                'reference_folder': self.reference_folder_var,
                'analysis': self.analysis_results,
                'comments': self.comments_var,
                'validated': validated_status,
                'manual_validation': self.manual_validation
            }

            step1_checks = self.main_window.session_data.get('client_info', {})

            report_path = report_generator.generate_acquisition_report(report_data, step1_checks)
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
            # Mettre à jour l'historique au cas où des données auraient été chargées
            self._update_history()

            # Mettre à jour les couleurs des onglets si des résultats d'analyse sont disponibles
            if hasattr(self, 'analysis_results') and self.analysis_results:
                self._update_tab_colors()

            # Mettre à jour les boutons de navigation
            self._update_nav_buttons()
        except Exception as e:
            logger.error(f"Erreur dans on_show: {str(e)}", exc_info=True)


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
