# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ForestRoadDesignerDockWidget
                                 A QGIS plugin
 This plugin serve as support of foresters in the design of forest roads
                     -------------------
        begin          : 2017-02-08
        git sha        : $Format:%H$
        copyright      : (C) 2017 by PANOimagen S.L.
        email          : info@panoimagen.com
        repository     : https://github.com/GobiernoLaRioja/forestroaddesigner
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software: you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation, either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       * 
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program.  If not, see <https://www.gnu.org/licenses/> *
 ***************************************************************************/

This module creates a new raster with the exclusion areas using Gdal Rasterize 
algorithm and returns the numpy array for this new raster.
"""
from __future__ import unicode_literals
from osgeo import gdal
from osgeo import ogr
from osgeo import gdalconst
from qgis.core import QGis
import tempfile
import os

def create_exclusion_array(dtm_layer, exclusion_areas_layer, 
                           output_fn = None):
    """Create a numpy array with the content of the exclusion areas 
    layer rasterized and the extent of the dtm_layer input
        No data value of new raster = 0
        Exclusion areas value of new raster = 1
    """
    if exclusion_areas_layer is None:
        return None
    
    if output_fn is None:
        f, output_fn = tempfile.mkstemp(prefix="frd_", suffix=".tif")
        os.close(f)
        delete_output = True
    else:
        delete_output = False
    
    target_ds = create_empty_raster_dataset(output_fn, dtm_layer)
    target_ds = rasterize_function(target_ds, exclusion_areas_layer)
    
    exclusion_areas_array = target_ds.GetRasterBand(1).ReadAsArray()
    
    if delete_output:
        del target_ds
        os.remove(output_fn)
        
    return exclusion_areas_array

def create_exclusion_raster(dtm_layer, exclusion_areas_layer,
                                output_fn = 'exclusion_raster.tif',
                                nodata_value = 0,
                                data_value = 1
                                ):
    """Create a raster with the exclusion areas and the dtm_layer input 
        extent. 
        No data value of new raster = NoDataValue (default 0). 
        Exclusion areas value of new raster = data_value (default 1).
    """
        
    target_ds = create_empty_raster_dataset(
                    output_fn, dtm_layer, nodata_value)
    target_ds = rasterize_function(
                    target_ds, exclusion_areas_layer, data_value)
    target_ds = None
    
    return output_fn

def create_empty_raster_dataset(output_fn, dtm_layer, NoDataValue=0):
    """Creates an empty geotiff with same size as dtm_layer.
    Creates an empty geotiff on disk with same extent and resolution
    as the dtm_layer"""

    (x_min, pixel_width, _, y_min, _, pixel_height, x_res, 
            y_res) = get_DTM_info(dtm_layer)
    
    target_ds = gdal.GetDriverByName(str('GTiff')).Create(
            output_fn, x_res, y_res, 1, gdalconst.GDT_Float64)
    target_ds.SetGeoTransform((
            x_min, pixel_width, 0, y_min, 0, -pixel_height))
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(NoDataValue)
    band.FlushCache()
    
    return target_ds
    
def get_DTM_info(dtm_layer):
    """Function to extract the extent and resolution of a raster layer.
    """

    dtm_layer_data = gdal.Open(dtm_layer.source(), gdalconst.GA_ReadOnly)
    dtm_geotransform = dtm_layer_data.GetGeoTransform()
    x_min = dtm_geotransform[0]
    y_max = dtm_geotransform[3]
    y_min = y_max + dtm_geotransform[5] * dtm_layer_data.RasterYSize
    x_res = dtm_layer_data.RasterXSize
    y_res = dtm_layer_data.RasterYSize
    pixel_width = dtm_geotransform[1]
    pixel_height = dtm_geotransform[5]
    
    return (x_min, pixel_width, 0.0, y_min, 0.0, pixel_height, x_res, y_res)

def rasterize_function(target_ds, exclusion_areas_layer, data_value=1):
    """ Function to rasterize the exclusion_areas_layer vectorLayer.
    The rasterized content is stored in band 1 of target_ds, which is the
    dataset of a raster layer.
    """ 

    mb_v = ogr.Open(exclusion_areas_layer.source())
    mb_l = mb_v.GetLayer()
    
    exclusion_area_value = [data_value]
    exclusion_area_band = [1]
    rasterize_option = ['ALL_TOUCHED=TRUE']
    
    gdal.RasterizeLayer(
            target_ds, 
            exclusion_area_band, 
            mb_l, 
            None, 
            None, 
            exclusion_area_value,
            rasterize_option)
    
    return target_ds

def exclusion_areas_geoms(exclusion_areas_layer):
    """ Extracts the wkb geometry of each feature in exclusion_areas_layer.
    (These geometries are later used to check that waypoints given 
    by the user are outside the exclusion zones in optimizer_qgis.py)
    """
    exclusion_areas_wkb = []
    features = exclusion_areas_layer.dataProvider().getFeatures()
    for feat in features:
        geom = feat.geometry()
        if geom.wkbType() == QGis.WKBPolygon:
            exclusion_areas_wkb.append(geom.asWkb())
        elif geom.wkbType() == QGis.WKBMultiPolygon:
            raise NotImplementedError(
            "Las capas de exclusión de tipo multipolígono " + 
            "no están soportadas.")
    return exclusion_areas_wkb