#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de génération de rapports pour l'assistant d'installation ZymoSoft
Version complète avec toutes les améliorations
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

    def _get_common_styles(self):
        """
        Retourne les styles communs réutilisables pour tous les rapports

        Returns:
            Dict contenant tous les styles
        """
        styles = getSampleStyleSheet()

        common_styles = {
            'title': ParagraphStyle(
                'Title',
                parent=styles['Title'],
                fontSize=20,
                textColor=colors.HexColor("#009967"),
                spaceAfter=18,
                alignment=1  # Centré
            ),
            'heading1': ParagraphStyle(
                'Heading1',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor("#009967"),
                spaceAfter=12,
                spaceBefore=12
            ),
            'heading2': ParagraphStyle(
                'Heading2',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor("#009967"),
                spaceAfter=8,
                spaceBefore=8,
                leftIndent=10
            ),
            'heading3': ParagraphStyle(
                'Heading3',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor("#009967"),
                spaceAfter=6,
                spaceBefore=6,
                leftIndent=20
            ),
            'normal': styles['Normal'],
            'italic': styles['Italic']
        }

        return common_styles

    def _create_report_header(self, elements, title: str, total_width: float):
        """
        Crée un en-tête de rapport commun avec logo et titre

        Args:
            elements: Liste des éléments du rapport
            title: Titre du rapport
            total_width: Largeur totale disponible
        """
        # Chemin vers le logo (à remplacer par le vrai chemin)
        logo_path = "assets/logo_zymosoft.png"  # Vous remplacerez ce chemin

        # Créer l'en-tête avec logo et titre
        if os.path.exists(logo_path):
            # En-tête avec logo
            header_data = [[Image(logo_path, width=2 * inch, height=1 * inch), title]]
            header_table = Table(header_data, colWidths=[2.5 * inch, total_width - 2.5 * inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#009967")),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 18),
            ]))
        else:
            # En-tête sans logo (fallback)
            header_data = [[title]]
            header_table = Table(header_data, colWidths=[total_width])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#009967")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 18),
            ]))

        elements.append(header_table)
        elements.append(Spacer(1, 0.25 * inch))

    def _create_wrapped_table(self, data, col_widths, header_color=colors.HexColor("#009967")):
        """
        Crée un tableau avec un wrapping de texte amélioré et coloration automatique des statuts

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
                    # Traitement spécial pour les cellules de statut avec icônes
                    cell_text = str(cell)
                    if "✓" in cell_text:
                        # Statut valide - texte vert
                        cell_text = cell_text.replace("<font color='green'>", "").replace("</font>", "")
                        processed_row.append(Paragraph(f"<font color='green'>{cell_text}</font>", normal_style))
                    elif "✗" in cell_text:
                        # Statut invalide - texte rouge
                        cell_text = cell_text.replace("<font color='red'>", "").replace("</font>", "")
                        processed_row.append(Paragraph(f"<font color='red'>{cell_text}</font>", normal_style))
                    else:
                        # Cellule normale
                        processed_row.append(Paragraph(cell_text, normal_style))
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

    def _determine_plate_type_context(self, analysis: Dict[str, Any]) -> tuple:
        """
        Détermine le contexte du type de plaque (nanofilm vs micro-dépôt)

        Args:
            analysis: Dictionnaire contenant les résultats d'analyse

        Returns:
            tuple: (is_nanofilm, type_description)
        """
        plate_type = analysis.get("plate_type", "").lower()
        is_nanofilm = "nanofilm" in plate_type

        if is_nanofilm:
            return True, "en épaisseur"
        else:
            return False, "en volume"

    def generate_step2_report(self, checks: Dict[str, Any]) -> str:
        """
        Generates a step 2 verification report in PDF format based on various installation
        checks. The report includes summary, errors, warnings, installation structure,
        and configuration file validations.

        :param checks: A dictionary containing details about verification results. It should
                       include keys such as 'installation_id', 'installation_valid',
                       'structure', 'errors', 'warnings', and detailed results for specific
                       configuration file checks like 'config_ini' and 'plate_config_ini'.

        :return: Path to the generated PDF report as a string.
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

        elements = []

        # Styles communs
        styles = self._get_common_styles()

        # Largeur totale pour les tableaux (largeur page - marges)
        total_width = letter[0] - doc.leftMargin - doc.rightMargin

        # En-tête du rapport
        self._create_report_header(elements, "Rapport de vérification de l'installation ZymUpload", total_width)

        # Date
        elements.append(Paragraph(f"Date : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['normal']))
        elements.append(Spacer(1, 0.3 * cm))

        # Section 1 : Résumé global
        elements.append(Paragraph("1. Résumé global", styles['heading1']))
        elements.append(Paragraph(
            "Ce rapport présente les résultats détaillés des vérifications de l'installation ZymUpload, "
            "incluant la structure des dossiers et la validité des fichiers de configuration principaux.",
            styles['normal']))
        elements.append(Spacer(1, 0.2 * cm))

        # Statut global
        if checks.get("installation_valid", False):
            elements.append(
                Paragraph("Statut global : <font color='green'>✓ Installation valide</font>", styles['normal']))
        else:
            elements.append(
                Paragraph("Statut global : <font color='red'>✗ Installation non valide</font>", styles['normal']))
        elements.append(Spacer(1, 0.2 * cm))

        # Section 2 : Erreurs et avertissements
        elements.append(Paragraph("2. Erreurs et avertissements", styles['heading1']))
        errors = []
        warnings = []

        # Collecter toutes les erreurs et avertissements
        for key, value in checks.items():
            if isinstance(value, dict) and "errors" in value:
                errors.extend(value["errors"])
            if isinstance(value, dict) and "warnings" in value:
                warnings.extend(value["warnings"])

        if errors:
            elements.append(Paragraph("2.1 Erreurs détectées", styles['heading2']))
            for error in errors:
                elements.append(Paragraph(f"• <font color='red'>{error}</font>", styles['normal']))
            elements.append(Spacer(1, 0.1 * cm))
        if warnings:
            elements.append(Paragraph("2.2 Avertissements", styles['heading2']))
            for warning in warnings:
                elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", styles['normal']))
            elements.append(Spacer(1, 0.1 * cm))
        if not errors and not warnings:
            elements.append(Paragraph("Aucune erreur ni avertissement détecté.", styles['normal']))
            elements.append(Spacer(1, 0.1 * cm))

        # Section 3 : Structure de l'installation
        elements.append(Paragraph("3. Structure de l'installation", styles['heading1']))
        elements.append(Paragraph(
            "Cette section détaille la présence des dossiers et fichiers essentiels à l'installation.",
            styles['normal']))
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
        elements.append(Paragraph("4. Vérification des fichiers de configuration", styles['heading1']))

        # 4.1 Config.ini
        config_ini_results = checks.get("config_ini", {})
        elements.append(Paragraph("4.1 Config.ini", styles['heading2']))
        elements.append(Paragraph(
            "Vérification des paramètres critiques du fichier <b>Config.ini</b>.", styles['normal']))
        status_text = "✓ Valide" if config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if config_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut : <font color='{status_color}'>{status_text}</font>", styles['normal']))
        elements.append(Spacer(1, 0.1 * cm))

        # Tableau des paramètres
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
        elements.append(Paragraph("4.2 PlateConfig.ini", styles['heading2']))
        elements.append(Paragraph(
            "Vérification des types de plaques et des configurations associées dans <b>PlateConfig.ini</b>.",
            styles['normal']))
        status_text = "✓ Valide" if plate_config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if plate_config_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut : <font color='{status_color}'>{status_text}</font>", styles['normal']))
        elements.append(Spacer(1, 0.1 * cm))
        data = [["Type/Paramètre", "Valeur", "Statut"]]
        # Types de plaques
        plate_types = plate_config_ini_results.get("plate_types", [])
        for pt in plate_types:
            data.append([
                "Type de plaque",
                f"{pt.get('name', '')} ({pt.get('config', '')})",
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
                if "errors" in plate_config_ini_results and any(
                        config["interf_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                    # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                    for err in plate_config_ini_results.get("errors", []):
                        if config["interf_params"] in err:
                            displayed_errors.add(err)
                status_color = "green" if statut == "✓" else "red"

                should_append = statut == "✗" and showSubItemErrors or statut == "✓" and showSubItemValid

                if should_append:
                    data.append([
                        f"{config_name}.InterfParams",
                        config["interf_params"],
                        f"<font color='{status_color}'>{statut}</font>"
                    ])

            # ReflectoParams
            if config.get("reflecto_params"):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(
                        config["reflecto_params"] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                    # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                    for err in plate_config_ini_results.get("errors", []):
                        if config["reflecto_params"] in err:
                            displayed_errors.add(err)
                status_color = "green" if statut == "✓" else "red"

                should_append = statut == "✗" and showSubItemErrors or statut == "✓" and showSubItemValid

                if should_append:
                    data.append([
                        f"{config_name}.ReflectoParams",
                        config["reflecto_params"],
                        f"<font color='{status_color}'>{statut}</font>"
                    ])
            # Fichiers de température
            for temp in config.get("temperature_files", []):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(
                        temp['file'] in e for e in plate_config_ini_results["errors"]):
                    statut = "✗"
                    # Ajouter les erreurs correspondantes à l'ensemble des erreurs affichées
                    for err in plate_config_ini_results.get("errors", []):
                        if temp['file'] in err:
                            displayed_errors.add(err)
                status_color = "green" if statut == "✓" else "red"

                should_append = statut == "✗" and showSubItemErrors or statut == "✓" and showSubItemValid

                if should_append:
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
        elements.append(Paragraph("4.3 ZymoCubeCtrl.ini", styles['heading2']))
        elements.append(Paragraph(
            "Vérification des paramètres principaux du fichier <b>ZymoCubeCtrl.ini</b>.", styles['normal']))
        status_text = "✓ Valide" if zymocube_ctrl_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if zymocube_ctrl_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut : <font color='{status_color}'>{status_text}</font>", styles['normal']))
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
        elements.append(Paragraph("Rapport généré automatiquement par ZymUpload", styles['italic']))

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

            # Déterminer le type de plaque pour les titres contextuels
            is_nanofilm, type_description = self._determine_plate_type_context(analysis)

            # Création du document PDF avec des marges réduites
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                leftMargin=0.5 * inch,
                rightMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch
            )

            elements = []

            # Styles communs
            styles = self._get_common_styles()

            # Définir des largeurs de colonnes standard pour tous les tableaux
            # Largeur totale disponible (7 pouces)
            total_width = 7.0 * inch

            # En-tête du rapport
            self._create_report_header(elements, "Rapport d'acquisition ZymoSoft", total_width)

            # Date
            elements.append(
                Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['normal']))
            elements.append(Spacer(1, 0.25 * inch))

            # 1. Informations sur l'acquisition
            elements.append(Paragraph("1. Informations sur l'acquisition", styles['heading1']))

            # Tableau des informations
            data = [
                ["Paramètre", "Valeur"],
                ["Type de plaque", analysis.get("plate_type", "inconnu")],
                ["Mode d'acquisition", analysis.get("acquisition_mode", "inconnu")],
                ["Dossier de résultats", analysis.get("folder", "")]
            ]

            # Statut corrigé - utiliser le statut validé par l'utilisateur
            is_validated = analysis.get("validated", analysis.get("valid", False))
            status_text = "✓ Acquisition valide" if is_validated else "✗ Acquisition non valide"
            data.append(["Statut", status_text])

            # Ajouter les commentaires s'ils existent
            comments = analysis.get("comments", "")
            if comments:
                data.append(["Commentaires", comments])

            # Utiliser des largeurs de colonnes standard
            col_widths = [total_width * 0.3, total_width * 0.7]
            table = self._create_wrapped_table(data, col_widths)
            elements.append(table)
            elements.append(Spacer(1, 0.15 * inch))

            # 2. Statistiques d'acquisition
            statistics = analysis.get("statistics", {})
            if statistics:
                elements.append(Paragraph("2. Statistiques d'acquisition", styles['heading1']))

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
                elements.append(Spacer(1, 0.15 * inch))

            # 3. Comparaison à la référence (avec contexte nanofilm/micro-dépôt)
            validation = analysis.get("validation", {})
            if validation and "comparison" in validation:
                # Titre contextualisé selon le type de plaque
                comparison_title = f"3. Comparaison à la référence, {type_description}"
                elements.append(Paragraph(comparison_title, styles['heading1']))

                # 3.1 Résumé de la comparaison
                elements.append(Paragraph("3.1 Résumé de la comparaison", styles['heading2']))

                # Import des critères de validation
                from zymosoft_assistant.utils.constants import VALIDATION_CRITERIA

                comp = validation["comparison"]

                # Préparation des données pour le tableau
                validation_data = [
                    ["Paramètre", "Valeur", "Critère de référence", "Statut"]
                ]

                # Définition des paramètres à afficher (sans "(validation)")
                validation_params = [
                    ("Pente", comp.get("slope", 0), "slope"),
                    ("Ordonnée à l'origine", comp.get("intercept", 0), "intercept"),
                    ("R²", comp.get("r_value", 0), "r2"),
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

                        # Formatage du texte des critères selon le paramètre
                        if criteria_key == "r2":
                            criteria_text = f"> {criteria['min']}"
                        elif criteria_key == "nb_puits_loin_fit":
                            criteria_text = "< 10 (biais relatif de 5%)"
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
                    total_width * 0.15  # Statut
                ]

                # Utiliser la méthode _create_wrapped_table pour une apparence cohérente
                validation_table = self._create_wrapped_table(validation_data, validation_col_widths)
                elements.append(validation_table)
                elements.append(Spacer(1, 0.15 * inch))

                # 3.2 Graphiques de comparaison aux références
                elements.append(Paragraph("3.2 Graphiques de comparaison", styles['heading2']))
                self._add_reference_comparison_graphs(elements, analysis, total_width)

            # 4. Comparaison des gammes de calibration
            if validation and "well_results_comparison" in validation:
                elements.append(Paragraph("4. Comparaison des gammes de calibration", styles['heading1']))

                try:
                    well_results_df = validation["well_results_comparison"]

                    # 4.1 Résumé
                    elements.append(Paragraph("4.1 Résumé", styles['heading2']))

                    # Préparation des données pour le tableau avec nouveaux en-têtes
                    well_results_data = [
                        ["Activité (U/mL)", "Zone", "ZU référence", "ZU déploiement", "Différence (point de %)",
                         "Validité"]]

                    # Limiter à 20 lignes maximum pour éviter un rapport trop long
                    max_rows = min(20, len(well_results_df))

                    for i in range(max_rows):
                        row = well_results_df.iloc[i]
                        well_results_data.append([
                            f"{row.get('activité', 0):.2f}",
                            f"{row.get('area', 0)}",
                            f"{row.get('reference', 0):.2f}",
                            f"{row.get('acquisition', 0):.2f}",
                            f"{row.get('CV', 0):.2f}",
                            "✓" if row.get('valid', False) else "✗"
                        ])

                    # Ajouter une ligne indiquant s'il y a plus de données
                    if len(well_results_df) > max_rows:
                        well_results_data.append(
                            [f"... {len(well_results_df) - max_rows} lignes supplémentaires non affichées", "", "", "",
                             "", ""])

                    # Utiliser des largeurs de colonnes proportionnelles à la largeur totale
                    well_results_col_widths = [
                        total_width * 0.18,  # Activité (U/mL)
                        total_width * 0.10,  # Zone
                        total_width * 0.18,  # ZU référence
                        total_width * 0.18,  # ZU déploiement
                        total_width * 0.20,  # Différence (point de %)
                        total_width * 0.16  # Validité
                    ]

                    # Utiliser la méthode _create_wrapped_table pour une apparence cohérente
                    well_results_table = self._create_wrapped_table(well_results_data, well_results_col_widths)
                    elements.append(well_results_table)
                    elements.append(Spacer(1, 0.15 * inch))

                    # 4.2 Graphiques des gammes de calibration enzymatique
                    elements.append(Paragraph("4.2 Graphiques des gammes de calibration", styles['heading2']))
                    self._add_enzymatic_calibration_graphs(elements, analysis, total_width)

                    # 4.3 Statistiques de comparaison des gammes de calibration
                    if not well_results_df.empty:
                        elements.append(Paragraph("4.3 Statistiques de comparaison", styles['heading2']))

                        # Calculer les statistiques globales
                        diff_mean = well_results_df['CV'].mean() if 'CV' in well_results_df.columns else 0
                        diff_std = well_results_df['CV'].std() if 'CV' in well_results_df.columns else 0

                        # Calculer le taux de validation
                        valid_count = well_results_df['valid'].sum() if 'valid' in well_results_df.columns else 0
                        total_count = len(well_results_df)
                        validation_rate = (valid_count / total_count * 100) if total_count > 0 else 0

                        well_stats_data = [
                            ["Statistique", "Valeur"],
                            ["Différence moyenne des activités enzymatiques (points de %)", f"{diff_mean:.2f}"],
                            ["Écart-type des différences (points de %)", f"{diff_std:.2f}"],
                            ["Taux de validation (%)", f"{validation_rate:.2f}% ({valid_count}/{total_count})"]
                        ]

                        # Utiliser les largeurs de colonnes standard
                        well_stats_table = self._create_wrapped_table(well_stats_data, col_widths)
                        elements.append(well_stats_table)
                        elements.append(Spacer(1, 0.15 * inch))

                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de la comparaison des résultats de puits: {str(e)}",
                                 exc_info=True)
                    elements.append(
                        Paragraph(f"Erreur lors de l'affichage des résultats de puits: {str(e)}", styles['normal']))
                    elements.append(Spacer(1, 0.15 * inch))

            # 5. Comparaison des LOD/LOQ avec nouveaux en-têtes
            if validation and "lod_loq_comparison" in validation:
                elements.append(Paragraph("5. Comparaison des LOD/LOQ", styles['heading1']))

                try:
                    lod_loq_df = validation["lod_loq_comparison"]

                    # Préparation des données pour le tableau avec nouveaux en-têtes
                    lod_loq_data = [["Zone", "LOD Ref (ZU)", "LOD déploiement (ZU)", "Diff LOD (point de %)",
                                     "LOQ Ref (ZU)", "LOQ déploiement (ZU)", "Diff LOQ (point de %)", "Validité"]]

                    # Ajouter les lignes pour chaque area
                    if not lod_loq_df.empty:
                        for i in range(len(lod_loq_df)):
                            row = lod_loq_df.iloc[i]

                            # Déterminer le statut de validité global (LOD ET LOQ doivent être valides)
                            lod_valid = row.get('Lod_Valid', row.get('Lod_valid', False))
                            loq_valid = row.get('Loq_Valid', row.get('Loq_valid', False))
                            overall_valid = lod_valid and loq_valid

                            lod_loq_data.append([
                                f"{row.get('Area', 0)}",
                                f"{row.get('LOD_Ref', 0):.4f}",
                                f"{row.get('LOD_Acq', 0):.4f}",
                                f"{row.get('Diff_LOD', 0):.4f}",
                                f"{row.get('LOQ_Ref', 0):.4f}",
                                f"{row.get('LOQ_Acq', 0):.4f}",
                                f"{row.get('Diff_LOQ', 0):.4f}",
                                "✓" if overall_valid else "✗"
                            ])

                    # Utiliser des largeurs de colonnes proportionnelles à la largeur totale
                    lod_loq_col_widths = [
                        total_width * 0.10,  # Zone
                        total_width * 0.13,  # LOD Ref (ZU)
                        total_width * 0.15,  # LOD déploiement (ZU)
                        total_width * 0.15,  # Diff LOD (point de %)
                        total_width * 0.13,  # LOQ Ref (ZU)
                        total_width * 0.15,  # LOQ déploiement (ZU)
                        total_width * 0.15,  # Diff LOQ (point de %)
                        total_width * 0.14  # Validité
                    ]

                    # Utiliser la méthode _create_wrapped_table pour une apparence cohérente
                    lod_loq_table = self._create_wrapped_table(lod_loq_data, lod_loq_col_widths)
                    elements.append(lod_loq_table)
                    elements.append(Spacer(1, 0.15 * inch))
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de la comparaison LOD/LOQ: {str(e)}", exc_info=True)
                    elements.append(Paragraph(f"Erreur lors de l'affichage des LOD/LOQ: {str(e)}", styles['normal']))
                    elements.append(Spacer(1, 0.15 * inch))

            # 6. Analyse technique (sans sous-section 6.1 s'il n'y a qu'une seule analyse)
            log_analysis = analysis.get("log_analysis", {})
            if log_analysis:
                elements.append(Paragraph("6. Analyse technique", styles['heading1']))

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
                    # Remplacer "nb max retry" par "nb alt retry"
                    ["Nombre de alt retry",
                     str(log_analysis.get("alt_retry_count", log_analysis.get("max_retry_count", 0)))]
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
                elements.append(Spacer(1, 0.15 * inch))

            # 7. Problèmes détectés (seulement s'il y a vraiment des erreurs)
            errors = analysis.get("errors", [])
            warnings = analysis.get("warnings", [])

            # Filtrer les erreurs génériques qui ne sont pas vraiment des problèmes
            filtered_errors = [error for error in errors if
                               not error.startswith("Impossible de charger les données d'acquisition")]

            if filtered_errors or warnings:
                elements.append(Paragraph("7. Problèmes détectés", styles['heading1']))

                if filtered_errors:
                    elements.append(Paragraph("7.1 Erreurs critiques", styles['heading2']))
                    for error in filtered_errors:
                        elements.append(Paragraph(f"• <font color='red'>{error}</font>", styles['normal']))
                    elements.append(Spacer(1, 0.15 * inch))

                if warnings:
                    elements.append(Paragraph("7.2 Avertissements", styles['heading2']))
                    for warning in warnings:
                        elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", styles['normal']))
                    elements.append(Spacer(1, 0.15 * inch))

            # Pied de page
            elements.append(Spacer(1, 0.5 * inch))
            elements.append(Paragraph("Rapport généré automatiquement par ZymUpload", styles['italic']))

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
                    leftMargin=0.5 * inch,
                    rightMargin=0.5 * inch,
                    topMargin=0.5 * inch,
                    bottomMargin=0.5 * inch
                )
                elements = []
                styles = self._get_common_styles()
                total_width = 7.0 * inch

                # En-tête du rapport
                self._create_report_header(elements, "Rapport d'acquisition ZymoSoft", total_width)

                # Date
                elements.append(
                    Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['normal']))
                elements.append(Spacer(1, 0.25 * inch))

                # Informations sur l'acquisition
                elements.append(Paragraph("Informations sur l'acquisition", styles['heading1']))

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
                elements.append(Spacer(1, 0.15 * inch))

                # Erreurs
                elements.append(Paragraph("Erreurs détectées", styles['heading1']))
                for error in analysis.get("errors", []):
                    elements.append(Paragraph(f"• <font color='red'>{error}</font>", styles['normal']))
                elements.append(Spacer(1, 0.15 * inch))

                # Pied de page
                elements.append(Spacer(1, 0.5 * inch))
                elements.append(Paragraph("Rapport généré automatiquement par ZymUpload", styles['italic']))

                # Génération du PDF
                doc.build(elements)

                logger.info(f"Rapport d'acquisition minimal généré avec erreurs: {pdf_path}")
                return pdf_path
            except Exception as inner_e:
                logger.error(f"Erreur lors de la génération du rapport minimal: {str(inner_e)}", exc_info=True)
                return ""

    def _add_reference_comparison_graphs(self, elements, analysis, total_width):
        """
        Ajoute les graphiques de comparaison aux références après le tableau de validation
        """
        try:
            # Chercher les graphiques de comparaison aux références
            validation_dir = ""
            if analysis.get("folder"):
                validation_dir = os.path.join(analysis["folder"], "validation_results", "validation_comparison")

            if os.path.exists(validation_dir):
                reference_graphs = []
                for file in os.listdir(validation_dir):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        reference_graphs.append(os.path.join(validation_dir, file))

                if reference_graphs:
                    # Traiter les graphiques par paires
                    for i in range(0, len(reference_graphs), 2):
                        graph_row = []

                        # Premier graphique de la paire
                        if i < len(reference_graphs) and os.path.exists(reference_graphs[i]):
                            graph_row.append(Image(reference_graphs[i], width=3.5 * inch, height=2.5 * inch))
                        else:
                            graph_row.append("")

                        # Deuxième graphique de la paire (s'il existe)
                        if i + 1 < len(reference_graphs) and os.path.exists(reference_graphs[i + 1]):
                            graph_row.append(Image(reference_graphs[i + 1], width=3.5 * inch, height=2.5 * inch))
                        else:
                            graph_row.append("")

                        # Créer une table pour cette paire de graphiques
                        if graph_row[0] or graph_row[1]:
                            graph_col_widths = [total_width * 0.5, total_width * 0.5]
                            graph_table = Table([graph_row], colWidths=graph_col_widths)
                            graph_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ]))
                            elements.append(graph_table)

                    elements.append(Spacer(1, 0.15 * inch))

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des graphiques de comparaison aux références: {str(e)}",
                         exc_info=True)

    def _add_enzymatic_calibration_graphs(self, elements, analysis, total_width):
        """
        Ajoute les graphiques des gammes de calibration enzymatique après le tableau des résultats de puits
        """
        try:
            # Chercher les graphiques de comparaison enzymatique
            validation_dir = ""
            if analysis.get("folder"):
                validation_dir = os.path.join(analysis["folder"], "validation_results", "comparaison_enzymo_routine")

            if os.path.exists(validation_dir):
                enzymo_graphs = []
                for file in os.listdir(validation_dir):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        enzymo_graphs.append(os.path.join(validation_dir, file))

                if enzymo_graphs:
                    # Traiter les graphiques par paires
                    for i in range(0, len(enzymo_graphs), 2):
                        graph_row = []

                        # Premier graphique de la paire
                        if i < len(enzymo_graphs) and os.path.exists(enzymo_graphs[i]):
                            graph_row.append(Image(enzymo_graphs[i], width=3.5 * inch, height=2.5 * inch))
                        else:
                            graph_row.append("")

                        # Deuxième graphique de la paire (s'il existe)
                        if i + 1 < len(enzymo_graphs) and os.path.exists(enzymo_graphs[i + 1]):
                            graph_row.append(Image(enzymo_graphs[i + 1], width=3.5 * inch, height=2.5 * inch))
                        else:
                            graph_row.append("")

                        # Créer une table pour cette paire de graphiques
                        if graph_row[0] or graph_row[1]:
                            graph_col_widths = [total_width * 0.5, total_width * 0.5]
                            graph_table = Table([graph_row], colWidths=graph_col_widths)
                            graph_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ]))
                            elements.append(graph_table)

                    elements.append(Spacer(1, 0.15 * inch))

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des graphiques de calibration enzymatique: {str(e)}", exc_info=True)

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
        elements = []

        # Styles communs
        styles = self._get_common_styles()

        # Largeur totale pour les tableaux (largeur page - marges)
        total_width = letter[0] - doc.leftMargin - doc.rightMargin

        # En-tête du rapport
        self._create_report_header(elements, "Rapport final d'installation ZymoSoft", total_width)

        # Date
        elements.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['normal']))
        elements.append(Spacer(1, 0.25 * inch))

        # Informations client
        elements.append(Paragraph("Informations client", styles['heading1']))

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
        elements.append(Spacer(1, 0.15 * inch))

        # Résumé des vérifications
        elements.append(Paragraph("Résumé des vérifications", styles['heading1']))

        step2_checks = full_data.get("step2_checks", {})
        check_results = step2_checks.get("check_results", {}) if "check_results" in step2_checks else step2_checks

        if check_results.get("installation_valid", False):
            elements.append(
                Paragraph("Statut global: <font color='green'>✓ Installation valide</font>", styles['normal']))
        else:
            elements.append(
                Paragraph("Statut global: <font color='red'>✗ Installation non valide</font>", styles['normal']))
        elements.append(Spacer(1, 0.15 * inch))

        # Détails des vérifications de configuration
        elements.append(Paragraph("Détails des vérifications de configuration", styles['heading1']))

        # Extraction et affichage des erreurs et avertissements
        errors = []
        warnings = []
        for key, value in check_results.items():
            if isinstance(value, dict) and "errors" in value:
                errors.extend(value["errors"])
            if isinstance(value, dict) and "warnings" in value:
                warnings.extend(value["warnings"])

        if errors:
            elements.append(Paragraph("Erreurs détectées", styles['heading2']))
            for error in errors:
                elements.append(Paragraph(f"• <font color='red'>{error}</font>", styles['normal']))
            elements.append(Spacer(1, 0.15 * inch))

        if warnings:
            elements.append(Paragraph("Avertissements", styles['heading2']))
            for warning in warnings:
                elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", styles['normal']))
            elements.append(Spacer(1, 0.15 * inch))

        # Structure de l'installation
        elements.append(Paragraph("Structure de l'installation", styles['heading2']))
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
            elements.append(Spacer(1, 0.15 * inch))

        # Config.ini
        config_ini_results = check_results.get("config_ini", {})
        if config_ini_results:
            elements.append(Paragraph("Vérification de Config.ini", styles['heading2']))
            status_text = "✓ Valide" if config_ini_results.get("config_valid", False) else "✗ Non valide"
            status_color = "green" if config_ini_results.get("config_valid", False) else "red"
            elements.append(Paragraph(f"Statut: <font color='{status_color}'>{status_text}</font>", styles['normal']))
            elements.append(Spacer(1, 0.1 * inch))

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
                if "errors" in config_ini_results and any(
                        param.split(".")[1] in e for e in config_ini_results["errors"]):
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
            table = self._create_wrapped_table(data, [0.45 * total_width, 0.4 * total_width, 0.15 * total_width])
            elements.append(table)
            elements.append(Spacer(1, 0.15 * inch))

        # PlateConfig.ini
        plate_config_ini_results = check_results.get("plate_config_ini", {})
        elements.append(Paragraph("Vérification de PlateConfig.ini", styles['heading2']))
        status_text = "✓ Valide" if plate_config_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if plate_config_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut: <font color='{status_color}'>{status_text}</font>", styles['normal']))
        elements.append(Spacer(1, 0.1 * inch))

        data = [["Type/Paramètre", "Valeur", "Statut"]]
        # Types de plaques
        plate_types = plate_config_ini_results.get("plate_types", [])
        for pt in plate_types:
            data.append([
                "Type de plaque",
                f"{pt.get('name', '')} ({pt.get('config', '')})",
                "<font color='green'>✓</font>"
            ])
        # Configs de plaques
        configs = plate_config_ini_results.get("configs", {})
        for config_name, config in configs.items():
            # InterfParams
            if config.get("interf_params"):
                statut = "✓"
                if "errors" in plate_config_ini_results and any(
                        config["interf_params"] in e for e in plate_config_ini_results["errors"]):
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
                if "errors" in plate_config_ini_results and any(
                        config["reflecto_params"] in e for e in plate_config_ini_results["errors"]):
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
                if "errors" in plate_config_ini_results and any(
                        temp['file'] in e for e in plate_config_ini_results["errors"]):
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
        table = self._create_wrapped_table(data, [0.45 * total_width, 0.4 * total_width, 0.15 * total_width])
        elements.append(table)
        elements.append(Spacer(1, 0.15 * inch))

        # ZymoCubeCtrl.ini
        zymocube_ctrl_ini_results = check_results.get("zymocube_ctrl_ini", {})
        elements.append(Paragraph("Vérification de ZymoCubeCtrl.ini", styles['heading2']))
        status_text = "✓ Valide" if zymocube_ctrl_ini_results.get("config_valid", False) else "✗ Non valide"
        status_color = "green" if zymocube_ctrl_ini_results.get("config_valid", False) else "red"
        elements.append(Paragraph(f"Statut: <font color='{status_color}'>{status_text}</font>", styles['normal']))
        elements.append(Spacer(1, 0.1 * inch))

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
        table = self._create_wrapped_table(data, [0.45 * total_width, 0.4 * total_width, 0.15 * total_width])
        elements.append(table)
        elements.append(Spacer(1, 0.15 * inch))

        # Pied de page
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("Rapport généré automatiquement par ZymUpload", styles['italic']))

        # Génération du PDF
        doc.build(elements)

        logger.info(f"Rapport final généré: {pdf_path}")
        return pdf_path