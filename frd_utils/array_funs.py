# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ForestRoadDesigner
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

This module contains a set of auxiliary functions to allow transforming
between QGis raster layers and numpy arrays, including functions to convert
to layer coordinates (_coord vars) to pixel indices (_index vars).
"""
from __future__ import unicode_literals
from __future__ import division
import os
import numpy as np
import glob

import logging

from osgeo import gdal, osr
from gdal import gdalconst as gcon
from qgis.core import (QGis, QgsGeometry, QgsPoint,
                       QgsVectorLayer, QgsFeature,
                       QgsVectorFileWriter)

import layers_attributes

logger = logging.getLogger("frd")

def _swap_xy(iterable_points):
    """swap x y coordinates of points
    
    The order of coords is swapped between qgis layers and numpy arrays.
    """
    return [p[::-1] for p in iterable_points]

def raster_no_data_value(dtm_layer):
    """ Function to get the dtm layer noDataValue
    """
    extent = dtm_layer.extent()
    provider = dtm_layer.dataProvider()
    rows = dtm_layer.rasterUnitsPerPixelY()
    cols = dtm_layer.rasterUnitsPerPixelX()
    block = provider.block(1, extent,  rows, cols)
    dtm_no_data_value = block.noDataValue()
    
    return dtm_no_data_value

def waypoints_list(waypoints_layer):
    """To extract the coordinates of the waypoints like a list [x,y]
    
    Input can be a layer of type WKBPoint or WKBLineString.
    """    
    provider = waypoints_layer.dataProvider().getFeatures()
    waypoints_coords_list = []
    for elem in provider:
        geom = elem.geometry()
        if geom.wkbType() == QGis.WKBLineString:
            line = geom.asPolyline()
            waypoints_coords_list = [[point.x(), point.y()] for point in line]
        elif geom.wkbType() == QGis.WKBPoint:
            point = geom.asPoint()
            waypoints_coords_list.append([point.x(), point.y()])

    return waypoints_coords_list

def raster_2_array(dtm_layer):
    """Function to transform a georeferenced raster layer to an array.
    """
    raster = gdal.Open(dtm_layer.source())
    raster_band = raster.GetRasterBand(1)
    raster_array = raster_band.ReadAsArray()

    return raster_array

def array_2_raster(
        dtm_layer, waypoints_layer, output_folder, waypoints_coords_list):
    """ Transform a numpy array to a raster layer with the information of the array
    """
    data_set = gdal.Open(dtm_layer.source())
    dtm_layer_path, dtm_layer_file_name = os.path.split(dtm_layer.source())
    dtm_layer_name, extension = os.path.splitext(dtm_layer_file_name)
    data_set_driver = data_set.GetDriver()
    data_set_band = data_set.GetRasterBand(1)
    data_set_array = data_set_band.ReadAsArray()
    data_set_geotransform = data_set.GetGeoTransform()
    data_set_origin_x = data_set_geotransform[0]
    data_set_origin_y = data_set_geotransform[3]
    data_set_pixel_width = data_set_geotransform[1]
    data_set_pixel_height = data_set_geotransform[5]

    cols = data_set_array.shape[1]
    rows = data_set_array.shape[0]

    newRasterfn = os.path.join(output_folder, 'raster_desde_array' + extension)
    data_set_out = data_set_driver.Create(
            newRasterfn, cols, rows, 1, gcon.GDT_Float32)
    data_set_out.SetGeoTransform((data_set_origin_x, data_set_pixel_width, 0,
                                  data_set_origin_y, 0, data_set_pixel_height))

    data_set_out_SRS = osr.SpatialReference()
    data_set_out_SRS.ImportFromWkt(data_set.GetProjectionRef())
    data_set_out.SetProjection(data_set_out_SRS.ExportToWkt())
    data_set_out_band = data_set_out.GetRasterBand(1)
    data_set_out_band.WriteArray(data_set_array)
    data_set_out_band.FlushCache()

class Converter(object):
    def __init__(self, layer):
        data_set = gdal.Open(layer.source())
        self.data_set_geotransform = data_set.GetGeoTransform()
        self.pixel_width = self.data_set_geotransform[1]
        self.pixel_height = self.data_set_geotransform[5]
    
        self.x_0_c = self.data_set_geotransform[0] + (
                self.data_set_geotransform[1] / 2)
        self.y_0_c = self.data_set_geotransform[3] + (
                self.data_set_geotransform[5] / 2)
    
    def coord_to_index(self, waypoints_coords_list):
        """ Convert coordinate waypoints to index waypoints
        """
        
        wpts_coords_array = np.array(waypoints_coords_list, dtype=np.float)
        if wpts_coords_array.size > 0:
            wpts_index_array = (
                (wpts_coords_array - 
                 np.array([[self.x_0_c, self.y_0_c]], dtype=np.float))
                / np.array([[self.pixel_width, self.pixel_height]], 
                           dtype=np.float))
            return _swap_xy(wpts_index_array)
        else:
            return np.array([], dtype=np.float)
    
    def index_to_coord(self, waypoints_index_array):
        """Convert index waypoints to coordinate waypoints
        """
        if len(waypoints_index_array) > 0:
            waypoints_coords_array = (
                np.array(_swap_xy(waypoints_index_array), dtype=np.float)
                * np.array([[self.pixel_width, self.pixel_height]], 
                           dtype=np.float)
                + np.array([[self.x_0_c, self.y_0_c]], dtype=np.float))
            return waypoints_coords_array
        else:
            return np.array([], dtype=np.float)

def coord_to_index(dtm_layer, waypoints_coords_list):
    """ Convert coordinate waypoints to index waypoints
    """
    data_set = gdal.Open(dtm_layer.source())
    data_set_geotransform = data_set.GetGeoTransform()

    x_0 = data_set_geotransform[0]
    y_0 = data_set_geotransform[3]
    pixel_width = data_set_geotransform[1]
    pixel_height = data_set_geotransform[5]

    x_0_c = x_0 + ( pixel_width / 2)
    y_0_c = y_0 + ( pixel_height / 2)

    wpts_coords_array = np.array(waypoints_coords_list, dtype=np.float)

    wpts_index_array = (
            (wpts_coords_array - 
             np.array([[x_0_c, y_0_c]], dtype=np.float))
            / np.array([[pixel_width, pixel_height]], dtype=np.float))
    return _swap_xy(wpts_index_array), data_set_geotransform


def index_to_coord(data_set_geotransform, waypoints_index_array):
    """Convert index waypoints to coordinate waypoints
    """

    pixel_width = data_set_geotransform[1]
    pixel_height = data_set_geotransform[5]

    x_0_c = data_set_geotransform[0] + (data_set_geotransform[1] / 2)
    y_0_c = data_set_geotransform[3] + (data_set_geotransform[5] / 2)

    waypoints_coords_array = (
        np.array(_swap_xy(waypoints_index_array), dtype=np.float)
        * np.array([[pixel_width, pixel_height]], dtype=np.float)
        + np.array([[x_0_c, y_0_c]], dtype=np.float))
    return waypoints_coords_array

def point_layer_from_coords_array(waypoints_coords_array, output_folder, 
                          crs, slope_label, points_height_data):
    """ Creating from points coordinates a points shapefile.
    """

    forest_road_points_mem_layer = QgsVectorLayer(
            'Point?crs={}'.format(crs.toWkt()),
            'road_points' , 'memory')

    provider = forest_road_points_mem_layer.dataProvider()
    for point in waypoints_coords_array:
        point_coord = QgsPoint(point[0], point[1])
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPoint(point_coord))
        provider.addFeatures([feature])
        forest_road_points_mem_layer.updateExtents()

    road_points_mask = 'forest_road_points_{}_num_{}.shp'
    key_for_glob = os.path.join(
            output_folder, 
            road_points_mask.format(slope_label, '*'))
    
    files_list = glob.glob(key_for_glob)
    points_file_name = road_points_mask.format(
            slope_label, len(files_list) + 1)

    points_out_path = os.path.join(output_folder, points_file_name)

    forest_road_points_writer = QgsVectorFileWriter.writeAsVectorFormat(
            forest_road_points_mem_layer,
            points_out_path,
            "UTF-8",
            crs,
            "ESRI Shapefile")
    del forest_road_points_writer
    forest_road_points = QgsVectorLayer(
            points_out_path, points_file_name , 'ogr')
    
    forest_road_points = layers_attributes.create_fields_for_points(
            forest_road_points,
            waypoints_coords_array,
            points_height_data)

    return forest_road_points

def line_layer_from_coords_array(
        waypoints_coords_array, output_folder, crs, slope_label, 
        lines_height_data, lines_section_slope, lines_projected_cum_dist):
    """ Creating from points coordinates lines shapefile
    """
    forest_road_lines_mem_layer = QgsVectorLayer(
            'LineString?crs={}'.format(crs.toWkt()),
            'forest_road' , "memory")

    provider = forest_road_lines_mem_layer.dataProvider()
    distances = []
    for point_0, point_1 in zip(waypoints_coords_array[:-1],
                                waypoints_coords_array[1:]):
        point_coord_0 = QgsPoint(*point_0)
        point_coord_1 = QgsPoint(*point_1)

        feature = QgsFeature()
        line_geom = QgsGeometry.fromPolyline([point_coord_0, point_coord_1])
        feature.setGeometry(line_geom)
        proj_dist = line_geom.length()
        distances.append(proj_dist)
        provider.addFeatures([feature])
        forest_road_lines_mem_layer.updateExtents()
    
    file_mask = 'forest_road_lines_{}_num_{}.shp'
    key_for_glob = os.path.join(
            output_folder, file_mask.format(slope_label, '*'))
    files_list = glob.glob(key_for_glob)
    lines_file_name = file_mask.format(slope_label, len(files_list) + 1)

    lines_out_path = os.path.join(output_folder, lines_file_name)
    writer_error = QgsVectorFileWriter.writeAsVectorFormat(
            forest_road_lines_mem_layer,
            lines_out_path,
            "UTF-8",
            crs,
            "ESRI Shapefile")
    
    forest_road_lines_mem_layer = None
    
    if writer_error != QgsVectorFileWriter.NoError:
        logger.error("Error escribiendo el fichero {} a disco".format(
                lines_out_path))
    
    forest_road_lines = QgsVectorLayer(lines_out_path, lines_file_name , 
                                       "ogr")

    forest_road_lines = layers_attributes.create_fields_for_lines(
            forest_road_lines,
            lines_height_data, 
            waypoints_coords_array,
            lines_section_slope,
            lines_projected_cum_dist,
            distances)
        
    return forest_road_lines
