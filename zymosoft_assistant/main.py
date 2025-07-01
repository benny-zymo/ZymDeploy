#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Assistant d'installation ZymoSoft
Point d'entrée de l'application
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication

# Ajouter le répertoire parent au path pour permettre les imports absolus
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from zymosoft_assistant.gui.main_window import MainWindow

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zymosoft_assistant.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Point d'entrée principal de l'application"""
    try:
        logger.info("Démarrage du ZymDeploy")

        # Création de l'application Qt
        app = QApplication(sys.argv)

        # Configuration de la police par défaut pour toute l'application
        font = app.font()
        font.setPointSize(font.pointSize() + 2)  # Augmenter la taille de police par défaut
        app.setFont(font)

        # Création et affichage de la fenêtre principale
        main_window = MainWindow()
        main_window.show()

        # Lancement de la boucle d'événements
        result = app.exec_()

        logger.info("Fermeture normale de l'application")
        return result
    except Exception as e:
        logger.error(f"Erreur non gérée: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
