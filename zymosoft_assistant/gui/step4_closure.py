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
from .clean_pc_dialog import CleanPCDialog

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

        # Résumé de l'installation (amélioré)
        summary_frame = QGroupBox("Résumé de l'installation")
        summary_layout = QVBoxLayout(summary_frame)
        right_panel_layout.addWidget(summary_frame)

        # Utilisation de labels pour un affichage plus propre
        self.summary_client_label = QLabel("Client: Non spécifié")
        summary_layout.addWidget(self.summary_client_label)

        self.summary_cs_label = QLabel("Responsable CS: Non spécifié")
        summary_layout.addWidget(self.summary_cs_label)

        self.summary_instrumentation_label = QLabel("Responsable instrumentation: Non spécifié")
        summary_layout.addWidget(self.summary_instrumentation_label)

        summary_layout.addSpacing(10)

        self.summary_checks_label = QLabel("Vérifications: Non effectuées")
        summary_layout.addWidget(self.summary_checks_label)

        self.summary_acquisitions_label = QLabel("Acquisitions validées: 0/0")
        summary_layout.addWidget(self.summary_acquisitions_label)

        summary_layout.addSpacing(10)

        self.summary_actions_label = QLabel("Actions à effectuer:")
        summary_layout.addWidget(self.summary_actions_label)

        self.summary_client_mode_label = QLabel("- Passer en mode client")
        self.summary_client_mode_label.setStyleSheet("padding-left: 15px;")
        summary_layout.addWidget(self.summary_client_mode_label)

        self.summary_clean_pc_label = QLabel("- Nettoyer le PC")
        self.summary_clean_pc_label.setStyleSheet("padding-left: 15px;")
        summary_layout.addWidget(self.summary_clean_pc_label)

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

        # Les boutons de navigation sont maintenant gérés par la fenêtre principale
        # pour une expérience utilisateur cohérente.
        # Le bouton "Terminer" de la fenêtre principale déclenchera la finalisation.

    def _update_summary(self):
        """
        Met à jour le résumé de l'installation avec les nouveaux labels
        """
        try:
            # Récupérer les informations client
            client_info = self.main_window.session_data.get("client_info", {})
            self.summary_client_label.setText(f"Client: {client_info.get('name', 'Non spécifié')}")
            self.summary_cs_label.setText(f"Responsable CS: {client_info.get('cs_responsible', 'Non spécifié')}")
            self.summary_instrumentation_label.setText(f"Responsable instrumentation: {client_info.get('instrumentation_responsible', 'Non spécifié')}")

            # Récupérer les informations sur les vérifications
            checks = self.main_window.session_data.get("step2_checks", {})
            if checks:
                checks_status = "✓ Réussies" if checks.get("installation_valid", False) else "✗ Échouées"
                self.summary_checks_label.setText(f"Vérifications: {checks_status}")
            else:
                self.summary_checks_label.setText("Vérifications: Non effectuées")

            # Récupérer les informations sur les acquisitions
            acquisitions = self.main_window.session_data.get("acquisitions", [])
            valid_acquisitions = [acq for acq in acquisitions if acq.get("validated", False)]
            self.summary_acquisitions_label.setText(f"Acquisitions validées: {len(valid_acquisitions)}/{len(acquisitions)}")

            # Mettre à jour les actions à effectuer
            client_mode_icon = '✓' if self.client_mode_var else '✗'
            self.summary_client_mode_label.setText(f"- {client_mode_icon} Passer en mode client")

            clean_pc_icon = '✓' if self.clean_pc_var else '✗'
            self.summary_clean_pc_label.setText(f"- {clean_pc_icon} Nettoyer le PC")

        except Exception as e:
            logger.error(f"Erreur dans _update_summary: {str(e)}", exc_info=True)

    def _update_history(self):
        """
        Met à jour l'historique des acquisitions
        """
        try:
            # Effacer l'historique précédent
            if self.history_tree is None:
                logger.error("Erreur dans _update_history: self.history_tree est None")
                return

            self.history_tree.clear()

            # Récupérer les acquisitions
            acquisitions = self.main_window.session_data.get("acquisitions", [])

            if not acquisitions:
                return

            # Récupérer les constantes
            try:
                plate_types = self.main_window.get_plate_types()
                acquisition_modes = self.main_window.get_acquisition_modes()
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des types de plaques ou modes d'acquisition: {str(e)}")
                # Utiliser des valeurs par défaut
                from zymosoft_assistant.utils.constants import PLATE_TYPES, ACQUISITION_MODES
                plate_types = PLATE_TYPES
                acquisition_modes = ACQUISITION_MODES

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
        except Exception as e:
            logger.error(f"Erreur dans _update_history: {str(e)}", exc_info=True)

    # La méthode _finalize_installation a été supprimée car la logique de finalisation
    # est maintenant initiée par la MainWindow pour une meilleure centralisation du contrôle.

    def _execute_actions(self):
        """
        Exécute les actions de finalisation. Le nettoyage du PC est fait dans le thread principal
        à cause de la boîte de dialogue, le reste est fait ici.
        """
        try:
            # Passer en mode client
            if self.client_mode_var:
                self._update_progress(10, "Passage en mode client...")
                try:
                    self._set_client_mode()
                    self.actions_status["client_mode"] = True
                except Exception as e:
                    logger.error(f"Erreur lors du passage en mode client: {str(e)}", exc_info=True)
                    self.actions_status["client_mode"] = False
                time.sleep(0.5)

            # Le nettoyage du PC est géré séparément
            self._update_progress(30, "En attente de l'action de nettoyage...")

            # Utiliser QTimer pour appeler la méthode de nettoyage dans le thread principal
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self._handle_pc_cleanup)

        except Exception as e:
            logger.error(f"Erreur lors de la finalisation: {str(e)}", exc_info=True)
            error_message = str(e)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._handle_finalization_error(error_message))

    def _handle_pc_cleanup(self):
        """
        Gère le nettoyage du PC, y compris l'affichage de la boîte de dialogue.
        Cette méthode est exécutée dans le thread principal.
        """
        if self.clean_pc_var:
            cleanup_success = self._clean_pc()
            self.actions_status["clean_pc"] = cleanup_success
            if not cleanup_success:
                # L'utilisateur a annulé ou une erreur est survenue
                self._handle_finalization_error("L'opération de nettoyage a été annulée ou a échoué.")
                return
        else:
            self.actions_status["clean_pc"] = True # L'action n'était pas requise, donc on la considère comme réussie

        # Continuer avec le reste des actions dans un thread
        threading.Thread(target=self._continue_actions_after_cleanup, daemon=True).start()

    def _continue_actions_after_cleanup(self):
        """
        Continue les actions de finalisation après le nettoyage du PC.
        """
        try:
            # Générer le rapport final
            self._update_progress(60, "Génération du rapport final...")
            try:
                self._do_generate_final_report()
            except Exception as e:
                logger.error(f"Erreur lors de la génération du rapport final: {str(e)}", exc_info=True)
            time.sleep(0.5)

            # Finalisation
            self._update_progress(100, "Installation finalisée avec succès.")

            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self._finalization_completed)
        except Exception as e:
            logger.error(f"Erreur après le nettoyage: {str(e)}", exc_info=True)
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

        # Les boutons sont gérés par la fenêtre principale, qui sera informée de l'erreur.
        # On peut envisager un signal pour communiquer l'état.
        self.main_window.on_finalization_error()


    def _finalization_completed(self):
        """
        Appelé lorsque la finalisation est terminée avec succès
        """
        # Afficher un message de succès
        QMessageBox.information(self.widget, "Succès",
                               "L'installation a été finalisée avec succès.\n\n"
                               "Le rapport final fusionné a été généré.")

        # Informer la fenêtre principale que la finalisation est terminée
        self.main_window.on_finalization_success()

    def _set_client_mode(self):
        """
        Passe ZymoSoft en mode client (ExpertMode=false)
        """
        try:
            # Récupérer le chemin du fichier Config.ini
            zymosoft_path = self.main_window.session_data.get("zymosoft_path", "")

            if not zymosoft_path:
                logger.warning("Chemin ZymoSoft non défini dans les données de session")
                # Utiliser le chemin par défaut
                from zymosoft_assistant.utils.constants import ZYMOSOFT_BASE_PATH
                zymosoft_path = ZYMOSOFT_BASE_PATH

            config_path = os.path.join(zymosoft_path, "etc", "Config.ini")

            # Vérifier si le dossier etc existe
            etc_dir = os.path.join(zymosoft_path, "etc")
            if not os.path.exists(etc_dir):
                try:
                    os.makedirs(etc_dir, exist_ok=True)
                    logger.info(f"Dossier etc créé: {etc_dir}")
                except Exception as e:
                    logger.error(f"Impossible de créer le dossier etc: {str(e)}")
                    # Continuer malgré l'erreur

            # Vérifier si le fichier Config.ini existe
            if not os.path.exists(config_path):
                logger.warning(f"Fichier Config.ini introuvable: {config_path}")
                # Créer un fichier Config.ini minimal
                try:
                    with open(config_path, 'w') as f:
                        f.write("[Application]\nExpertMode=false\n")
                    logger.info(f"Fichier Config.ini créé: {config_path}")
                    self.actions_status["client_mode"] = True
                    return
                except Exception as e:
                    logger.error(f"Impossible de créer le fichier Config.ini: {str(e)}")
                    # Ne pas lever d'exception, juste marquer l'action comme échouée
                    self.actions_status["client_mode"] = False
                    return

            # Lire le fichier
            try:
                with open(config_path, 'r') as f:
                    lines = f.readlines()
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du fichier Config.ini: {str(e)}")
                # Créer un nouveau fichier
                try:
                    with open(config_path, 'w') as f:
                        f.write("[Application]\nExpertMode=false\n")
                    logger.info(f"Fichier Config.ini recréé: {config_path}")
                    self.actions_status["client_mode"] = True
                    return
                except Exception as e2:
                    logger.error(f"Impossible de créer le fichier Config.ini: {str(e2)}")
                    self.actions_status["client_mode"] = False
                    return

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
            try:
                with open(config_path, 'w') as f:
                    f.writelines(lines)
                logger.info(f"Mode client activé dans {config_path}")
                self.actions_status["client_mode"] = True
            except Exception as e:
                logger.error(f"Erreur lors de l'écriture du fichier Config.ini: {str(e)}")
                self.actions_status["client_mode"] = False

        except Exception as e:
            logger.error(f"Erreur lors du passage en mode client: {str(e)}", exc_info=True)
            self.actions_status["client_mode"] = False
            # Ne pas lever d'exception pour éviter d'interrompre le processus de finalisation

    def _clean_pc(self):
        """
        Ouvre une boîte de dialogue pour permettre à l'utilisateur de nettoyer le PC de manière sélective.
        Retourne True si l'opération est réussie ou si l'utilisateur annule, False en cas d'échec.
        """
        try:
            items_to_clean = []

            # 1. Trouver le dossier Diag/Temp
            diag_temp_path = os.path.join("C:", "Users", "Public", "Zymoptiq", "Diag", "Temp")
            if os.path.exists(diag_temp_path):
                items_to_clean.append(diag_temp_path)

            # 2. Trouver les dossiers d'acquisition de test
            acquisitions = self.main_window.session_data.get("acquisitions", [])
            for acquisition in acquisitions:
                results_folder = acquisition.get("results_folder", "")
                # On ne cible que les acquisitions invalidées ou celles contenant "test"
                if results_folder and os.path.exists(results_folder):
                    if not acquisition.get("validated", True) or "test" in results_folder.lower():
                        items_to_clean.append(results_folder)

            if not items_to_clean:
                QMessageBox.information(self.widget, "Nettoyage", "Aucun élément à nettoyer n'a été trouvé.")
                return True

            # Afficher la boîte de dialogue
            dialog = CleanPCDialog(items_to_clean, self.widget)
            result = dialog.exec_()

            if result == QDialog.Accepted:
                logger.info("Nettoyage du PC effectué avec succès via la boîte de dialogue.")
                return True
            else:
                logger.warning("L'utilisateur a annulé le nettoyage du PC.")
                return False # L'utilisateur a annulé

        except Exception as e:
            logger.error(f"Erreur lors de la préparation du nettoyage du PC: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la préparation du nettoyage:\n{e}")
            return False

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
        # La méthode generate_final_report attend maintenant le dictionnaire de session complet
        full_data = self.main_window.session_data.copy()
        full_data.update({
            "general_comments": self.general_comments,
            "actions": {
                "client_mode": self.client_mode_var,
                "clean_pc": self.clean_pc_var
            },
            "actions_status": self.actions_status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

        # Génération du rapport fusionné
        report_path = report_generator.generate_final_report(full_data)

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

    def execute_cleanup_actions(self):
        """
        Exécute les actions de nettoyage lors de la finalisation dans un thread séparé.
        Cette méthode est appelée par la fenêtre principale lors de la finalisation.
        """
        # Récupérer les commentaires
        self.general_comments = self.comments_text.toPlainText().strip()

        # Sauvegarder les données
        self.save_data()

        # Réinitialiser la barre de progression
        self.progress_bar.setValue(0)
        self.progress_label.setText("Préparation de la finalisation...")

        # Lancer les actions dans un thread séparé pour ne pas bloquer l'UI
        action_thread = threading.Thread(target=self._execute_actions, daemon=True)
        action_thread.start()

        return True

    def generate_final_report(self):
        """
        Génère le rapport final
        Cette méthode est appelée par la fenêtre principale lors de la finalisation

        Returns:
            Le chemin vers le rapport généré
        """
        return self._do_generate_final_report()

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
        try:
            # Mettre à jour l'historique
            self._update_history()

            # Mettre à jour le résumé
            self._update_summary()
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'étape 4: {str(e)}", exc_info=True)
