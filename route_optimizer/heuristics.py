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

from __future__ import unicode_literals
from __future__ import division
from scipy.ndimage import zoom
from math import sqrt
from distance_transform import constrained_distance_transform

import logging

class Distance(object):
    
    def __init__(self, max_dist=1e10):
        self.max_dist = max_dist
    
    def __call__(self, a, b, dist=None):
        """Shortest distance"""
        if dist is None:       
            return sqrt( (b[1]-a[1]) ** 2 + (b[0]-a[0]) ** 2 )
        else:
            return dist

class PrecalculatedOptimalDistanceSlopeConstrained(object):    
    def __init__(self, max_dist, dtm_array, max_slope, scale_m_per_pix, target_scale=None):
        
        self.max_dist = max_dist
        self.max_slope = max_slope
        self.scale_m_per_pix = scale_m_per_pix
        
        if target_scale is None:
            self.target_scale = min(256.0/max(dtm_array.shape), 1.0)
                        
        else:
            self.target_scale = target_scale
            
        self.scaled_size = [int(s*self.target_scale) 
                            for s in dtm_array.shape]
        
        self.dtm_array_scaled = zoom(dtm_array, 
                                       self.target_scale, 
                                       output=None, 
                                       order=3, 
                                       mode='constant', 
                                       cval=self.max_dist, 
                                       prefilter=True)
        
        self.original_size = dtm_array.shape

        self.target_point = None
        self.distance_transformed_dtm = None

    def point_scale(self, point):
        return (int(p*self.target_scale) for p in point)
    
    def retarget(self, point):
        """Precalculate the distance transform for given point."""
        self.target_point = point
        point_scaled = self.point_scale(point)
        logging.error("Recalculating for point {}".format(point))
    
        distance_transformed_dtm_scaled = constrained_distance_transform(
                    self.dtm_array_scaled, 
                    [point_scaled], 
                    self.max_slope, 
                    self.scale_m_per_pix/self.target_scale
                    )
                
        self.distance_transformed_dtm = zoom(distance_transformed_dtm_scaled, 
                                             1.0/self.target_scale, 
                                             output=None, 
                                             order=3, 
                                             mode='constant', 
                                             cval=self.max_dist, 
                                             prefilter=True)
        
    def __call__(self, a, b, dist=None):
        if b != self.target_point:
            self.retarget(b)        
        return self.distance_transformed_dtm[a]

class DistanceFakeSlope(object):
    
    def __init__(self, max_dist=1e10):
        self.max_dist = max_dist
    
    def __call__(self, a, b, dist=None):
        """Shortest distance"""
        if dist is None:       
            return sqrt( (b[1]-a[1]) ** 2 + (b[0]-a[0]) ** 2 ), 0
        else:
            return dist, 0

class DistanceSquared(object):
    
    def __init__(self, max_dist=1e10):
        self.max_dist = max_dist
    
    def __call__(self, a, b, dist=None):
        """Shortest distance squared"""
        if dist is None:
            return (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        else:
            return dist * dist

class DistanceSquaredFakeSlope(object):
    
    def __init__(self, max_dist=1e10):
        self.max_dist = max_dist
    
    def __call__(self, a, b, dist=None):
        """Shortest distance squared"""
        if dist is None:
            return (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2, 0
        else:
            return dist * dist, 0

"""Functor for heuristics (returns distance and slope"""

class DistanceSlopeMetric(object):

    def __init__(self, array, max_slope, max_dist):
        self.array = array
        self.max_slope = max_slope
        self.max_dist = max_dist       
        
    @staticmethod    
    def distance(a, b):
        
        return sqrt( (b[1]-a[1]) ** 2 + (b[0]-a[0]) ** 2 )
    
    def __call__(self, a, b, dist):
        """Distance between points a and b.
        max_slope is the max slope
        
        """
        local_slope = (self.array[b] - self.array[a]) / dist

        if abs(local_slope) < self.max_slope:

            return dist, local_slope
        else:
            dist += self.max_dist * (
                    1 + abs(abs(local_slope)-self.max_slope))
            return dist, local_slope

class DistanceMinMaxSlopeMetric(object):
    def __init__(self, array, max_slope, 
                 max_dist, min_slope=-1):
        """Give min_slope_corrected a value <=0 to disable min slope checking.
        """
        self.array = array
        self.min_slope = min_slope
        self.max_slope = max_slope
        self.max_dist = max_dist       
        
    @staticmethod    
    def distance(a, b):

        return sqrt( (b[1]-a[1]) ** 2 + (b[0]-a[0]) ** 2 )
    
    def __call__(self, a, b, dist):
        """Distance between points a and b.
        max_slope is the max slope
        
        """

        local_slope = (self.array[b] - self.array[a]) / dist

        if self.min_slope < abs(local_slope) < self.max_slope:  #NOQA            
            return dist, local_slope
        else:
            dist += self.max_dist + \
                    min(abs(abs(local_slope)-self.max_slope),
                        abs(abs(local_slope)-self.min_slope))
            return dist, local_slope