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
from reportlab.lib.units import inch
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

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
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        # Création du document PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

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
        normal_style = styles['Normal']

        # Titre et date
        elements.append(Paragraph("Rapport de vérification de l'installation ZymoSoft", title_style))
        elements.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 0.25*inch))

        # Résumé des vérifications
        elements.append(Paragraph("Résumé des vérifications", heading_style))
        if checks.get("installation_valid", False):
            elements.append(Paragraph("Statut global: <font color='green'>✓ Installation valide</font>", normal_style))
        else:
            elements.append(Paragraph("Statut global: <font color='red'>✗ Installation non valide</font>", normal_style))
        elements.append(Spacer(1, 0.15*inch))

        # Extraction et affichage des erreurs
        errors = []
        warnings = []
        for key, value in checks.items():
            if isinstance(value, dict) and "errors" in value:
                errors.extend(value["errors"])
            if isinstance(value, dict) and "warnings" in value:
                warnings.extend(value["warnings"])

        if errors:
            elements.append(Paragraph("Erreurs détectées", heading_style))
            for error in errors:
                elements.append(Paragraph(f"• <font color='red'>{error}</font>", normal_style))
            elements.append(Spacer(1, 0.15*inch))

        if warnings:
            elements.append(Paragraph("Avertissements", heading_style))
            for warning in warnings:
                elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", normal_style))
            elements.append(Spacer(1, 0.15*inch))

        # Structure de l'installation
        elements.append(Paragraph("Structure de l'installation", heading_style))

        # Tableau des vérifications
        data = [["Élément", "Statut"]]

        # Ajout des éléments vérifiés au tableau
        check_items = [
            ("bin_exists", "Dossier bin/"),
            ("etc_exists", "Dossier etc/"),
            ("resultats_exists", "Dossier Resultats/"),
            ("zymocubectrl_exists", "ZymoCubeCtrl.exe"),
            ("zymosoft_exists", "ZymoSoft.exe"),
            ("workers_exists", "Dossier workers/")
        ]

        for check_key, check_label in check_items:
            if check_key in checks:
                status = "✓" if checks[check_key] else "✗"
                data.append([check_label, status])

        # Création du tableau
        if len(data) > 1:  # S'il y a des données en plus de l'en-tête
            table = Table(data, colWidths=[4*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#009967")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(table)

        # Pied de page
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Rapport généré automatiquement par l'Assistant d'installation ZymoSoft", 
                                 styles['Italic']))

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

        # Préparation des données
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"rapport_acquisition_{timestamp}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        # Création du document PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

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
        normal_style = styles['Normal']

        # Titre et date
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
            ["Statut", "✓ Acquisition valide" if analysis.get("valid", False) else "✗ Acquisition non valide"]
        ]

        table = Table(data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#009967")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.15*inch))

        # Statistiques
        statistics = analysis.get("statistics", {})
        if statistics:
            elements.append(Paragraph("Statistiques", heading_style))

            stats_data = [
                ["Paramètre", "Valeur"],
                ["Pente", str(round(statistics.get("slope", 0), 4))],
                ["Ordonnée à l'origine", str(round(statistics.get("intercept", 0), 4))],
                ["Coefficient de détermination (R²)", str(round(statistics.get("r2", 0), 4))],
                ["Nombre de valeurs aberrantes", str(statistics.get("outliers_count", 0))],
                ["Pourcentage de valeurs aberrantes", f"{round(statistics.get('outliers_percentage', 0), 2)}%"]
            ]

            stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#009967")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 0.15*inch))

        # Graphiques
        graphs = analysis.get("graphs", [])
        if graphs:
            elements.append(Paragraph("Graphiques", heading_style))
            for graph_path in graphs:
                if os.path.exists(graph_path):
                    img = Image(graph_path, width=6*inch, height=4*inch)
                    elements.append(img)
                    elements.append(Spacer(1, 0.1*inch))

        # Erreurs et avertissements
        errors = analysis.get("errors", [])
        if errors:
            elements.append(Paragraph("Erreurs détectées", heading_style))
            for error in errors:
                elements.append(Paragraph(f"• <font color='red'>{error}</font>", normal_style))
            elements.append(Spacer(1, 0.15*inch))

        warnings = analysis.get("warnings", [])
        if warnings:
            elements.append(Paragraph("Avertissements", heading_style))
            for warning in warnings:
                elements.append(Paragraph(f"• <font color='orange'>{warning}</font>", normal_style))
            elements.append(Spacer(1, 0.15*inch))

        # Pied de page
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Rapport généré automatiquement par l'Assistant d'installation ZymoSoft", 
                                 styles['Italic']))

        # Génération du PDF
        doc.build(elements)

        logger.info(f"Rapport d'acquisition généré: {pdf_path}")
        return pdf_path

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
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        # Création du document PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

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

        client_table = Table(client_data, colWidths=[2.5*inch, 3.5*inch])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#009967")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(client_table)
        elements.append(Spacer(1, 0.15*inch))

        # Résumé des vérifications
        elements.append(Paragraph("Résumé des vérifications", heading_style))

        step2_checks = full_data.get("step2_checks", {})
        if step2_checks.get("installation_valid", False):
            elements.append(Paragraph("Statut global: <font color='green'>✓ Installation valide</font>", normal_style))
        else:
            elements.append(Paragraph("Statut global: <font color='red'>✗ Installation non valide</font>", normal_style))
        elements.append(Spacer(1, 0.15*inch))

        # Acquisitions réalisées
        elements.append(Paragraph("Acquisitions réalisées", heading_style))

        acquisitions = full_data.get("acquisitions", [])
        if acquisitions:
            for i, acquisition in enumerate(acquisitions):
                elements.append(Paragraph(f"Acquisition #{acquisition.get('id', i+1)}", subheading_style))

                acq_data = [
                    ["Type de plaque", acquisition.get("plate_type", "")],
                    ["Mode", acquisition.get("mode", "")],
                    ["Dossier de résultats", acquisition.get("results_folder", "")],
                    ["Statut", "✓ Validée" if acquisition.get("validated", False) else "✗ Non validée"]
                ]

                acq_table = Table(acq_data, colWidths=[2*inch, 4*inch])
                acq_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(acq_table)

                # Statistiques de l'acquisition
                analysis = acquisition.get("analysis", {})
                if analysis:
                    elements.append(Paragraph("Statistiques", subheading_style))
                    stats_data = [
                        ["Pente", str(round(analysis.get("slope", 0), 4))],
                        ["R²", str(round(analysis.get("r2", 0), 4))]
                    ]

                    stats_table = Table(stats_data, colWidths=[2*inch, 4*inch])
                    stats_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(stats_table)

                # Commentaires de l'acquisition
                comments = acquisition.get("comments", "")
                if comments:
                    elements.append(Paragraph("Commentaires", subheading_style))
                    elements.append(Paragraph(comments, normal_style))

                elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(Paragraph("Aucune acquisition réalisée.", normal_style))
            elements.append(Spacer(1, 0.15*inch))

        # Actions de finalisation
        elements.append(Paragraph("Actions de finalisation", heading_style))

        cleanup_actions = full_data.get("cleanup_actions", [])
        if cleanup_actions:
            for action in cleanup_actions:
                if action == "client_mode":
                    elements.append(Paragraph("• Passage en mode client", normal_style))
                elif action == "clean_pc":
                    elements.append(Paragraph("• Nettoyage du PC", normal_style))
                else:
                    elements.append(Paragraph(f"• {action}", normal_style))
        else:
            elements.append(Paragraph("Aucune action de finalisation.", normal_style))

        elements.append(Spacer(1, 0.15*inch))

        # Commentaires généraux
        final_comments = full_data.get("final_comments", "")
        if final_comments:
            elements.append(Paragraph("Commentaires généraux", heading_style))
            elements.append(Paragraph(final_comments, normal_style))
            elements.append(Spacer(1, 0.15*inch))

        # Pied de page
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Rapport généré automatiquement par l'Assistant d'installation ZymoSoft", 
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
