# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterFeatureSink,
                       QgsUnitTypes)
from qgis import processing
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsVectorLayer,QgsRasterLayer, QgsProject

from .. import optimizer_qgis as oq
from .. import frd_utils
from .. frd_utils import array_funs, inputs_checker
# from .. frd_utils import logging_qgis as logging
import logging
import tempfile
from pathlib import Path
from osgeo import gdal
import os


def create_loging_file():
    """Crear y configura un fichero logger de registro
    """
    base_dir = os.path.join(os.path.dirname(__file__), 'logs')
    base_dir_path = Path(base_dir)
    base_dir_path.mkdir(exist_ok=True)
    log_filename = str(os.path.join(base_dir, 'logfile.log'))
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    print(f'log_filename FILE {log_filename} ')
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.DEBUG,   # Nivel de los eventos que se registran en el logger
        filename=log_filename,  # Fichero de  logs
        format=log_format      # Formato de registro
        )
    
logger = logging.getLogger("frd")
logger.setLevel(logging.DEBUG)
logger.info("--- START LOGGING PROCESSING ALGORITHM ---")



class ForestRoadDesignerProcessingAlgorithm(QgsProcessingAlgorithm):
    """    
    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    EXCLUDED_INPUT = 'EXCLUDED_INPUT'
    POLILINE = 'POLILINE'
    OUTPUT_DIR = "OUTPUT_DIR"
    MIN_SLOPE = 'MIN_SLOPE'
    MAX_SLOPE = 'MAX_SLOPE'
    MIN_CURVE_RADIO = 'MIN_CURVE_RADIO'
    ACTIVATED_ROAD_OPTIONS = 'ACTIVATED_ROAD_OPTIONS'
    W_ROAD = 'W_ROAD'
    CUT_ANGLE = 'CUT_ANGLE'
    CUT_HMAX = 'CUT_HMAX'
    FILL_ANGLE = 'FILL_ANGLE'
    FILL_HMAX = 'FILL_HMAX'
    PENALTY_FACTOR_XY = 'PENALTY_FACTOR_XY'
    PENALTY_FACTOR_Z = 'PENALTY_FACTOR_Z'
    SEMI_SIZE = 'SEMI_SIZE'
    POLILINE_TRESHOLD = 'POLILINE_TRESHOLD'
    SLOPE_PENALTY = 'SLOPE_PENALTY'
    RADIUS_PENALTY = 'RADIUS_PENALTY'
    CUTFILL_PENALTY = 'CUTFILL_PENALTY'

    PARAM_TYPE_DOUBLE = 'double'
    PARAM_TYPE_INTEGER = 'integer'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ForestRoadDesignerProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Forest Road Designer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        #return self.tr("Example algorithm short description")
        return ''

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        icon = QIcon(':/plugins/ForestRoadDesigner/icons/icon.png')
        return icon

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """ 
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Introduce capa')
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.EXCLUDED_INPUT,
                self.tr('Introduce zona de exclusión'),
                [QgsProcessing.TypeVectorPolygon],
                optional = True
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.POLILINE,
                self.tr('Introduce polilínea para proceso por lotes'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_DIR,
                self.tr('Introduce carpeta destino de resultados'),
                defaultValue = None,
                optional  = False,
                createByDefault = False
            )
        )

        param_road_option = QgsProcessingParameterBoolean(
                self.ACTIVATED_ROAD_OPTIONS,
                self.tr('Activa/desactiva opciones de pendiente/terraplen')
            )

        #param_road_option.setFlags(param_road_option.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        self.set_parameters_number(self.MIN_SLOPE, 'Introduce min_slope', self.PARAM_TYPE_DOUBLE, 0, 10000)
        self.set_parameters_number(self.MAX_SLOPE, 'Introduce max_slope', self.PARAM_TYPE_DOUBLE, 0, 10000, 12.50)
        self.set_parameters_number(self.MIN_CURVE_RADIO, 'Introduce radio mínimo de curvatura', self.PARAM_TYPE_DOUBLE, 0, 10000)
        self.addParameter(param_road_option)
        self.set_parameters_number(self.W_ROAD, 'Introduce ancho de pista', self.PARAM_TYPE_DOUBLE, 0, 10000)
        self.set_parameters_number(self.CUT_ANGLE, 'Introduce pendiente de desmonte', self.PARAM_TYPE_DOUBLE, 0, 10000)
        self.set_parameters_number(self.CUT_HMAX, 'Introduce altura máxima de desmonte', self.PARAM_TYPE_DOUBLE, 0, 10000)
        self.set_parameters_number(self.FILL_ANGLE, 'Introduce pendiente máxima de terraplén', self.PARAM_TYPE_DOUBLE, 0, 10000)
        self.set_parameters_number(self.FILL_HMAX, 'Introduce altura máxima de terraplén', self.PARAM_TYPE_DOUBLE, 0, 10000)        
        self.set_parameters_number(self.PENALTY_FACTOR_XY, 'Introduce penalización por cambio de dirección', self.PARAM_TYPE_INTEGER, 0, 100, 40)
        self.set_parameters_number(self.PENALTY_FACTOR_Z, 'Introduce penalización por cambio de rasante', self.PARAM_TYPE_INTEGER, 0, 100, 40)
        self.set_parameters_number(self.SEMI_SIZE, 'Introduce longitud segmento mínima', self.PARAM_TYPE_INTEGER, 2, 10 , 2)
        self.set_parameters_number(self.POLILINE_TRESHOLD, 'Introduce tolerancia al resultado', self.PARAM_TYPE_INTEGER, 0, 5 , 0)
        self.set_parameters_number(self.SLOPE_PENALTY, 'Introduce factor penalización de pendiente', self.PARAM_TYPE_INTEGER, 1, 10 , 1)
        self.set_parameters_number(self.RADIUS_PENALTY, 'Introduce factor penalización de radio', self.PARAM_TYPE_INTEGER, 1, 10, 1)
        self.set_parameters_number(self.CUTFILL_PENALTY, 'Introduce factor penalización de desmonte/terraplén', self.PARAM_TYPE_INTEGER, 1, 10,1)
       
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         self.OUTPUT,
        #         self.tr('Output layer')
        #     )
        # )
        logger.info("--- PROCESSING ALGORITHM --- START ---")

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        outputFolder = tempfile.mkdtemp("frd")
        feedback.pushInfo('..outputFolder..1.. {}'.format(outputFolder))
        input_parameters = {}
        input_dtm = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        exclusion_areas_layer = self.parameterAsVectorLayer(parameters, self.EXCLUDED_INPUT, context)
        input_v_layer = self.parameterAsVectorLayer(parameters, self.POLILINE, context)
        outputFolder = self.parameterAsFileOutput(parameters, self.OUTPUT_DIR, context)
        feedback.pushInfo('..outputFolder..type.. {}'.format(type(outputFolder)))
        name = Path(outputFolder).name
        feedback.pushInfo('..outputFolder..type.. {}'.format(name))
        if Path(outputFolder).name == self.OUTPUT_DIR:
            outputFolder = tempfile.mkdtemp("frd")
        poliline_treshold = self.parameterAsInt(parameters, self.POLILINE_TRESHOLD, context)

        input_parameters["min_slope_pct"] = self.parameterAsDouble(parameters, self.MIN_SLOPE, context)
        input_parameters["max_slope_pct"] = self.parameterAsDouble(parameters, self.MAX_SLOPE, context)
        input_parameters["min_curve_radio_m"] = self.parameterAsDouble(parameters, self.MIN_CURVE_RADIO, context)
        input_parameters["w_road_m"] = self.parameterAsDouble(parameters, self.W_ROAD, context)
        input_parameters["activated_road_options"] = self.parameterAsBoolean(parameters, self.ACTIVATED_ROAD_OPTIONS, context)
        input_parameters["cut_angle_tan"] = self.parameterAsDouble(parameters, self.CUT_ANGLE, context)
        input_parameters["cut_hmax_m"] = self.parameterAsDouble(parameters, self.CUT_HMAX, context)
        input_parameters["fill_angle_tan"] = self.parameterAsDouble(parameters, self.FILL_ANGLE, context)
        input_parameters["fill_hmax_m"] = self.parameterAsDouble(parameters, self.FILL_HMAX, context)
        input_parameters["penalty_factor_xy"] = self.parameterAsInt(parameters, self.PENALTY_FACTOR_XY, context)
        input_parameters["penalty_factor_z"] = self.parameterAsInt(parameters, self.PENALTY_FACTOR_Z, context)
        input_parameters["semi_size"] = self.parameterAsInt(parameters, self.SEMI_SIZE, context)
        input_parameters["slope_penalty_factor"] = self.parameterAsInt(parameters, self.SLOPE_PENALTY, context)
        input_parameters["radius_penalty_factor"] = self.parameterAsInt(parameters, self.RADIUS_PENALTY, context)
        input_parameters["cutfill_penalty_factor"] = self.parameterAsInt(parameters, self.CUTFILL_PENALTY, context)

        try:
            if input_dtm is None:
                raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            else:
                raster = gdal.Open(input_dtm.source())
                raster.GetGeoTransform()
                geotransform = raster.GetGeoTransform()
                dtm_pixel_size = geotransform[1]
                input_parameters["semi_size"] = self.parameterAsInt(parameters, self.SEMI_SIZE, context) / dtm_pixel_size
            
            if input_v_layer is None:
                raise QgsProcessingException(self.invalidSourceError(parameters, self.POLILINE))

            if outputFolder is None:
                raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT_DIR))

            if not input_parameters["activated_road_options"] == self.ckeck_road_options(input_parameters):
                
                raise QgsProcessingException("Error: ¡Error en las opciones de pista!")            

            QgsProject.instance().addMapLayer(input_v_layer)
            QgsProject.instance().addMapLayer(input_dtm)
            QgsProject.instance().addMapLayer(exclusion_areas_layer)

            finder = oq.BestPathFinder(input_dtm, exclusion_areas_layer)
            finder.set_parameters(input_parameters)
            finder.set_output_folder(outputFolder)
            raw_layer = finder.create_raw_output_layer()

            for point_index in array_funs.waypoints_list(input_v_layer):
                finder.add_segment_to(point_index)  
        
            simplified_layer, summary = finder.create_simplified_output_layer(
                                        poliline_treshold)

            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayers([raw_layer], False)
            for layer in [raw_layer]:
                root.insertLayer(0, layer)

            QgsProject.instance().addMapLayers([simplified_layer], False)
            for layer in [simplified_layer]:
                root.insertLayer(0, layer)

            #sink = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
            # Send some information to the user

            feedback.pushInfo('input_dtm Type is {}'.format(type(input_dtm)))
            feedback.pushInfo('exclusion_areas_layer Type is {}'.format(type(exclusion_areas_layer)))
            feedback.pushInfo('input_v_layer Type is {}'.format(type(input_v_layer)))
            feedback.pushInfo('ckeck_road_options {}'.format(self.ckeck_road_options(input_parameters)))

            feedback.pushInfo('..simplified_layer.isValid() {}'.format(simplified_layer.isValid()))
            feedback.pushInfo('..featureCount {}'.format(raw_layer.dataProvider().featureCount()))
            feedback.pushInfo('..simplified_layer..summary {}'.format(summary))
            feedback.pushInfo('..outputFolder.. {}'.format(outputFolder))

            dtmMapUnit = self._updateMapUnits(input_dtm) 
            summary_msg = self.create_sumary_message(summary, dtmMapUnit, input_parameters)
            feedback.pushInfo(summary_msg)
            # If sink was not created, throw an exception to indicate that the algorithm
            # encountered a fatal error. The exception text can be any string, but in this
            # case we use the pre-built invalidSinkError method to return a standard
            # helper text for when a sink cannot be evaluated
            if outputFolder is None:
                raise QgsProcessingException('Error en archivo salida')

            if feedback.isCanceled():
                    raise Exception('Process cancelled by user')
            #     # Stop the algorithm if cancel button has been clicked
            #     if feedback.isCanceled():
            #         break

            #     # Add a feature in the sink
            #     sink.addFeature(feature, QgsFeatureSink.FastInsert)

            #     # Update the progress bar
            #     feedback.setProgress(int(current * total))

            # To run another Processing algorithm as part of this algorithm, you can use
            # processing.run(...). Make sure you pass the current context and feedback
            # to processing.run to ensure that all temporary layer outputs are available
            # to the executed algorithm, and that the executed algorithm can send feedback
            # reports to the user (and correctly handle cancellation and progress reports!)
            
            # Return the results of the algorithm. In this case our only result is
            # the feature sink which contains the processed features, but some
            # algorithms may return multiple feature sinks, calculated numeric
            # statistics, etc. These should all be included in the returned
            # dictionary, with keys matching the feature corresponding parameter
            # or output names.
            logger.info("--- PROCESSING ALGORITHM --- FINISH ---")
        except Exception as ex:
            logger.error(f"ERROR TYPE {type(ex)}")
            logger.error(f"ERROR ARGS {ex.args}")
            logger.error(f"ERROR {str(ex)}")

        return {self.OUTPUT_DIR: outputFolder}

    def set_parameters_number(self, param_name, input_text, param_type, param_minimum, param_maximum, default = None, param_flag = None):

        param = None

        if param_type is "integer":

            param = QgsProcessingParameterNumber(
                param_name,
                self.tr(input_text),
                QgsProcessingParameterNumber.Integer,
                defaultValue = default if default else 0
            )

        if param_type is "double":

            param = QgsProcessingParameterNumber(
                param_name,
                self.tr(input_text),
                QgsProcessingParameterNumber.Double,
                defaultValue = default if default else 0
            )        
            param.setMetadata( {'widget_wrapper': { 'decimals': 2 }}) 

        param.setMinimum(param_minimum)
        param.setMaximum(param_maximum)
        if param_flag:
            param.setFlags(param.flags() | self.assign_flag(param_flag)) 
        self. addParameter(param)

    def assign_flag(self, param_flag):
        if param_flag is "advanced":
            return QgsProcessingParameterDefinition.FlagAdvanced
        if param_flag is "hidden":
            return QgsProcessingParameterDefinition.FlagHidden
        if param_flag is "optional":
            return QgsProcessingParameterDefinition.FlagOptional
        if param_flag is "isModelOutput":
            return QgsProcessingParameterDefinition.FlagIsModelOutput 	

    def ckeck_road_options(self, parameters):
        """check if there are values  for road options"""
        check = False
        if (parameters["w_road_m"] > 0 and
            parameters["cut_angle_tan"] > 0 and
            parameters["cut_hmax_m"] > 0 and
            parameters["fill_angle_tan"] > 0 and
            parameters["fill_hmax_m"] > 0 ):            
            check = True

        return check

    def create_sumary_message(self, summary_dic, dtmMapUnit, input_parameters ):
        """Create a message to show the sumay results"""
       
        msg_gen = """    Distancia origen-destino {:.2f}{}
    Distancia recorrido total {:.2f}{}
    Desnivel neto {:.2f}{}
    Desnivel acumulado {:.2f}{}
    Desnivel medio neto {:.2f}{}
    Desnivel medio acumulado {:.2f}{}
    Número penalizaciones pendiente {}""".format(
                    summary_dic["straight_distance"], dtmMapUnit,
                    summary_dic["total_cumsum"], dtmMapUnit,
                    summary_dic["raw_slope"], dtmMapUnit,
                    summary_dic["total_acumulative_slope"], dtmMapUnit,
                    summary_dic["average_slope"], dtmMapUnit,
                    summary_dic["average_acum_slope"], dtmMapUnit,                    
                    summary_dic["total_slope_pen"]
                )

        msg_radius = """\n   Número penalizaciones radio {}""".format(
                    summary_dic["total_rad_pen"]) if input_parameters["min_curve_radio_m"] > 0 else ""

        msg_cutfill = """\n   Número penalizaciones desmonte/terraplén {}""".format(
                    summary_dic["tota_cutfill_pen"]) if input_parameters["activated_road_options"] else "" 

        msg_twist_number = """\n   Número de giros {}""".format(
                    summary_dic["twist_number"])

        msg_track_quality = """\n   Indice de calidad de trazado {:.2f}""".format(
                    summary_dic["track_quality"])

        msg = msg_gen + msg_radius + msg_cutfill + msg_twist_number + msg_track_quality

        return msg

    def _updateMapUnits(self, dtmLayer):
        """ returns metric unit from the layer"""
        
        if dtmLayer.isValid():
            # dtmLayer is a QgsRasterLayer
            crs = dtmLayer.crs()
            # crs is a QgsCoordinateReferenceSystem 
            unit = crs.mapUnits()
            s_unit = QgsUnitTypes.toAbbreviatedString(unit)
        else:
            s_unit =""
        return s_unit