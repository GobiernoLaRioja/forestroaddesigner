# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 09:43:15 2017

@author: Javier
"""
"""Penalty functors for AStar optimizer.
This classes implement dynamic (i.e. path dependent) and static (i.e.
pixel dependent) penalization factors for a given route.

NoPenalty always returns 0 (i.e. no penalties at all)

ExclusionPenalty returns 0 (i.e. no penalties at all)

ParabolicPenalty implements dynamic penalization in the xy and z planes,
and allows static penalization too. The penalization profile is parabolic.
"""
import numpy as np

from math import atan, floor, sqrt
import logging
import datetime


# TODO: remove after review
# from pathlib import Path
# today = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
# base_dir = Path(r'\logs')
# base_dir.mkdir(exist_ok=True)
# filenamelog = base_dir/ f'test_penalties_{today}.log'
# logging.basicConfig(filename=filenamelog, filemode='w', level=logging.DEBUG)

def init_penalties(self, neighbors):
        """Precalculation of penalties for given list of neighbors."""
        angles = []
        radii = []
        for c_from, d_from, _, _ in zip(*neighbors):
            row = []
            if self._min_curve_radius is not None:
                row_rad = []
            for c_to, d_to, _, _ in zip(*neighbors):
                
                angle = np.arccos(min(max(
                    np.dot(c_from, c_to)/(np.linalg.norm(c_from)
                    * np.linalg.norm(c_to)),-1),1))
  
                row.append(angle)
                if self._min_curve_radius is not None:
                    rad_pen = (self._min_curve_radius -1 /  (np.tan(angle / 2))) if (angle != 0 and 1 / (np.tan(angle / 2)) < self._min_curve_radius) else 0
                    row_rad.append(rad_pen)
            angles.append(row)
            if self._min_curve_radius is not None:
                radii.append(row_rad)
        self.neighbor_penalty = (self._penalty_xy * (np.array(angles)/np.pi) ** 2)
        if self._min_curve_radius is not None:
            print(self._min_curve_radius, self._penalty_radius)
            self.neighbor_radius_penalty_xy = self._penalty_radius * (np.array(radii)**2)
        else:
            self.neighbor_radius_penalty_xy = None

class NoPenalty(object):

    def __init__(self, neighbors):
        """A penalty factor of 1 equals a 1m distance penalisation for a 
            180º turn.
            
            """
        self.neighbors = neighbors
      
    def __call__(self, *args):
        return 0


class ParabolicPenalty(object):
    """Dynamic penalty, changes in every point, according to current path.

    This function allows penalization on curves (penalty_factor_xy)
    and on slope changes (penalty_factor_z).
    """    
    def __init__(self, 
                 neighbors, 
                 penalty_factor_xy, 
                 penalty_factor_z,
                 min_curve_radius_px,  # Optional for min curvature radius
                 penalty_radius):      # Optional for min curvature radius
        """A penalty_factor_xy of 1 equals a 1m distance penalisation for a 
            180º turn.
        A penalty_factor_z of 1 means a 1m distance penalisation for a 
        slope difference of pi/8 degrees.
        The penalty profile is parabolic (i.e. follows a deviation**2 law).
        """
        self._penalty_xy = penalty_factor_xy
        self._penalty_z = penalty_factor_z
        self._penalty_z_scaled = self._penalty_z/(np.pi/8)**2
        

        self._min_curve_radius = min_curve_radius_px
        self._penalty_radius = penalty_radius

        init_penalties(self, neighbors)
        self.neighbors = neighbors       
    
        
    def __call__(self, current,
                     idx_from,
                     idx_to,
                     slope_from,
                     slope_to):
        """Return the penalty for current point, when coming from idx_from
        and going to idx_to, with slopes of the from and to being given
        precalculated."""        
        if idx_from is not None and idx_to is not None:
            penal_neig = self.neighbor_penalty[idx_from, idx_to]
            penal_z = self._penalty_z_scaled * (atan(slope_from)-atan(slope_to))**2            
            penalt = penal_neig + penal_z

            if self._min_curve_radius is not None:
                penal_rad = self.neighbor_radius_penalty_xy[idx_from, idx_to]
                penalt += penal_rad

            return penalt
        else:
            """Starting point has idx_from: None, no """
            return 0


class ParabolicPenaltyCutFill(object):
    """Dynamic penalty, changes in every point, according to current path.

    This function allows penalization on curves (penalty_factor_xy)
    and on slope changes (penalty_factor_z).
    """    
    def __init__(self,neighbors,
                penalty_factor_xy, 
                penalty_factor_z,
                min_curve_radius_px,
                penalty_radius,
                penalty_cutfill,
                array,
                cut_hmax,
                fill_hmax,
                cut_angle,
                fill_angle,
                w_road,
                orto_points):
        self._penalty_xy = penalty_factor_xy
        self._penalty_z = penalty_factor_z
        self._penalty_z_scaled = self._penalty_z/(np.pi/8)**2        
        self._min_curve_radius = min_curve_radius_px
        self._penalty_radius = penalty_radius
        self._penalty_cutfill = penalty_cutfill
        self.neighbors = neighbors
        self.orto_points = orto_points       

        self.array = array
        self.cut_hmax = cut_hmax
        self.fill_hmax = fill_hmax 
        self.cut_angle = cut_angle
        self.fill_angle = fill_angle
        self.w_road = w_road

        # distance to consider to make the grid
        self.dist_cut = self.cut_hmax/float(self.cut_angle)
        self.dist_fill = self.fill_hmax/float(self.fill_angle)
        self.road_dist_max = self.w_road/2.0 + max(self.dist_cut, self.dist_fill)
        init_penalties(self,neighbors)


    def _cutfill_penalty_idx_to(self, current, idx_to):
        pen = 0
        orto_list = self.orto_points[idx_to]
        pen_orto_list = [] 
        for orto in orto_list:
            orto_real = orto + current
            pen_orto= 0
            if (0 <= orto_real[0] < self.array.shape[0]
                and 0<= orto_real[1] < self.array.shape[1] ):
                h_orto_cut = self.cut_angle*(abs(np.linalg.norm(orto) - self.w_road/2))
                h_orto_fill = self.fill_angle*(abs(np.linalg.norm(orto) - self.w_road/2))
                hmax = min(self.cut_hmax, h_orto_cut)
                hmin = min(self.fill_hmax, h_orto_fill)
                h_dif = self.array[orto_real[0],orto_real[1]] - self.array[current[0],current[1]]
                if (0 <= h_dif < hmax or 0 >= h_dif > -hmin ): 
                    pass
                else:
                    pen_max = self._penalty_cutfill * abs(1 - h_dif/hmax)**2 if h_dif > 0 else 0
                    pen_min = self._penalty_cutfill * abs(1 - abs(h_dif/hmin))**2 if h_dif < 0 else 0
                    pen_orto = max(pen_max, pen_min)
            else:
                pen_orto = self._penalty_cutfill ** 2
            
            pen_orto_list.append(pen_orto)
        pen = max(pen_orto_list)
        return pen 
    

    def __call__(self, current,
                     idx_from,
                     idx_to,
                     slope_from,
                     slope_to):
        """Return the penalty for current point, when coming from idx_from
        and going to idx_to, with slopes of the from and to being given
        precalculated."""
              
        if idx_from is not None and idx_to is not None:
            penal_neig = self.neighbor_penalty[idx_from, idx_to]
            penal_z = self._penalty_z_scaled * (atan(slope_from)-atan(slope_to))**2            
            penalt = penal_neig + penal_z

            if self._min_curve_radius is not None:
                penal_rad = self.neighbor_radius_penalty_xy[idx_from, idx_to]
                penalt += penal_rad

            penal_cut_fill = self._cutfill_penalty_idx_to( current, idx_to)
            penalt += penal_cut_fill
            return penalt 
        else:
            """Starting point has idx_from: None, no """
            return 0

import types
def WithStaticPenalty(static_penalty_map, dynamic_penalty):
    __call__dyn = dynamic_penalty.__call__

    def __call__with_static(self, *args):
        """print("value at point {}: {}".format(
                            args[0], self.static_penalty_map[args[0]]))"""

        static_pen = static_penalty_map[args[0]]
        dyn_pen = __call__dyn(self, *args)
        print('static call')
        return static_pen + dyn_pen
    dynamic_penalty.__call__ = types.MethodType( __call__with_static, dynamic_penalty)
    
    return dynamic_penalty

class PenaltyStatic:
    """This class adds a static penalty map to an existing dynamic penalty.

        Usage:
            dynamic = ParabolicPenalty(...)
            dynamic_with_static = PenaltyStatic(exclusion_zone, dynamic)
    
    """
    def __init__(self,
                 static_penalty_map,
                 dynamic_penalty):
        vars(self).update(vars(dynamic_penalty))    
        
        self.static_penalty_map = static_penalty_map
        self.dynamic_penalty = dynamic_penalty

    def __call__(self, *args):
        """print("value at point {}: {}".format(
                            args[0], self.static_penalty_map[args[0]]))"""

        static_pen = self.static_penalty_map[args[0]]
        dyn_pen = self.dynamic_penalty(*args)
        return static_pen + dyn_pen    
