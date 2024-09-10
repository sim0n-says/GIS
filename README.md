# Hexagonal Grid Generator

Ce projet génère une grille hexagonale basée sur une couche de projet QGIS ou un fichier de forme.

Les grilles hexagonales sont cruciales en analyse spatiale environnementale pour plusieurs raisons :
    • Uniformité et couverture complète : Elles garantissent une analyse précise sans espaces vides.
    
    • Distance constante entre les centres : Facilite les calculs de proximité et de voisinage.
    
    • Réduction des effets de bord : Améliore la modélisation des phénomènes naturels.
    
    • Applications spécifiques : Utilisées pour le suivi de la biodiversité, la gestion des ressources naturelles et les études climatiques.
    
    • Visualisation esthétique : Offre une représentation intuitive et compréhensible des données.
    
    • Connectivité des habitats : Modélise précisément les corridors écologiques, réduit la fragmentation, et améliore     l’analyse des flux de populations et des échanges génétiques.
    
Ces caractéristiques rendent les grilles hexagonales particulièrement efficaces pour les études environnementales et la conservation des écosystèmes.

#HexagonalGrid #SpatialAnalysis #EnvironmentalScience #Biodiversity #ResourceManagement #ClimateStudies #HabitatConnectivity #GIS #QGIS #ConservationPlanning #Shapefile


## Prérequis

- Python 3.x
- PyQt5
- QGIS
- Fiona

## Installation

1. Clonez le dépôt :
    ```bash
    git clone https://github.com/sim0n-says/GIS.git
    cd votre-repo
    ```

2. Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

## Utilisation

1. Exécutez le script :
    ```bash
    python HEXABIN_0.1.py
    ```

2. Suivez les instructions dans l'interface utilisateur pour sélectionner une couche ou un fichier shapefile, définir la superficie des hexagones, et choisir un fichier de sortie.

## Licence

Ce projet est sous licence Unlicense. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
