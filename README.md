# Cahier des charges - Assistant d'installation ZymoSoft

## Vue d'ensemble

Le logiciel d'assistance à l'installation ZymoSoft est une application Python qui guide les techniciens étape par étape dans le processus de validation d'une installation ZymoSoft. Il s'agit d'un système d'onboarding interactif qui vérifie la configuration, valide les acquisitions et génère des rapports automatiques.

## Architecture générale

### Workflow principal
1. **Saisie des informations client**
2. **Vérifications pré-validation**
3. **Validation par acquisitions** (peut être répétée plusieurs fois)
4. **Clôture de l'installation**

### Technologies requises
- **Python 3.8+**
- **Interface graphique** :  PyQt5
- **Génération PDF** : reportlab ou weasyprint
- **Traitement données** : pandas, matplotlib
- **Validation fichiers** : configparser, pathlib

---

## ÉTAPE 1 : Saisie des informations

### Interface utilisateur
- **Champ texte** : Nom du client (obligatoire)
- **Champ texte** : Nom du responsable CS (obligatoire)
- **Champ texte** : Nom du responsable instrumentation (obligatoire)
- **Bouton** : "Lancer la validation" (actif uniquement si tous les champs sont remplis)

### Validation
- Vérifier que tous les champs sont non-vides
- Possibilité de sauvegarder les informations pour réutilisation

---

## ÉTAPE 2 : Vérifications pré-validation

### 2.1 Vérification de l'installation ZymoSoft

#### Structure de dossiers à vérifier
```
C:/Users/Public/Zymoptiq/ZymoSoft_V[version]/
├── bin/
│   ├── ZymoCubeCtrl.exe ✓
│   ├── ZymoSoft.exe ✓
│   └── workers/ ✓
└── etc/ ✓
└── Resultats/ ✓
```

