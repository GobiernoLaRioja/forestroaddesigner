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

from __future__ import unicode_literals
from __future__ import division

import os
import logging

from qgis.utils import iface, plugins
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint
from qgis.gui import QgsMessageBar

from slope_symbology import AttributeLayerSymbology
from frd_utils import array_funs as af
from frd_utils import exclusion_areas_fn
import viewers
from route_optimizer import a_star
from route_optimizer.polysimplify import polysimplify

try:
    profiler_plugin = plugins['profiletool']
    profiler = profiler_plugin.profiletool
    profiler.clearProfil()

except KeyError:
    logging.info("We could not find Profiletool plugin.")
    profiler = None
except AttributeError:
    logging.info("We could not find Profiletool plugin compatible with FRD.")
    profiler = None

logger = logging.getLogger("frd")

def showMessage(message,
                msg_type="Info", level=QgsMessageBar.INFO, duration=3):
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
        logger.info(message)

def _slope_label(min_slope_pct, max_slope_pct):
    """Create the label for design slope value
    """
    label = ""
    if min_slope_pct > 0:
        label = "{}_".format(min_slope_pct)
    label += "{}_percent".format(max_slope_pct)
    return label

class BestPathFinder(object):

    RAW_FN_TEMPLATE = 'frd_raw_{}_num_{}.shp'
    SIMPLIFIED_FN_TEMPLATE = 'frd_simplified_{}_num_{}.shp'

    def __init__(self, dtm_layer,
                     exclusion_areas_layer=None):
        
        self.dtm = {"layer": dtm_layer,
                    "array":  af.raster_2_array(dtm_layer)}
        self.converter = af.Converter(dtm_layer)

        self.exclusion_areas = {
                "layer": exclusion_areas_layer,
                "array": exclusion_areas_fn.create_exclusion_array(
                            dtm_layer,
                            exclusion_areas_layer)}

        self.optimizer = a_star.DefaultConstraintsOptimizer(
                self.dtm["array"],
                self.converter.pixel_width)
        self.set_parameters({"semi_size": 5,
                             "min_slope_pct": 0,
                             "max_slope_pct": 10,
                             "penalty_factor_xy": 50,
                             "penalty_factor_z": 50})

    def _slope_label(self):
        return _slope_label(self.parameters["min_slope_pct"],
                            self.parameters["max_slope_pct"]
                            )

    def set_output_folder(self, output_folder):

        self.output_folder = output_folder

    def set_parameters(self, parameters):

        self.parameters = parameters

        self.optimizer.reset_config(
                     parameters["min_slope_pct"] / 100.0,
                     parameters["max_slope_pct"] / 100.0,
                     parameters["semi_size"],
                     parameters["penalty_factor_xy"],
                     parameters["penalty_factor_z"],
                     self.exclusion_areas["array"])

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
        """Check for given points not inside exclusion areas and not out of
        dtm extent limits
        """
        if not self.dtm['layer'].extent().contains(
                QgsPoint(goal_coords[0], goal_coords[-1])):
            raise(ValueError(
                    u"Error: ¡No se admiten puntos fuera de la extensión\n" +
                    u" del Modelo Digital del Terreno!."))

        if self.exclusion_areas["layer"]:
            if self.optimizer._waypoints_index == []:
                for elem in self.exclusion_areas[
                        "layer"].dataProvider().getFeatures():
                    if elem.geometry().contains(
                            QgsPoint(goal_coords[0], goal_coords[-1])):
                        raise(ValueError(
                                u"Error: ¡No se admiten puntos dentro de" +
                                u" las áreas de exclusión!"))

    def _output_raw_filename(self):
        """Output the raw filename with last updated output index on set
            folder.
        """
        import glob
        file_mask = 'forest_road_lines_{}_num_{}.shp' # due raw_points_layer is a memory layer
        key_for_glob = os.path.join(
            self.output_folder, file_mask.format(self._slope_label(), '*'))
        files_list = glob.glob(key_for_glob)
        raw_file_name = self.RAW_FN_TEMPLATE.format(self._slope_label(),
                                         len(files_list) + 1)
        
        return os.path.join(
                self.output_folder, raw_file_name)

    def create_raw_output_layer(self):
        """creates the raw layer as point memory layer
        """
        fn = self._output_raw_filename()
        layer_name = os.path.splitext(os.path.split(fn)[-1])[0]

        self.raw_layer = QgsVectorLayer(
            'Point?crs={}'.format(self.dtm["layer"].crs().toWkt()),
            layer_name , 'memory')

        self._update_output_layer()
        if profiler:
            profiler.toolrenderer.setSelectionMethod(2)

        return self.raw_layer

    def _update_output_layer(self):
        """Updates the output layer (raw)
        """
        if self.raw_layer is None or not self.raw_layer.isValid():
            return False
        raw_path_index = self.optimizer.waypoints_index()
        raw_path_height_profile, _, _ = \
                dtm_values_at_points(self.dtm["array"],
                                     raw_path_index,
                                     self.parameters["max_slope_pct"] / 100.0,
                                     self.converter.pixel_width)
        dp = self.raw_layer.dataProvider()
        dp.deleteFeatures(
                self.raw_layer.allFeatureIds())

        raw_path_coords = self.converter.index_to_coord(raw_path_index)

        features = []
        for point_coords in raw_path_coords:
            new_feature= QgsFeature()
            new_feature.setGeometry(QgsGeometry.fromPoint(
                                        QgsPoint(*point_coords)))
            features.append(new_feature)

        result, _ = dp.addFeatures(features)
        dp.updateExtents()
        self.raw_layer.triggerRepaint()

        return result

    def create_simplified_output_layer(self,
                                       polyline_threshold):
        """Create the simplified layer (LineString Layer)
        """
        raw_path_index = self.optimizer.waypoints_index()

        if polyline_threshold>0 and len(raw_path_index)>0:
            path_simplifier = polysimplify.VWSimplifier(
                    raw_path_index)
            simp_path_index = path_simplifier.from_threshold(
                    polyline_threshold)
        else:
            simp_path_index = raw_path_index


        """Recover the height profile and create the lines layer."""
        lines_height_data, lines_section_slope, lines_projected_cum_dist = \
                dtm_values_at_points(self.dtm["array"],
                                     simp_path_index,
                                     self.parameters["max_slope_pct"] / 100.0,
                                     self.converter.pixel_width)

        road_layer = af.line_layer_from_coords_array(
                self.converter.index_to_coord(simp_path_index),
                self.output_folder,
                self.dtm["layer"].crs(),
                self._slope_label(),
                lines_height_data,
                lines_section_slope,
                lines_projected_cum_dist)

        AttributeLayerSymbology(road_layer,
                                "slope_p",
                                self.parameters["max_slope_pct"])
        return road_layer

def dtm_values_at_points(dtm_array,
                         points_index,
                         max_slope,
                         dtm_resolution_m):
    """Return z values for each point in points_index_rot"""
    height_data, section_slope, projected_cum_dist = \
            viewers.height_profile(dtm_array,
                                   points_index,
                                   max_slope,
                                   dtm_resolution_m)

    return height_data, section_slope, projected_cum_dist