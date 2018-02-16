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

from math import atan


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
                 penalty_factor_z):
        """A penalty_factor_xy of 1 equals a 1m distance penalisation for a 
            180º turn.
        A penalty_factor_z of 1 means a 1m distance penalisation for a 
        slope difference of pi/8 degrees.
        The penalty profile is parabolic (i.e. follows a deviation**2 law).
        """
        self._penalty_xy = penalty_factor_xy
        self._penalty_z = penalty_factor_z
        self._penalty_z_scaled = self._penalty_z/(np.pi/8)**2
        self._init_penalties(neighbors)
        self.neighbors = neighbors
        
    
    def _init_penalties(self, neighbors):
        """Precalculation of penalties for given list of neighbors."""
        angles = []
        for c_from, d_from, _, _ in zip(*neighbors):
            row = []
            for c_to, d_to, _, _ in zip(*neighbors):
                
                angle = np.arccos(min(max(
                    np.dot(c_from, c_to)/(np.linalg.norm(c_from)
                    * np.linalg.norm(c_to)),-1),1))
  
                row.append(angle)
            angles.append(row)
        self.neighbor_penalty = (
            self._penalty_xy * (np.array(angles)/np.pi) ** 2)
        
    def __call__(self, current,
                     idx_from,
                     idx_to,
                     slope_from,
                     slope_to):
        """Return the penalty for current point, when coming from idx_from
        and going to idx_to, with slopes of the from and to being given
        precalculated."""        
        if idx_from is not None and idx_to is not None:  
            return (self.neighbor_penalty[idx_from, idx_to]
                    + self._penalty_z_scaled
                        * (atan(slope_from)-atan(slope_to))**2)                    
        else:
            return 0

class ParabolicPenaltyStatic(ParabolicPenalty):
    def __init__(self,                  
                 static_penalty_map,
                 *args,
                 **kwargs):
        super(ParabolicPenaltyStatic, self).__init__(*args, **kwargs)
        self.static_penalty_map = static_penalty_map
    
    def __call__(self, *args):
        """print("value at point {}: {}".format(
                args[0], self.static_penalty_map[args[0]]))"""
        return ParabolicPenalty.__call__(self, *args) + \
                self.static_penalty_map[args[0]]