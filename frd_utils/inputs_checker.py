# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ForestRoadDesigner
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
"""

from __future__ import unicode_literals

from osgeo import gdal
from qgis.core import QGis, QgsGeometry, QgsPoint
                      
import numpy as np
import exclusion_areas_fn
from array_funs import waypoints_list

def check_layers(dtm_layer, waypoints_layer, exclusion_areas_layer = None):
    """Check if waypoints, dtm and exclusion_areas_layer's contents are ok
    
    Check that waypoints_layer is a line layer with at least one line.
    Check that exclusion_areas_layer is a Polygon layer with at least one 
    polygon feature.
    Check that the pixel's are square (for dtm_layer).
    Check that dtm_layer, waypoints_layer adn exclusion layer share the same 
    CRS.
    """
        
    if waypoints_layer is not None:
        if waypoints_layer.isEditable() == True:
            message = ('La capa que contiene los puntos de paso (waypoints)' + 
                       ' está en modo de edición. \nPor favor cierre el' +
                       ' modo de edición de la capa y relance el proceso.')
            return False, message
            
        if not waypoints_layer.isValid():
            message = ("La capa que contiene los puntos de" +
                       " paso (waypoints), no es válida.\nPor favor," +
                       " solucionelo y relance el proceso.")
            return False, message
       
        elif not check_layer_type(waypoints_layer):
            message = ("La capa seleccionada como entrada para los puntos de" +
                       " paso no es de tipo linea.\nSolo se admiten geometrías" + 
                       " tipo WKBLineString y WKBMultiLineString.\nPor favor," +
                       " solucionelo y relance el proceso.")
            return False, message
            
        try:
            waypoints_list(waypoints_layer)
        except AttributeError:
            message = ('La capa que contiene los puntos de paso (waypoints)' +
                       ' no es válida.\nPor favor, compruebe su geometría y' +
                       ' relance el proceso.')
            return False, message

        if (waypoints_layer.wkbType() == QGis.WKBLineString
               and waypoints_layer.dataProvider().featureCount() <= 0):
            message = (
                   "Error: ¡No hay suficientes puntos para realizar la" +
                   " optimización!.\n" +
                   "Pruebe a seleccionar una capa con dos o más puntos de" + 
                   " paso o cierre la edición de la capa actual y relance" + 
                   " el proceso.")
    
            return False, message
    
        elif not check_feature_count(waypoints_layer):
            message = ("Forest Road Designer no admite como archivo de" +
                   " entrada para los puntos de paso (waypoints) capas con" +
                   " más de un elemento (feature). Por favor, seleccione un" +
                   " archivo con solo un elemento (feature) y relance el" + 
                   " proceso.")
            return False, message
            
    if exclusion_areas_layer is not None:
        if exclusion_areas_layer.isEditable() == True:
            message = ('La capa que contiene las zonas a excluir del trazado' + 
                       ' está en modo de edición. \nPor favor cierre el' +
                       ' modo de edición de la capa y relance el proceso.')
            return False, message
            
        if not exclusion_areas_layer.isValid():
            message = ("La capa que incluye las areas de exclusión no es" +
                       " válida.\nPor favor, solucionelo y relance el" +
                       " proceso.")
            return False, message
        
        from osgeo import ogr
        mb_v = ogr.Open(exclusion_areas_layer.source())
        try:     
            mb_v.GetLayer()
        except AttributeError:
            message = ("El proceso requiere que la capa con las areas de" + 
                       " exclusión para el trazado esté almacenada en disco" +
                       ", no se admiten capas en memoria.\nPor favor," + 
                       " soluciónelo y relance el proceso.")
            return False, message
        
        try:
            if waypoints_layer is not None:
                if not check_waypoints_not_excluded(waypoints_layer, 
                                          exclusion_areas_layer):
                    
                    message = (
                            "Existe al menos un punto de paso contenido en la" 
                            + " zona de exclusión. " + 
                            "Reviselo y relance el proceso")
                    return False, message
        except AttributeError:
            message = ('La capa que contiene las areas de exclusión' +
                   ' no es válida.\nPor favor, compruebe su geometría y' +
                   ' relance el proceso.')
            return False, message
        
        if not (exclusion_areas_layer.featureCount() >= 1):
            message = ("La capa que incluye las areas de exclusión no posee" +
                       " ninguna entidad (feature).\nPor favor, compruebelo" +
                       " y relance el proceso.")
            return False, message
        
        elif not (exclusion_areas_layer.wkbType() == QGis.WKBPolygon): 
            message = ("La capa  con las zonas de exclusión debe ser de" +
                       " tipo polígono.\nPor favor, solucionelo y relance" + 
                       " el proceso.")
            return False, message

    
    elif not dtm_layer.isValid():
        message = ("Hay un problema con el Modelo Digital del Terreno," +
                   " no es válido.\nPor favor solucionelo y relance el" +
                   " proceso.")
        return False, message
    
    raster = gdal.Open(dtm_layer.source())
    try:
        
        raster.GetGeoTransform()
    except AttributeError:
        message = ('Error: La capa seleccionada como Modelo Digital del' + 
                  ' Terreno no es compatible.\nPor favor asegurese de' + 
                  ' que ha seleccionado la capa correcta y relance el' +
                  ' proceso.')
        return False, message
        

    if not check_pixel_size(dtm_layer):
        message = ("El ancho y alto de pixel del modelo digital del terreno" + 
                " difiere en más del 5 %, por favor seleccione un DTM con " + 
                " menor diferencia entre ancho y alto de pixel y relance" +
                " el proceso.")
        return False, message
        
    elif not check_crs(dtm_layer, waypoints_layer, exclusion_areas_layer):
        message = ("Los ficheros de entrada tienen distintos sistemas" +
                "de referencia (CRS), esto puede producir resultados" +
                " inesperados. Establezca los sistemas de referencia" +
                " de las capas y relance el proceso.")
        return False, message
        
    elif not check_bounds(dtm_layer, waypoints_layer):
        message = ("Los puntos dados exceden la extensión del DTM, por" + 
                " favor solucionelo y relance el proceso")
        return False, message
    
    return True, ""


def check_layer_type(waypoints_layer):
    """Check that waypoint layer is LineString
    """
    if waypoints_layer.wkbType() in (QGis.WKBLineString, 
                                       QGis.WKBMultiLineString):
        return True
    else:
        return False

def check_feature_count(waypoints_layer):
    """Check if the input vector layer has only one feature
    """
    return waypoints_layer.featureCount() == 1


def check_crs(dtm_layer, waypoints_layer, exclusion_areas_layer=None):
    """Check input files CRS. If them are not the same launch message.
    """
    if not exclusion_areas_layer is None:
        if waypoints_layer is None:
            return (dtm_layer.crs().authid() == 
                    exclusion_areas_layer.crs().authid())
        return (dtm_layer.crs().authid() == waypoints_layer.crs().authid() 
                == exclusion_areas_layer.crs().authid())
    else:
        return (waypoints_layer is None or 
                dtm_layer.crs().authid() == waypoints_layer.crs().authid())

def check_bounds(dtm_layer, waypoints_layer):
    """Check if the input waypoints layer is contained in the input DTM.
    """
    return (waypoints_layer is None or 
            dtm_layer.extent().contains(waypoints_layer.extent()))

def check_waypoints_not_excluded(waypoints_layer,
                                 exclusion_areas_layer = None):
    """Check if the input waypoints are contained in the exclusion areas.
    Check user mistake
    """
    if exclusion_areas_layer is None:
        return True
    else:
        polygon_wkb = exclusion_areas_fn.exclusion_areas_geoms(
                exclusion_areas_layer)
        
        waypoints_coords_list = waypoints_list(waypoints_layer)
        
        included_points = []
        for geom_ent in polygon_wkb:
            exclusion_geom = QgsGeometry()
            exclusion_geom.fromWkb(geom_ent)
            for point in waypoints_coords_list:
                point_coord = QgsPoint(point[0], point[1])
                if exclusion_geom.contains(point_coord):
                    included_points.append(point_coord)
        
        return included_points == []

def check_pixel_size(dtm_layer):
    """ Extract the pixel information of the DTM layer pixel size
    """
    dtm_layer_path = dtm_layer.source()
    raster = gdal.Open(dtm_layer_path) # is necesary a dtm raster file saved in disk
    geotransform = raster.GetGeoTransform()
    pixel_size = []
    pixel_size.append([geotransform[1], geotransform[5]])
    return np.isclose(abs(geotransform[1]), abs(geotransform[5]), rtol = 0.05)
