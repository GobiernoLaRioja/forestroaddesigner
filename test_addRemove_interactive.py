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

Test for solve the IndexError in remove last segment for segments added with 
ctrl with interactive processing mode

"""

import unittest
import numpy as np
from osgeo import gdal
from route_optimizer import a_star, heuristics, penalties

class RemoveCtrlSegmentClass(unittest.TestCase):

    def setUp(self):
        """Set the input points (as index, not as geo-coordinates) and 
        parameters to launch process
        """
        self.point_type_list = [[1480.39805825, 1817.75728155], 
                                [1424.47572816, 1932.70873786], 
                                [1359.23300971, 2066.30097087],
                                [1396.51456311, 2283.77669903],
                                [1589.13592233, 2035.23300971],
                                [1662.14563107, 1914.06796117],
                                [1662.14563107, 1999.50485437]]

        dtm_path = '.\\test_data\\dtm_h242_25830_5_metros_clip.tif'
        dtm_data_set = gdal.Open(dtm_path)
        dtm_band = dtm_data_set.GetRasterBand(1)
        self.dtm_array = dtm_band.ReadAsArray().astype(np.float)
        self.dtm_resolution = 5

        self.max_slope = 0.1
        self.semi_size = 5    
        self.neighbors = a_star.precalc_neighbourhood(self.semi_size)
        self.max_dist_index = 100 * np.sum(np.square(self.dtm_array.shape))
        self.penalty_factor_xy = 40
        self.penalty_factor_z = 0
    
        self.heuristic = heuristics.DistanceSlopeMetric(
                self.dtm_array,
                self.max_slope, 
                self.max_dist_index)
        self.tentative_heuristic = heuristics.Distance(self.max_dist_index)
        self.penalty = penalties.ParabolicPenalty(self.neighbors,
                               self.penalty_factor_xy,
                               self.penalty_factor_z)

        self.astar_optimizer = a_star.AStarOptimizer(self.dtm_array, 
                                                     self.dtm_resolution,
                                                     self.heuristic,
                                                     self.tentative_heuristic,
                                                     self.penalty)

    def test_addRemoveSegment(self):
        """Test for add segment and remove segment for defined points
        """
        self.assertEqual(self.astar_optimizer._waypoints_index, [])
        for value in self.point_type_list:
            self.astar_optimizer.add_segment_to(value, force=True)
        self.assertEqual(len(self.astar_optimizer._waypoints_index),
                         len(self.point_type_list))
        
        for _ in range(len(self.astar_optimizer._waypoints_index)):
            long_previa = len(self.astar_optimizer._waypoints_index)
            a_quitar = self.astar_optimizer._waypoints_index[-1]
            self.astar_optimizer.remove_last_segment()
            long_post = len(self.astar_optimizer._waypoints_index)
            self.assertFalse(a_quitar in self.astar_optimizer._waypoints_index)
            self.assertEqual((long_previa - 1), long_post)
        
    def tearDown(self):
        self.point_type_list = None
        
if __name__ == "__main__":
    
    from test.utilities import get_qgis_app
    QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

    # from PyQt4 import QtGui
    # from qgis.core import QgsApplication
    # import os
    # import logging
    # logging.getLogger().setLevel(logging.DEBUG)
     
    # import atexit
    # atexit.register(QgsApplication.exitQgis)
    # app = QtGui.QApplication([])
    
    # qgis_prefix = os.getenv("QGIS_PREFIX_PATH")
    # Initialize qgis libraries
    # QgsApplication.setPrefixPath(qgis_prefix, True)
    # QgsApplication.initQgis()
    
    unittest.main()