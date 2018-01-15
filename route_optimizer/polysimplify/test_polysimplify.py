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
import numpy as np
from polysimplify import VWSimplifier
import unittest
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class VWSimplifierTest(unittest.TestCase):
    def test_thresholds(self):
        RELATIVE_THRESHOLD = .00001
        test_pts = np.load(os.path.join(BASE_DIR, 'fuzzy_circle.npy'))
        simplified = VWSimplifier(test_pts)

        test_thresholds = np.load(os.path.join(BASE_DIR,
            'fuzzy_thresholds.npy'))
             
        np.testing.assert_allclose(
               simplified.thresholds, test_thresholds, 
               rtol = RELATIVE_THRESHOLD )
        

if __name__ == '__main__':
    unittest.main()