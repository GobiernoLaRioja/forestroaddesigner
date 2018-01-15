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
A-star code based on initial class from Christian Careaga 
(christian.careaga7@gmail.com)
A* Pathfinding in Python (2.7)

Modified by PANOimagen for its use on ForestRoadDesigner QGis plugin.
"""
from __future__ import division

import logging

import numpy as np
import heapq
import heuristics
import datetime
import penalties

logger = logging.getLogger('frd')

def precalc_neighbourhood(semi_size=1, remove_repeated_angles=True):

    x, y = np.meshgrid(np.arange(-semi_size, semi_size+1, dtype=np.int), 
                      np.arange(-semi_size, semi_size+1, dtype=np.int))
    coords = np.vstack((np.ndarray.flatten(x), np.ndarray.flatten(y))).T
    # Remove central element.
    coords = np.delete(coords, [semi_size*(2*semi_size+2)],axis=0)
    angles = np.degrees(np.arctan2(coords[:,0], coords[:,1]))
    dists_index = np.sqrt(np.sum(np.square(coords),axis=1))
    
    if remove_repeated_angles:            
        alpha = None
        non_repeated = []
        for neighbor in sorted(zip(angles, dists_index, coords)):
            if neighbor[0] != alpha:
                alpha = neighbor[0]
                non_repeated.append(neighbor[2])
        non_repeated = np.array(non_repeated, dtype=np.int)
        angles = np.degrees(np.arctan2(non_repeated[:,0], non_repeated[:,1]))
        dists_index = np.sqrt(np.sum(np.square(non_repeated),axis=1))
        return non_repeated, dists_index, angles, range(len(angles))
    else:
        
        return coords, dists_index, angles, range(len(dists_index))

class CouldNotFindAWay(BaseException):
    pass

class AStarOptimizer(object):
    """
    Distance between one point and the next step is precalculated at the
    neighbours structure, which is containted in penalty.
    penalty, in addition to the neighbors structure, can be called to retrieve
    the dynamic penalty incurred when going from current pixel to the next
    neighbour. This can be dependent on slope change, direction change, etc.    
    """

    STRICT_MODE = 0  # Respects constraints thouroughly, a 
                     # proper solution might not exists
    LOOSE_MODE = 1  # May find some segments which are non complying but will
                    # always find a solution
                    
    
    def __init__(self, dtm, dtm_resolution_m_per_pix,                 
                 heuristic=None,
                 tentative_heuristic=None,
                 penalty=None
                 ):
        """dtm represents height (in meters) of given terrain.
        
        max_slope is the maximum allowed slope. if None (default value)
                 then slope is not taken into account on the calculation.
                 The value of max_slope will be scaled according to the dtm 
                 resolution (in m/pix)
                 (i.e for a raster with 2m/pix resolution, the corrected
                 max_slope for a specified slope of 10% will be 
                     0.10m/m*2m/pix = 0.20m/pix)
        
        """
        #  Vars with suffix _index are in image coordinates.
        # Vars with suffix _corrected are in m coordinates (aka real world 
        # meters, with origin (0,0) on top left corner of the image).
        
        # array contains the dtm scaled by resolution, so that slopes
        # are calculated properly (using indices for the x and y axes 
        # equal to work with the axis scaled by dtm_resolution_m_per_pix)
        
        # Array values are scaled so that the slopes remain constant in pixels
        
        self.array = dtm/dtm_resolution_m_per_pix
        
        self.heuristic_mode = self.LOOSE_MODE
        self.heuristic = heuristic
        self.tentative_heuristic = tentative_heuristic
        self.penalty = penalty
        
        self.array_resolution_m_per_pix = dtm_resolution_m_per_pix        
        self._waypoints_index = []  # Allows increasing the waypoints list gradually
                            # via calls to add_point
        # Required for interactive
        self._number_of_segments = 1
        self.reset()
        self.progress_callback = lambda p: p
            
    def waypoints_index(self):
        return [point 
                for segment in self._waypoints_index 
                for point in segment]

    def astar(self, points):
        assert(self.heuristic is not None)
        assert(self.tentative_heuristic is not None)
        assert(self.penalty is not None)
        self._waypoints_index = []
        self._number_of_segments = len(points) - 1
        for goal in points:  
            self.add_segment_to(goal)
        return self.waypoints_index()
    
    def send_progress(self, progress_in_current_segment_pct):
        
        if self._number_of_segments > 1:
            total_progress = (
                progress_in_current_segment_pct / self._number_of_segments
                + (self._segment_id-1)*100.0/self._number_of_segments)
        else:
            total_progress = progress_in_current_segment_pct

        self.progress_callback(total_progress)
        
        
    def add_segment_to(self, goal, max_dist=None, iterative=False, 
                       force=False):
        """Adds a new segment to go from last point to goal.
        
        If max_dist is specified, we approach to goal using a segment of 
        that aproximate length (in fact, the first segment reached with 
        length greater than max_dist is taken, or smaller if the goal is 
        reached before).
        If iterative is True, new segments are added iteratively until the
        point is reached.
        """
        goal = tuple(int(round(x)) for x in goal)
        if self._waypoints_index:
            if self._waypoints_index[-1][-1] == goal:
                pass
            else:
                self._segment_id += 1
                one_more = True
                # logger.info("goal: {}".format(goal))
                while one_more:
                    new_segment = self._add_segment(
                            self._waypoints_index[-1][-1], goal, max_dist,
                            force)

                    if new_segment:
                        # Remove the first point, which the same as the last 
                        # one in the _waypoints_index list
                        assert(self._waypoints_index[-1][-1] == new_segment[0])
                        self._waypoints_index.append(new_segment[1:])
                    else:
                        # Straight line if we can not make it...
                        self._waypoints_index.append([goal])
                        # raise CouldNotFindAWay
                                    
                    one_more = (self._waypoints_index[-1][-1] != 
                                goal) and iterative
        else:
            self.reset()
            self._waypoints_index.append([goal])
        
            
    def remove_last_segment(self):
        if len(self._waypoints_index)>1:
            del self._waypoints_index[-1]
            del self._last_passing_point[-1]
            self._visited[self._visited == self._segment_id] = 0
            self._segment_id -= 1
        else:
            self.reset()
            
    
    def reset(self):
        """Clear the calculated waypoints.
        
        The input array and configuration remains stored in the object."""
        self._waypoints_index = []
        self._visited = np.zeros_like(self.array)
        self._segment_id = 0
        self._last_passing_point = [(None, None, None)]
        
    def _add_segment(self, start, goal, max_dist=None, force=False): 
        
        if force:
            self._last_passing_point.append((None, None, None))
            return start, goal
        
        advancement_pct = 0  # Estimation of the attained percentage
        heuristic_compliant = True  # False if any of the segments 
                                    # returns a non-compliance heuristic value
                                    # (e.g. slope is greater than max allowed)
                                    # If mode is strict. it will return None        
        came_from = {}
        # gscore: cost from start up to this point
        gscore = {start:0}
        # fscore: estimated cost from start up to goal passing through this 
        # point
        fscore = {start: self.tentative_heuristic(start, goal)}
        oheap = []
            
        heapq.heappush(
            oheap, 
            (fscore[start], 
             0,
            (start, self._last_passing_point[-1][1], 0, 0)))

        neighbors_list = zip(*self.penalty.neighbors)
        
        while oheap:
    
            current_f_score, current_d_goal, current_passing_point = \
                    heapq.heappop(oheap)
            current, idx_from, slope_from, dist_to_current = \
                current_passing_point
                
            # Estimation of percentage of advancement
            # as a function of current score and remaining distance to goal.
            if current_d_goal>0:
                new_pct = ((100.0 * (current_f_score-current_d_goal)) / 
                                                  current_f_score)
                if new_pct > advancement_pct:
                    self.send_progress(new_pct)            
                    advancement_pct = new_pct
            
            if current == goal or (
                    max_dist is not None 
                    and dist_to_current > max_dist):
                # We reached our goal!!!
                data = []
                self._last_passing_point.append(current_passing_point)
                while current in came_from:
                    data.append(current)
                    current = came_from[current]
                data.append(start)     
                # Return the wa from start to finish, as a list of
                # points [[Y0,X0], [Y1, X1]....]
                data.reverse()
                return data
            if self._visited[current] == self._segment_id:
                continue
            
            self._visited[current] = self._segment_id
            for delta, dist_to_neighbor, _, idx_to in neighbors_list:
                neighbor = current[0] + delta[0], current[1] + delta[1]
                if (0 <= neighbor[0] < self.array.shape[0]
                    and 0 <= neighbor[1] < self.array.shape[1]):
                        # inbounds, do nothing
                    pass
                else:
                    # array outside x or y walls, do not consider
                    continue
                            
                if self._visited[neighbor]:
                    continue
            
                # Tentative: cost of coming up to here, + cost of going
                # from here to neighbor, + eventually a penalty estimated
                # from a direction/slope change
                cost_to, slope_to = self.heuristic(
                        current, neighbor, dist_to_neighbor) 
                if cost_to >= self.heuristic.max_dist:
                    heuristic_compliant = False
                    if self.heuristic_mode == self.STRICT_MODE:
                        continue
                tentative_g_score = (
                     gscore[current] + 
                     cost_to)
                try:
                    tentative_g_score += self.penalty(
                                current, 
                                idx_from,
                                idx_to,
                                slope_from,
                                slope_to)
                except TypeError:
                    # May happen with first idx_from == None
                    pass
                                
                # if we have a better alternative to reach the neighbor, 
                # continue with the next one
                if (neighbor in gscore and 
                    tentative_g_score >= gscore[neighbor]):
                    continue
                # if neighbor has no score yet or we got a better alternative:
                # if  tentative_g_score < gscore.get(neighbor, np.inf):
                else:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score                    
                    d_goal = self.tentative_heuristic(neighbor, goal)
                    # logger.error("distancia {}->{}: {}".format(
                    #       neighbor, goal, d_goal))
                    # fscore determines the next best option to develop.                    
                    fscore[neighbor] = (tentative_g_score + 
                            d_goal)
                    heapq.heappush(oheap, 
                            (fscore[neighbor],                             
                             d_goal,
                             (
                                neighbor, 
                                idx_to, 
                                slope_to,
                                dist_to_current + dist_to_neighbor)))
                        
        # We checked all the possible paths without reaching the goal.
        # return None
        # logger.error(
        #        "Could not find the path between {} and {} respecting " +
        #        "given constraints.".format(start, goal))
        return None

class DefaultConstraintsOptimizer(AStarOptimizer):
    """Qrapper for AStarOptimizer.
    
    This class takes configuration parameters in __init__ and initializes
    the corresponding penalties and heuristics functions.
    """
    
    def reset_config(self,
                 min_slope,
                 max_slope,
                 semi_size,
                 penalty_factor_xy,
                 penalty_factor_z,
                 exclusion_array
                 ):
        """Create default heuristics, tentative_heuristic and penalty objects.
        """
        max_dist_index = 100 * np.sum(
                np.square(np.array(self.array) 
                            * self.array_resolution_m_per_pix))
        
        neighbors = precalc_neighbourhood(semi_size)

        if min_slope is None and max_slope is None:
            self.heuristic = heuristics.DistanceSquaredFakeSlope(
                    max_dist_index)
            self.tentative_heuristic = heuristics.DistanceSquared(
                    max_dist_index)            
        else:
            
            
            if min_slope is None or min_slope <= 0:
                
                self.heuristic = heuristics.DistanceSlopeMetric(
                        self.array,
                        max_slope, 
                        max_dist_index)
            else:
                self.heuristic = heuristics.DistanceMinMaxSlopeMetric(
                        self.array,
                        max_slope,
                        max_dist_index, 
                        min_slope)

            use_precalc = False
            if use_precalc:
                assert(min_slope<=0)
                self.tentative_heuristic = \
                heuristics.PrecalculatedOptimalDistanceSlopeConstrained(
                    max_dist_index, 
                    self.array,
                    max_slope  * self.array_resolution_m_per_pix, 
                    1.0, 
                    target_scale=None)
            else:
                self.tentative_heuristic = heuristics.Distance(max_dist_index)
        
        if exclusion_array is not None:
            """Use specialized class that supports exclusion, slower."""
            
            self.penalty = penalties.ParabolicPenaltyStatic(
                               exclusion_array[::-1] * (3 * max_dist_index),
                               neighbors,
                               penalty_factor_xy,
                               penalty_factor_z)
        elif penalty_factor_xy != 0 or penalty_factor_z != 0:
            """Approx. 20% faster than ParabolicPenaltyStatic."""
            self.penalty = penalties.ParabolicPenalty(neighbors,
                                       penalty_factor_xy,
                                       penalty_factor_z)
        else:
            self.penalty = penalties.NoPenalty(neighbors)
                
    def __init__(self,
                 dtm_m,
                 scale_m_per_pix
                 ):

        super(DefaultConstraintsOptimizer, self).__init__(
                dtm_m, 
                scale_m_per_pix)    
    
        
if __name__ == "__main__":

    nmap = np.array([
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,1,1,1,1,1,1,1,1,1,1,0,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,1,1,1,1,1,1,1,1,1,1,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,1,1,1,0,1,1,1,1,1,1,0,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,1,1,1,1,1,1,1,1,1,1,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,1,1,1,1,1,1,1,1,1,1,0,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0]])
    
    nmap = np.zeros([1000, 1000])
    starting_time = datetime.datetime.now()

    max_slope = 0.1
    semi_size = 5    
    scale_m_per_pix = 1
    
    neighbors = precalc_neighbourhood(semi_size)
    max_dist_index = 100 * np.sum(np.square(nmap.shape) * scale_m_per_pix ** 2)
    
    if max_slope is None:
        heuristic = heuristics.DistanceSquaredFakeSlope(max_dist_index)
        tentative_heuristic = heuristics.DistanceSquared(max_dist_index)
        penalty = NoPenalty(neighbors)
    
    else:
        penalty_factor_xy = 40
        penalty_factor_z = 0
        
        heuristic = heuristics.DistanceSlopeMetric(
                nmap,
                max_slope, 
                max_dist_index)
        
        penalty = penalties.ParabolicPenalty(neighbors,
                                   penalty_factor_xy,
                                   penalty_factor_z)
        use_precalc = True
        if use_precalc:
            tentative_heuristic = \
            heuristics.PrecalculatedOptimalDistanceSlopeConstrained(
                max_dist_index, 
                nmap, 
                max_slope, 
                scale_m_per_pix, 
                target_scale=None)
        else:
            tentative_heuristic = heuristics.Distance(max_dist_index)
            
    astar = AStarOptimizer(nmap, 1, 
                           heuristic,
                           tentative_heuristic,
                           penalty)
    
    starting_point = (1, 0)
    intermediate = (20, int(nmap.shape[1] * 0.8))
    ending_point = (nmap.shape[0]-1, nmap.shape[1]-1)
    waypoints = astar.astar([starting_point,intermediate, ending_point])
    logger.info("Total time: {}".format(datetime.datetime.now()-starting_time))
    
    output = nmap.copy()
    output[np.array(waypoints)[:,0], np.array(waypoints)[:,1] ] = 2
    logger.info(output)