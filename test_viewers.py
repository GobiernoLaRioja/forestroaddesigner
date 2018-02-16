# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ForestRoadDesigner
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
from __future__ import unicode_literals

import unittest
import numpy as np

import viewers

class ViewersTestCase(unittest.TestCase):
    def test_remove_undef_values_malformed(self):
        """Test the remove undef values works fine with malformed dtm.
        
        Check that if no defined values exist, the function still works.
        """
        undefined_value = -9999
        dtm_m = np.zeros([10,10]) + undefined_value
        dtm_m2 = viewers.remove_undef(dtm_m, undefined_value)
        self.assertEqual(dtm_m2[dtm_m2<=undefined_value].nbytes, 0)
        np.testing.assert_allclose(dtm_m, np.zeros(dtm_m.shape))
    
    def test_remove_undef_values(self):
        """Test the remove undef values works fine with dtm with undefs."""
        undefined_value = -9999
        dtm_m = np.zeros([10,10]) + undefined_value
        dtm_m[1,1] = 10
        dtm_m2 = viewers.remove_undef(dtm_m, undefined_value)
        self.assertEqual(dtm_m2[dtm_m2<=undefined_value].nbytes, 0)
        np.testing.assert_allclose(dtm_m, np.ones(dtm_m.shape)*dtm_m[1,1])

    def test_remove_undef_values_no_undefs(self):
        """Test the remove undef values works fine with dtm with undefs."""
        undefined_value = -9999
        dtm_m = np.ones([10,10])
        dtm_m2 = viewers.remove_undef(dtm_m, undefined_value)
        self.assertEqual(dtm_m2[dtm_m2<=undefined_value].nbytes, 0)
        np.testing.assert_allclose(dtm_m, np.ones(dtm_m.shape))

if __name__ == "__main__":
    unittest.main()