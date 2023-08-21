import time
import numpy as np

import scipy.interpolate
import scipy.optimize
from scipy.interpolate import interp2d
from math import ceil, floor

try:
    from ..frd_utils import logging_qgis as logging
except (ValueError, ImportError):
    import logging


logger = logging.getLogger("frd")

def get_interpol(array):
    
    coords_y = list(range(array.shape[0]))
    coords_x = list(range(array.shape[1]))
    interpolator = scipy.interpolate.RegularGridInterpolator((coords_y, coords_x), array, bounds_error=False)
    return interpolator


class InteractiveDefaultConstraintsOptimizer(object):


    def __init__(self, dtm, dtm_resolution_m_per_pix):
        """dtm represents height (in meters) of given terrain.

        max_slope is the maximum allowed slope. if None (default value)
                 then slope is not taken into account on the calculation.
                 The value of max_slope will be scaled according to the dtm
                 resolution (in m/pix)
                 (i.e for a raster with 2m/pix resolution, the corrected
                 max_slope for a specified slope of 10% will be
                     0.10m/m*2m/pix = 0.20m/pix)

        """
        self.dtm = dtm
        self.array = dtm/dtm_resolution_m_per_pix        
        self.array_resolution_m_per_pix = dtm_resolution_m_per_pix
        self._waypoints_index = []  # Allows increasing the waypoints list gradually
                            # via calls to add_point
        # Required for interactive
        self._number_of_segments = 1
        self.reset()
        self.interpolator = get_interpol(self.array)
        # default progress_callback has no effect, it is modified in designer_dockwidget to 
        # feed the progress bar on QGIS
        self.progress_callback = lambda *args, **kwargs: None


    def reset(self):
        """Clear the calculated waypoints.

        The input array and configuration remains stored in the object."""
        # print(f"MODO INTERACTIVO interactive_opt reset ")
        self._waypoints_index = []
        self._visited = np.zeros_like(self.array)
        self._segment_id = 0
        self._last_passing_point = [(None, None, None)]

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
    
    def interactive_add_segment_to(self, goal, iterative=False):
        """Adds a new segment to go from last point to goal.

        If max_dist is specified, we approach to goal using a segment of
        that aproximate length (in fact, the first segment reached with
        length greater than max_dist is taken, or smaller if the goal is
        reached before).
        If iterative is True, new segments are added iteratively until the
        point is reached.
        """

        goal = tuple(x for x in goal)
        if self._waypoints_index:
            # print(f"MODO INTERACTIVO interactive_add_segment_to self._waypoints_index[-1][-1] {self._waypoints_index[-1][-1]} GOAL {goal}")
            if self._waypoints_index[-1][-1] == goal:
                pass
            else:
                self._segment_id += 1
                one_more = True
                # logger.info("goal: {}".format(goal))
                while one_more:
                    new_segment, goal = self.interactive_add_segment(
                            self._waypoints_index[-1][-1], goal)
                    # print(f"MODO INTERACTIVO interactive_add_segment_to NEW SEGMENT {new_segment}")
                    if new_segment:
                        # Remove the first point, which the same as the last
                        # one in the _waypoints_index list
                        assert(self._waypoints_index[-1][-1] == new_segment[0])
                        self._waypoints_index.append(new_segment[1:])
                        # print(f"MODO INTERACTIVO interactive_add_segment_to NEW SEGMENT NEW SEGMENT {new_segment}")
                    else:
                        # Straight line if we can not make it...
                        self._waypoints_index.append([goal])
                        # raise CouldNotFindAWay
                        # print(f"MODO INTERACTIVO interactive_add_segment_to NEW SEGMENT ELSE {new_segment}")
                    one_more = (self._waypoints_index[-1][-1] !=
                                goal) and iterative
        else:
            # print(f"MODO INTERACTIVO interactive_add_segment_to ELSE ELSE ")
            self.reset()
            self._waypoints_index.append([goal])

    def interactive_add_segment_to_straight(self, goal):
        goal = tuple(x for x in goal)
        if self._waypoints_index:
            # print(f"MODO INTERACTIVO interactive_add_segment_to_straight self._waypoints_index[-1][-1] {self._waypoints_index[-1][-1]} GOAL {goal}")
            if self._waypoints_index[-1][-1] == goal:
                pass
            else:
                self._waypoints_index.append([goal])
        else:
            # print(f"MODO INTERACTIVO interactive_add_segment_to_straight ELSE ")
            self.reset()
            self._waypoints_index.append([goal])        

    def remove_last_segment(self):
        if len(self._waypoints_index)>1:
            del self._waypoints_index[-1]
            # del self._last_passing_point[-1]
            self._visited[self._visited == self._segment_id] = 0
            self._segment_id -= 1
        else:
            self.reset()

    def interactive_add_segment(self, start, goal):
        self._gui_update_time = time.time()        
        
        # Coordinates of candidates at distance R0_m from center_x, center_y
        center_x = start[0]
        center_y = start[1]
        alpha_0 = np.arctan2(goal[1] - center_y, goal[0] - center_x)
        circle_x, circle_y, alpha_rad = self.candidates( center_x, center_y, self.array_resolution_m_per_pix, self.R0_px)
        # self._last_passing_point.append(current_passing_point)
        # print(f"MODI INTERACTIVO interactive_add_segment ALPHA_0 {alpha_0}")

        dist = self.find_roots(self.interpolator, alpha_rad, circle_x, circle_y, center_x, center_y, alpha_0, self.delta_z_px)
        
        alpha_opt, delta_z_opt = min(dist)[1:]
        
        x_p, y_p = self.alpha_to_xy(alpha_opt, self.R0_px)
        point_x, point_y = center_x + x_p, center_y + y_p
        point_z_interp = self.interpolator([point_x, point_y]) 
        # print(f"MODO INTERACTIVO interactive_add_segment POINT_X ({point_x}, {point_y}) POINT_Z {point_z_interp}" )
        return None, [point_x, point_y]
