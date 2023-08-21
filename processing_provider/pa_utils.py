# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ForestRoadDesignerDockWidget
                                 A QGIS plugin
 This plugin serve as support of foresters in the design of forest roads
                             -------------------
        begin                : 2017-02-08
        git sha              : $Format:%H$
        copyright            : (C) 2017 by PANOimagen S.L.
        email                : info@panoimagen.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
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

INPUT_DTM_ERROR = "Error: ¡No se ha seleccionado un DTM!\nPor favor seleccione uno."
INPT_V_LAYER_ERROR = "Error: ¡No se ha seleccionado ninguna capa con\nlos puntos de paso!\nPor favor seleccione una."
ROAD_OPTIONS_ERROR = "Error: ¡Error en las opciones de pista!\nPor favor revise los valores o desactive la opción"
OPTIMIZE_ERROR = "Error del optimizador"
param = ""
INPUT_PARAMETER_ERROR = f"Error: El parámetro {param} es incorrecto"


def ckeck_road_options(self, parameters):
    """check if there are values  for road options"""
    check = False
    if (parameters["w_road_m"] > 0 and
        parameters["cut_angle_tan"] > 0 and
        parameters["cut_hmax_m"] > 0 and
        parameters["fill_angle_tan"] > 0 and
        parameters["fill_hmax_m"] > 0 ):            
        check = True
    if parameters["activated_road_options"] == check:
        message = ROAD_OPTIONS_ERROR
        return False, message
    else:
        return True, ""

def check_parameters(self, parameters):
    """check if input parameters are fine"""
    
    message = ""
    check_parameter(self,parameters["min_slope_pct"], 0, 100000)
    check_parameter(self,parameters["max_slope_pct"], 2, 100000)
    check_parameter(self,parameters["min_curve_radio_m"], 2, 100000)
    check_parameter(self,parameters["w_road_m"], 2, 100000)
    check_parameter(self,parameters["cut_angle_tan"], 2, 100000)
    check_parameter(self,parameters["cut_hmax_m"], 2, 100000)
    check_parameter(self,parameters["fill_angle_tan"], 2, 100000)
    check_parameter(self,parameters["fill_hmax_m"], 2, 100000)
    check_parameter(self,parameters["penalty_factor_xy"], 2, 100000)
    check_parameter(self,parameters["penalty_factor_z"], 2, 100000)
    check_parameter(self,parameters["semi_size"], 2, 100000)
    check_parameter(self,parameters["slope_penalty_factor"], 2, 100000)
    check_parameter(self,parameters["radius_penalty_factor"], 2, 100000)
    check_parameter(self,parameters["cutfill_penalty_factor"], 2, 100000)
        
        

def check_parameter(self,param, lower_limit, upper_limit):
    """Check that parameter in into de value limits. Retur a message"""
    message = ""
    if param < lower_limit:
        message += f"el parámetro {param} no puede ser menor que {lower_limit}\n"
    if param > upper_limit:
        message += f"el parámetro {param} no puede ser mayor que {lower_limit}\n"
    return message



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

    msg = msg_gen + msg_radius + msg_cutfill

    return msg


def updateMapUnits(self, dtmLayer):
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