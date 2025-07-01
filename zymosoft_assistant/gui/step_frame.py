#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contenant la classe de base pour les frames d'étapes de l'assistant d'installation ZymoSoft
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout

logger = logging.getLogger(__name__)

class StepFrame:
    """
    Classe de base pour les frames d'étapes
    """

    def __init__(self, parent, main_window):
        """
        Initialise le frame d'étape

        Args:
            parent: Widget parent
            main_window: Référence vers la fenêtre principale
        """
        self.parent = parent
        self.main_window = main_window
        self.widget = QWidget(parent)
        self.layout = QVBoxLayout(self.widget)
        self.widget.setLayout(self.layout)

        # Création des widgets
        self.create_widgets()

    def create_widgets(self):
        """
        Crée les widgets de l'étape (à implémenter dans les sous-classes)
        """
        pass

    def show(self):
        """
        Affiche l'étape
        """
        self.widget.show()

    def hide(self):
        """
        Masque l'étape
        """
        self.widget.hide()

    def validate(self):
        """
        Valide les données de l'étape

        Returns:
            True si les données sont valides, False sinon
        """
        logger.debug(f"Validation de l'étape {self.__class__.__name__} (méthode par défaut)")
        return True

    def save_data(self):
        """
        Sauvegarde les données de l'étape dans la session
        """
        logger.debug(f"Sauvegarde des données de l'étape {self.__class__.__name__} (méthode par défaut)")
        pass

    def load_data(self):
        """
        Charge les données de la session dans l'étape
        """
        logger.debug(f"Chargement des données de l'étape {self.__class__.__name__} (méthode par défaut)")
        pass

    def reset(self):
        """
        Réinitialise l'étape
        """
        logger.debug(f"Réinitialisation de l'étape {self.__class__.__name__} (méthode par défaut)")
        pass

    def on_show(self):
        """
        Appelé lorsque l'étape est affichée
        """
        logger.debug(f"Affichage de l'étape {self.__class__.__name__} (méthode par défaut)")
        pass
