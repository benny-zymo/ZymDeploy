#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for the Clean PC dialog, allowing selective deletion or moving of files.
"""

import os
import shutil
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QFileDialog, QMessageBox, QLabel)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class CleanPCDialog(QDialog):
    """
    A dialog to show files to be cleaned and allow the user to select
    which ones to delete or move.
    """
    def __init__(self, items_to_clean, parent=None):
        """
        Initializes the dialog.

        Args:
            items_to_clean (list): A list of paths to files/folders to be cleaned.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.items_to_clean = items_to_clean
        self.setWindowTitle("Nettoyage du PC")
        self.setMinimumSize(600, 400)
        self.setModal(True)

        self.setupUi()
        self.populate_tree()

    def setupUi(self):
        """
        Sets up the UI of the dialog.
        """
        main_layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel("Sélectionnez les éléments à nettoyer, puis choisissez de les supprimer ou de les déplacer.")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # Tree widget to display files
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Élément", "Chemin"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        main_layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.move_button = QPushButton("Déplacer la sélection...")
        self.move_button.clicked.connect(self.move_selected_items)
        button_layout.addWidget(self.move_button)

        self.delete_button = QPushButton("Supprimer la sélection")
        self.delete_button.setStyleSheet("background-color: #dc3545; color: white;")
        self.delete_button.clicked.connect(self.delete_selected_items)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

    def populate_tree(self):
        """
        Populates the tree widget with the items to be cleaned.
        """
        for path in self.items_to_clean:
            if os.path.exists(path):
                item = QTreeWidgetItem(self.tree, [os.path.basename(path), path])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked)

    def get_selected_items(self):
        """
        Gets the paths of the selected items in the tree.

        Returns:
            A list of paths for the checked items.
        """
        selected_paths = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                selected_paths.append(item.text(1))
        return selected_paths

    def move_selected_items(self):
        """
        Moves the selected items to a user-chosen directory.
        """
        selected_paths = self.get_selected_items()
        if not selected_paths:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner au moins un élément à déplacer.")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "Choisir le dossier de destination", "/")
        if not dest_dir:
            return

        try:
            for path in selected_paths:
                base_name = os.path.basename(path)
                dest_path = os.path.join(dest_dir, base_name)
                logger.info(f"Déplacement de {path} vers {dest_path}")
                shutil.move(path, dest_path)
            QMessageBox.information(self, "Succès", "Les éléments sélectionnés ont été déplacés avec succès.")
            self.accept()
        except Exception as e:
            logger.error(f"Erreur lors du déplacement des fichiers: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors du déplacement des fichiers:\n{e}")

    def delete_selected_items(self):
        """
        Deletes the selected items.
        """
        selected_paths = self.get_selected_items()
        if not selected_paths:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner au moins un élément à supprimer.")
            return

        reply = QMessageBox.question(self, "Confirmation",
                                     "Êtes-vous sûr de vouloir supprimer définitivement les éléments sélectionnés ?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            for path in selected_paths:
                logger.info(f"Suppression de {path}")
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            QMessageBox.information(self, "Succès", "Les éléments sélectionnés ont été supprimés avec succès.")
            self.accept()
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des fichiers: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la suppression des fichiers:\n{e}")
