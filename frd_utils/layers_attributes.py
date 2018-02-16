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
from PyQt4.QtCore import QVariant
from qgis.core import QgsField
import numpy as np
import logging_qgis as logging
logger = logging.getLogger("frd")

def field_names(layer):
    """Auxiliary function to recover all the attribute names in a layer."""
    names = []
    for f in layer.dataProvider().getFeatures():
        for f_id, field in enumerate(f.fields()):
            names.append(field.name())
        break
    return names

def initialize_field(layer, field_name, values, check_field_input=False):
    """Create attribute with given field_name and given values.
    """
    layer.startEditing() 
    layer.dataProvider().addAttributes([QgsField(field_name, QVariant.Double)])
    layer.commitChanges()    

    layer.updateFields()
    layer.startEditing() 
    att_idx = layer.fieldNameIndex(field_name)    
    for row_idx, val in enumerate(values):
        v = {att_idx: float(val)}        
        layer.dataProvider().changeAttributeValues({row_idx: v})
        if check_field_input:
            for r, f in enumerate(layer.dataProvider().getFeatures()):
                if r == row_idx:
                    print("{} - {} - {} == {} ({})".format(
                            row_idx, att_idx, val, f[field_name], type(val)))
                    assert(np.allclose([f[field_name]], [val]))
    layer.commitChanges()
    layer.updateFields()
    
    
def create_fields_for_points(points_layer, waypoints_coords_array, 
                             height_data):
    """Create fields for points layer with geo information. Also writes the
    the info into the fields
    """
    new_fields = {}
    new_fields['x_coord'] = [p[0] for p in waypoints_coords_array]
    new_fields['y_coord'] = [p[1] for p in waypoints_coords_array]
    new_fields['z_coord'] = height_data
    
    for field_name, values in new_fields.iteritems():
        initialize_field(points_layer, field_name, values)   

    return points_layer
    
def create_fields_for_lines(layer,
                            height_data, 
                            waypoints_coords_array,
                            lines_section_slope, 
                            lines_projected_cum_dist,
                            distances_proj):
    """Create fields for LineString layer with geo and geometry info.
    Also writes the the information into the fields
    """
    new_fields = {}
    new_fields['start_x'] = [p[0] for p in waypoints_coords_array[:-1]]
    new_fields['arri_x'] = [p[0] for p in waypoints_coords_array[1:]]
    new_fields['start_y'] = [p[1] for p in waypoints_coords_array[:-1]]
    new_fields['arri_y'] = [p[1] for p in waypoints_coords_array[1:]]
    new_fields['start_z'] = height_data[:-1]   
    new_fields['arri_z'] = height_data[1:]
    new_fields['proj_d_m'] = distances_proj
    new_fields['cum_pr_m']= np.cumsum(distances_proj)
    new_fields['real_d_m'] = np.sqrt(
            (np.array(new_fields['arri_x']) 
             - np.array(new_fields['start_x'])) ** 2 +
            (np.array(new_fields['arri_y']) 
             - np.array(new_fields['start_y'])) ** 2 +
            (np.array(new_fields['arri_z']) 
             - np.array(new_fields['start_z'])) ** 2)
    new_fields['cum_re_m']= np.cumsum(np.array(new_fields['real_d_m']))
    new_fields['slope_p'] = [s*100 for s in lines_section_slope[1:]]
    new_fields['slope_d'] = [np.rad2deg(np.arctan(s)) 
                             for s in lines_section_slope[1:]]
    new_fields['z_var'] = np.diff(height_data)

    for field_name, values in new_fields.iteritems():
        initialize_field(layer, field_name, values)   

    return layer