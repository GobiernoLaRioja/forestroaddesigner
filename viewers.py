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
import numpy as np
import frd_utils.logging_qgis as logging
logger = logging.getLogger("frd")

def remove_undef(dtm_m, dtm_no_data_value):
    """Remove undef values from lidar dtms (usually -XXXXX height value)."""
    try:
        min_val = np.min(dtm_m[dtm_m > dtm_no_data_value])
    except ValueError:
        min_val = 0
    dtm_m[dtm_m <= dtm_no_data_value] = min_val
    return dtm_m

def slope_pct_to_rad(slope_pct):
    """Transform a slope in percentage (delta y/delta x) to radians
    
    The returned value expresses the angle between the line 
    going from (0,0) to (delta_x, delta_y) and the horizontal
    in radians.
    """
    return np.arctan(slope_pct)

def height_profile(dtm_m, waypoints, max_slope, scale_m_per_pix):
    """Extracts geometry parameters for designed road as slope, heigth and 
        element length
    """
    # force int type as they will be used as indices to dtm_m
    waypoints = np.array(waypoints, dtype=np.int)
    
    height_prof = [dtm_m[y,x] for y, x in waypoints]
    dist_xy = [scale_m_per_pix*np.linalg.norm(p1-p0) for p0, p1 in
               zip(waypoints[:-1], waypoints[1:]) ]
    slope = np.diff(height_prof)/dist_xy
    dist_xy = np.hstack((0, dist_xy))
    slope = np.hstack((0, slope))
    
    cumdist_xy = np.cumsum(dist_xy)

    return height_prof, slope, cumdist_xy