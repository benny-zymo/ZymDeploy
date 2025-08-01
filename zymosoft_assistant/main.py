#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Assistant d'installation ZymoSoft
Point d'entrée de l'application
"""

import sys
import os
import logging
import subprocess
#import pkg_resources
import importlib.metadata as pkg_resources
from PyQt5.QtWidgets import QApplication, QMessageBox

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

# Ajouter le répertoire parent au path pour permettre les imports absolus
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Vérifier la version de NumPy avant de continuer
def check_numpy_version():
    """
    Vérifie la version de NumPy et la rétrograde si nécessaire
    """
    try:
        numpy_version = pkg_resources.get_distribution("numpy").version
        logger.info(f"Version actuelle de NumPy: {numpy_version}")

        if numpy_version.startswith("2."):
            logger.warning("NumPy version 2.x détectée. Cela peut causer des problèmes de compatibilité.")

            # Utiliser un QMessageBox pour informer l'utilisateur
            app = QApplication(sys.argv)  # Créer une application temporaire pour afficher le message
            result = QMessageBox.question(
                None, 
                "Incompatibilité de version NumPy", 
                f"La version actuelle de NumPy ({numpy_version}) peut causer des problèmes de compatibilité.\n\n"
                "Voulez-vous rétrograder NumPy à une version compatible (< 2.0.0) ?\n\n"
                "Note: Cette opération peut prendre quelques instants.",
                QMessageBox.Yes | QMessageBox.No
            )

            if result == QMessageBox.Yes:
                logger.info("Rétrogradation de NumPy à une version < 2.0.0...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy<2.0.0", "--force-reinstall"])

                    QMessageBox.information(
                        None,
                        "Rétrogradation terminée",
                        "NumPy a été rétrogradé avec succès. L'application va maintenant se fermer.\n\n"
                        "Veuillez la redémarrer pour appliquer les changements."
                    )
                    sys.exit(0)
                except Exception as e:
                    logger.error(f"Erreur lors de la rétrogradation de NumPy: {str(e)}", exc_info=True)
                    QMessageBox.critical(
                        None,
                        "Erreur",
                        f"Une erreur est survenue lors de la rétrogradation de NumPy:\n{str(e)}\n\n"
                        "L'application peut ne pas fonctionner correctement."
                    )
            else:
                logger.info("L'utilisateur a choisi de ne pas rétrograder NumPy.")
                QMessageBox.warning(
                    None,
                    "Avertissement",
                    "L'application peut ne pas fonctionner correctement avec NumPy 2.x."
                )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la version de NumPy: {str(e)}", exc_info=True)


# Vérifier la version de NumPy avant d'importer les modules qui en dépendent
check_numpy_version()

from zymosoft_assistant.gui.main_window import MainWindow
from zymosoft_assistant.utils.helpers import resource_path
from zymosoft_assistant.utils.constants import APP_CONFIG

def main():
    """Point d'entrée principal de l'application"""
    try:
        logger.info("Démarrage du ZymDeploy")

        # Configuration de l'icône de l'application
        try:
            icon_path = resource_path("assets\\icons\\icon.png")
            APP_CONFIG['icon_path'] = icon_path
            logger.info(f"Chemin de l'icône de l'application: {icon_path}")
        except Exception as e:
            logger.warning(f"Impossible de charger l'icône de l'application: {e}")
            APP_CONFIG['icon_path'] = None

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


'''
TODO : 

check step 3 analyser les resutlats problème 

'''
