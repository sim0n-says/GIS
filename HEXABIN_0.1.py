import logging
import math
import os
import sys
import signal
import fiona
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                             QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout, QProgressBar)
from PyQt5.QtCore import QTimer
from logging.handlers import RotatingFileHandler

from qgis.core import (QgsFeature, QgsField,
                       QgsGeometry, QgsPointXY, QgsProject, QgsVectorFileWriter,
                       QgsVectorLayer)
from qgis.PyQt.QtCore import QVariant

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
    
    # Vider tous les handlers pour s'assurer que les logs sont écrits
    for handler in logger.handlers:
        handler.flush()
    
    clean_up()
    sys.exit(1)

def signal_handler(signal, frame):
    """Gérer les signaux pour un arrêt propre."""
    logging.info(f"Signal reçu : {signal}. Fermeture propre en cours.")
    clean_up()
    sys.exit(0)

# Enregistrer les gestionnaires de signaux
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def clean_up():
    """Ferme les instances PyQt et libère la mémoire sans fermer QGIS."""
    try:
        # Nettoyage des ressources si nécessaire
        for var in ['hex_grid_layer', 'existing_layer']:
            if var in globals():
                del globals()[var]
        logging.info("Ressources nettoyées.")
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage des ressources : {e}")
        print(f"Erreur lors du nettoyage des ressources : {e}")
    finally:
        # Fermer les fenêtres ou widgets PyQt spécifiques
        for widget in QApplication.topLevelWidgets():
            widget.close()
        logging.info("Instances PyQt fermées.")
        print("Instances PyQt fermées.")

class HexGridDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Options de Grille Hexagonale')

        layout = QVBoxLayout()

        # Sélection de la couche
        self.layer_label = QLabel(
            'Sélectionner une couche du projet ou un fichier shapefile:')
        self.layer_combo = QComboBox()

        layers = [layer.name()
                  for layer in QgsProject.instance().mapLayers().values()]
        if layers:
            self.layer_combo.addItems(layers)
        self.layer_combo.addItem('Sélectionner un fichier shapefile...')
        self.layer_combo.currentIndexChanged.connect(
            self.layer_selection_changed)

        layout.addWidget(self.layer_label)
        layout.addWidget(self.layer_combo)

        # Entrée du shapefile
        self.shapefile_input = QLineEdit()
        self.shapefile_input.setPlaceholderText('Chemin du fichier shapefile')
        self.shapefile_button = QPushButton('Parcourir')
        self.shapefile_button.clicked.connect(self.select_shapefile)
        self.shapefile_input.setEnabled(False)
        self.shapefile_button.setEnabled(False)

        shapefile_layout = QHBoxLayout()
        shapefile_layout.addWidget(self.shapefile_input)
        shapefile_layout.addWidget(self.shapefile_button)

        layout.addLayout(shapefile_layout)

        # Entrée de la superficie des hexagones
        self.area_label = QLabel('Superficie des hexagones:')
        self.area_input = QDoubleSpinBox()
        self.area_input.setRange(0, 1e10)
        self.area_input.setValue(20)

        layout.addWidget(self.area_label)
        layout.addWidget(self.area_input)

        # Sélection de l'unité
        self.unit_label = QLabel('Unité de mesure:')
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(
            ['hectares', 'acres', 'km²', 'miles²', 'mètres²'])

        layout.addWidget(self.unit_label)
        layout.addWidget(self.unit_combo)

        # Sélection du fichier de sortie
        self.output_label = QLabel('Enregistrer la grille hexagonale:')
        self.output_input = QLineEdit()
        self.output_button = QPushButton('Parcourir')
        self.output_button.clicked.connect(self.select_output_file)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(self.output_button)

        layout.addWidget(self.output_label)
        layout.addLayout(output_layout)

        # Ajouter une case à cocher pour découper les hexagones
        self.clip_hexagons_checkbox = QCheckBox('Couper les hexagones avec les polygones de la couche d\'emprise')
        self.clip_hexagons_checkbox.setChecked(False)
        layout.addWidget(self.clip_hexagons_checkbox)

        # Barre de progression
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Boutons OK et Annuler
        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.start_processing)
        self.cancel_button = QPushButton('Annuler')
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def layer_selection_changed(self):
        if self.layer_combo.currentText() == 'Sélectionner un fichier shapefile...':
            logging.info("Sélection d'un fichier shapefile activée.")
            self.shapefile_input.setEnabled(True)
            self.shapefile_button.setEnabled(True)
        else:
            logging.info("Sélection d'une couche du projet activée.")
            self.shapefile_input.setEnabled(False)
            self.shapefile_button.setEnabled(False)

    def select_shapefile(self):
        shapefile_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier shapefile", "", "Shapefiles (*.shp)")
        if shapefile_path:
            logging.info(f"Shapefile sélectionné : {shapefile_path}")
            self.shapefile_input.setText(shapefile_path)

    def select_output_file(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer la grille hexagonale", "", "Shapefiles (*.shp)")
        if output_path:
            logging.info(f"Fichier de sortie sélectionné : {output_path}")
            self.output_input.setText(output_path)

    def start_processing(self):
        self.ok_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        layer_name = self.layer_combo.currentText()
        shapefile_path = self.shapefile_input.text()
        hex_area = self.area_input.value()
        unit = self.unit_combo.currentText().strip()  # Récupérer l'unité sélectionnée
        output_path = self.output_input.text()
        clip_hexagons = self.clip_hexagons_checkbox.isChecked()

        if layer_name != 'Sélectionner un fichier shapefile...':
            extent = get_extent_from_layer(layer_name)
        elif shapefile_path:
            extent = get_extent_from_shapefile(shapefile_path)
        else:
            logging.error("Aucun fichier shapefile ou couche sélectionné.")
            self.ok_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            return

        if extent:
            hex_area_m2 = convert_area_to_square_meters(hex_area, unit)
            crs = QgsProject.instance().mapLayersByName(layer_name)[0].crs()

            try:
                # Vérification et suppression de la couche existante
                existing_layer = QgsProject.instance().mapLayersByName('HexGrid')
                if existing_layer:
                    for i in range(1, 100):  # Limite à 100 couches pour éviter une boucle infinie
                        new_layer_name = f'HexGrid_{i}'
                        if not QgsProject.instance().mapLayersByName(new_layer_name):
                            break
                    else:
                        logging.error("Trop de couches HexGrid existantes.")
                        self.ok_button.setEnabled(True)
                        self.cancel_button.setEnabled(True)
                        return
                else:
                    new_layer_name = 'HexGrid'

                # Création de la grille hexagonale
                def update_progress(current, total):
                    self.progress_bar.setValue(int((current / total) * 100))
                    QApplication.processEvents()

                hex_grid_layer = create_hexagonal_grid(
                    new_layer_name, hex_area_m2, extent, crs, update_progress, layer_name if clip_hexagons else None)
                if hex_grid_layer:
                    QgsProject.instance().addMapLayer(hex_grid_layer)

                    if output_path:
                        error = QgsVectorFileWriter.writeAsVectorFormat(
                            hex_grid_layer, output_path, "UTF-8", crs, "ESRI Shapefile")
                        if error == QgsVectorFileWriter.NoError:
                            logging.info(
                                "Grille hexagonale sauvegardée avec succès.")
                        else:
                            logging.error(
                                f"Erreur lors de la sauvegarde de la grille hexagonale: {error}")
                    else:
                        logging.error(
                            "Chemin du fichier de sortie non spécifié.")
            except Exception as e:
                logging.error(f"Une erreur est survenue : {e}")

        self.ok_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

        # Fermer la fenêtre après 5 secondes
        QTimer.singleShot(5000, self.close)

def get_extent_from_shapefile(shapefile_path):
    try:
        with fiona.open(shapefile_path, 'r') as src:
            bounds = src.bounds
        logging.info(f"Limites du shapefile : {bounds}")
        return bounds
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du shapefile: {e}")
        return None

def get_extent_from_layer(layer_name):
    try:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        extent = layer.extent()
        logging.info(f"Limites de la couche {layer_name} : {extent}")
        return (extent.xMinimum(), extent.yMinimum(),
                extent.xMaximum(), extent.yMaximum())
    except IndexError:
        logging.error(f"Couche {layer_name} non trouvée.")
        return None

def convert_area_to_square_meters(area, unit):
    """
    Convertir une superficie en mètres carrés en fonction de l'unité donnée.
    
    Paramètres:
    area (float): La superficie à convertir.
    unit (str): L'unité de la superficie.
    
    Retourne:
    float: La superficie en mètres carrés.
    """
    # Dictionnaire de conversion pour les superficies
    conversion_factors = { 
        'hectares': 10000,
        'acres': 4046.86,
        'km²': 1e6,
        'miles²': 2.59e6,
        'mètres²': 1
    }

    if unit not in conversion_factors:
        logging.error(f"Unité de mesure inconnue : {unit}")
        return None

    try:
        area_m2 = area * conversion_factors[unit]
        logging.info(f"Superficie convertie en mètres carrés : {area_m2}")
        return area_m2
    except Exception as e:
        logging.error(f"Erreur lors de la conversion : {e}")
        return None

def create_hexagon(x, y, radius, feature_id):
    points = [
        QgsPointXY(
            x + radius * math.cos(math.radians(angle)),
            y + radius * math.sin(math.radians(angle))
        ) for angle in range(0, 360, 60)
    ]
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
    feature.setAttributes([feature_id])
    return feature

def create_hexagonal_grid(layer_name, hex_area, extent, crs, progress_callback, clip_with_layer=None):
    try:
        # Calculer le rayon du cercle circonscrit de l'hexagone
        radius = math.sqrt(hex_area / (3 * math.sqrt(3) / 2))
        width = 2 * radius
        height = math.sqrt(3) * radius
        layer = QgsVectorLayer(
            f'Polygon?crs={crs.authid()}', layer_name, 'memory')
        provider = layer.dataProvider()

        provider.addAttributes([QgsField('id', QVariant.Int)])
        layer.updateFields()

        features = []
        feature_id = 0

        x_min, y_min, x_max, y_max = extent

        y = y_min
        row = 0
        tasks = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            while y < y_max:
                x = x_min
                if row % 2 == 1:
                    x += width * 0.75
                while x < x_max:
                    tasks.append(executor.submit(create_hexagon, x, y, radius, feature_id))
                    feature_id += 1
                    x += width * 1.5
                y += height * 0.5
                row += 1

            total_tasks = len(tasks)
            for i, future in enumerate(as_completed(tasks)):
                features.append(future.result())
                progress_callback(i + 1, total_tasks)

        provider.addFeatures(features)
        layer.updateExtents()

        if clip_with_layer:
            clip_layer = QgsProject.instance().mapLayersByName(clip_with_layer)[0]
            clipped_layer = processing.run("qgis:clip", {
                'INPUT': layer,
                'OVERLAY': clip_layer,
                'OUTPUT': 'memory:'
            })['OUTPUT']
            return clipped_layer

        return layer
    except Exception as e:
        logging.error(
            f"Erreur lors de la création de la grille hexagonale: {e}")
        return None

for widget in QApplication.allWidgets():
    if isinstance(widget, HexGridDialog):
        widget.close()

dialog = HexGridDialog()
dialog.exec_()