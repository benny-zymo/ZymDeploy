#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'analyse des résultats d'acquisition ZymoSoft
"""

import os
import logging
import json
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AcquisitionAnalyzer:
    """
    Classe responsable de l'analyse des résultats d'acquisition
    et de la génération de graphiques
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialise l'analyseur d'acquisition
        
        Args:
            output_dir: Répertoire de sortie pour les graphiques générés
                       (par défaut: dossier temporaire)
        """
        self.output_dir = output_dir
        if not self.output_dir:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
        
        # Création du dossier de sortie s'il n'existe pas
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Analyseur d'acquisition initialisé avec dossier de sortie: {self.output_dir}")
    
    def analyze_results(self, results_folder: str) -> Dict[str, Any]:
        """
        Analyse les résultats d'acquisition dans le dossier spécifié
        
        Args:
            results_folder: Chemin vers le dossier contenant les résultats d'acquisition
            
        Returns:
            Dictionnaire avec les résultats d'analyse
        """
        if not os.path.exists(results_folder) or not os.path.isdir(results_folder):
            logger.error(f"Dossier de résultats non valide: {results_folder}")
            return {
                "valid": False,
                "errors": [f"Dossier de résultats non valide: {results_folder}"]
            }
        
        logger.info(f"Analyse des résultats dans: {results_folder}")
        
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "folder": results_folder,
            "plate_type": self._detect_plate_type(results_folder),
            "acquisition_mode": self._detect_acquisition_mode(results_folder),
            "data": None,
            "statistics": None,
            "graphs": []
        }
        
        # Chargement des données
        data = self._load_acquisition_data(results_folder)
        if not data:
            results["valid"] = False
            results["errors"].append("Impossible de charger les données d'acquisition")
            return results
        
        results["data"] = data
        
        # Calcul des statistiques
        statistics = self.calculate_statistics(data)
        results["statistics"] = statistics
        
        # Génération des graphiques
        graph_paths = self.generate_graphs(data)
        results["graphs"] = graph_paths
        
        return results
    
    def _detect_plate_type(self, results_folder: str) -> str:
        """
        Détecte le type de plaque à partir du dossier de résultats
        
        Args:
            results_folder: Chemin vers le dossier de résultats
            
        Returns:
            Type de plaque détecté ou "inconnu"
        """
        # Recherche d'un fichier de configuration ou de métadonnées
        metadata_file = os.path.join(results_folder, "metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if "plate_type" in metadata:
                        return metadata["plate_type"]
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du fichier metadata.json: {str(e)}")
        
        # Analyse du nom du dossier
        folder_name = os.path.basename(results_folder)
        if "micro" in folder_name.lower():
            return "micro_depot"
        elif "nano" in folder_name.lower():
            return "nanofilm"
        
        # Par défaut
        return "inconnu"
    
    def _detect_acquisition_mode(self, results_folder: str) -> str:
        """
        Détecte le mode d'acquisition à partir du dossier de résultats
        
        Args:
            results_folder: Chemin vers le dossier de résultats
            
        Returns:
            Mode d'acquisition détecté ("client", "expert" ou "inconnu")
        """
        # Recherche d'un fichier de configuration ou de métadonnées
        metadata_file = os.path.join(results_folder, "metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if "acquisition_mode" in metadata:
                        return metadata["acquisition_mode"]
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du fichier metadata.json: {str(e)}")
        
        # Analyse du nom du dossier
        folder_name = os.path.basename(results_folder)
        if "expert" in folder_name.lower():
            return "expert"
        elif "client" in folder_name.lower():
            return "client"
        
        # Par défaut
        return "inconnu"
    
    def _load_acquisition_data(self, results_folder: str) -> Optional[pd.DataFrame]:
        """
        Charge les données d'acquisition à partir du dossier de résultats
        
        Args:
            results_folder: Chemin vers le dossier de résultats
            
        Returns:
            DataFrame pandas contenant les données ou None en cas d'erreur
        """
        # Recherche des fichiers CSV dans le dossier
        csv_files = list(Path(results_folder).glob("*.csv"))
        
        if not csv_files:
            logger.error(f"Aucun fichier CSV trouvé dans {results_folder}")
            return None
        
        # Utilisation du premier fichier CSV trouvé
        # Dans une implémentation réelle, il faudrait une logique plus sophistiquée
        # pour identifier le bon fichier de données
        data_file = str(csv_files[0])
        logger.info(f"Chargement des données depuis {data_file}")
        
        try:
            # Lecture du fichier CSV
            df = pd.read_csv(data_file, sep=';', decimal=',')
            
            # Vérification des colonnes minimales requises
            required_columns = ["Volume", "Epaisseur"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Colonnes manquantes dans le fichier CSV: {missing_columns}")
                return None
            
            return df
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier CSV: {str(e)}")
            return None
    
    def calculate_statistics(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calcule les statistiques à partir des données d'acquisition
        
        Args:
            data: DataFrame pandas contenant les données d'acquisition
            
        Returns:
            Dictionnaire avec les statistiques calculées
        """
        if data is None or data.empty:
            logger.error("Impossible de calculer les statistiques: données manquantes ou vides")
            return {
                "slope": 0.0,
                "intercept": 0.0,
                "r2": 0.0,
                "outliers_count": 0,
                "outliers_percentage": 0.0
            }
        
        statistics = {}
        
        try:
            # Calcul de la régression linéaire (Volume en fonction de l'épaisseur)
            x = data["Epaisseur"].values
            y = data["Volume"].values
            
            # Suppression des valeurs NaN
            mask = ~np.isnan(x) & ~np.isnan(y)
            x = x[mask]
            y = y[mask]
            
            if len(x) < 2:
                logger.warning("Pas assez de données pour calculer une régression linéaire")
                return {
                    "slope": 0.0,
                    "intercept": 0.0,
                    "r2": 0.0,
                    "outliers_count": 0,
                    "outliers_percentage": 0.0
                }
            
            # Calcul de la régression linéaire
            slope, intercept = np.polyfit(x, y, 1)
            
            # Calcul du coefficient de détermination R²
            y_pred = slope * x + intercept
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            ss_res = np.sum((y - y_pred) ** 2)
            r2 = 1 - (ss_res / ss_tot)
            
            # Détection des valeurs aberrantes (outliers)
            # Considère comme aberrant un point dont l'écart à la droite de régression
            # est supérieur à 2 fois l'écart-type des résidus
            residuals = y - y_pred
            residual_std = np.std(residuals)
            outliers_mask = np.abs(residuals) > 2 * residual_std
            outliers_count = np.sum(outliers_mask)
            outliers_percentage = (outliers_count / len(x)) * 100
            
            statistics = {
                "slope": slope,
                "intercept": intercept,
                "r2": r2,
                "outliers_count": int(outliers_count),
                "outliers_percentage": outliers_percentage
            }
            
            logger.info(f"Statistiques calculées: pente={slope:.4f}, R²={r2:.4f}, "
                       f"outliers={outliers_count}/{len(x)} ({outliers_percentage:.2f}%)")
            
            return statistics
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                "slope": 0.0,
                "intercept": 0.0,
                "r2": 0.0,
                "outliers_count": 0,
                "outliers_percentage": 0.0
            }
    
    def generate_graphs(self, data: pd.DataFrame) -> List[str]:
        """
        Génère des graphiques à partir des données d'acquisition
        
        Args:
            data: DataFrame pandas contenant les données d'acquisition
            
        Returns:
            Liste des chemins vers les graphiques générés
        """
        if data is None or data.empty:
            logger.error("Impossible de générer des graphiques: données manquantes ou vides")
            return []
        
        graph_paths = []
        
        try:
            # Configuration du style des graphiques
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # 1. Graphique Volume en fonction de l'Épaisseur
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            
            # Données pour la régression linéaire
            x = data["Epaisseur"].values
            y = data["Volume"].values
            
            # Suppression des valeurs NaN
            mask = ~np.isnan(x) & ~np.isnan(y)
            x = x[mask]
            y = y[mask]
            
            # Calcul de la régression linéaire
            slope, intercept = np.polyfit(x, y, 1)
            
            # Tracé des points
            ax1.scatter(x, y, color='#009967', alpha=0.7, label='Mesures')
            
            # Tracé de la droite de régression
            x_line = np.linspace(min(x), max(x), 100)
            y_line = slope * x_line + intercept
            ax1.plot(x_line, y_line, color='#007d54', linestyle='-', linewidth=2,
                    label=f'Régression: y = {slope:.4f}x + {intercept:.4f}')
            
            # Calcul du R²
            y_pred = slope * x + intercept
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            ss_res = np.sum((y - y_pred) ** 2)
            r2 = 1 - (ss_res / ss_tot)
            
            # Ajout du R² au graphique
            ax1.text(0.05, 0.95, f'R² = {r2:.4f}', transform=ax1.transAxes,
                    fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Configuration du graphique
            ax1.set_title('Volume en fonction de l\'Épaisseur', fontsize=14)
            ax1.set_xlabel('Épaisseur (µm)', fontsize=12)
            ax1.set_ylabel('Volume (nL)', fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.legend(loc='lower right')
            
            # Sauvegarde du graphique
            volume_vs_thickness_path = os.path.join(self.output_dir, 'volume_vs_thickness.png')
            fig1.savefig(volume_vs_thickness_path, dpi=300, bbox_inches='tight')
            plt.close(fig1)
            
            graph_paths.append(volume_vs_thickness_path)
            logger.info(f"Graphique généré: {volume_vs_thickness_path}")
            
            # 2. Graphique Épaisseur en fonction du Volume
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            # Tracé des points
            ax2.scatter(y, x, color='#17a2b8', alpha=0.7, label='Mesures')
            
            # Calcul de la régression linéaire (inverse)
            slope_inv, intercept_inv = np.polyfit(y, x, 1)
            
            # Tracé de la droite de régression
            y_line = np.linspace(min(y), max(y), 100)
            x_line = slope_inv * y_line + intercept_inv
            ax2.plot(y_line, x_line, color='#0c7b8a', linestyle='-', linewidth=2,
                    label=f'Régression: y = {slope_inv:.4f}x + {intercept_inv:.4f}')
            
            # Calcul du R² (inverse)
            x_pred = slope_inv * y + intercept_inv
            ss_tot_inv = np.sum((x - np.mean(x)) ** 2)
            ss_res_inv = np.sum((x - x_pred) ** 2)
            r2_inv = 1 - (ss_res_inv / ss_tot_inv)
            
            # Ajout du R² au graphique
            ax2.text(0.05, 0.95, f'R² = {r2_inv:.4f}', transform=ax2.transAxes,
                    fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Configuration du graphique
            ax2.set_title('Épaisseur en fonction du Volume', fontsize=14)
            ax2.set_xlabel('Volume (nL)', fontsize=12)
            ax2.set_ylabel('Épaisseur (µm)', fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.7)
            ax2.legend(loc='lower right')
            
            # Sauvegarde du graphique
            thickness_vs_volume_path = os.path.join(self.output_dir, 'thickness_vs_volume.png')
            fig2.savefig(thickness_vs_volume_path, dpi=300, bbox_inches='tight')
            plt.close(fig2)
            
            graph_paths.append(thickness_vs_volume_path)
            logger.info(f"Graphique généré: {thickness_vs_volume_path}")
            
            # 3. Graphique de distribution des résidus
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            
            # Calcul des résidus
            residuals = y - y_pred
            
            # Tracé de l'histogramme des résidus
            ax3.hist(residuals, bins=20, color='#ffc107', alpha=0.7, edgecolor='black')
            
            # Ajout d'une ligne verticale à zéro
            ax3.axvline(x=0, color='#dc3545', linestyle='--', linewidth=2)
            
            # Configuration du graphique
            ax3.set_title('Distribution des Résidus', fontsize=14)
            ax3.set_xlabel('Résidu (Volume observé - Volume prédit)', fontsize=12)
            ax3.set_ylabel('Fréquence', fontsize=12)
            ax3.grid(True, linestyle='--', alpha=0.7)
            
            # Sauvegarde du graphique
            residuals_path = os.path.join(self.output_dir, 'residuals_distribution.png')
            fig3.savefig(residuals_path, dpi=300, bbox_inches='tight')
            plt.close(fig3)
            
            graph_paths.append(residuals_path)
            logger.info(f"Graphique généré: {residuals_path}")
            
            return graph_paths
        except Exception as e:
            logger.error(f"Erreur lors de la génération des graphiques: {str(e)}")
            return graph_paths