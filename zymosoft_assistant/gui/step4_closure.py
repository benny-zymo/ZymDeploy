#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de l'étape 4 de l'assistant d'installation ZymoSoft : Clôture de l'installation
"""

import os
import logging
import threading
import time
import shutil
from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QFrame, QFileDialog, QMessageBox,
                            QProgressBar, QTabWidget, QWidget, QScrollArea,
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QCheckBox, QRadioButton, QGroupBox, QTextEdit,
                            QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QVariant
from PyQt5.QtGui import QPixmap

from zymosoft_assistant.utils.constants import COLOR_SCHEME, APP_CONFIG
from zymosoft_assistant.core.report_generator import ReportGenerator
from .step_frame import StepFrame

logger = logging.getLogger(__name__)

class Step4Closure(StepFrame):
    """
    Classe pour l'étape 4 : Clôture de l'installation
    """

    def __init__(self, parent, main_window):
        """
        Initialise l'étape 4

        Args:
            parent: Widget parent
            main_window: Référence vers la fenêtre principale
        """
        # Variables pour les options de clôture
        self.client_mode_var = True
        self.clean_pc_var = True
        self.general_comments = ""

        # Statut des actions
        self.actions_status = {
            "client_mode": False,
            "clean_pc": False
        }

        super().__init__(parent, main_window)

        logger.info("Étape 4 initialisée")

    def create_widgets(self):
        """
        Crée les widgets de l'étape 4
        """
        # Utilisation du layout vertical principal
        main_layout = QVBoxLayout()
        self.layout.addLayout(main_layout)

        # Titre de l'étape
        title_label = QLabel("Étape 4 : Clôture de l'installation")
        title_label.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {COLOR_SCHEME['primary']};")
        main_layout.addWidget(title_label)
        main_layout.addSpacing(20)

        # Conteneur principal
        main_container = QWidget()
        main_layout.addWidget(main_container)
        main_container_layout = QHBoxLayout(main_container)
        main_container_layout.setContentsMargins(20, 0, 20, 0)

        # Panneau gauche: Commentaires et historique
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout(left_panel)
        main_container_layout.addWidget(left_panel)

        # Commentaire général
        comments_frame = QGroupBox("Commentaire général")
        comments_layout = QVBoxLayout(comments_frame)
        left_panel_layout.addWidget(comments_frame)

        comments_label = QLabel("Ajoutez un commentaire général sur l'installation :")
        comments_label.setWordWrap(True)
        comments_label.setMinimumWidth(400)
        comments_layout.addWidget(comments_label)

        self.comments_text = QTextEdit()
        self.comments_text.setMinimumHeight(150)
        comments_layout.addWidget(self.comments_text)

        # Historique des acquisitions
        history_frame = QGroupBox("Historique des acquisitions")
        history_layout = QVBoxLayout(history_frame)
        left_panel_layout.addWidget(history_frame)

        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["#", "Type de plaque", "Mode", "Statut"])
        self.history_tree.setColumnWidth(0, 50)
        self.history_tree.setColumnWidth(1, 150)
        self.history_tree.setColumnWidth(2, 150)
        self.history_tree.setColumnWidth(3, 100)
        self.history_tree.setMaximumHeight(100)
        history_layout.addWidget(self.history_tree)

        # Panneau droit: Actions de fin
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        main_container_layout.addWidget(right_panel)

        # Actions de fin
        actions_frame = QGroupBox("Actions de fin")
        actions_layout = QVBoxLayout(actions_frame)
        right_panel_layout.addWidget(actions_frame)

        # Passer en mode client
        client_mode_cb = QCheckBox("Passer en mode client (ExpertMode=false)")
        client_mode_cb.setChecked(self.client_mode_var)
        client_mode_cb.toggled.connect(lambda checked: setattr(self, 'client_mode_var', checked))
        actions_layout.addWidget(client_mode_cb)

        client_mode_desc = QLabel("Modifie le fichier Config.ini pour désactiver le mode expert.")
        client_mode_desc.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        client_mode_desc.setWordWrap(True)
        client_mode_desc.setContentsMargins(30, 0, 0, 5)
        actions_layout.addWidget(client_mode_desc)

        # Nettoyer le PC
        clean_pc_cb = QCheckBox("Nettoyer le PC")
        clean_pc_cb.setChecked(self.clean_pc_var)
        clean_pc_cb.toggled.connect(lambda checked: setattr(self, 'clean_pc_var', checked))
        actions_layout.addWidget(clean_pc_cb)

        clean_pc_desc = QLabel("Supprime les données d'acquisitions de test et vide le dossier Diag/Temp.")
        clean_pc_desc.setStyleSheet(f"color: {COLOR_SCHEME['text_secondary']};")
        clean_pc_desc.setWordWrap(True)
        clean_pc_desc.setContentsMargins(30, 0, 0, 5)
        actions_layout.addWidget(clean_pc_desc)

        # Résumé de l'installation
        summary_frame = QGroupBox("Résumé de l'installation")
        summary_layout = QVBoxLayout(summary_frame)
        right_panel_layout.addWidget(summary_frame)

        self.summary_text = QTextEdit()
        self.summary_text.setMinimumHeight(150)
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)

        # Barre de progression
        self.progress_frame = QWidget()
        progress_layout = QVBoxLayout(self.progress_frame)
        main_layout.addWidget(self.progress_frame)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignLeft)
        progress_layout.addWidget(self.progress_label)

        # Boutons d'action
        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(buttons_frame)

        self.prev_step_button = QPushButton("Étape précédente")
        self.prev_step_button.clicked.connect(self.main_window.previous_step)
        buttons_layout.addWidget(self.prev_step_button, 0, Qt.AlignLeft)

        self.finalize_button = QPushButton("Finaliser l'installation")
        self.finalize_button.clicked.connect(self._finalize_installation)
        self.finalize_button.setStyleSheet(f"background-color: {COLOR_SCHEME['primary']}; color: white;")
        buttons_layout.addWidget(self.finalize_button, 0, Qt.AlignRight)

        # Bouton pour générer le rapport final
        self.report_button = QPushButton("Générer rapport final")
        self.report_button.clicked.connect(self._generate_final_report)
        self.report_button.setEnabled(False)
        buttons_layout.addWidget(self.report_button, 0, Qt.AlignRight)

    def _update_summary(self):
        """
        Met à jour le résumé de l'installation
        """
        # Récupérer les informations client
        client_info = self.main_window.session_data.get("client_info", {})
        client_name = client_info.get("name", "Non spécifié")
        cs_responsible = client_info.get("cs_responsible", "Non spécifié")
        instrumentation_responsible = client_info.get("instrumentation_responsible", "Non spécifié")

        # Récupérer les informations sur les vérifications
        checks = self.main_window.session_data.get("step2_checks", {})
        checks_status = "✓ Réussies" if checks.get("all_passed", False) else "✗ Échouées"

        # Récupérer les informations sur les acquisitions
        acquisitions = self.main_window.session_data.get("acquisitions", [])
        valid_acquisitions = [acq for acq in acquisitions if acq.get("validated", False)]

        # Construire le résumé
        summary = (
            f"Client: {client_name}\n"
            f"Responsable CS: {cs_responsible}\n"
            f"Responsable instrumentation: {instrumentation_responsible}\n\n"
            f"Vérifications: {checks_status}\n"
            f"Acquisitions validées: {len(valid_acquisitions)}/{len(acquisitions)}\n\n"
            f"Actions à effectuer:\n"
            f"- {'✓' if self.client_mode_var else '✗'} Passer en mode client\n"
            f"- {'✓' if self.clean_pc_var else '✗'} Nettoyer le PC\n"
        )

        # Mettre à jour le texte
        self.summary_text.setPlainText(summary)

    def _update_history(self):
        """
        Met à jour l'historique des acquisitions
        """
        # Effacer l'historique précédent
        self.history_tree.clear()

        # Récupérer les acquisitions
        acquisitions = self.main_window.session_data.get("acquisitions", [])

        if not acquisitions:
            return

        # Récupérer les constantes
        plate_types = self.main_window.get_plate_types()
        acquisition_modes = self.main_window.get_acquisition_modes()

        # Ajouter les acquisitions à l'historique
        for acquisition in acquisitions:
            # Récupérer les noms lisibles
            plate_type_id = acquisition.get('plate_type', '')
            mode_id = acquisition.get('mode', '')

            plate_type_name = next((pt['name'] for pt in plate_types if pt['id'] == plate_type_id), "Inconnu")
            mode_name = next((m['name'] for m in acquisition_modes if m['id'] == mode_id), "Inconnu")

            # Statut
            status = "✓ Validée" if acquisition.get('validated', False) else "✗ Invalidée"

            # Créer l'élément
            item = QTreeWidgetItem([str(acquisition.get('id', '')), plate_type_name, mode_name, status])

            # Définir la couleur en fonction du statut
            if acquisition.get('validated', False):
                item.setForeground(3, Qt.green)
            else:
                item.setForeground(3, Qt.red)

            # Ajouter à l'arbre
            self.history_tree.addTopLevelItem(item)

    def _finalize_installation(self):
        """
        Finalise l'installation en appliquant les actions sélectionnées
        """
        # Récupérer les commentaires
        self.general_comments = self.comments_text.toPlainText().strip()

        # Vérifier que les étapes précédentes sont valides
        if not self._validate_previous_steps():
            return

        # Confirmer les actions
        reply = QMessageBox.question(
            self.widget,
            "Confirmation",
            "Êtes-vous sûr de vouloir finaliser l'installation ?\n\n"
            "Les actions sélectionnées seront appliquées et un rapport final sera généré.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Désactiver les boutons pendant le traitement
        self.finalize_button.setEnabled(False)
        self.prev_step_button.setEnabled(False)

        # Réinitialiser la barre de progression
        self.progress_bar.setValue(0)
        self.progress_label.setText("Préparation...")

        # Sauvegarder les données
        self.save_data()

        # Lancer les actions dans un thread séparé
        threading.Thread(target=self._execute_actions, daemon=True).start()

    def _execute_actions(self):
        """
        Exécute les actions de finalisation dans un thread séparé
        """
        try:
            # Passer en mode client
            if self.client_mode_var:
                self._update_progress(10, "Passage en mode client...")
                self._set_client_mode()
                time.sleep(0.5)  # Simuler un traitement

            # Nettoyer le PC
            if self.clean_pc_var:
                self._update_progress(30, "Nettoyage du PC...")
                self._clean_pc()
                time.sleep(0.5)  # Simuler un traitement

            # Générer le rapport final
            self._update_progress(60, "Génération du rapport final...")
            self._do_generate_final_report()
            time.sleep(0.5)  # Simuler un traitement

            # Finalisation
            self._update_progress(100, "Installation finalisée avec succès.")

            # Mettre à jour l'interface dans le thread principal
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self._finalization_completed)
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation: {str(e)}", exc_info=True)
            error_message = str(e)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._handle_finalization_error(error_message))

    def _update_progress(self, value, message):
        """
        Met à jour la barre de progression et le message

        Args:
            value: Valeur de progression (0-100)
            message: Message à afficher
        """
        # Utiliser QTimer pour mettre à jour l'interface dans le thread principal
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._do_update_progress(value, message))

    def _do_update_progress(self, value, message):
        """
        Effectue la mise à jour de la barre de progression et du message

        Args:
            value: Valeur de progression (0-100)
            message: Message à afficher
        """
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)

    def _handle_finalization_error(self, error_message):
        """
        Gère les erreurs survenues pendant la finalisation

        Args:
            error_message: Message d'erreur
        """
        QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors de la finalisation:\n{error_message}")
        self.progress_label.setText(f"Erreur: {error_message}")

        # Réactiver les boutons
        self.finalize_button.setEnabled(True)
        self.prev_step_button.setEnabled(True)

    def _finalization_completed(self):
        """
        Appelé lorsque la finalisation est terminée avec succès
        """
        # Afficher un message de succès
        QMessageBox.information(self.widget, "Succès", 
                               "L'installation a été finalisée avec succès.\n\n"
                               "Un rapport final a été généré.")

        # Activer le bouton de rapport
        self.report_button.setEnabled(True)

        # Réactiver le bouton précédent
        self.prev_step_button.setEnabled(True)

    def _set_client_mode(self):
        """
        Passe ZymoSoft en mode client (ExpertMode=false)
        """
        try:
            # Récupérer le chemin du fichier Config.ini
            zymosoft_path = self.main_window.session_data.get("zymosoft_path", "")
            config_path = os.path.join(zymosoft_path, "etc", "Config.ini")

            if not os.path.exists(config_path):
                logger.error(f"Fichier Config.ini introuvable: {config_path}")
                raise FileNotFoundError(f"Fichier Config.ini introuvable: {config_path}")

            # Lire le fichier
            with open(config_path, 'r') as f:
                lines = f.readlines()

            # Modifier la ligne ExpertMode
            modified = False
            for i, line in enumerate(lines):
                if line.strip().startswith("ExpertMode="):
                    lines[i] = "ExpertMode=false\n"
                    modified = True
                    break

            if not modified:
                # Si la ligne n'existe pas, l'ajouter dans la section [Application]
                application_section_found = False
                for i, line in enumerate(lines):
                    if line.strip() == "[Application]":
                        application_section_found = True
                        # Trouver la fin de la section
                        for j in range(i+1, len(lines)):
                            if lines[j].strip().startswith("["):
                                # Insérer avant la prochaine section
                                lines.insert(j, "ExpertMode=false\n")
                                modified = True
                                break
                        if not modified:
                            # Si pas d'autre section, ajouter à la fin
                            lines.append("ExpertMode=false\n")
                            modified = True
                        break

                if not application_section_found:
                    # Si la section [Application] n'existe pas, la créer
                    lines.append("\n[Application]\n")
                    lines.append("ExpertMode=false\n")
                    modified = True

            # Écrire le fichier modifié
            with open(config_path, 'w') as f:
                f.writelines(lines)

            logger.info(f"Mode client activé dans {config_path}")
            self.actions_status["client_mode"] = True
        except Exception as e:
            logger.error(f"Erreur lors du passage en mode client: {str(e)}", exc_info=True)
            raise

    def _clean_pc(self):
        """
        Nettoie le PC en supprimant les données d'acquisitions de test et en vidant le dossier Diag/Temp
        """
        try:
            # Récupérer le chemin de ZymoSoft
            zymosoft_path = self.main_window.session_data.get("zymosoft_path", "")

            # Vider le dossier Diag/Temp
            diag_temp_path = os.path.join("C:", "Users", "Public", "Zymoptiq", "Diag", "Temp")

            if os.path.exists(diag_temp_path):
                # Supprimer tous les fichiers du dossier
                for filename in os.listdir(diag_temp_path):
                    file_path = os.path.join(diag_temp_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logger.warning(f"Erreur lors de la suppression de {file_path}: {str(e)}")

                logger.info(f"Dossier Diag/Temp vidé: {diag_temp_path}")
            else:
                logger.warning(f"Dossier Diag/Temp introuvable: {diag_temp_path}")

            # Supprimer les acquisitions de test
            # Récupérer les dossiers d'acquisition
            acquisitions = self.main_window.session_data.get("acquisitions", [])
            for acquisition in acquisitions:
                results_folder = acquisition.get("results_folder", "")
                if results_folder and os.path.exists(results_folder) and "test" in results_folder.lower():
                    try:
                        shutil.rmtree(results_folder)
                        logger.info(f"Dossier d'acquisition supprimé: {results_folder}")
                    except Exception as e:
                        logger.warning(f"Erreur lors de la suppression de {results_folder}: {str(e)}")

            self.actions_status["clean_pc"] = True
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du PC: {str(e)}", exc_info=True)
            raise

    def _generate_final_report(self):
        """
        Génère le rapport final de l'installation
        """
        # Récupérer les commentaires
        self.general_comments = self.comments_text.toPlainText().strip()

        # Sauvegarder les données
        self.save_data()

        # Générer le rapport
        try:
            self._do_generate_final_report()

            # Afficher un message de succès
            QMessageBox.information(self.widget, "Rapport", "Le rapport final a été généré avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport final: {str(e)}", exc_info=True)
            QMessageBox.critical(self.widget, "Erreur", f"Une erreur est survenue lors de la génération du rapport final:\n{str(e)}")

    def _do_generate_final_report(self):
        """
        Génère effectivement le rapport final
        """
        # Création du générateur de rapports
        report_generator = ReportGenerator()

        # Préparation des données pour le rapport
        report_data = {
            "client_info": self.main_window.session_data.get("client_info", {}),
            "step2_checks": self.main_window.session_data.get("step2_checks", {}),
            "acquisitions": self.main_window.session_data.get("acquisitions", []),
            "general_comments": self.general_comments,
            "actions": {
                "client_mode": self.client_mode_var,
                "clean_pc": self.clean_pc_var
            },
            "actions_status": self.actions_status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Génération du rapport
        report_path = report_generator.generate_final_report(report_data)

        # Stocker le chemin du rapport dans les données de session
        self.main_window.session_data["final_report_path"] = report_path

        # Ouverture du rapport
        os.startfile(report_path)

        logger.info(f"Rapport final généré: {report_path}")

        return report_path

    def _validate_previous_steps(self):
        """
        Vérifie que les étapes précédentes sont valides

        Returns:
            True si les étapes précédentes sont valides, False sinon
        """
        # Vérifier les informations client
        client_info = self.main_window.session_data.get("client_info", {})
        if not client_info.get("name") or not client_info.get("cs_responsible") or not client_info.get("instrumentation_responsible"):
            QMessageBox.critical(self.widget, "Validation", "Les informations client sont incomplètes. Veuillez revenir à l'étape 1.")
            return False

        # Vérifier les acquisitions
        acquisitions = self.main_window.session_data.get("acquisitions", [])
        valid_acquisitions = [acq for acq in acquisitions if acq.get("validated", False)]
        if not valid_acquisitions:
            QMessageBox.critical(self.widget, "Validation", "Aucune acquisition n'a été validée. Veuillez revenir à l'étape 3.")
            return False

        return True

    def validate(self):
        """
        Valide les données de l'étape 4

        Returns:
            True si les données sont valides, False sinon
        """
        # Cette étape est la dernière, donc pas de validation nécessaire pour passer à l'étape suivante
        return True

    def save_data(self):
        """
        Sauvegarde les données de l'étape 4 dans la session
        """
        self.main_window.session_data["final_comments"] = self.general_comments
        self.main_window.session_data["cleanup_actions"] = {
            "client_mode": self.client_mode_var,
            "clean_pc": self.clean_pc_var
        }
        self.main_window.session_data["actions_status"] = self.actions_status

        logger.info("Données de l'étape 4 sauvegardées")

    def load_data(self):
        """
        Charge les données de la session dans l'étape 4
        """
        # Charger les commentaires
        self.general_comments = self.main_window.session_data.get("final_comments", "")
        self.comments_text.setPlainText(self.general_comments)

        # Charger les actions
        cleanup_actions = self.main_window.session_data.get("cleanup_actions", {})
        # Handle the case where cleanup_actions is a list instead of a dictionary
        if isinstance(cleanup_actions, list):
            # Use default values if cleanup_actions is a list
            self.client_mode_var = True
            self.clean_pc_var = True
            logger.warning("cleanup_actions is a list instead of a dictionary, using default values")
        else:
            # Normal case: cleanup_actions is a dictionary
            self.client_mode_var = cleanup_actions.get("client_mode", True)
            self.clean_pc_var = cleanup_actions.get("clean_pc", True)

        # Charger le statut des actions
        self.actions_status = self.main_window.session_data.get("actions_status", {
            "client_mode": False,
            "clean_pc": False
        })

        # Mettre à jour l'historique
        self._update_history()

        # Mettre à jour le résumé
        self._update_summary()

        # Activer le bouton de rapport si un rapport a déjà été généré
        if "final_report_path" in self.main_window.session_data:
            self.report_button.setEnabled(True)

        logger.info("Données de l'étape 4 chargées")

    def reset(self):
        """
        Réinitialise l'étape 4
        """
        # Réinitialiser les commentaires
        self.general_comments = ""
        self.comments_text.setPlainText("")

        # Réinitialiser les actions
        self.client_mode_var = True
        self.clean_pc_var = True

        # Réinitialiser le statut des actions
        self.actions_status = {
            "client_mode": False,
            "clean_pc": False
        }

        # Réinitialiser la barre de progression
        self.progress_bar.setValue(0)
        self.progress_label.setText("")

        # Désactiver le bouton de rapport
        self.report_button.setEnabled(False)

        # Réactiver les boutons
        self.finalize_button.setEnabled(True)
        self.prev_step_button.setEnabled(True)

        # Mettre à jour l'historique
        self._update_history()

        # Mettre à jour le résumé
        self._update_summary()

        logger.info("Étape 4 réinitialisée")

    def on_show(self):
        """
        Appelé lorsque l'étape est affichée
        """
        # Mettre à jour l'historique
        self._update_history()

        # Mettre à jour le résumé
        self._update_summary()
