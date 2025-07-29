#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de génération de rapports pour l'assistant d'installation ZymoSoft
"""

import os
import logging
import json
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

showSubItemValid = False
showSubItemErrors = True

class ReportGenerator:
    """
    Classe responsable de la génération des rapports PDF
    pour les différentes étapes de l'assistant d'installation
    """

    def __init__(self, templates_dir: str = None, output_dir: str = None):
        """
        Initialise le générateur de rapports

        Args:
            templates_dir: Répertoire contenant les templates HTML
                          (par défaut: dossier templates/ du projet)
            output_dir: Répertoire de sortie pour les rapports générés
                       (par défaut: dossier reports/ du projet)
        """
        # Détermination du répertoire des templates
        if templates_dir is None:
            # Utilise le dossier templates/ du projet
            self.templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "templates"
            )
        else:
            self.templates_dir = templates_dir

        # Détermination du répertoire de sortie
        if output_dir is None:
            # Utilise le dossier reports/ du projet
            self.output_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "reports"
            )
        else:
            self.output_dir = output_dir

        # Création du répertoire de sortie s'il n'existe pas
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialisation de l'environnement Jinja2
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )

        logger.info(f"Générateur de rapports initialisé avec templates: {self.templates_dir}, "
                   f"sortie: {self.output_dir}")

    def _get_installation_dir(self, installation_id: str) -> str:
        """
        Retourne le chemin du sous-dossier pour une installation spécifique

        Args:
            installation_id: Identifiant de l'installation

        Returns:
            Chemin complet du sous-dossier
        """
        if not installation_id:
            return self.output_dir

        # Création du sous-dossier pour l'installation
        installation_dir = os.path.join(self.output_dir, installation_id)
        os.makedirs(installation_dir, exist_ok=True)

        return installation_dir

    def _create_wrapped_table(self, data, col_widths, header_color=colors.HexColor("#009967")):
        """
        Crée un tableau avec un wrapping de texte amélioré pour éviter les débordements

        Args:
            data: Données du tableau (liste de listes)
            col_widths: Largeurs des colonnes
            header_color: Couleur de l'en-tête (par défaut: vert ZymoSoft)

        Returns:
            Table: Objet Table avec style appliqué
        """
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']

        # Convertir les cellules en Paragraph pour permettre le wrapping
        processed_data = []
        for row_idx, row in enumerate(data):
            processed_row = []
            for col_idx, cell in enumerate(row):
                # Si c'est déjà un Paragraph, on le garde tel quel
                if isinstance(cell, Paragraph):
                    processed_row.append(cell)
                else:
                    # Sinon, on le convertit en Paragraph
                    processed_row.append(Paragraph(str(cell), normal_style))
            processed_data.append(processed_row)

        # Créer le tableau avec les données traitées
        table = Table(processed_data, colWidths=col_widths)

        # Appliquer un style avec padding supplémentaire et wrapping amélioré
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
            # Ajouter plus de padding pour éviter les débordements
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))

        return table

    def generate_step2_report(self, checks: Dict[str, Any]) -> str:
        """
        Génère un rapport PDF pour l'étape 2 (vérifications pré-validation)

        Args:
            checks: Dictionnaire contenant les résultats des vérifications

        Returns:
            Chemin vers le fichier PDF généré
        """
        logger.info("Génération du rapport de l'étape 2 (vérifications pré-validation)")

        # Préparation des données
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"rapport_verification_{timestamp}.pdf"

        # Utilisation du sous-dossier de l'installation si disponible
        installation_id = checks.get("installation_id", "")
        output_dir = self._get_installation_dir(installation_id)
        pdf_path = os.path.join(output_dir, pdf_filename)

        # Création du document PDF avec marges uniformes
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )
        styles = getSampleStyleSheet()
        elements = []

        # Styles personnalisés
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.HexColor("#009967"),
            spaceAfter=18,
            alignment=1  # Centré
        )
        h1_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor("#009967"),
            spaceAfter=12,
            spaceBefore=12
        )
        h2_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor("#009967"),
            marginLeft=10,
            spaceAfter=8,
            spaceBefore=8
        )
        h3_style = ParagraphStyle(
            'Heading3',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor("#009967"),
            spaceAfter=6,
            spaceBefore=6
        )
        normal_style = styles['Normal']

        # Largeur totale pour les tableaux (largeur page - marges)
        total_width = letter[0] - doc.leftMargin - doc.rightMargin

        # Titre principal
        elements.append(Paragraph("Rapport de vérification de l'installation ZymUpload", title_style))
        elements.append(Paragraph(f"Date : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 0.3 * cm))

        # Section 1 : Résumé global
        elements.append(Paragraph("1. Résumé global", h1_style))
        elements.append(Paragraph(
            "Ce rapport présente les résultats détaillés des vérifications de l'installation ZymUpload, "
            "incluant la structure des dossiers et la validité des fichiers de configuration principaux.", normal_style))
        elements.append(Spacer(1, 0.2 * cm))

        # Statut global
        if checks.get("installation_valid", False):
            elements.append(Paragraph("Statut global : <font color='green'>✓ Installation valide</font>", normal_style))
        else:
            elements.append(Paragraph("Statut global : <font color='red'>✗ Installation non valide</font>", normal_style))
        elements.append(Spacer(1, 0.2 * cm))

        # Section 2 : Erreurs et avertissements
        elements.append(Paragraph("2. Erreurs et avertissements", h1_style))
        errors = []
        warnings = []

        # Collecter toutes les erreurs et avertissements
        for key, value in checks.items():
            if isinstance(value, dict) and "errors" in value:
                errors.extend(value["errors"])
            if isinstance(value, dict) and "warnings" in value:
                warnings.extend(value["warnings"])

        # Filtrer les erreurs qui seront affichées dans les sections détaillées
        # Note: Cette partie est préventive, car les erreurs seront filtrées dans les sections détaillées
        # mais nous les collectons ici avant qu'elles ne soient filtrées

        if errors:
            elements.append(Paragraph("2.1 Erreurs détectées", h2_style))
            for error in errors:
                elements.append(Paragraph(f"• <font color='red'>{error}</font>", normal_style))
            elements.append(Spacer(1, 0.1 * cm))
        if warnings:
            elements.append(Paragraph("2.2 Avertissements", h2_style))
            for warning in warnings:
                elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", normal_style))
            elements.append(Spacer(1, 0.1 * cm))
        if not errors and not warnings:
            elements.append(Paragraph("Aucune erreur ni avertissement détecté.", normal_style))
            elements.append(Spacer(1, 0.1 * cm))

        # Section 3 : Structure de l'installation
        elements.append(Paragraph("3. Structure de l'installation", h1_style))
        elements.append(Paragraph(
            "Cette section détaille la présence des dossiers et fichiers essentiels à l'installation.", normal_style))
        elements.append(Spacer(1, 0.1 * cm))

        structure_results = checks.get("structure", {})
        data = [["Élément", "Statut"]]
        for key, value in structure_results.items():
            if key != "installation_valid":
                item_text = key.replace("_exists", "").replace("_", " ").capitalize()
                status = "✓" if value else "✗"
                status_color = "green" if value else "red"
                data.append([item_text, f"<font color='{status_color}'>{status}</font>"])
        if len(data) > 1:
            table = self._create_wrapped_table(data, [0.7 * total_width, 0.3 * total_width])
            elements.append(table)
            elements.append(Spacer(1, 0.2 * cm))

        # Section 4 : Vérification des fichiers de configuration
        elements.append(Paragraph("4. Vérification des fichiers de configuration", h1_style))

        # 4.1 Config.ini
        config_ini_results = checks.get("config_ini", {})
        elements.append(Paragraph("4.1 Config.ini", h2_style))
        elements.append(Paragraph(
            "Vérification des paramètres critiques du fichier <b>Config.ini</b>.", normal_style))
        status_text = "✓ Valide" if config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if config_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut : <font color='{status_color}'>{status_text}</font>", normal_style))
        elements.append(Spacer(1, 0.1 * cm))
        # Ajout colonne Statut
        checks_list = [
            ("Application.ExpertMode", "ExpertMode"),
            ("Application.ExportAcquisitionDetailResults", "ExportAcquisitionDetailResults"),
            ("Hardware.Controller", "Controller"),
            ("Interf.Worker", "Worker"),
            ("Reflecto.Worker", "Worker")
        ]
        values = config_ini_results.get("values", {})
        data = [["Paramètre", "Valeur", "Statut"]]

        # Ensemble pour suivre les erreurs déjà affichées
        displayed_errors = set()

        for param, key in checks_list:
            value = values.get(param, "")
            statut = "✓"
            if "errors" in config_ini_results and any(param.split(".")[1] in e for e in config_ini_results["errors"]):
                statut = "✗"
                # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                for err in config_ini_results.get("errors", []):
                    if param.split(".")[1] in err:
                        displayed_errors.add(err)
            elif value == "":
                statut = "✗"
            status_color = "green" if statut == "✓" else "red"
            data.append([param, str(value), f"<font color='{status_color}'>{statut}</font>"])
        # Affichage des erreurs spécifiques (autres que les paramètres ci-dessus)
        if "errors" in config_ini_results:
            for err in config_ini_results["errors"]:
                if not any(k in err for _, k in checks_list) and err not in displayed_errors:
                    data.append(["Erreur", err, "<font color='red'>✗</font>"])
        table = self._create_wrapped_table(data, [0.45 * total_width, 0.4 * total_width, 0.15 * total_width])
        elements.append(table)
        elements.append(Spacer(1, 0.1 * cm))

        # 4.2 PlateConfig.ini
        plate_config_ini_results = checks.get("plate_config_ini", {})
        elements.append(Paragraph("4.2 PlateConfig.ini", h2_style))
        elements.append(Paragraph(
            "Vérification des types de plaques et des configurations associées dans <b>PlateConfig.ini</b>.", normal_style))
        status_text = "✓ Valide" if plate_config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if plate_config_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut : <font color='{status_color}'>{status_text}</font>", normal_style))
        elements.append(Spacer(1, 0.1 * cm))
        data = [["Type/Paramètre", "Valeur", "Statut"]]
        # Types de plaques
        plate_types = plate_config_ini_results.get("plate_types", [])
        for pt in plate_types:
            data.append([
                "Type de plaque",
                f"{pt.get('name','')} ({pt.get('config','')})",
                "<font color='green'>✓</font>"
            ])
        # Ensemble pour suivre les erreurs déjà affichées
        displayed_errors = set()

        # Configs de plaques
        configs = plate_config_ini_results.get("configs", {})
        for config_name, config in configs.items():
            # InterfParams
            if config.get("interf_params"):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(config["interf_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                    # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                    for err in plate_config_ini_results.get("errors", []):
                        if config["interf_params"] in err:
                            displayed_errors.add(err)
                status_color = "green" if statut == "✓" else "red"

                should_append = statut == "✗" and showSubItemErrors or statut == "✓" and showSubItemValid

                if should_append :
                    data.append([
                        f"{config_name}.InterfParams",
                        config["interf_params"],
                        f"<font color='{status_color}'>{statut}</font>"
                    ])

            # ReflectoParams
            if config.get("reflecto_params"):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(config["reflecto_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                    # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                    for err in plate_config_ini_results.get("errors", []):
                        if config["reflecto_params"] in err:
                            displayed_errors.add(err)
                status_color = "green" if statut == "✓" else "red"

                should_append = statut == "✗" and showSubItemErrors or statut == "✓" and showSubItemValid

                if should_append :
                    data.append([
                        f"{config_name}.ReflectoParams",
                        config["reflecto_params"],
                        f"<font color='{status_color}'>{statut}</font>"
                    ])
            # Fichiers de température
            for temp in config.get("temperature_files", []):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(temp['file'] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                    # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                    for err in plate_config_ini_results.get("errors", []):
                        if temp['file'] in err:
                            displayed_errors.add(err)
                status_color = "green" if statut == "✓" else "red"

                should_append = statut == "✗" and showSubItemErrors or statut == "✓" and showSubItemValid

                if should_append :
                    # Ajout du nom de la configuration et de la clé
                    data.append([
                        f"{config_name}.{temp['key']}",
                        temp['file'],
                        f"<font color='{status_color}'>{statut}</font>"
                    ])
        # Erreurs spécifiques (seulement celles qui n'ont pas déjà été affichées)
        if "errors" in plate_config_ini_results:
            for err in plate_config_ini_results["errors"]:
                if err not in displayed_errors:
                    data.append(["Erreur", err, "<font color='red'>✗</font>"])

        table = self._create_wrapped_table(data, [0.45 * total_width, 0.4 * total_width, 0.15 * total_width])
        elements.append(table)
        elements.append(Spacer(1, 0.1 * cm))

        # 4.3 ZymoCubeCtrl.ini
        zymocube_ctrl_ini_results = checks.get("zymocube_ctrl_ini", {})
        elements.append(Paragraph("4.3 ZymoCubeCtrl.ini", h2_style))
        elements.append(Paragraph(
            "Vérification des paramètres principaux du fichier <b>ZymoCubeCtrl.ini</b>.", normal_style))
        status_text = "✓ Valide" if zymocube_ctrl_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if zymocube_ctrl_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut : <font color='{status_color}'>{status_text}</font>", normal_style))
        elements.append(Spacer(1, 0.1 * cm))
        data = [["Paramètre", "Valeur", "Statut"]]
        values = zymocube_ctrl_ini_results.get("values", {})

        # Ensemble pour suivre les erreurs déjà affichées
        displayed_errors = set()

        for param, value in values.items():
            statut = "✓"
            if "errors" in zymocube_ctrl_ini_results and any(param in e for e in zymocube_ctrl_ini_results["errors"]):
                statut = "✗"
                # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                for err in zymocube_ctrl_ini_results.get("errors", []):
                    if param in err:
                        displayed_errors.add(err)
            status_color = "green" if statut == "✓" else "red"
            data.append([param, str(value), f"<font color='{status_color}'>{statut}</font>"])
        # Types de plaques
        plate_types = zymocube_ctrl_ini_results.get("plate_types", [])
        for pt in plate_types:
            data.append(["PlateType", pt, "<font color='green'>✓</font>"])
        # Erreurs spécifiques (seulement celles qui n'ont pas déjà été affichées)
        if "errors" in zymocube_ctrl_ini_results:
            for err in zymocube_ctrl_ini_results["errors"]:
                if err not in displayed_errors:
                    data.append(["Erreur", err, "<font color='red'>✗</font>"])
        table = self._create_wrapped_table(data, [0.45 * total_width, 0.4 * total_width, 0.15 * total_width])
        elements.append(table)
        elements.append(Spacer(1, 0.1 * cm))

        # Pied de page
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(
            "Rapport généré automatiquement par ZymUpload", styles['Italic']))

        # Génération du PDF
        doc.build(elements)

        logger.info(f"Rapport de l'étape 2 généré: {pdf_path}")
        return pdf_path

    def generate_acquisition_report(self, analysis: Dict[str, Any]) -> str:
        """
        Génère un rapport PDF pour une acquisition (étape 3)

        Args:
            analysis: Dictionnaire contenant les résultats d'analyse de l'acquisition

        Returns:
            Chemin vers le fichier PDF généré
        """
        logger.info("Génération du rapport d'acquisition (étape 3)")

        try:
            # Préparation des données
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"rapport_acquisition_{timestamp}.pdf"

            # Utilisation du sous-dossier de l'installation si disponible
            installation_id = analysis.get("installation_id", "")
            output_dir = self._get_installation_dir(installation_id)
            pdf_path = os.path.join(output_dir, pdf_filename)

            # Création du document PDF avec des marges réduites
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                leftMargin=0.5*inch,
                rightMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            styles = getSampleStyleSheet()
            elements = []

            # Styles personnalisés avec hiérarchie claire
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                textColor=colors.HexColor("#009967"),
                spaceAfter=12,
                fontSize=20,
                alignment=1  # Centré
            )
            heading_style = ParagraphStyle(
                'Heading1',
                parent=styles['Heading1'],
                textColor=colors.HexColor("#009967"),
                spaceAfter=8,
                spaceBefore=12,
                fontSize=16
            )
            subheading_style = ParagraphStyle(
                'Heading2',
                parent=styles['Heading2'],
                textColor=colors.HexColor("#009967"),
                spaceAfter=6,
                spaceBefore=8,
                fontSize=14,
                leftIndent=10
            )
            section_style = ParagraphStyle(
                'Heading3',
                parent=styles['Heading3'],
                textColor=colors.HexColor("#009967"),
                spaceAfter=4,
                spaceBefore=6,
                fontSize=12,
                leftIndent=20
            )
            normal_style = styles['Normal']

            # Définir des largeurs de colonnes standard pour tous les tableaux
            # Largeur totale disponible (7 pouces)
            total_width = 7.0 * inch

            # En-tête moderne avec couleur de fond et logo
            header_data = [["Rapport d'acquisition ZymoSoft"]]
            header_table = Table(header_data, colWidths=[total_width])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#009967")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
            ]))
            elements.append(header_table)

            # Titre et date
            elements.append(Paragraph("Rapport d'acquisition ZymoSoft", title_style))
            elements.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
            elements.append(Spacer(1, 0.25*inch))

            # Informations sur l'acquisition
            elements.append(Paragraph("1. Informations sur l'acquisition", heading_style))

            # Tableau des informations
            data = [
                ["Paramètre", "Valeur"],
                ["Type de plaque", analysis.get("plate_type", "inconnu")],
                ["Mode d'acquisition", analysis.get("acquisition_mode", "inconnu")],
                ["Dossier de résultats", analysis.get("folder", "")],
                ["Statut", "✓ Acquisition valide" if analysis.get("valid", False) else "✗ Acquisition non valide"]
            ]

            # Ajouter les commentaires s'ils existent
            comments = analysis.get("comments", "")
            if comments:
                data.append(["Commentaires", comments])

            # Utiliser des largeurs de colonnes standard
            col_widths = [total_width * 0.3, total_width * 0.7]
            table = self._create_wrapped_table(data, col_widths)
            elements.append(table)
            elements.append(Spacer(1, 0.15*inch))

            # Statistiques
            statistics = analysis.get("statistics", {})
            if statistics:
                elements.append(Paragraph("2. Statistiques d'acquisition", heading_style))

                stats_data = [
                    ["Paramètre", "Valeur"],
                    ["Pente", str(round(statistics.get("slope", 0), 4))],
                    ["Ordonnée à l'origine", str(round(statistics.get("intercept", 0), 4))],
                    ["Coefficient de détermination (R²)", str(round(statistics.get("r2", 0), 4))],
                    ["Nombre de valeurs aberrantes", str(statistics.get("outliers_count", 0))],
                    ["Pourcentage de valeurs aberrantes", f"{round(statistics.get('outliers_percentage', 0), 2)}%"]
                ]

                # Utiliser les largeurs de colonnes standard
                stats_table = self._create_wrapped_table(stats_data, col_widths)
                elements.append(stats_table)
                elements.append(Spacer(1, 0.15*inch))

            # Résultats de validation (comparaison aux références)
            validation = analysis.get("validation", {})
            if validation and "comparison" in validation:
                elements.append(Paragraph("3. Résultats de validation", heading_style))
                elements.append(Paragraph("3.1 Comparaison aux références", subheading_style))

                # Import des critères de validation
                from zymosoft_assistant.utils.constants import VALIDATION_CRITERIA

                comp = validation["comparison"]

                # Préparation des données pour le tableau
                validation_data = [
                    ["Paramètre", "Valeur", "Critère de référence", "Statut"]
                ]

                # Définition des paramètres à afficher
                validation_params = [
                    ("Pente (validation)", comp.get("slope", 0), "slope"),
                    ("Ordonnée à l'origine (validation)", comp.get("intercept", 0), "intercept"),
                    ("R² (validation)", comp.get("r_value", 0), "r2"),
                    ("Points hors tolérance", comp.get("nb_puits_loin_fit", "N/A"), "nb_puits_loin_fit"),
                    ("Différence relative moyenne", f"{comp.get('diff_mean', 0):.2f}%", None),
                    ("CV de la différence relative", f"{comp.get('diff_cv', 0):.2f}%", None)
                ]

                # Création des lignes du tableau avec vérification des critères
                for param, value, criteria_key in validation_params:
                    status = ""
                    criteria_text = ""

                    if criteria_key and criteria_key in VALIDATION_CRITERIA:
                        criteria = VALIDATION_CRITERIA[criteria_key]

                        # Formatage du texte des critères
                        if criteria_key == "r2":
                            criteria_text = f"> {criteria['min']}"
                        else:
                            criteria_text = f"{criteria['min']} - {criteria['max']}"

                        # Vérification si la valeur respecte les critères
                        try:
                            val = float(value) if isinstance(value, (int, float)) else 0
                            is_valid = val >= criteria['min'] and val <= criteria['max']
                            status = "✓" if is_valid else "✗"
                        except (ValueError, TypeError):
                            status = "?"

                    # Formatage de la valeur pour l'affichage
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:.4f}" if criteria_key in ["slope", "intercept", "r2"] else str(value)
                    else:
                        formatted_value = str(value)

                    validation_data.append([param, formatted_value, criteria_text, status])

                # Utiliser des largeurs de colonnes proportionnelles à la largeur totale
                validation_col_widths = [
                    total_width * 0.35,  # Paramètre
                    total_width * 0.22,  # Valeur
                    total_width * 0.28,  # Critère
                    total_width * 0.15   # Statut
                ]

                # Utiliser la méthode _create_wrapped_table pour une apparence cohérente
                validation_table = self._create_wrapped_table(validation_data, validation_col_widths)

                # Ajout de couleurs conditionnelles pour la colonne de statut
                for i, row in enumerate(validation_data[1:], 1):
                    if row[3] == "✓":
                        validation_table.setStyle(TableStyle([
                            ('TEXTCOLOR', (3, i), (3, i), colors.green),
                            ('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
                        ]))
                    elif row[3] == "✗":
                        validation_table.setStyle(TableStyle([
                            ('TEXTCOLOR', (3, i), (3, i), colors.red),
                            ('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
                        ]))

                elements.append(validation_table)
                elements.append(Spacer(1, 0.15*inch))

            # Comparaison des résultats de puits (Well Results)
            if validation and "well_results_comparison" in validation:
                elements.append(Paragraph("3.2 Comparaison des résultats de puits", subheading_style))

                try:
                    well_results_df = validation["well_results_comparison"]

                    # Préparation des données pour le tableau
                    well_results_data = [["Activité", "Area", "Acquisition", "Référence", "Différence", "Validité"]]

                    # Limiter à 20 lignes maximum pour éviter un rapport trop long
                    max_rows = min(20, len(well_results_df))

                    for i in range(max_rows):
                        row = well_results_df.iloc[i]
                        well_results_data.append([
                            f"{row.get('activité', 0):.2f}",
                            f"{row.get('area', 0)}",
                            f"{row.get('acquisition', 0):.2f}",
                            f"{row.get('reference', 0):.2f}",
                            f"{row.get('CV', 0):.2f}",
                            "✓" if row.get('valid', False) else "✗"
                        ])

                    # Ajouter une ligne indiquant s'il y a plus de données
                    if len(well_results_df) > max_rows:
                        well_results_data.append([f"... {len(well_results_df) - max_rows} lignes supplémentaires non affichées", "", "", "", "", ""])

                    # Utiliser des largeurs de colonnes proportionnelles à la largeur totale
                    well_results_col_widths = [
                        total_width * 0.15,  # Activité
                        total_width * 0.10,  # Area
                        total_width * 0.20,  # Acquisition
                        total_width * 0.20,  # Référence
                        total_width * 0.20,  # Différence
                        total_width * 0.15   # Validité
                    ]

                    # Utiliser la méthode _create_wrapped_table pour une apparence cohérente
                    well_results_table = self._create_wrapped_table(well_results_data, well_results_col_widths)

                    # Ajouter des styles spécifiques pour les indicateurs de validité
                    for i in range(1, len(well_results_data)):
                        if i < len(well_results_data) and well_results_data[i][-1] == "✓":
                            well_results_table.setStyle(TableStyle([
                                ('TEXTCOLOR', (5, i), (5, i), colors.green),
                                ('FONTNAME', (5, i), (5, i), 'Helvetica-Bold')
                            ]))
                        elif i < len(well_results_data) and well_results_data[i][-1] == "✗":
                            well_results_table.setStyle(TableStyle([
                                ('TEXTCOLOR', (5, i), (5, i), colors.red),
                                ('FONTNAME', (5, i), (5, i), 'Helvetica-Bold')
                            ]))

                    elements.append(well_results_table)
                    elements.append(Spacer(1, 0.15*inch))

                    # Ajouter des statistiques globales
                    if not well_results_df.empty:
                        elements.append(Paragraph("3.2.1 Statistiques de comparaison des puits", section_style))

                        # Calculer les statistiques globales
                        diff_mean = well_results_df['CV'].mean() if 'CV' in well_results_df.columns else 0
                        diff_std = well_results_df['CV'].std() if 'CV' in well_results_df.columns else 0

                        # Calculer le taux de validation
                        valid_count = well_results_df['valid'].sum() if 'valid' in well_results_df.columns else 0
                        total_count = len(well_results_df)
                        validation_rate = (valid_count / total_count * 100) if total_count > 0 else 0

                        well_stats_data = [
                            ["Statistique", "Valeur"],
                            ["Différence moyenne", f"{diff_mean:.2f}"],
                            ["Écart-type", f"{diff_std:.2f}"],
                            ["Taux de validation", f"{validation_rate:.2f}% ({valid_count}/{total_count})"]
                        ]

                        # Utiliser les largeurs de colonnes standard
                        well_stats_table = self._create_wrapped_table(well_stats_data, col_widths)
                        elements.append(well_stats_table)
                        elements.append(Spacer(1, 0.15*inch))
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de la comparaison des résultats de puits: {str(e)}", exc_info=True)
                    elements.append(Paragraph(f"Erreur lors de l'affichage des résultats de puits: {str(e)}", normal_style))
                    elements.append(Spacer(1, 0.15*inch))

            # Comparaison LOD/LOQ
            if validation and "lod_loq_comparison" in validation:
                elements.append(Paragraph("3.3 Comparaison des LOD/LOQ", subheading_style))

                try:
                    lod_loq_df = validation["lod_loq_comparison"]

                    # Préparation des données pour le tableau
                    lod_loq_data = [["Area", "LOD Acq", "LOD Ref", "Diff LOD", "LOQ Acq", "LOQ Ref", "Diff LOQ", "Validité"]]

                    # Ajouter les lignes pour chaque area
                    if not lod_loq_df.empty:
                        for i in range(len(lod_loq_df)):
                            row = lod_loq_df.iloc[i]
                            lod_loq_data.append([
                                f"{row.get('Area', 0)}",
                                f"{row.get('LOD_Acq', 0):.4f}",
                                f"{row.get('LOD_Ref', 0):.4f}",
                                f"{row.get('Diff_LOD', 0):.4f}",
                                f"{row.get('LOQ_Acq', 0):.4f}",
                                f"{row.get('LOQ_Ref', 0):.4f}",
                                f"{row.get('Diff_LOQ', 0):.4f}",
                                "✓" if row.get('Lod_Valid', False) and row.get('Loq_Valid', False) else "✗"
                            ])

                    # Utiliser des largeurs de colonnes proportionnelles à la largeur totale
                    lod_loq_col_widths = [
                        total_width * 0.10,  # Area
                        total_width * 0.12,  # LOD Acq
                        total_width * 0.12,  # LOD Ref
                        total_width * 0.12,  # Diff LOD
                        total_width * 0.12,  # LOQ Acq
                        total_width * 0.12,  # LOQ Ref
                        total_width * 0.12,  # Diff LOQ
                        total_width * 0.10   # Validité
                    ]

                    # Utiliser la méthode _create_wrapped_table pour une apparence cohérente
                    lod_loq_table = self._create_wrapped_table(lod_loq_data, lod_loq_col_widths)

                    # Ajouter des styles spécifiques pour les indicateurs de validité
                    for i in range(1, len(lod_loq_data)):
                        if lod_loq_data[i][-1] == "✓":
                            lod_loq_table.setStyle(TableStyle([
                                ('TEXTCOLOR', (7, i), (7, i), colors.green),
                                ('FONTNAME', (7, i), (7, i), 'Helvetica-Bold')
                            ]))
                        elif lod_loq_data[i][-1] == "✗":
                            lod_loq_table.setStyle(TableStyle([
                                ('TEXTCOLOR', (7, i), (7, i), colors.red),
                                ('FONTNAME', (7, i), (7, i), 'Helvetica-Bold')
                            ]))

                    elements.append(lod_loq_table)
                    elements.append(Spacer(1, 0.15*inch))
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de la comparaison LOD/LOQ: {str(e)}", exc_info=True)
                    elements.append(Paragraph(f"Erreur lors de l'affichage des LOD/LOQ: {str(e)}", normal_style))
                    elements.append(Spacer(1, 0.15*inch))

            # Graphiques en grille de 2
            graphs = analysis.get("graphs", [])
            if graphs:
                elements.append(Paragraph("4. Visualisation des données", heading_style))
                elements.append(Paragraph("4.1 Graphiques d'analyse", subheading_style))

                # Traiter les graphiques par paires
                for i in range(0, len(graphs), 2):
                    graph_row = []

                    # Premier graphique de la paire
                    if i < len(graphs) and os.path.exists(graphs[i]):
                        graph_row.append(Image(graphs[i], width=3.5*inch, height=2.5*inch))
                    else:
                        graph_row.append("")

                    # Deuxième graphique de la paire (s'il existe)
                    if i+1 < len(graphs) and os.path.exists(graphs[i+1]):
                        graph_row.append(Image(graphs[i+1], width=3.5*inch, height=2.5*inch))
                    else:
                        graph_row.append("")

                    # Créer une table pour cette paire de graphiques
                    if graph_row[0] or graph_row[1]:  # S'assurer qu'au moins un graphique existe
                        # Utiliser des largeurs proportionnelles à la largeur totale
                        graph_col_widths = [total_width * 0.5, total_width * 0.5]
                        graph_table = Table([graph_row], colWidths=graph_col_widths)
                        graph_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        elements.append(graph_table)
                        elements.append(Spacer(1, 0.15*inch))

            # Analyse des logs
            log_analysis = analysis.get("log_analysis", {})
            if log_analysis:
                elements.append(Paragraph("5. Analyse technique", heading_style))
                elements.append(Paragraph("5.1 Analyse des logs d'acquisition", subheading_style))

                # Type d'acquisition et durée
                acquisition_type = log_analysis.get("acquisition_type", "inconnu")
                acquisition_duration = log_analysis.get("acquisition_duration", {})
                duration_minutes = acquisition_duration.get("duration_minutes", 0)

                log_data = [
                    ["Paramètre", "Valeur"],
                    ["Type d'acquisition", acquisition_type],
                    ["Durée d'acquisition (minutes)", f"{duration_minutes:.2f}"],
                    ["Nombre total de puits", str(log_analysis.get("total_wells", 0))],
                    ["Nombre de drift fixes", str(log_analysis.get("drift_fix_count", 0))],
                    ["Nombre de max retry", str(log_analysis.get("max_retry_count", 0))]
                ]

                # Ajouter les informations spécifiques au type d'acquisition
                if acquisition_type == "prior":
                    log_data.append(["Nombre moyen de loops", f"{log_analysis.get('average_value', 0):.2f}"])
                    log_data.append(["Nombre total de mesures", str(log_analysis.get("total_measurements", 0))])
                    log_data.append(["Mesures 'Done'", str(log_analysis.get("done_measurements", 0))])
                    log_data.append(["Mesures 'Timeout'", str(log_analysis.get("timeout_measurements", 0))])
                else:  # custom_focus
                    log_data.append(["Nombre moyen de moves", f"{log_analysis.get('average_value', 0):.2f}"])
                    log_data.append(["Nombre total de mesures", str(log_analysis.get("total_measurements", 0))])

                # Utiliser les largeurs de colonnes standard
                log_table = self._create_wrapped_table(log_data, col_widths)
                elements.append(log_table)
                elements.append(Spacer(1, 0.15*inch))

            # Erreurs et avertissements
            errors = analysis.get("errors", [])
            warnings = analysis.get("warnings", [])

            if errors or warnings:
                elements.append(Paragraph("6. Problèmes détectés", heading_style))

                if errors:
                    elements.append(Paragraph("6.1 Erreurs critiques", subheading_style))
                    for error in errors:
                        elements.append(Paragraph(f"• <font color='red'>{error}</font>", normal_style))
                    elements.append(Spacer(1, 0.15*inch))

                if warnings:
                    elements.append(Paragraph("6.2 Avertissements", subheading_style))
                    for warning in warnings:
                        elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", normal_style))
                    elements.append(Spacer(1, 0.15*inch))

            # Pied de page
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph("Rapport généré automatiquement par ZymUpload", 
                                    styles['Italic']))

            # Génération du PDF
            doc.build(elements)

            logger.info(f"Rapport d'acquisition généré: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport d'acquisition: {str(e)}", exc_info=True)
            # Ajouter l'erreur à la liste des erreurs dans analysis
            if "errors" not in analysis:
                analysis["errors"] = []
            analysis["errors"].append(f"Impossible de charger les données d'acquisition: {str(e)}")

            # Essayer de générer un rapport minimal avec l'erreur
            try:
                # Création du document PDF avec des marges réduites
                doc = SimpleDocTemplate(
                    pdf_path, 
                    pagesize=letter,
                    leftMargin=0.5*inch,
                    rightMargin=0.5*inch,
                    topMargin=0.5*inch,
                    bottomMargin=0.5*inch
                )
                styles = getSampleStyleSheet()
                elements = []

                # En-tête moderne avec couleur de fond
                header_data = [["Rapport d'acquisition ZymoSoft"]]
                header_table = Table(header_data, colWidths=[7*inch])
                header_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#009967")),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                    ('TOPPADDING', (0, 0), (-1, -1), 15),
                ]))
                elements.append(header_table)

                # Titre et date
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Title'],
                    textColor=colors.HexColor("#009967"),
                    spaceAfter=12,
                    fontSize=18
                )
                heading_style = ParagraphStyle(
                    'Heading2',
                    parent=styles['Heading2'],
                    textColor=colors.HexColor("#009967"),
                    spaceAfter=6
                )
                normal_style = styles['Normal']

                elements.append(Paragraph("Rapport d'acquisition ZymoSoft", title_style))
                elements.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
                elements.append(Spacer(1, 0.25*inch))

                # Informations sur l'acquisition
                elements.append(Paragraph("Informations sur l'acquisition", heading_style))

                # Tableau des informations
                data = [
                    ["Paramètre", "Valeur"],
                    ["Type de plaque", analysis.get("plate_type", "inconnu")],
                    ["Mode d'acquisition", analysis.get("acquisition_mode", "inconnu")],
                    ["Dossier de résultats", analysis.get("folder", "")],
                    ["Statut", "✗ Acquisition non valide"]
                ]

                # Utiliser des largeurs de colonnes standard
                col_widths = [total_width * 0.3, total_width * 0.7]
                table = self._create_wrapped_table(data, col_widths)
                elements.append(table)
                elements.append(Spacer(1, 0.15*inch))

                # Erreurs
                elements.append(Paragraph("Erreurs détectées", heading_style))
                for error in analysis.get("errors", []):
                    elements.append(Paragraph(f"• <font color='red'>{error}</font>", normal_style))
                elements.append(Spacer(1, 0.15*inch))

                # Pied de page
                elements.append(Spacer(1, 0.5*inch))
                elements.append(Paragraph("Rapport généré automatiquement par ZymUpload", 
                                        styles['Italic']))

                # Génération du PDF
                doc.build(elements)

                logger.info(f"Rapport d'acquisition minimal généré avec erreurs: {pdf_path}")
                return pdf_path
            except Exception as inner_e:
                logger.error(f"Erreur lors de la génération du rapport minimal: {str(inner_e)}", exc_info=True)
                return ""

    def generate_final_report(self, full_data: Dict[str, Any]) -> str:
        """
        Génère un rapport PDF final complet (étape 4)

        Args:
            full_data: Dictionnaire contenant toutes les données de l'installation

        Returns:
            Chemin vers le fichier PDF généré
        """
        logger.info("Génération du rapport final (étape 4)")

        # Préparation des données
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        client_name = full_data.get("client_info", {}).get("name", "client").replace(" ", "_")
        pdf_filename = f"rapport_installation_{client_name}_{timestamp}.pdf"

        # Utilisation du sous-dossier de l'installation si disponible
        installation_id = full_data.get("installation_id", "")
        output_dir = self._get_installation_dir(installation_id)
        pdf_path = os.path.join(output_dir, pdf_filename)

        # Création du document PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Largeur totale pour les tableaux (largeur page - marges)
        total_width = letter[0] - doc.leftMargin - doc.rightMargin

        # Styles personnalisés
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            textColor=colors.HexColor("#009967"),
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            textColor=colors.HexColor("#009967"),
            spaceAfter=6
        )
        subheading_style = ParagraphStyle(
            'Heading3',
            parent=styles['Heading3'],
            textColor=colors.HexColor("#009967"),
            spaceAfter=4
        )
        normal_style = styles['Normal']

        # Titre et date
        elements.append(Paragraph("Rapport final d'installation ZymoSoft", title_style))
        elements.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 0.25*inch))

        # Informations client
        elements.append(Paragraph("Informations client", heading_style))

        client_info = full_data.get("client_info", {})
        client_data = [
            ["Paramètre", "Valeur"],
            ["Nom du client", client_info.get("name", "")],
            ["Responsable CS", client_info.get("cs_responsible", "")],
            ["Responsable instrumentation", client_info.get("instrumentation_responsible", "")],
            ["Date de début", full_data.get("timestamp_start", "")],
            ["Identifiant d'installation", full_data.get("installation_id", "")]
        ]

        # Utiliser des largeurs de colonnes standard
        col_widths = [total_width * 0.3, total_width * 0.7]
        client_table = self._create_wrapped_table(client_data, col_widths)
        elements.append(client_table)
        elements.append(Spacer(1, 0.15*inch))

        # Résumé des vérifications
        elements.append(Paragraph("Résumé des vérifications", heading_style))

        step2_checks = full_data.get("step2_checks", {})
        check_results = step2_checks.get("check_results", {}) if "check_results" in step2_checks else step2_checks

        if check_results.get("installation_valid", False):
            elements.append(Paragraph("Statut global: <font color='green'>✓ Installation valide</font>", normal_style))
        else:
            elements.append(Paragraph("Statut global: <font color='red'>✗ Installation non valide</font>", normal_style))
        elements.append(Spacer(1, 0.15*inch))

        # Détails des vérifications de configuration
        elements.append(Paragraph("Détails des vérifications de configuration", heading_style))

        # Extraction et affichage des erreurs et avertissements
        errors = []
        warnings = []
        for key, value in check_results.items():
            if isinstance(value, dict) and "errors" in value:
                errors.extend(value["errors"])
            if isinstance(value, dict) and "warnings" in value:
                warnings.extend(value["warnings"])

        if errors:
            elements.append(Paragraph("Erreurs détectées", subheading_style))
            for error in errors:
                elements.append(Paragraph(f"• <font color='red'>{error}</font>", normal_style))
            elements.append(Spacer(1, 0.15*inch))

        if warnings:
            elements.append(Paragraph("Avertissements", subheading_style))
            for warning in warnings:
                elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", normal_style))
            elements.append(Spacer(1, 0.15*inch))

        # Structure de l'installation
        elements.append(Paragraph("Structure de l'installation", subheading_style))
        structure_results = check_results.get("structure", {})
        data = [["Élément", "Statut"]]
        for key, value in structure_results.items():
            if key != "installation_valid":
                item_text = key.replace("_exists", "").replace("_", " ").capitalize()
                status = "✓" if value else "✗"
                status_color = "green" if value else "red"
                data.append([item_text, f"<font color='{status_color}'>{status}</font>"])
        if len(data) > 1:
            table = self._create_wrapped_table(data, [0.7 * total_width, 0.3 * total_width])
            elements.append(table)
            elements.append(Spacer(1, 0.15*inch))

        # Config.ini
        config_ini_results = check_results.get("config_ini", {})
        if config_ini_results:
            elements.append(Paragraph("Vérification de Config.ini", subheading_style))
            status_text = "✓ Valide" if config_ini_results.get("config_valid", False) else "✗ Non valide"
            status_color = "green" if config_ini_results.get("config_valid", False) else "red"
            elements.append(Paragraph(f"Statut: <font color='{status_color}'>{status_text}</font>", normal_style))
            elements.append(Spacer(1, 0.1*inch))

            # Affichage tableau paramètre/valeur/statut
            values = config_ini_results.get("values", {})
            checks = [
                ("Application.ExpertMode", "ExpertMode"),
                ("Application.ExportAcquisitionDetailResults", "ExportAcquisitionDetailResults"),
                ("Hardware.Controller", "Controller"),
                ("Interf.Worker", "Worker"),
                ("Reflecto.Worker", "Worker")
            ]
            data = [["Paramètre", "Valeur", "Statut"]]
            for param, key in checks:
                value = values.get(param, "")
                statut = "✓"
                if "errors" in config_ini_results and any(param.split(".")[1] in e for e in config_ini_results["errors"]):
                    statut = "✗"
                elif value == "":
                    statut = "✗"
                status_color = "green" if statut == "✓" else "red"
                data.append([param, str(value), f"<font color='{status_color}'>{statut}</font>"])
            # Affichage des erreurs spécifiques (autres que les paramètres ci-dessus)
            if "errors" in config_ini_results:
                for err in config_ini_results["errors"]:
                    if not any(k in err for _, k in checks):
                        data.append(["Erreur", err, "<font color='red'>✗</font>"])
            table = self._create_wrapped_table(data, [0.45*total_width, 0.4*total_width, 0.15*total_width])
            elements.append(table)
            elements.append(Spacer(1, 0.15*inch))

        # PlateConfig.ini
        plate_config_ini_results = check_results.get("plate_config_ini", {})
        elements.append(Paragraph("Vérification de PlateConfig.ini", subheading_style))
        status_text = "✓ Valide" if plate_config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if plate_config_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut: <font color='{status_color}'>{status_text}</font>", normal_style))
        elements.append(Spacer(1, 0.1*inch))

        data = [["Type/Paramètre", "Valeur", "Statut"]]
        # Types de plaques
        plate_types = plate_config_ini_results.get("plate_types", [])
        for pt in plate_types:
            data.append([
                "Type de plaque",
                f"{pt.get('name','')} ({pt.get('config','')})",
                "<font color='green'>✓</font>"
            ])
        # Configs de plaques
        configs = plate_config_ini_results.get("configs", {})
        for config_name, config in configs.items():
            # InterfParams
            if config.get("interf_params"):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(config["interf_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                status_color = "green" if statut == "✓" else "red"
                data.append([
                    f"{config_name}.InterfParams",
                    config["interf_params"],
                    f"<font color='{status_color}'>{statut}</font>"
                ])
            # ReflectoParams
            if config.get("reflecto_params"):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(config["reflecto_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                status_color = "green" if statut == "✓" else "red"
                data.append([
                    f"{config_name}.ReflectoParams",
                    config["reflecto_params"],
                    f"<font color='{status_color}'>{statut}</font>"
                ])
            # Fichiers de température
            for temp in config.get("temperature_files", []):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(temp['file'] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                status_color = "green" if statut == "✓" else "red"
                data.append([
                    f"{config_name}.{temp['key']}",
                    temp['file'],
                    f"<font color='{status_color}'>{statut}</font>"
                ])
        # Erreurs spécifiques
        if "errors" in plate_config_ini_results:
            for err in plate_config_ini_results["errors"]:
                data.append(["Erreur", err, "<font color='red'>✗</font>"])
        table = self._create_wrapped_table(data, [0.45*total_width, 0.4*total_width, 0.15*total_width])
        elements.append(table)
        elements.append(Spacer(1, 0.15*inch))

        # ZymoCubeCtrl.ini
        zymocube_ctrl_ini_results = check_results.get("zymocube_ctrl_ini", {})
        elements.append(Paragraph("Vérification de ZymoCubeCtrl.ini", subheading_style))
        status_text = "✓ Valide" if zymocube_ctrl_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if zymocube_ctrl_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut: <font color='{status_color}'>{status_text}</font>", normal_style))
        elements.append(Spacer(1, 0.1*inch))

        data = [["Paramètre", "Valeur", "Statut"]]
        values = zymocube_ctrl_ini_results.get("values", {})
        for param, value in values.items():
            statut = "✓"
            if "errors" in zymocube_ctrl_ini_results and any(param in e for e in zymocube_ctrl_ini_results["errors"]):
                statut = "✗"
            status_color = "green" if statut == "✓" else "red"
            data.append([param, str(value), f"<font color='{status_color}'>{statut}</font>"])
        # Types de plaques
        plate_types = zymocube_ctrl_ini_results.get("plate_types", [])
        for pt in plate_types:
            data.append(["PlateType", pt, "<font color='green'>✓</font>"])
        # Erreurs spécifiques
        if "errors" in zymocube_ctrl_ini_results:
            for err in zymocube_ctrl_ini_results["errors"]:
                data.append(["Erreur", err, "<font color='red'>✗</font>"])
        table = self._create_wrapped_table(data, [0.45*total_width, 0.4*total_width, 0.15*total_width])
        elements.append(table)
        elements.append(Spacer(1, 0.15*inch))

        # Pied de page
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Rapport généré automatiquement par ZymUpload", 
                                 styles['Italic']))

        # Génération du PDF
        doc.build(elements)

        logger.info(f"Rapport final généré: {pdf_path}")
        return pdf_path

    def _create_html_template(self, template_name: str, default_content: str) -> str:
        """
        Crée un fichier de template HTML s'il n'existe pas

        Args:
            template_name: Nom du fichier de template
            default_content: Contenu par défaut du template

        Returns:
            Chemin vers le fichier de template
        """
        template_path = os.path.join(self.templates_dir, template_name)

        # Vérification si le fichier existe déjà
        if os.path.exists(template_path):
            return template_path

        # Création du fichier avec le contenu par défaut
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(default_content)

        logger.info(f"Template créé: {template_path}")
        return template_path

    def create_default_templates(self) -> None:
        """
        Crée les fichiers de templates HTML par défaut s'ils n'existent pas
        """
        # Template pour le rapport de l'étape 2
        step2_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #009967;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #009967;
            padding-bottom: 10px;
        }
        .section {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .success {
            color: #28a745;
        }
        .error {
            color: #ff0000;
        }
        .warning {
            color: #ffc107;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #009967;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Date: {{ date }}</p>
    </div>

    <div class="section">
        <h2>Résumé des vérifications</h2>
        <p>Statut global: 
            {% if installation_valid %}
            <span class="success">✓ Installation valide</span>
            {% else %}
            <span class="error">✗ Installation non valide</span>
            {% endif %}
        </p>
    </div>

    {% if errors %}
    <div class="section">
        <h2>Erreurs détectées</h2>
        <ul>
            {% for error in errors %}
            <li class="error">{{ error }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    {% if warnings %}
    <div class="section">
        <h2>Avertissements</h2>
        <ul>
            {% for warning in warnings %}
            <li class="warning">{{ warning }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="section">
        <h2>Structure de l'installation</h2>
        <table>
            <tr>
                <th>Élément</th>
                <th>Statut</th>
            </tr>
            {% if checks.bin_exists is defined %}
            <tr>
                <td>Dossier bin/</td>
                <td>{% if checks.bin_exists %}✓{% else %}✗{% endif %}</td>
            </tr>
            {% endif %}
            {% if checks.etc_exists is defined %}
            <tr>
                <td>Dossier etc/</td>
                <td>{% if checks.etc_exists %}✓{% else %}✗{% endif %}</td>
            </tr>
            {% endif %}
            {% if checks.resultats_exists is defined %}
            <tr>
                <td>Dossier Resultats/</td>
                <td>{% if checks.resultats_exists %}✓{% else %}✗{% endif %}</td>
            </tr>
            {% endif %}
            {% if checks.zymocubectrl_exists is defined %}
            <tr>
                <td>ZymoCubeCtrl.exe</td>
                <td>{% if checks.zymocubectrl_exists %}✓{% else %}✗{% endif %}</td>
            </tr>
            {% endif %}
            {% if checks.zymosoft_exists is defined %}
            <tr>
                <td>ZymoSoft.exe</td>
                <td>{% if checks.zymosoft_exists %}✓{% else %}✗{% endif %}</td>
            </tr>
            {% endif %}
            {% if checks.workers_exists is defined %}
            <tr>
                <td>Dossier workers/</td>
                <td>{% if checks.workers_exists %}✓{% else %}✗{% endif %}</td>
            </tr>
            {% endif %}
        </table>
    </div>

    <div class="footer">
        <p>Rapport généré automatiquement par l'Assistant d'installation ZymoSoft</p>
    </div>
</body>
</html>
"""

        # Template pour le rapport d'acquisition
        acquisition_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #009967;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #009967;
            padding-bottom: 10px;
        }
        .section {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .success {
            color: #28a745;
        }
        .error {
            color: #ff0000;
        }
        .warning {
            color: #ffc107;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #009967;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .graph-container {
            text-align: center;
            margin: 20px 0;
        }
        .graph-container img {
            max-width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Date: {{ date }}</p>
    </div>

    <div class="section">
        <h2>Informations sur l'acquisition</h2>
        <table>
            <tr>
                <th>Paramètre</th>
                <th>Valeur</th>
            </tr>
            <tr>
                <td>Type de plaque</td>
                <td>{{ plate_type }}</td>
            </tr>
            <tr>
                <td>Mode d'acquisition</td>
                <td>{{ acquisition_mode }}</td>
            </tr>
            <tr>
                <td>Dossier de résultats</td>
                <td>{{ analysis.folder }}</td>
            </tr>
            <tr>
                <td>Statut</td>
                <td>
                    {% if acquisition_valid %}
                    <span class="success">✓ Acquisition valide</span>
                    {% else %}
                    <span class="error">✗ Acquisition non valide</span>
                    {% endif %}
                </td>
            </tr>
        </table>
    </div>

    {% if statistics %}
    <div class="section">
        <h2>Statistiques</h2>
        <table>
            <tr>
                <th>Paramètre</th>
                <th>Valeur</th>
            </tr>
            <tr>
                <td>Pente</td>
                <td>{{ statistics.slope|round(4) }}</td>
            </tr>
            <tr>
                <td>Ordonnée à l'origine</td>
                <td>{{ statistics.intercept|round(4) }}</td>
            </tr>
            <tr>
                <td>Coefficient de détermination (R²)</td>
                <td>{{ statistics.r2|round(4) }}</td>
            </tr>
            <tr>
                <td>Nombre de valeurs aberrantes</td>
                <td>{{ statistics.outliers_count }}</td>
            </tr>
            <tr>
                <td>Pourcentage de valeurs aberrantes</td>
                <td>{{ statistics.outliers_percentage|round(2) }}%</td>
            </tr>
        </table>
    </div>
    {% endif %}

    {% if graphs %}
    <div class="section">
        <h2>Graphiques</h2>
        {% for graph in graphs %}
        <div class="graph-container">
            <img src="{{ graph }}" alt="Graphique d'analyse">
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if errors %}
    <div class="section">
        <h2>Erreurs détectées</h2>
        <ul>
            {% for error in errors %}
            <li class="error">{{ error }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    {% if warnings %}
    <div class="section">
        <h2>Avertissements</h2>
        <ul>
            {% for warning in warnings %}
            <li class="warning">{{ warning }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="footer">
        <p>Rapport généré automatiquement par l'Assistant d'installation ZymoSoft</p>
    </div>
</body>
</html>
"""

        # Template pour le rapport final
        final_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #009967;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #009967;
            padding-bottom: 10px;
        }
        .section {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .success {
            color: #28a745;
        }
        .error {
            color: #ff0000;
        }
        .warning {
            color: #ffc107;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #009967;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .acquisition-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
        }
        .comments {
            background-color: #f9f9f9;
            padding: 10px;
            border-left: 4px solid #009967;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Date: {{ date }}</p>
    </div>

    <div class="section">
        <h2>Informations client</h2>
        <table>
            <tr>
                <th>Paramètre</th>
                <th>Valeur</th>
            </tr>
            <tr>
                <td>Nom du client</td>
                <td>{{ client_info.name }}</td>
            </tr>
            <tr>
                <td>Responsable CS</td>
                <td>{{ client_info.cs_responsible }}</td>
            </tr>
            <tr>
                <td>Responsable instrumentation</td>
                <td>{{ client_info.instrumentation_responsible }}</td>
            </tr>
            <tr>
                <td>Date de début</td>
                <td>{{ timestamp_start }}</td>
            </tr>
            <tr>
                <td>Identifiant d'installation</td>
                <td>{{ installation_id }}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>Résumé des vérifications</h2>
        <p>Statut global: 
            {% if step2_checks.installation_valid %}
            <span class="success">✓ Installation valide</span>
            {% else %}
            <span class="error">✗ Installation non valide</span>
            {% endif %}
        </p>
    </div>

    <div class="section">
        <h2>Acquisitions réalisées</h2>
        {% if acquisitions %}
            {% for acquisition in acquisitions %}
            <div class="acquisition-card">
                <h3>Acquisition #{{ acquisition.id }}</h3>
                <table>
                    <tr>
                        <td>Type de plaque</td>
                        <td>{{ acquisition.plate_type }}</td>
                    </tr>
                    <tr>
                        <td>Mode</td>
                        <td>{{ acquisition.mode }}</td>
                    </tr>
                    <tr>
                        <td>Dossier de résultats</td>
                        <td>{{ acquisition.results_folder }}</td>
                    </tr>
                    <tr>
                        <td>Statut</td>
                        <td>
                            {% if acquisition.validated %}
                            <span class="success">✓ Validée</span>
                            {% else %}
                            <span class="error">✗ Non validée</span>
                            {% endif %}
                        </td>
                    </tr>
                </table>

                {% if acquisition.analysis %}
                <h4>Statistiques</h4>
                <table>
                    <tr>
                        <td>Pente</td>
                        <td>{{ acquisition.analysis.slope|round(4) }}</td>
                    </tr>
                    <tr>
                        <td>R²</td>
                        <td>{{ acquisition.analysis.r2|round(4) }}</td>
                    </tr>
                </table>
                {% endif %}

                {% if acquisition.comments %}
                <div class="comments">
                    <h4>Commentaires</h4>
                    <p>{{ acquisition.comments }}</p>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <p>Aucune acquisition réalisée.</p>
        {% endif %}
    </div>

    <div class="section">
        <h2>Actions de finalisation</h2>
        <ul>
            {% for action in cleanup_actions %}
            <li>
                {% if action == "client_mode" %}
                Passage en mode client
                {% elif action == "clean_pc" %}
                Nettoyage du PC
                {% else %}
                {{ action }}
                {% endif %}
            </li>
            {% endfor %}
        </ul>
    </div>

    {% if final_comments %}
    <div class="section">
        <h2>Commentaires généraux</h2>
        <div class="comments">
            <p>{{ final_comments }}</p>
        </div>
    </div>
    {% endif %}

    <div class="footer">
        <p>Rapport généré automatiquement par l'Assistant d'installation ZymoSoft</p>
    </div>
</body>
</html>
"""

        # Création des templates
        self._create_html_template("report_step2.html", step2_template)
        self._create_html_template("report_acquisition.html", acquisition_template)
        self._create_html_template("report_final.html", final_template)

        logger.info("Templates par défaut créés")