#### Vérifications bin/
- [x] **ZymoCubeCtrl.exe** existe
- [x] **ZymoSoft.exe** existe  
- [x] Vérifier que la version de ZymoSoft.exe correspond à la version du dossier
- [x] Dossier **workers/** existe

#### Vérifications workers/
- [x] Vérifier l'existence des workers définis dans config.ini
- [x] Valider les versions des workers

### 2.2 Vérification du fichier Config.ini

#### Propriétés obligatoires
```ini
[Application]
ExpertMode=true ✓
ExportAcquisitionDetailResults=true ✓

[Hardware]
Controller=ZymoCubeCtrl ✓

[Interf]
Worker=./workers/Interf_V[version]/Interf ✓
MaxProcesses=6

[Reflecto]  
Worker=./workers/Reflecto_V[version]/Reflecto ✓
MaxProcesses=6
```

#### Validation
- Vérifier que les chemins des workers existent
- Valider les versions dans les noms de dossiers

### 2.3 Vérification du fichier PlateConfig.ini

#### PlateTypes à lister
```ini
[PlateType]
Ax_v1 = Config1
AM_v1 = Config8
BG_v1 = Config9
# ... autres types de plaques
```

#### Vérifications par configuration
Pour chaque `[PlateConfig:ConfigX]` :

- **InterfParams** : vérifier existence dans `etc/Interf/`
- **ReflectoParams** : vérifier existence dans `etc/Reflecto/`

#### Fichiers de température (CSV)
Vérifier l'existence des fichiers non-commentés :
- `IMin455=IMin455_Temperature_default.csv` → dans `etc/Reflecto/`
- `IMax455=IMax455_Temperature_default.csv` → dans `etc/Reflecto/`
- `IMin730=IMin730_Temperature_default.csv` → dans `etc/Reflecto/`
- `IMax730=IMax730_Temperature_default.csv` → dans `etc/Reflecto/`

### 2.4 Vérification du fichier ZymoCubeCtrl.ini

#### Propriétés à vérifier
```ini
[Motors]
Port=COM6 → Afficher le port COM

[Defaults]
VideoPreview=false ✓
ImageDestDir=C:\\Users\\Public\\Zymoptiq\\Diag\\Temp ✓

[PlateType]
# Lister les types de plaques disponibles
```

#### Validation
- Vérifier que `ImageDestDir` existe
- Lister les PlateTypes configurés

### Interface de l'étape 2
- **Liste de vérifications** avec statut (✓/✗)
- **Boutons** :
  - "Étape précédente"
  - "Relancer les vérifications"
  - "Valider et continuer" (actif si toutes les vérifications sont OK)

### Rapport étape 2
- **Génération automatique** d'un PDF avec :
  - Résumé des vérifications
  - Liste des fichiers trouvés/manquants
  - Configuration détectée

---

## ÉTAPE 3 : Validation par acquisitions

### 3.1 Configuration de l'acquisition

#### Interface de sélection
- **Radio buttons** : Type de plaque
  - Micro dépôt
  - Nanofilm
- **Radio buttons** : Mode
  - Client
  - Expert
- **Bouton** : "Acquisition réalisée"

### 3.2 Sélection des résultats

#### Interface
- **Explorateur de fichiers** : Choisir le dossier des résultats d'acquisition
- **Validation** du dossier sélectionné

### 3.3 Analyse des résultats

#### Scripts Python d'analyse
Traitement automatique générant :

**Données numériques :**
- Pente
- Ordonnée à l'origine  
- Coefficient de corrélation R²
- Nombre de puits trop éloignés de la référence

**Graphiques :**
- Volume en fonction de l'épaisseur
- Épaisseur en fonction du volume
- Autres graphiques de validation

#### Interface d'affichage
- **Tableau** : Résultats numériques
- **Galerie d'images** : Graphiques générés
- **Zone de texte** : Commentaires de l'opérateur

### 3.4 Actions possibles

#### Boutons de navigation
- **"Valider cette acquisition et recommencer"** 
  - Génère un rapport d'acquisition
  - Retour à la configuration (3.1)
- **"Invalider et refaire"**
  - Génère un rapport d'échec
  - Retour à la configuration (3.1)
- **"Valider et étape suivante"**
  - Génère un rapport final d'acquisitions
  - Passage à l'étape 4

### Rapports étape 3
- **Rapport par acquisition** :
  - Type de plaque et mode utilisés
  - Résultats d'analyse
  - Commentaires opérateur
  - Images générées
- **Rapport consolidé** : synthèse de toutes les acquisitions

---

## ÉTAPE 4 : Clôture de l'installation

### 4.1 Commentaire général

#### Interface
- **Zone de texte large** : Commentaire général sur la validation
- **Historique** : Résumé des acquisitions réalisées

### 4.2 Actions de fin

#### Cases à cocher
- [x] **Passer en mode client**
  - Modifie `Config.ini` : `ExpertMode=false`
- [x] **Nettoyer le PC**
  - Supprime les données d'acquisitions de test
  - Vide le dossier `Diag/Temp`

#### Bouton final
- **"Finaliser l'installation"**
  - Applique les actions cochées
  - Génère le rapport final complet

### Rapport final
- **Rapport d'installation complet** :
  - Informations client
  - Résumé des vérifications
  - Historique des acquisitions
  - Actions de finalisation
  - Commentaires généraux

---

## Spécifications techniques

### Interface utilisateur

```
 'color_scheme': {
        'primary': '#009967',
        'primary_hover': '#007d54',
        'primary_pressed': '#006b47',
        'background': '#f5f5f5',
        'surface': '#ffffff',
        'text': '#333333',
        'text_secondary': '#666666',
        'border': '#cccccc',
        'disabled': '#cccccc',
        'error': '#ff0000',
        'success': '#28a745',
        'warning': '#ffc107',
        'info': '#17a2b8'
    }
````

### Structure du projet
```
zymosoft_assistant/
├── main.py                    # Point d'entrée
├── gui/
│   ├── __init__.py
│   ├── main_window.py         # Fenêtre principale
│   ├── step1_info.py          # Étape 1
│   ├── step2_checks.py        # Étape 2  
│   ├── step3_acquisition.py   # Étape 3
│   └── step4_closure.py       # Étape 4
├── core/
│   ├── __init__.py
│   ├── config_checker.py      # Vérifications config
│   ├── file_validator.py      # Validation fichiers
│   ├── acquisition_analyzer.py # Analyse résultats
│   └── report_generator.py    # Génération PDF
├── utils/
│   ├── __init__.py
│   ├── constants.py           # Constantes chemins
│   └── helpers.py             # Fonctions utilitaires
└── templates/
    ├── report_step2.html      # Template rapport étape 2
    ├── report_acquisition.html # Template rapport acquisition
    └── report_final.html      # Template rapport final
```

### Classes principales

#### ConfigChecker
```python
class ConfigChecker:
    def check_installation_structure(self) -> Dict[str, bool]
    def validate_config_ini(self) -> Dict[str, Any]  
    def validate_plate_config_ini(self) -> Dict[str, Any]
    def validate_zymocube_ctrl_ini(self) -> Dict[str, Any]
```

#### AcquisitionAnalyzer
```python
class AcquisitionAnalyzer:
    def analyze_results(self, results_folder: str) -> Dict[str, Any]
    def generate_graphs(self, data: Dict) -> List[str]
    def calculate_statistics(self, data: Dict) -> Dict[str, float]
```

#### ReportGenerator
```python
class ReportGenerator:
    def generate_step2_report(self, checks: Dict) -> str
    def generate_acquisition_report(self, analysis: Dict) -> str  
    def generate_final_report(self, full_data: Dict) -> str
```

### Gestion des données

#### Format de sauvegarde
- **JSON** pour les données de session
- **SQLite** pour l'historique des installations (optionnel)

#### Structure de données de session
```json
{
  "installation_id": "uuid",
  "timestamp_start": "2025-01-01T10:00:00",
  "client_info": {
    "name": "Client ABC",
    "cs_responsible": "Jean Dupont", 
    "instrumentation_responsible": "Marie Martin"
  },
  "step2_checks": {
    "software_structure": true,
    "config_validation": true,
    "files_found": ["list", "of", "files"]
  },
  "acquisitions": [
    {
      "id": 1,
      "plate_type": "micro_depot",
      "mode": "expert", 
      "results_folder": "/path/to/results",
      "analysis": {"slope": 1.23, "r2": 0.98},
      "comments": "Acquisition OK",
      "validated": true
    }
  ],
  "final_comments": "Installation réussie",
  "cleanup_actions": ["client_mode", "clean_pc"]
}
```

### Gestion des erreurs

#### Types d'erreurs à gérer
- **Fichiers manquants** : affichage clair des éléments absents
- **Erreurs de configuration** : suggestions de correction
- **Échecs d'analyse** : possibilité de retry
- **Erreurs système** : logs détaillés

### Tests

#### Tests unitaires
- Validation des parsers de configuration
- Tests des fonctions d'analyse
- Validation de la génération de rapports

#### Tests d'intégration  
- Workflow complet avec données de test
- Validation des rapports générés

---

## Installation et déploiement

### Dépendances
```
pip install -r requirements.txt
```

### Packaging
- **PyInstaller** pour créer un exécutable standalone
- **NSIS** pour l'installateur Windows

### Configuration de déploiement
- Détection automatique des chemins ZymoSoft
- Configuration par défaut adaptable



## Conclusion

Ce logiciel d'assistance à l'installation ZymoSoft permettra de standardiser et d'automatiser le processus de validation des installations, réduisant les erreurs humaines et améliorant la traçabilité des interventions.