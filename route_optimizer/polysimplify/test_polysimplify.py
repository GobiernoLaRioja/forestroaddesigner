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
import os
import numpy as np
from polysimplify import VWSimplifier
import unittest

class VWSimplifierTest(unittest.TestCase):
    def test_thresholds(self):
        RELATIVE_THRESHOLD = .00001
        absPath, _ = os.path.split(__file__)
        test_pts = np.load(os.path.join(absPath, 'fuzzy_circle.npy'))        
        simplified = VWSimplifier(test_pts)

        test_thresholds = np.load(os.path.join(
                absPath, 'fuzzy_thresholds.npy'))

        np.testing.assert_allclose(
               simplified.thresholds, test_thresholds, 
               rtol = RELATIVE_THRESHOLD )

if __name__ == '__main__':
    unittest.main()