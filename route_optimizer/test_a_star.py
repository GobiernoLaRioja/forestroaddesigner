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
import unittest
import numpy as np

import a_star
from polysimplify import polysimplify
import penalties
import heuristics

class AStarTestCase(unittest.TestCase):

    def _test_full_stack_no_penalty(self):
        """Test a multipoint optimization, with polysimplification."""
        nmap = np.zeros([200, 200])
        starting_point = (1, 0)
        intermediate = (20, int(nmap.shape[1] * 0.8))
        ending_point = (nmap.shape[0]-1, nmap.shape[1]-1)
    
        """Optimization"""
        
        semi_size = 5    
        neighbors = a_star.precalc_neighbourhood(semi_size)
        max_dist_index = 100 * np.sum(np.square(nmap.shape))
            
        heuristic = heuristics.DistanceSquaredFakeSlope(max_dist_index)
        tentative_heuristic = heuristics.DistanceSquared(max_dist_index)
        penalty = penalties.NoPenalty(neighbors)
    
        astar = a_star.AStarOptimizer(nmap, 5, 
                               heuristic,
                               tentative_heuristic,
                               penalty)
            
        waypoints = astar.astar([starting_point,intermediate, ending_point])
        
        path_simplifier = polysimplify.VWSimplifier(waypoints)    
        path_simplified = path_simplifier.from_threshold(0.01)
        self.assertGreater(len(path_simplified), 0)

    def test_parabolic_penalty(self):
        """Test a multipoint optimization, with polysimplification."""
        nmap = np.zeros([200, 200])
        starting_point = (7, 7)
        intermediate = (20, int(nmap.shape[1] * 0.8))
        ending_point = (nmap.shape[0]-10, nmap.shape[1]-10)
    
        """Optimization"""
        
        max_slope = 0.1
        semi_size = 5    
        neighbors = a_star.precalc_neighbourhood(semi_size)
        max_dist_index = 100 * np.sum(np.square(nmap.shape))
        penalty_factor_xy = 40
        penalty_factor_z = 0
    
        heuristic = heuristics.DistanceSlopeMetric(
                nmap,
                max_slope, 
                max_dist_index)
        tentative_heuristic = heuristics.Distance(max_dist_index)
        penalty = penalties.ParabolicPenalty(neighbors,
                               penalty_factor_xy,
                               penalty_factor_z)

    
        astar = a_star.AStarOptimizer(nmap, 5, 
                               heuristic,
                               tentative_heuristic,
                               penalty)
            
        waypoints = astar.astar([starting_point,intermediate, ending_point])
        
        self.assertGreater(len(waypoints), 0)
    
    def _test_parabolic_penalty_static(self):
        """Test a multipoint optimization, static conditioning."""
        nmap = np.zeros([200, 200])
        starting_point = (7, 7)
        intermediate = (20, int(nmap.shape[1] * 0.8))
        ending_point = (nmap.shape[0]-10, nmap.shape[1]-10)
    
        """Optimization"""
        
        max_slope = 0.1
        semi_size = 5    
        neighbors = a_star.precalc_neighbourhood(semi_size)
        max_dist_index = 100 * np.sum(np.square(nmap.shape))
        penalty_factor_xy = 40
        penalty_factor_z = 0
    
        heuristic = heuristics.DistanceSlopeMetric(
                nmap,
                max_slope, 
                max_dist_index)
        tentative_heuristic = heuristics.Distance(max_dist_index)
        static_map = np.zeros(nmap.shape)
        static_map[0:30,40:60] = 10000
        penalty = penalties.ParabolicPenaltyStatic(
                               static_map,
                               neighbors,
                               penalty_factor_xy,
                               penalty_factor_z)

        astar = a_star.AStarOptimizer(nmap, 5, 
                               heuristic,
                               tentative_heuristic,
                               penalty)
        
        waypoints = astar.astar([starting_point,intermediate, ending_point])
        # print(waypoints)
        self.assertGreater(len(waypoints), 0)
    
    def _test_full_stack_distance_transform_precalc_penalty(self):
        """Test a multipoint optimization, with polysimplification."""
        nmap = np.zeros([100, 100])
        starting_point = (7, 7)
        intermediate = (20, int(nmap.shape[1] * 0.8))
        ending_point = (nmap.shape[0]-10, nmap.shape[1]-10)
    
        """Optimization"""
        
        max_slope = 0.1
        semi_size = 5    
        neighbors = a_star.precalc_neighbourhood(semi_size)
        max_dist_index = 100 * np.sum(np.square(nmap.shape))
        penalty_factor_xy = 40
        penalty_factor_z = 0
        scale_m_per_pix = 5
        
        heuristic = heuristics.DistanceSlopeMetric(
                nmap,
                max_slope, 
                max_dist_index)
        tentative_heuristic = \
            heuristics.PrecalculatedOptimalDistanceSlopeConstrained(
                max_dist_index, 
                nmap, 
                max_slope, 
                scale_m_per_pix, 
                target_scale=1)
        penalty = penalties.ParabolicPenalty(neighbors,
                               penalty_factor_xy,
                               penalty_factor_z)

        astar = a_star.AStarOptimizer(nmap, scale_m_per_pix, 
                               heuristic,
                               tentative_heuristic,
                               penalty)
            
        waypoints = astar.astar([starting_point,intermediate, ending_point])
        
        path_simplifier = polysimplify.VWSimplifier(waypoints) 
        path_simplified = path_simplifier.from_threshold(0.01)
        self.assertGreater(len(path_simplified), 0)
        
if __name__ == "__main__":
    unittest.main()