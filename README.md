# HEXABIN - Générateur de grilles hexagonales
## Utilisation

Pour exécuter le script dans QGIS, suivez les étapes suivantes :

1. Ouvrez QGIS.
2. Allez dans le menu `Plugins` et sélectionnez `Python Console`.
3. Dans la console Python, exécutez le script en utilisant la commande suivante :
    ```python
    exec(open('chemin/vers/HEXABIN_0.1.py').read())
    ```

Remplacez `chemin/vers/HEXABIN_0.1.py` par le chemin réel vers votre script.

## Description

Ce script génère une grille hexagonale et utilise QGIS pour manipuler les données géospatiales. Il utilise également PyQt5 pour l'interface utilisateur.

### Importance des grilles hexagonales en analyse spatiale environnementale

Les grilles hexagonales sont cruciales en analyse spatiale environnementale pour plusieurs raisons :

- **Uniformité et couverture complète** : Elles garantissent une analyse précise sans espaces vides.
- **Distance constante entre les centres** : Facilite les calculs de proximité et de voisinage.
- **Réduction des effets de bordures** : Améliore la modélisation des phénomènes naturels.
- **Applications spécifiques** : Utilisées pour le suivi de la biodiversité, la gestion des ressources naturelles et les études climatiques.
- **Visualisation esthétique** : Offre une représentation intuitive et compréhensible des données.
- **Connectivité des habitats** : Modélise précisément les corridors écologiques, réduit la fragmentation, et améliore l’analyse des flux de populations et des échanges génétiques.

Ces caractéristiques rendent les grilles hexagonales particulièrement efficaces pour les études environnementales.

## Configuration de la journalisation

Le script configure la journalisation pour écrire dans un fichier `hexgrid.log` situé dans le même répertoire que le script. La journalisation utilise un gestionnaire de fichiers rotatifs pour limiter la taille du fichier de log à 5 Mo et conserver jusqu'à 2 fichiers de sauvegarde.

### Exemple de configuration de la journalisation

```python
# Obtenir le répertoire du script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Configurer la journalisation pour écrire dans un fichier dans le même répertoire que le script
log_file = os.path.join(script_dir, 'hexgrid.log')

# Configurer le gestionnaire de fichiers rotatifs
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

# Configurer la journalisation
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler]
)

# Créer un logger
logger = logging.getLogger()
```
## Gestion des exceptions
Le script utilise un hook d'exception pour journaliser les exceptions non interceptées et terminer le script proprement.

### Exemple de gestion des exceptions
```python
def handle_exception(exc_type, exc_value, exc_traceback):
    """Journaliser les exceptions non interceptées et terminer le script."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Ne pas journaliser KeyboardInterrupt pour éviter d'encombrer le fichier de log
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        "Exception non interceptée",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
```
## Mots clés / Keywords
#HexagonalGrid #SpatialAnalysis #EnvironmentalScience #Biodiversity #ResourceManagement #ClimateStudies #HabitatConnectivity #GIS #QGIS #ConservationPlanning #Shapefile #Python #PyQt5 #QGISCore #Fiona #GeospatialData #DataVisualization #ProximityCalculations #NaturalPhenomenaModeling #EcologicalCorridors #PopulationFlowAnalysis #GeneticExchangeAnalysis
