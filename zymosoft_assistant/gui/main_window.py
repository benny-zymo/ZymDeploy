#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de la fenêtre principale de l'assistant d'installation ZymoSoft
"""

import os
import sys
import logging
import uuid
import datetime
import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QProgressBar, QMessageBox,
                             QFileDialog, QStackedWidget, QAction, QMenu, QMenuBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from zymosoft_assistant.utils.constants import COLOR_SCHEME, APP_CONFIG, STEPS, PLATE_TYPES, ACQUISITION_MODES
from zymosoft_assistant.utils.helpers import create_empty_session, save_session_data, load_session_data
from .step1_info import Step1Info
from .step2_checks import Step2Checks
from .step3_acquisition import Step3Acquisition
from .step4_closure import Step4Closure

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Classe principale de l'interface graphique de l'assistant d'installation ZymoSoft
    """

    def __init__(self):
        """
        Initialise la fenêtre principale de l'application
        """
        super().__init__()

        self.setWindowTitle(APP_CONFIG['title'])
        self.resize(APP_CONFIG['window_width'], APP_CONFIG['window_height'])
        self.setMinimumSize(APP_CONFIG['min_width'], APP_CONFIG['min_height'])
        self.initial_load = True

        # Icône de l'application (si disponible)
        if APP_CONFIG['icon_path'] and os.path.exists(APP_CONFIG['icon_path']):
            self.setWindowIcon(QIcon(APP_CONFIG['icon_path']))

        # Initialisation des données de session
        self.session_data = create_empty_session()

        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        # Supprimer toutes les marges du layout principal
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Création de l'interface
        self.create_widgets()
        self.create_menu()

        # Initialisation des étapes
        self.steps = []
        self.current_step_index = 0
        self.initialize_steps()

        # Affichage de la première étape
        self.show_step(0)

        logger.info("Fenêtre principale initialisée")

    def get_style_sheet(self):
        """
        Retourne la feuille de style CSS pour l'application
        """
        return f"""
            /* Style global - fond blanc uniforme */
            QMainWindow {{
                background-color: {COLOR_SCHEME['background']};
            }}

            QWidget {{
                color: {COLOR_SCHEME['text']};
                background-color: {COLOR_SCHEME['background']};
            }}

            QLabel {{
                background-color: transparent;
            }}

            QLabel[header="true"] {{
                font-size: 18pt;
                font-weight: bold;
                color: {COLOR_SCHEME['primary']};
            }}

            QLabel[subheader="true"] {{
                font-size: 12pt;
                font-weight: bold;
            }}

            QLabel[success="true"] {{
                color: {COLOR_SCHEME['success']};
            }}

            QLabel[error="true"] {{
                color: {COLOR_SCHEME['error']};
            }}

            QLabel[warning="true"] {{
                color: {COLOR_SCHEME['warning']};
            }}

            QPushButton {{
                background-color: {COLOR_SCHEME['primary']};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }}

            QPushButton:hover {{
                background-color: {COLOR_SCHEME['primary_hover']};
            }}

            QPushButton:pressed {{
                background-color: {COLOR_SCHEME['primary_pressed']};
            }}

            QPushButton:disabled {{
                background-color: {COLOR_SCHEME['disabled']};
            }}

            /* Menu bar - bordure bas et fond uniforme */
            QMenuBar {{
background-color: #f5f6fa;                
border: none;
                color: {COLOR_SCHEME['text']};
                padding: 0px;
                margin: 0px;
                border-top: 1px solid {COLOR_SCHEME['border']};
                border-bottom: 1px solid {COLOR_SCHEME['border']};
            }}

            QMenuBar::item {{
                background-color: transparent;
                padding: 5px 10px;
            }}

            QMenuBar::item:selected {{
                background-color: {COLOR_SCHEME['primary']};
                color: white;
            }}

            /* Sidebar (colonne de gauche) */
            #leftColumn {{
                background-color: {COLOR_SCHEME['background']};
                border-right: 1px solid {COLOR_SCHEME['border']};
                margin: 0px;
                padding: 0px;
            }}

            /* Barre de progression */
            QProgressBar {{
                border: none;
                background-color: {COLOR_SCHEME['surface']};
                text-align: center;
                height: 20px;
                margin: 10px;
            }}

            QProgressBar::chunk {{
                background-color: {COLOR_SCHEME['primary']};
            }}

            /* Indicateurs d'étapes - prennent toute la largeur */
            #stepIndicatorContainer {{
                background-color: {COLOR_SCHEME['background']};
                border: none;
                border_bottom: 1px solid {COLOR_SCHEME['border']};
                border-right: 3px solid transparent;
                margin: 0px;
                padding: 0px;
            }}

            #stepIndicatorContainer[status="completed"] {{
                background-color: {COLOR_SCHEME['background']};
                border-right: 3px solid {COLOR_SCHEME['success']};
            }}

            #stepIndicatorContainer[status="current"] {{
                background-color: {COLOR_SCHEME['background']};
                border-right: 3px solid orange;
            }}

            #stepIndicatorContainer[status="invalid"] {{
                background-color: {COLOR_SCHEME['background']};
                border-right: 3px solid {COLOR_SCHEME['error']};
            }}

            #stepIndicatorContainer[status="pending"] {{
                background-color: {COLOR_SCHEME['background']};
                border-right: 3px solid gray;
            }}

            #stepIndicator {{
                font-size: 14pt;
                font-weight: bold;
                color: {COLOR_SCHEME['text']};
                background-color: transparent;
            }}

            #stepIndicator[status="completed"] {{
                color: {COLOR_SCHEME['success']};
            }}

            #stepIndicator[status="current"] {{
                color: {COLOR_SCHEME['primary']};
            }}

            #stepIndicator[status="invalid"] {{
                color: {COLOR_SCHEME['error']};
            }}

            #stepIndicator[status="pending"] {{
                color: {COLOR_SCHEME['text_secondary']};
            }}

            /* Colonne de droite - sans padding */
            #rightColumn {{
                background-color: {COLOR_SCHEME['background']};
                margin: 0px;
                padding: 0px;
            }}

            /* En-tête de l'étape */
            #topRow {{
                background-color: {COLOR_SCHEME['background']};
                border-bottom: 1px solid {COLOR_SCHEME['border']};
                padding: 15px;
                margin: 0px;
            }}

            #stepTitle {{
                font-size: 14pt;
                font-weight: bold;
                color: {COLOR_SCHEME['primary']};
                margin: 0px;
                padding-top: 15px;
                padding-left: 15px;
            }}

            #stepDescription {{
                font-size: 10pt;
                color: {COLOR_SCHEME['text_secondary']};
                margin-top: 1px;

                padding: 15px;
                padding-top: 0px;
            }}

            /* Conteneur des étapes */
            #stepContainer {{
                background-color: {COLOR_SCHEME['background']};
                margin: 0px;
                padding: 0px;
            }}

            /* Barre de navigation */
            #navigationBar {{
                background-color: {COLOR_SCHEME['background']};
                border-top: 1px solid {COLOR_SCHEME['border']};
                padding: 15px;
                margin: 0px;
            }}

            /* Barre de statut */
            #statusBar {{
                background-color: {COLOR_SCHEME['background']};
                border-top: 1px solid {COLOR_SCHEME['border']};
                padding: 5px 15px;
                margin: 0px;
            }}

            /* Barre de progression standard */
            QProgressBar {{
                border: none;
                background-color: {COLOR_SCHEME['surface']};
                text-align: center;
                border-radius: 25px;
            }}

            QProgressBar::chunk {{
                background-color: {COLOR_SCHEME['primary']};
                border-radius: 25px;
            }}
        """

    def create_widgets(self):
        """
        Crée les widgets de la fenêtre principale
        """
        # Appliquer la feuille de style
        self.setStyleSheet(self.get_style_sheet())

        # Layout principal horizontal (colonnes) - sans espacement
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        main_horizontal_layout.setSpacing(0)
        self.main_layout.addLayout(main_horizontal_layout)

        # Sidebar (colonne de gauche)
        left_column = QWidget()
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(0)
        left_column.setFixedWidth(80)  # Largeur un peu plus large pour une vraie sidebar
        left_column.setObjectName("leftColumn")
        main_horizontal_layout.addWidget(left_column)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumWidth(60)
        left_column_layout.addWidget(self.progress_bar)
        left_column_layout.addSpacing(10)

        # Indicateurs d'étapes - prennent toute la largeur disponible
        self.step_indicators = []
        for i, step in enumerate(STEPS):
            indicator_container = QWidget()
            indicator_container.setObjectName("stepIndicatorContainer")
            indicator_container.setFixedHeight(60)
            indicator_layout = QVBoxLayout(indicator_container)
            indicator_layout.setContentsMargins(0, 0, 0, 0)
            indicator_layout.setAlignment(Qt.AlignCenter)

            indicator = QLabel(f"{i + 1}")
            indicator.setAlignment(Qt.AlignCenter)
            indicator.setObjectName("stepIndicator")
            indicator_layout.addWidget(indicator)

            left_column_layout.addWidget(indicator_container)
            self.step_indicators.append(indicator)

        left_column_layout.addStretch(1)

        # Colonne de droite (principale) - sans espacement
        right_column = QWidget()
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_column_layout.setSpacing(0)
        right_column.setObjectName("rightColumn")
        main_horizontal_layout.addWidget(right_column, 1)  # Prend tout l'espace restant

        # En-tête avec le nom de l'étape et sa description
        top_row = QWidget()
        top_row_layout = QVBoxLayout(top_row)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row.setObjectName("topRow")
        right_column_layout.addWidget(top_row)

        self.step_title_label = QLabel()
        self.step_title_label.setObjectName("stepTitle")
        top_row_layout.addWidget(self.step_title_label)

        self.step_description_label = QLabel()
        self.step_description_label.setObjectName("stepDescription")
        top_row_layout.addWidget(self.step_description_label)

        # Conteneur principal pour les étapes - sans espacement
        self.step_container = QStackedWidget()
        self.step_container.setObjectName("stepContainer")
        right_column_layout.addWidget(self.step_container, 1)

        # Barre de navigation en bas
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_widget.setObjectName("navigationBar")
        right_column_layout.addWidget(nav_widget)

        self.prev_button = QPushButton("Précédent")
        self.prev_button.clicked.connect(self.previous_step)
        nav_layout.addWidget(self.prev_button)

        nav_layout.addStretch(1)

        self.next_button = QPushButton("Suivant")
        self.next_button.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_button)

        # Barre de statut (footer) - sans espacement
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_widget.setObjectName("statusBar")
        self.main_layout.addWidget(status_widget)

        self.status_label = QLabel("Prêt")
        status_layout.addWidget(self.status_label)

    def create_menu(self):
        """
        Crée le menu de l'application
        """
        menubar = self.menuBar()

        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")

        new_session_action = QAction("Nouvelle session", self)
        new_session_action.triggered.connect(self.new_session)
        file_menu.addAction(new_session_action)

        load_session_action = QAction("Charger session", self)
        load_session_action.triggered.connect(self.load_session)
        file_menu.addAction(load_session_action)

        save_session_action = QAction("Sauvegarder session", self)
        save_session_action.triggered.connect(self.save_session)
        file_menu.addAction(save_session_action)

        file_menu.addSeparator()

        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.quit_app)
        file_menu.addAction(quit_action)

        # Menu Aide
        help_menu = menubar.addMenu("Aide")

        doc_action = QAction("Documentation", self)
        doc_action.triggered.connect(self.show_documentation)
        help_menu.addAction(doc_action)

        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def initialize_steps(self):
        """
        Initialise les différentes étapes de l'assistant
        """
        logger.info("Initialisation des étapes de l'assistant")

        try:
            # Étape 1: Saisie des informations client
            logger.info("Initialisation de l'étape 1: Saisie des informations client")
            step1 = Step1Info(self.step_container, self)
            self.step_container.addWidget(step1.widget)
            self.steps.append(step1)
            logger.info("Étape 1 initialisée avec succès")

            # Étape 2: Vérifications pré-validation
            logger.info("Initialisation de l'étape 2: Vérifications pré-validation")
            step2 = Step2Checks(self.step_container, self)
            self.step_container.addWidget(step2.widget)
            self.steps.append(step2)
            logger.info("Étape 2 initialisée avec succès")

            # Étape 3: Validation par acquisitions
            logger.info("Initialisation de l'étape 3: Validation par acquisitions")
            step3 = Step3Acquisition(self.step_container, self)
            self.step_container.addWidget(step3.widget)
            self.steps.append(step3)
            logger.info("Étape 3 initialisée avec succès")

            # Étape 4: Clôture de l'installation
            logger.info("Initialisation de l'étape 4: Clôture de l'installation")
            step4 = Step4Closure(self.step_container, self)
            self.step_container.addWidget(step4.widget)
            self.steps.append(step4)
            logger.info("Étape 4 initialisée avec succès")

            logger.info("Toutes les étapes ont été initialisées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des étapes: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur d'initialisation",
                                 f"Une erreur est survenue lors de l'initialisation des étapes:\n{str(e)}\n\n"
                                 f"L'application risque de ne pas fonctionner correctement.")

    def show_step(self, index):
        """
        Affiche l'étape spécifiée

        Args:
            index: Index de l'étape à afficher
        """
        logger.info(f"Tentative d'affichage de l'étape {index + 1}")

        if index < 0 or index >= len(self.steps):
            logger.error(f"Index d'étape invalide: {index}")
            QMessageBox.critical(self, "Erreur", f"Index d'étape invalide: {index}")
            return

        try:
            # Afficher la nouvelle étape dans le QStackedWidget
            logger.debug(f"Changement de l'index du QStackedWidget à {index}")
            self.step_container.setCurrentIndex(index)
            self.current_step_index = index

            # Mise à jour du titre et de la description de l'étape
            self.step_title_label.setText(STEPS[index]['title'])
            self.step_description_label.setText(STEPS[index]['description'])

            # Mise à jour des indicateurs d'étapes avec les statuts
            logger.debug("Mise à jour des indicateurs d'étapes")
            for i, indicator in enumerate(self.step_indicators):
                indicator_container = indicator.parentWidget()
                if i < index:
                    indicator_container.setProperty("status", "completed")
                    indicator.setProperty("status", "completed")
                elif i == index:
                    indicator_container.setProperty("status", "current")
                    indicator.setProperty("status", "current")
                elif not self.initial_load and not self.steps[i].validate():
                    indicator_container.setProperty("status", "invalid")
                    indicator.setProperty("status", "invalid")
                else:
                    indicator_container.setProperty("status", "pending")
                    indicator.setProperty("status", "pending")

                # Forcer le rafraîchissement du style pour chaque indicateur et son conteneur
                indicator_container.style().unpolish(indicator_container)
                indicator_container.style().polish(indicator_container)
                indicator.style().unpolish(indicator)
                indicator.style().polish(indicator)

            if self.initial_load and index == 0:
                self.initial_load = False

            # Mise à jour de la barre de progression
            progress_value = int((index / (len(self.steps) - 1)) * 100)
            logger.debug(f"Mise à jour de la barre de progression à {progress_value}%")
            self.progress_bar.setValue(progress_value)

            # Mise à jour des boutons de navigation
            self.prev_button.setVisible(True)
            self.next_button.setVisible(True)

            self.prev_button.setEnabled(index > 0)

            # Disable the main 'Next' button only on Step 3, as it has its own navigation
            #if index == 2:
                # self.next_button.setEnabled(False)
            #else:
            self.next_button.setEnabled(True)

            if index == len(self.steps) - 1:
                logger.debug("Dernière étape, bouton suivant devient 'Terminer'")
                self.next_button.setText("Terminer")
            else:
                logger.debug("Bouton suivant devient 'Suivant'")
                self.next_button.setText("Suivant")

            # Mise à jour du statut
            status_text = f"Étape {index + 1}/{len(self.steps)}: {STEPS[index]['title']}"
            logger.debug(f"Mise à jour du statut: {status_text}")
            self.status_label.setText(status_text)

            # Appeler la méthode on_show de l'étape si elle existe
            if hasattr(self.steps[index], 'on_show') and callable(getattr(self.steps[index], 'on_show')):
                logger.debug(f"Appel de la méthode on_show de l'étape {index + 1}")
                self.steps[index].on_show()

            logger.info(f"Affichage de l'étape {index + 1}: {STEPS[index]['title']} réussi")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'étape {index + 1}: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur",
                                 f"Une erreur est survenue lors de l'affichage de l'étape {index + 1}:\n{str(e)}")

    def next_step(self):
        """
        Passe à l'étape suivante
        """
        logger.info(f"Tentative de passage à l'étape suivante depuis l'étape {self.current_step_index + 1}")

        try:
            # Validation de l'étape actuelle
            logger.info(f"Validation de l'étape {self.current_step_index + 1}")
            if not self.steps[self.current_step_index].validate():
                logger.warning(f"Validation de l'étape {self.current_step_index + 1} échouée")
                QMessageBox.critical(self, "Validation", "Veuillez corriger les erreurs avant de continuer.")
                return

            logger.info(f"Validation de l'étape {self.current_step_index + 1} réussie")

            # Sauvegarde des données de l'étape actuelle
            logger.info(f"Sauvegarde des données de l'étape {self.current_step_index + 1}")
            self.steps[self.current_step_index].save_data()
            logger.info(f"Données de l'étape {self.current_step_index + 1} sauvegardées")

            # Passage à l'étape suivante ou finalisation
            if self.current_step_index < len(self.steps) - 1:
                logger.info(f"Passage à l'étape {self.current_step_index + 2}")
                self.show_step(self.current_step_index + 1)
            else:
                # Dernière étape, finalisation
                logger.info("Dernière étape atteinte, lancement de la finalisation")
                self.finalize()
        except Exception as e:
            logger.error(f"Erreur lors du passage à l'étape suivante: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur",
                                 f"Une erreur est survenue lors du passage à l'étape suivante:\n{str(e)}")

    def previous_step(self):
        """
        Revient à l'étape précédente
        """
        logger.info(f"Tentative de retour à l'étape précédente depuis l'étape {self.current_step_index + 1}")

        try:
            if self.current_step_index > 0:
                # Sauvegarde des données de l'étape actuelle
                logger.info(f"Sauvegarde des données de l'étape {self.current_step_index + 1}")
                self.steps[self.current_step_index].save_data()
                logger.info(f"Données de l'étape {self.current_step_index + 1} sauvegardées")

                # Retour à l'étape précédente
                logger.info(f"Retour à l'étape {self.current_step_index}")
                self.show_step(self.current_step_index - 1)
            else:
                logger.info("Déjà à la première étape, impossible de revenir en arrière")
        except Exception as e:
            logger.error(f"Erreur lors du retour à l'étape précédente: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur",
                                 f"Une erreur est survenue lors du retour à l'étape précédente:\n{str(e)}")

    def finalize(self):
        """
        Finalise l'assistant et génère le rapport final
        """
        # Confirmation
        reply = QMessageBox.question(self, "Finalisation",
                                     "Êtes-vous sûr de vouloir finaliser l'installation ?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            # Exécution des actions de finalisation
            self.steps[3].execute_cleanup_actions()

            # Génération du rapport final
            report_path = self.steps[3].generate_final_report()

            # Affichage du message de succès
            QMessageBox.information(self, "Finalisation",
                                    f"Installation finalisée avec succès !\n\n"
                                    f"Le rapport final a été généré :\n{report_path}")

            # Sauvegarde de la session
            self.save_session()

            # Fermeture de l'application
            self.quit_app()
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la finalisation:\n{str(e)}")

    def new_session(self):
        """
        Crée une nouvelle session
        """
        reply = QMessageBox.question(self, "Nouvelle session",
                                     "Êtes-vous sûr de vouloir créer une nouvelle session ? "
                                     "Toutes les données non sauvegardées seront perdues.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.session_data = create_empty_session()
            self.show_step(0)

            # Réinitialisation des étapes
            for step in self.steps:
                step.reset()

            logger.info("Nouvelle session créée")

    def load_session(self):
        """
        Charge une session depuis un fichier
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Charger une session",
            "",
            "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
        )

        if not file_path:
            return

        try:
            data = load_session_data(file_path)
            if data:
                self.session_data = data

                # Mise à jour des étapes avec les nouvelles données
                for step in self.steps:
                    step.load_data()

                # Affichage de la première étape
                self.show_step(0)

                QMessageBox.information(self, "Chargement", "Session chargée avec succès.")
                logger.info(f"Session chargée depuis {file_path}")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de charger la session.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la session: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors du chargement:\n{str(e)}")

    def save_session(self):
        """
        Sauvegarde la session dans un fichier
        """
        # Sauvegarde des données de l'étape actuelle
        self.steps[self.current_step_index].save_data()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder la session",
            "",
            "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
        )

        if not file_path:
            return

        try:
            save_session_data(self.session_data, file_path)
            QMessageBox.information(self, "Sauvegarde", "Session sauvegardée avec succès.")
            logger.info(f"Session sauvegardée dans {file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la session: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la sauvegarde:\n{str(e)}")

    def show_documentation(self):
        """
        Affiche la documentation
        """
        QMessageBox.information(self, "Documentation",
                                "La documentation de l'Assistant d'installation ZymoSoft "
                                "est disponible dans le dossier 'docs' de l'application.")

    def show_about(self):
        """
        Affiche les informations sur l'application
        """
        QMessageBox.information(self, "À propos",
                                f"Assistant d'installation ZymoSoft\n"
                                f"Version {APP_CONFIG['version']}\n\n"
                                f"© 2025 Zymoptiq")

    def quit_app(self):
        """
        Quitte l'application
        """
        reply = QMessageBox.question(self, "Quitter",
                                     "Êtes-vous sûr de vouloir quitter ? "
                                     "Toutes les données non sauvegardées seront perdues.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()

    # La méthode run() n'est plus nécessaire car la boucle principale est gérée par QApplication.exec_() dans main.py

    def get_plate_types(self):
        """
        Retourne les types de plaques définis dans les constantes

        Returns:
            list: Liste des types de plaques
        """
        return PLATE_TYPES

    def get_acquisition_modes(self):
        """
        Retourne les modes d'acquisition définis dans les constantes

        Returns:
            list: Liste des modes d'acquisition
        """
        return ACQUISITION_MODES
