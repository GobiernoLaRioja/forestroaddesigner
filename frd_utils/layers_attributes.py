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
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsField
import numpy as np
from collections import OrderedDict
#from . import logging_qgis as logging
import logging
logger = logging.getLogger("frd")

def field_names(layer):
    """Auxiliary function to recover all the attribute names in a layer."""
    names = []
    for f in layer.dataProvider().getFeatures():
        for f_id, field in enumerate(f.fields()):
            names.append(field.name())
        break
    return names

def initialize_field(layer, field_name, values, variant, check_field_input=False):
    """Create attribute with given field_name and given values.
    """
    layer.startEditing()
    if variant == "int":
        layer.dataProvider().addAttributes([QgsField(field_name, QVariant.Int)])
    if variant == "double":
        layer.dataProvider().addAttributes([QgsField(field_name, QVariant.Double,'',20,3)])
    if variant == "str":
        layer.dataProvider().addAttributes([QgsField(field_name, QVariant.String)]) 
    
    layer.commitChanges()

    layer.updateFields()
    layer.startEditing()
    att_idx = layer.dataProvider().fieldNameIndex(field_name)

    for row_idx, val in enumerate(values):
        v = {att_idx: float(val)}
        layer.dataProvider().changeAttributeValues({row_idx: v})
        if check_field_input:
            for r, f in enumerate(layer.dataProvider().getFeatures()):
                if r == row_idx:
                    print(("{} - {} - {} == {} ({})".format(
                            row_idx, att_idx, val, f[field_name], type(val))))
                    assert(np.allclose([f[field_name]], [val]))

    layer.commitChanges()
    layer.updateFields()

def delete_field(layer, field_name_list):
    layer.startEditing()
    layer.dataProvider().deleteAttributes(field_name_list)
    layer.commitChanges()
    layer.updateFields()

def create_fields_for_points(points_layer, waypoints_coords_array,
                             height_data):

    new_fields = OrderedDict()
    new_fields['x_coord'] = [p[0] for p in waypoints_coords_array]
    new_fields['y_coord'] = [p[1] for p in waypoints_coords_array]
    new_fields['z_coord'] = height_data

    for field_name, values in new_fields.items():
        initialize_field(points_layer, field_name, values)

    return points_layer

def create_fields_for_lines(layer,
                            height_data,
                            waypoints_coords_array,
                            lines_section_slope,
                            lines_projected_cum_dist,
                            distances_proj,
                            radius_data,
                            height_cutfill,
                            cutfill_data,
                            cutfill_pen_data,
                            penalties_slope_rad,
                            turn_number_list):

    turn_number = [tn[1] for tn in turn_number_list]
    rad_avg = [ra[2] for ra in turn_number_list]
    new_fields = OrderedDict()
    new_fields_extra = OrderedDict()

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
    new_fields['radius_m'] = radius_data
    new_fields['h_cutfill'] = height_cutfill
    new_fields['cut_fill'] = cutfill_data
    new_fields['cutfill_p']= cutfill_pen_data
    new_fields['penalty'] = penalties_slope_rad
    
    new_fields['radius_avg'] = rad_avg
    new_fields_extra['turn_num'] = turn_number

    for field_name, values in new_fields.items():
        if values is not None:
            initialize_field(layer, field_name, values, "double")
    
    for field_name, values in new_fields_extra.items():
        if values is not None:
            initialize_field(layer, field_name, values, "int")

    return layer

def interactive_create_fields_for_lines(layer,
                            height_data,
                            waypoints_coords_array,
                            lines_section_slope,
                            lines_projected_cum_dist,
                            distances_proj,
                            turn_number_list
                            ):

    turn_number = [tn[1] for tn in turn_number_list]
    rad_avg = [ra[2] for ra in turn_number_list]
    new_fields = OrderedDict()
    new_fields_extra = OrderedDict()

    new_fields['start_x'] = [p[0] for p in waypoints_coords_array[:-1]]
    new_fields['arri_x'] = [p[0] for p in waypoints_coords_array[1:]]
    new_fields['start_y'] = [p[1] for p in waypoints_coords_array[:-1]]
    new_fields['arri_y'] = [p[1] for p in waypoints_coords_array[1:]]
    # new_fields['start_z'] = height_data[:-1]
    # new_fields['arri_z'] = height_data[1:]    
    new_fields['start_z'] = [h[0] for h in height_data[:-1]]
    new_fields['arri_z'] = [h[0] for h in height_data[1:]]
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
    new_fields['z_var'] = [(h1-h0) for h0, h1 in
               zip(height_data[:-1], height_data[1:]) ]
    # new_fields['z_var'] = np.diff(height_data)
    
    new_fields_extra['turn_num'] = turn_number

    for field_name, values in new_fields.items():
        print(f"field_name {field_name}")
        if values is not None:
            initialize_field(layer, field_name, values, "double")
    
    for field_name, values in new_fields_extra.items():
        if values is not None:
            initialize_field(layer, field_name, values, "int")

    return layer