# ------------------------- DAVID NEW ---------------------------
    def interactive_search_segment_to_(self, goal):
        """Search a new segment to go from last point to goal.
        """
        goal = tuple(x for x in goal)
        if self._waypoints_index:
            if self._waypoints_index[-1][-1] == goal:
                pass
            else:
                goal, up_down = self.interactive_search_segment(self._waypoints_index[-1][-1], goal)
        return goal, up_down
    

    def interactive_search_segment(self, start, goal):
        
        center_x = start[0]
        center_y = start[1]
        alpha_0 = np.arctan2(goal[1] - center_y, goal[0] - center_x)
        # circle_x, circle_y, alpha_rad = self.candidates_NEW( center_x, center_y)
        circle_x, circle_y, alpha_rad = self.candidates( center_x, center_y, self.array_resolution_m_per_pix, self.R0_px)

        dist = self.find_roots(self.interpolator, alpha_rad, circle_x, circle_y, center_x, center_y, alpha_0, self.delta_z_px)
        if len(dist) > 0:
            alpha_opt, delta_z_opt = min(dist)[1:]

            x_p, y_p = self.alpha_to_xy(alpha_opt, self.R0_px)
            point_x, point_y = center_x + x_p, center_y + y_p
            point_z_interp = self.interpolator([point_x, point_y])
            poinz_z_center = self.interpolator([center_x, center_y])
            # print(f"MODO INTERACTIVO interactive_search_segment POINT_X ({point_x}, {point_y}) POINT_Z {point_z_interp}" )         
            return [point_x, point_y], self.up_down_segment(point_z_interp, poinz_z_center)
        else:
            return None, None          

    def up_down_segment(self, z_inter, z_center):
        if z_center - z_inter > 0:
            return True
        else:
            return False
        
    def reset_config(self, inter_slope_pct, inter_length, exclusion_array):
        """Create default heuristics, tentative_heuristic and penalty objects.        """
        
        self.slope_pct = inter_slope_pct 
        self.R0_m = inter_length
        self.R0_px = self.R0_m/ self.array_resolution_m_per_pix
        self.delta_z_m = inter_length * (self.slope_pct/100)
        self.delta_z_px = self.delta_z_m / self.array_resolution_m_per_pix         

    def candidates(self, center_x, center_y, dtm_m, R0_px):
    
        delta_alpha_rad = np.arctan2(dtm_m/40,R0_px)        
        # Normalize delta_alpha so that we get values at 0, pi/2, pi and 3pi/2
        N_aux = np.ceil(2*np.pi/delta_alpha_rad/4)*4
        N = N_aux if N_aux > 720 else 720
        # print(f"N {N}")
        
        alpha_rad = np.linspace(0, 2*np.pi, int(N)+1, endpoint=True)   # Include endpoint to find roots in the interval [360º-360º/N -> 360º] 

        # Coordinates of circle with radius R0 and 
        circle_x = R0_px*np.cos(alpha_rad)+center_x
        circle_y = R0_px*np.sin(alpha_rad)+center_y 
       
        return circle_x, circle_y, alpha_rad
    

    
    def approx_roots(self, alpha, z):
        sign_change = np.sign(z[:-1])*np.sign(z[1:]) < 0
        # print(f'{alpha[:-1][sign_change]} <-> {alpha[1:][sign_change]}')
    
        alpha_0 = alpha[:-1][sign_change]
        alpha_1 = alpha[1:][sign_change]
        z_0 = z[:-1][sign_change]
        z_1 = z[1:][sign_change]
        roots = []
        for a0, a1, z0, z1 in zip(alpha_0, alpha_1, z_0, z_1):
            delta_a_root = -z0/(z1-z0)*(a1-a0)
            a_root = a0 + delta_a_root
            roots.append(a_root)
        return roots
    
    def periodic(self, fun):
        """This function converts any function in periodic around [0->2*pi]"""
        def fun_period(*args):
            return fun(args[0] %(2*np.pi), *args[1:])
        return fun_period


    def find_roots(self, interpolator, alpha, circle_x, circle_y, center_x, center_y, alpha_0, delta_z_px, up_and_down=True):
        # Value of z at candidates and at the center
        circle_z = interpolator(np.array([circle_x, circle_y]).T) 
        z_center = interpolator(np.array([center_x, center_y]))

        # print(f"MODO INTERACTIVO find_roots  center {center_x}, {center_y} z_center_interp {z_center}")
        
        if up_and_down:
            deltas = (delta_z_px, -delta_z_px)
        else:
            deltas = (delta_z_px,)
    
        alphas = []
        circles = []
        for d_z_m in deltas:
            # The function to optimize, the intersection between the value of z at radius R0_m and the center + delta_z_m (should check for -delta_z_m too)
            circle_func = self.periodic(scipy.interpolate.interp1d(alpha, circle_z-(z_center+d_z_m), fill_value='extrapolate'))
            # circle_func_prime = periodic(scipy.interpolate.interp1d(alpha[:-1]+0.5*(alpha[1]-alpha[0]), np.diff(circle_func(alpha))/np.diff(alpha), fill_value='extrapolate'))
            
            try:
                roots = self.approx_roots(alpha,circle_func(alpha))
                # alpha_opt = scipy.optimize.newton(circle_func, x0=alpha_0, fprime=None) # root_scalar , method='newton')
                alphas.extend([alpha_opt, d_z_m] for alpha_opt in roots)
                # print(f'alphas: {alphas}')
                for alpha_opt in roots:
                    circles.append([circle_func(alpha), circle_func(alpha_0), circle_func(alpha_opt)])
        
                # print(alpha_z)
            except RuntimeError:
                print('Error: no solution at given slope & altitude change for this map!!!!')
                dists = []

        if not alphas:
            # raise DPOptimizationError('No solutions could be found for alpha_0: {alpha_0}')
            dists = []
        
        x_0 = np.cos(alpha_0)
        y_0 = np.sin(alpha_0)
        # print(f"ALPHA_0 X_0 {x_0} Y_0 {y_0}")
        dists = [[(np.cos(alpha)-x_0)**2 + (np.sin(alpha)-y_0)**2, alpha, d_z_m] for alpha,d_z_m in alphas]
        # print(dists)
    
        return dists


    def alpha_to_xy(self, alpha, r):
        return r * np.cos(alpha), r * np.sin(alpha)

            

class DPOptimizationError(RuntimeError):
    """Exception raised when no valid solution is found"""
    pass