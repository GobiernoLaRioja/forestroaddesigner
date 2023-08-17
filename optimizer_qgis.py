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

This module receives layers from QGis interface, extracts the raster of the
region of interest and handles it to the numpy based optimizer code.
After obtaining the optimal path, pixel coordinates are georeferenced back
and stored in the given shapefile.
"""

import os
import logging
import glob

import numpy as np #para pruebas

from qgis.utils import iface, plugins
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint, Qgis, QgsPointXY,QgsWkbTypes, QgsMarkerSymbol, QgsSimpleMarkerSymbolLayerBase 
from qgis.PyQt import QtGui
from PyQt5.QtGui import QColorConstants 

try:
    from . import frd_utils
    from . import slope_symbology
    from .slope_symbology import AttributeLayerSymbology
    from .frd_utils import array_funs as af
    from .frd_utils import exclusion_areas_fn
    from . import viewers
    from .route_optimizer import a_star
    from .route_optimizer import interactive_opt
    from .route_optimizer.polysimplify import polysimplify
except ImportError:
    import frd_utils
    import slope_symbology
    from slope_symbology import AttributeLayerSymbology
    from frd_utils import array_funs as af
    from frd_utils import exclusion_areas_fn
    import viewers
    from route_optimizer import a_star
    from route_optimizer.polysimplify import polysimplify

#import slope_symbology
# from .slope_symbology import AttributeLayerSymbology

#import frd_utils
#import frd_utils.array_funs
#import frd_utils.exclusion_areas_fn
# from .frd_utils import array_funs as af
# from .frd_utils import exclusion_ares_fn

#import viewers
#from route_optimizer import a_star
#from route_optimizer.polysimplify import polysimplify

# try:
#     profiler_plugin = plugins['profiletool']
#     profiler = profiler_plugin.profiletool
#     # clearProfil is only available in compatible versions of the plugin.
#     profiler.clearProfil()

# except KeyError:
#     logging.info("We could not find Profiletool plugin.")
#     profiler = None
# except AttributeError:
#     logging.info("We could not find Profiletool plugin compatible with FRD.")
#     profiler = None

logger = logging.getLogger("frd")

def showMessage(message,
                msg_type="Info", level=Qgis.Info, duration=3):
    """Compatibility function to allow running on QGis and test environments.
    This function is used to show messages in qgis interface if it is
    available, using the plugin custom frd logger if not available
    (e.g. during testing)."""
    try:
        iface.messageBar().pushMessage(
                msg_type,
                message,
                level=level,
                duration=duration)
    except AttributeError:
        # Running without iface present, maybe in testing
        logger.info(message)

def _interactive_label(length, slope_pct):
    label = ""    
    label = "L_{}_S_{}".format(length, slope_pct)
    return label

def _slope_label(min_slope_pct, max_slope_pct):
    label = ""
    if min_slope_pct > 0:
        label = "{}_".format(min_slope_pct)
    label += "{}_percent".format(max_slope_pct)
    return label

def _slope_radius_label(min_slope_pct, max_slope_pct, radius):
    label = ""
    label = "S_{}_{}_R_{}".format(min_slope_pct, max_slope_pct, radius)
    return label

def _road_options_label(slabel, r_options, w_road, cut, hc, fill, hf):
    label = slabel
    if r_options:
        cut_norm = "{0:.2f}".format(cut)
        fill_norm = "{0:.2f}".format(fill)
        label += "_W_{}_C_{}_HC_{}_F_{}_HF_{}".format(w_road, cut_norm, hc, fill_norm, hf)
    return label

def _factor_options(slabel, sf, rf, cff):
    label = slabel + "_FAC_{}_{}_{}".format( sf, rf, cff)
    return label
class InvalidPointError(ValueError):
    """Exception raised when a target point is out of bounds, or within an exclusion zone."""
    pass
class BestPathFinder(object):

    RAW_FN_TEMPLATE = 'frd_raw_{}_num_{}.shp'
    SIMPLIFIED_FN_TEMPLATE = 'frd_simplified_{}_num_{}.shp'

    def __init__(self, dtm_layer,
                     exclusion_areas_layer=None):
        # This two parameters are defined at start, can not be changed later.

        self.dtm = {"layer": dtm_layer,
                    "array":  frd_utils.array_funs.raster_2_array(dtm_layer)}
        self.converter = frd_utils.array_funs.Converter(dtm_layer)

        self.exclusion_areas = {
                "layer": exclusion_areas_layer,
                "array": frd_utils.exclusion_areas_fn.create_exclusion_array(
                            dtm_layer,
                            exclusion_areas_layer)}

        self.optimizer = a_star.DefaultConstraintsOptimizer(
                self.dtm["array"],
                self.converter.pixel_width)
                
        self.set_parameters({"semi_size": 5,
                             "min_slope_pct": 0,
                             "max_slope_pct": 10,
                             "penalty_factor_xy": 50,
                             "penalty_factor_z": 50,
                             "activated_road_options": False,
                             "cut_angle_tan": 200.0,
                             "fill_angle_tan": 200.0,
                             "cut_hmax_m": 10000.0,
                             "fill_hmax_m": 10000.0,
                             "min_curve_radio_m": 0.0,
                             "w_road_m": 0.0,
                             "slope_penalty_factor":1,
                             "radius_penalty_factor":1,
                             "cutfill_penalty_factor":1})

    def _slope_label(self):
        return _slope_label(self.parameters["min_slope_pct"],
                            self.parameters["max_slope_pct"]
                            )

    def _slopelabelcomplete(self):
        slabel = _slope_radius_label(self.parameters["min_slope_pct"],
                                     self.parameters["max_slope_pct"],
                                     self.parameters.get("min_curve_radio_m", ""))
        
        rolabel =_road_options_label(slabel,
                                     self.parameters.get("activated_road_options", ""),
                                     self.parameters.get("w_road_m", ""),
                                     self.parameters.get("cut_angle_tan", ""),
                                     self.parameters.get("cut_hmax_m", ""),
                                     self.parameters.get("fill_angle_tan", ""),
                                     self.parameters.get("fill_hmax_m", ""))

        flabel = _factor_options(rolabel,
                                 self.parameters.get("slope_penalty_factor", ""),
                                 self.parameters.get("radius_penalty_factor", ""),
                                 self.parameters.get("cutfill_penalty_factor", ""))
    
        return flabel

        
    def set_output_folder(self, output_folder):

        self.output_folder = output_folder
        self.current_output_index = self._find_available_output_suffix()

    def _find_available_output_suffix(self):
        """Check all the files in output_dir to find the first available
        suffix for both simplified and raw layers."""
        
        index = 1
        for template in (self.RAW_FN_TEMPLATE, self.SIMPLIFIED_FN_TEMPLATE):
            key_for_glob = os.path.join(
                self.output_folder, template.format(self._slopelabelcomplete(), '*'))
                #template.format(self._slope_label(), '*'))

            files_list = glob.glob(key_for_glob)
            for fn in files_list:
                fn_index = int(os.path.splitext(fn[0].split("_")[-1]))
                index = max(index, fn_index)

        return "{:02d}".format(index)

    def set_parameters(self, parameters):
        
        self.parameters = parameters

        self.optimizer.reset_config(
                     parameters["min_slope_pct"] / 100.0,
                     parameters["max_slope_pct"] / 100.0,
                     parameters["semi_size"],
                     parameters["penalty_factor_xy"],
                     parameters["penalty_factor_z"],
                     parameters.get("activated_road_options", None),
                     parameters.get("cut_angle_tan", None),
                     parameters.get("fill_angle_tan", None),
                     parameters.get("cut_hmax_m", None),
                     parameters.get("fill_hmax_m", None),
                     parameters.get("min_curve_radio_m", None),
                     parameters.get("w_road_m", None),
                     parameters.get("slope_penalty_factor",None), 
                     parameters.get("radius_penalty_factor",None), 
                     parameters.get("cutfill_penalty_factor", None),
                     self.exclusion_areas.get("array", None))

    def add_segment_to(self, goal_coords,
                        max_dist_m=None,
                        iterative=False,
                        force=False):

        self.check_point(goal_coords)
        goal_index =  self.converter.coord_to_index(
                        [goal_coords])
        self.optimizer.add_segment_to(goal_index[0],
                                      max_dist_m,
                                      iterative,
                                      force)
        self._update_output_layer()
        self._update_output_layer()

    def remove_last_segment(self):

        self.optimizer.remove_last_segment()

        self._update_output_layer()
        self._update_output_layer()

    def check_point(self, goal_coords):
        """Check that the target point is not out of the map and that it does not 
        lie within an exclusion zone."""

        if not self.dtm['layer'].extent().contains(
                QgsPointXY(goal_coords[0], goal_coords[-1])):
            raise InvalidPointError

        if self.exclusion_areas["layer"]:
            if self.optimizer._waypoints_index == []:
                for elem in self.exclusion_areas[
                        "layer"].dataProvider().getFeatures():
                    if elem.geometry().contains(
                            QgsPointXY(goal_coords[0], goal_coords[-1])):
                        print(f'Point at {goal_coords} lies within the exclusion zone!!!! Avoiding.')
                        raise InvalidPointError
                    else:
                        print(f'Point at {goal_coords} OK.')

    def _output_raw_filename(self):
        """Output the raw filename with last updated output index on set
            folder.
        """
        return os.path.join(
                self.output_folder,
                self.RAW_FN_TEMPLATE.format(
                        self._slopelabelcomplete(),
                        self.current_output_index))

    def create_raw_output_layer(self):

        fn = self._output_raw_filename()
        layer_name = os.path.splitext(os.path.split(fn)[-1])[0]

        # self.raw_layer = QgsVectorLayer(
        #     'Point?crs={}'.format(self.dtm["layer"].crs().toWkt()),
        #     layer_name , 'memory')
        
        self.raw_layer = QgsVectorLayer(
            'MultiLineString?crs={}'.format(self.dtm["layer"].crs().toWkt()),
            layer_name , 'memory')
        # self.raw_layer.setCrs(self.dtm["layer"].crs())
        self._update_output_layer()
        # if profiler:
        #     # Make layer selection the active mode
        #     profiler.toolrenderer.setSelectionMethod(2)

        return self.raw_layer
        #self.raw_points_mem_layer = QgsVectorLayer(
        #        'Point?crs={}'.format(self.dtm["layer"].crs().toWkt()),
        #        'road_points' , 'memory')

    def _update_output_layer(self, raw_path_index=None):
        self.features = None
        if self.raw_layer is None or not self.raw_layer.isValid():
            # print("Something is wrong with raw output layer")
            return False
        if raw_path_index is None:
            raw_path_index = self.optimizer.waypoints_index()
            raw_path_height_profile, _, _, _, radius_data, _, height_cutfill, cutfill_data, cutfill_pen_data, penalties_slope_rad= \
                    viewers.penalty_profile(self.dtm["array"],
                                        raw_path_index,
                                        self.parameters["min_slope_pct"] / 100.0,
                                        self.parameters["max_slope_pct"] / 100.0,                                     
                                        self.converter.pixel_width,
                                        self.parameters.get("min_curve_radio_m", None),
                                        self.parameters.get("activated_road_options", None),
                                        self.parameters.get("cut_angle_tan", None),
                                        self.parameters.get("fill_angle_tan", None),
                                        self.parameters.get("cut_hmax_m", None),
                                        self.parameters.get("fill_hmax_m", None),
                                        self.parameters.get("w_road_m", None))
        # Update the output layer with given points
        dp = self.raw_layer.dataProvider()
        dp.deleteFeatures(
                self.raw_layer.allFeatureIds())

        raw_path_coords = self.converter.index_to_coord(raw_path_index)

        features = []
        # for point_coords in raw_path_coords:
        #     new_feature= QgsFeature()
        #     new_feature.setGeometry(QgsGeometry.fromPointXY(
        #                                 QgsPointXY(*point_coords)))
        #     features.append(new_feature)
        for point_0, point_1 in zip(raw_path_coords[:-1], raw_path_coords[1:]):
            # print(f"point_0 {point_0} point_1 {point_1}")
            point_coord_0 = QgsPoint(*point_0)
            point_coord_1 = QgsPoint(*point_1)            
            feature = QgsFeature()
            line_geom = QgsGeometry.fromPolyline([point_coord_0, point_coord_1])
            feature.setGeometry(line_geom)
            # dp.addFeatures([feature])
            # dp.updateExtents()
            features.append(feature)
            # print(f"features {type(features)}")
        result, _ = dp.addFeatures(features)
        dp.updateExtents()
        self.raw_layer.renderer().symbol().setColor(QColorConstants.DarkRed)
        self.raw_layer.renderer().symbol().setWidth(0.6)
        # self.raw_layer.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.Star)
        props = self.raw_layer.renderer().symbol().symbolLayer(0).properties()
        # props['line_color'] = QColorConstants.Red
        # props['name'] = 'square'
        # props['size'] = '2'
        # self.raw_layer.renderer().setSymbol(QgsMarkerSymbol.createSimple(props))
        # print(props)
        self.raw_layer.triggerRepaint()

        return result
   
   

    def create_simplified_output_layer(self,
                                       polyline_threshold,
                                       show_graphics=False):
        # Recover the dtm values at given coordinates for the raw values
        # These values will respect the min/max slope constraint.

        raw_path_index = self.optimizer.waypoints_index()

        if polyline_threshold>0 and len(raw_path_index)>0:
            # logger.info("Simplificando polilínea con umbral {}".format(
            #        polyline_threshold))
            path_simplifier = polysimplify.VWSimplifier(
                    raw_path_index)
            simp_path_index = path_simplifier.from_threshold(
                    polyline_threshold)
        else:
            # logger.info("Sin simplificación de polilínea (umbral = {})"
                          #.format(polyline_threshold))
            simp_path_index = raw_path_index


        """Recover the height profile and create the lines layer."""
        lines_height_data, lines_section_slope, lines_projected_cum_dist, slope_pen, radius_data, row_rad_pen, height_cutfill, cutfill_data, cutfill_pen_data, penalties_slope_rad_cutfill = \
                viewers.penalty_profile(self.dtm["array"],
                                     simp_path_index,
                                     self.parameters["min_slope_pct"] / 100.0,
                                     self.parameters["max_slope_pct"] / 100.0,                                     
                                     self.converter.pixel_width,
                                     self.parameters.get("min_curve_radio_m", None),
                                     self.parameters.get("activated_road_options", None),
                                     self.parameters.get("cut_angle_tan", None),
                                     self.parameters.get("fill_angle_tan", None),
                                     self.parameters.get("cut_hmax_m", None),
                                     self.parameters.get("fill_hmax_m", None),
                                     self.parameters.get("w_road_m", None))

        summary, turn_number_list = viewers.summary( simp_path_index,
                                self.converter.pixel_width,
                                lines_height_data,
                                slope_pen,
                                radius_data,
                                row_rad_pen,
                                cutfill_pen_data)

        road_layer = frd_utils.array_funs.line_layer_from_coords_array(
                self.converter.index_to_coord(simp_path_index),
                self.output_folder,
                self.dtm["layer"].crs(),
                self._slopelabelcomplete(),
                lines_height_data,
                lines_section_slope,
                lines_projected_cum_dist,
                radius_data,
                height_cutfill,
                cutfill_data,
                cutfill_pen_data,
                penalties_slope_rad_cutfill,
                turn_number_list)
        # Add to the generated road layer a symbology that changes its color
        # according to its slope
        slope_symbology.AttributeLayerSymbology(road_layer,
                                "slope_p",
                                "radius_m",
                                "penalty",
                                "cut_fill",
                                "h_cutfill",
                                "cutfill_p",
                                self.parameters["min_slope_pct"],
                                self.parameters["max_slope_pct"],
                                self.parameters.get("min_curve_radio_m", None),
                                self.parameters.get("activated_road_options", None),
                                )
        # Return both the raw, points layer and the simplified polyline layer
        return road_layer, summary

class BestInteractivePathFinder(object):
        
    # RAW_FN_TEMPLATE = 'frd_raw_{}_num_{}.shp'
    # SIMPLIFIED_FN_TEMPLATE = 'frd_simplified_{}_num_{}.shp'

    RAW_FN_TEMPLATE = 'frd_raw_num_{}.shp'
    SIMPLIFIED_FN_TEMPLATE = 'frd_simplified_num_{}.shp'

    def __init__(self, dtm_layer,
                     exclusion_areas_layer=None):
        # This two parameters are defined at start, can not be changed later.        
        self.dtm = {"layer": dtm_layer,
                    "array":  frd_utils.array_funs.raster_2_array(dtm_layer)}
        self.converter = frd_utils.array_funs.Converter(dtm_layer)

        self.exclusion_areas = {
                "layer": exclusion_areas_layer,
                "array": frd_utils.exclusion_areas_fn.create_exclusion_array(
                            dtm_layer,
                            exclusion_areas_layer)}

        #DAVID CAMBIADO
        self.optimizer = interactive_opt.InteractiveDefaultConstraintsOptimizer(
                self.dtm["array"],
                self.converter.pixel_width)
                
        self.set_parameters({"inter_slope_pct": 0,
                             "inter_length": 0,
                             })

    def _slope_label(self):
        return _interactive_label(self.parameters["inter_slope_pct"],
                            self.parameters["inter_length"]
                            )
        
    def set_output_folder(self, output_folder):

        self.output_folder = output_folder
        self.current_output_index = self._find_available_output_suffix()

    def _find_available_output_suffix(self):
        """Check all the files in output_dir to find the first available
        suffix for both simplified and raw layers."""
        
        index = 1
        for template in (self.RAW_FN_TEMPLATE, self.SIMPLIFIED_FN_TEMPLATE):
            key_for_glob = os.path.join(
                self.output_folder, template.format( '*'))
                #template.format(self._slope_label(), '*'))

            files_list = glob.glob(key_for_glob)
            for fn in files_list:
                fn_index = int(os.path.splitext(fn[0].split("_")[-1]))
                index = max(index, fn_index)

        return "{:02d}".format(index)

    def set_parameters(self, parameters):
        
        self.parameters = parameters
        #DAVID CHANGED
        self.optimizer.reset_config(
                     parameters["inter_slope_pct"],
                     parameters["inter_length"],
                     self.exclusion_areas.get("array", None))

    def search_segment_to(self, goal_coords):
        # self.check_point(goal_coords)
        if self.interactive_check_point(goal_coords):
            # print(f"Optimizer_qgis search_segment_to goal_coords {goal_coords}")
            goal_index =  self.converter.coord_to_index(
                            [goal_coords])
            # print(f"Optimizer_qgis search_segment_to goal_index {goal_index}")
            goal_result, up_down = self.optimizer.interactive_search_segment_to_(goal_index[0])
            if goal_result is not None:
                goal_result_coord = self.converter.index_to_coord([goal_result])
                return goal_result_coord[0], up_down
            else:
                return None, None
        else:
            # print(f"Optimizer_qgis search_segment_to goal_coords {goal_coords} IS OUT")
            return None, None


    def add_segment_to(self, goal_coords,
                        max_dist_m=None,
                        iterative=False,
                        force=False):

        # self.check_point(goal_coords)
        if self.interactive_check_point(goal_coords):
            # print(f"Optimizer_qgis add_segment_to goal_coords {goal_coords}")
            goal_index =  self.converter.coord_to_index(
                            [goal_coords])
            # print(f"Optimizer_qgis add_segment_to goal_index {goal_index}")
            if force:
                self.optimizer.interactive_add_segment_to_straight(goal_index[0])
            else:
                self.optimizer.interactive_add_segment_to(goal_index[0], iterative)
            self._update_output_layer()
            self._update_output_layer()
        
        else:
            print(f"Optimizer_qgis add_segment_to goal_coords {goal_coords} IS OUT")


    def remove_last_segment(self):

        self.optimizer.remove_last_segment()

        self._update_output_layer()
        self._update_output_layer()

    def check_point(self, goal_coords):
        """Check that the target point is not out of the map and that it does not 
        lie within an exclusion zone."""

        if not self.dtm['layer'].extent().contains(
                QgsPointXY(goal_coords[0], goal_coords[-1])):
            raise InvalidPointError

        if self.exclusion_areas["layer"]:
            if self.optimizer._waypoints_index == []:
                for elem in self.exclusion_areas[
                        "layer"].dataProvider().getFeatures():
                    if elem.geometry().contains(
                            QgsPointXY(goal_coords[0], goal_coords[-1])):
                        print(f'Point at {goal_coords} lies within the exclusion zone!!!! Avoiding.')
                        raise InvalidPointError
                    else:
                        print(f'Point at {goal_coords} OK.')
    
    def interactive_check_point(self, goal_coords):
        """Check that the target point is not out of the map and that it does not 
        lie within an exclusion zone."""

        if not self.dtm['layer'].extent().contains(
                QgsPointXY(goal_coords[0], goal_coords[-1])):
            return False

        if self.exclusion_areas["layer"]:
            if self.optimizer._waypoints_index == []:
                for elem in self.exclusion_areas[
                        "layer"].dataProvider().getFeatures():
                    if elem.geometry().contains(
                            QgsPointXY(goal_coords[0], goal_coords[-1])):
                        print(f'Point at {goal_coords} lies within the exclusion zone!!!! Avoiding.')
                        return False
                    else:
                        print(f'Point at {goal_coords} OK.')
        
        return True

    def _output_raw_filename(self):
        """Output the raw filename with last updated output index on set
            folder.
        """
        return os.path.join(
                self.output_folder,
                self.RAW_FN_TEMPLATE.format(                        
                        self.current_output_index))

    def create_raw_output_layer(self):

        fn = self._output_raw_filename()
        layer_name = os.path.splitext(os.path.split(fn)[-1])[0]

        # self.raw_layer = QgsVectorLayer(
        #     'Point?crs={}'.format(self.dtm["layer"].crs().toWkt()),
        #     layer_name , 'memory')
        
        self.raw_layer = QgsVectorLayer(
            'MultiLineString?crs={}'.format(self.dtm["layer"].crs().toWkt()),
            layer_name , 'memory')
        # self.raw_layer.setCrs(self.dtm["layer"].crs())
        #DAVID CAMBIAR
        # self._update_output_layer()
        # if profiler:
        #     # Make layer selection the active mode
        #     profiler.toolrenderer.setSelectionMethod(2)

        return self.raw_layer
        #self.raw_points_mem_layer = QgsVectorLayer(
        #        'Point?crs={}'.format(self.dtm["layer"].crs().toWkt()),
        #        'road_points' , 'memory')

    #DAVID CAMBIAR Viewers
    def _update_output_layer(self, raw_path_index=None):
        self.features = None
        if self.raw_layer is None or not self.raw_layer.isValid():
            # print("Something is wrong with raw output layer")
            return False
        if raw_path_index is None:
            raw_path_index = self.optimizer.waypoints_index()
            # print(f"MODO INTERACTIVO Optimizer_qgis _update_output_layer raw_path_index {raw_path_index}")
            
        # Update the output layer with given points
        dp = self.raw_layer.dataProvider()
        dp.deleteFeatures(
                self.raw_layer.allFeatureIds())

        raw_path_coords = self.converter.index_to_coord(raw_path_index)
        # raw_path_coords = raw_path_index

        features = []
        # for point_coords in raw_path_coords:
        #     new_feature= QgsFeature()
        #     new_feature.setGeometry(QgsGeometry.fromPointXY(
        #                                 QgsPointXY(*point_coords)))
        #     features.append(new_feature)
        for point_0, point_1 in zip(raw_path_coords[:-1], raw_path_coords[1:]):
            # print(f"point_0 {point_0} point_1 {point_1}")
            point_coord_0 = QgsPoint(*point_0)
            point_coord_1 = QgsPoint(*point_1)            
            feature = QgsFeature()
            line_geom = QgsGeometry.fromPolyline([point_coord_0, point_coord_1])
            feature.setGeometry(line_geom)
            # dp.addFeatures([feature])
            # dp.updateExtents()
            features.append(feature)
            # print(f"features {type(features)}")
        result, _ = dp.addFeatures(features)
        dp.updateExtents()
        self.raw_layer.renderer().symbol().setColor(QColorConstants.DarkRed)
        self.raw_layer.renderer().symbol().setWidth(0.6)
        # self.raw_layer.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.Star)
        props = self.raw_layer.renderer().symbol().symbolLayer(0).properties()
        # props['line_color'] = QColorConstants.Red
        # props['name'] = 'square'
        # props['size'] = '2'
        # self.raw_layer.renderer().setSymbol(QgsMarkerSymbol.createSimple(props))
        # print(props)
        self.raw_layer.triggerRepaint()
        if len(raw_path_coords) > 0:
            self.raw_path_coords_last_point = raw_path_coords[-1]
        else:
            self.raw_path_coords_last_point = None
        return result
   
   
    #DAVID
    def create_simplified_output_layer(self,
                                       polyline_threshold,
                                       show_graphics=False):
        # Recover the dtm values at given coordinates for the raw values
        # These values will respect the min/max slope constraint.

        raw_path_index = self.optimizer.waypoints_index()       

        simp_path_index = raw_path_index
        """Recover the height profile and create the lines layer."""
        lines_height_data, lines_section_slope, lines_projected_cum_dist = viewers.interactive_height_profile(self.optimizer.interpolator,
                                     simp_path_index,                                                                         
                                     self.converter.pixel_width)
        
        summary, turn_number_list = viewers.interactive_summary( simp_path_index,
                                self.converter.pixel_width,
                                lines_height_data,
                                )
       

        road_layer = frd_utils.array_funs.interactive_line_layer_from_coords_array(
                self.converter.index_to_coord(simp_path_index),
                self.output_folder,
                self.dtm["layer"].crs(),
                self._slope_label(),
                lines_height_data,
                lines_section_slope,
                lines_projected_cum_dist,                
                turn_number_list)
        # Add to the generated road layer a symbology that changes its color
        # according to its slope
        slope_symbology.InteractiveAttributeLayerSymbology(road_layer,
                                "slope_p",                                
                                )
        # Return both the raw, points layer and the simplified polyline layer
        return road_layer, summary