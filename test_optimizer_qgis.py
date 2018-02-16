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

from qgis.core import QgsVectorLayer,QgsRasterLayer, QgsMapLayerRegistry

import optimizer_qgis as oq

from frd_utils import array_funs as af
from frd_utils import inputs_checker
import frd_utils.logging_qgis as logging
import viewers

logging.info("Launching test_optimizer_qgis_line.")
logger = logging.getLogger("frd")

class OptimizerQGisCase(unittest.TestCase):

    def setUp(self):
        """Set the input layers and the output directory
        """
        input_v_layer_path = '.\\test_data\\line_4_road_design.shp'
        self.input_v_layer = QgsVectorLayer(
                input_v_layer_path, 'input_path', 'ogr')
        
        input_dtm_path = '.\\test_data\\dtm_h242_25830_5_metros_clip.tif'
        self.input_dtm = QgsRasterLayer(input_dtm_path, 'dtm_5m')
        
        exclusion_areas_path = \
                '.\\test_data\\excluded_areas\\exclusion_areas_file.shp'
        self.exclusion_areas_layer = QgsVectorLayer(
                exclusion_areas_path, 'exclusion_areas', 'ogr')
        
        
        self.empty_layer = QgsVectorLayer(
            'Line?crs={}'.format(self.input_dtm.crs().toWkt()),
            "Vacia" , 'memory')
        
        self.outputfolder = 'C:\\ForestRoadDesigner\\pruebas'
        
        QgsMapLayerRegistry.instance().addMapLayer(self.input_v_layer)
        QgsMapLayerRegistry.instance().addMapLayer(self.input_dtm)
        QgsMapLayerRegistry.instance().addMapLayer(self.exclusion_areas_layer)
        
        
    def test_coords_and_indexes(self):
        """Test conversion between coordinates and indexes
        """
        waypoints_coords_list = af.waypoints_list(
                                        self.input_v_layer)
        wpts_index_array, ds_geotransform = af.coord_to_index(
                        self.input_dtm,
                        waypoints_coords_list)
        q_coords = af.index_to_coord(
                ds_geotransform,
                wpts_index_array)
        
        np.testing.assert_allclose(np.array(waypoints_coords_list), q_coords)


    def test_bounds_check(self):
        """Test if input data (layers) are in dtm extension limits
        """
        self.assertTrue(inputs_checker.check_bounds(
                self.input_dtm, self.input_v_layer))
        self.assertFalse(inputs_checker.check_bounds(
                self.input_v_layer, self.input_dtm))

    def testVectorLayer(self):   
        """
        """
        v_layer_feat = self.input_v_layer.getFeatures()
        points_coords_list = []
        for elem in v_layer_feat:
            geom = elem.geometry()
            point = geom.asPoint()
            points_coords_list.append([point.x(), point.y()])            
        self.assertNotEqual(len(points_coords_list), 0)
        
    def test_raster_2_array(self):
        """Testing raster 2 array function
        """
        dtm_array = af.raster_2_array(self.input_dtm)        
        self.assertEqual(dtm_array.shape, (136, 176))
        
    def testBestPathFinder(self):
        """Test full process to obtain layers (points and Lines layers)
        """
        import tempfile
        outputFolder = tempfile.mkdtemp("frd")
        
        polylineThreshold = 5
               
        parameters = {
            "min_slope_pct": 0,
            "max_slope_pct": 10, 
            "semi_size": 2,
            "penalty_factor_xy": 40,
            "penalty_factor_z": 40
            }
        
        finder = oq.BestPathFinder(self.input_dtm, self.exclusion_areas_layer)
        finder.set_parameters(parameters)
        finder.set_output_folder(outputFolder)
        raw_layer = finder.create_raw_output_layer()
        
        simplified_layer = finder.create_simplified_output_layer( 
                                       polylineThreshold)

        for point_index in af.waypoints_list(self.input_v_layer):
            finder.add_segment_to(point_index)

        self.assertEqual(
                raw_layer.dataProvider().featureCount(), 179)
        self.assertTrue(simplified_layer.isValid())

    def test_checkAttrsValues(self):
        """Test for layers attributes
        """
        import tempfile
        outputFolder = tempfile.mkdtemp("frd")
        polylineThreshold = 0
               
        parameters = {
            "min_slope_pct": 0.5,
            "max_slope_pct": 10,
            "semi_size": 2,
            "penalty_factor_xy": 40,
            "penalty_factor_z": 40
            }
        
#        finder = oq.BestPathFinder(self.input_dtm, self.exclusion_areas_layer)
        finder = oq.BestPathFinder(self.input_dtm)
        finder.set_parameters(parameters)
        finder.set_output_folder(outputFolder)
        _ = finder.create_raw_output_layer()        
        simplified_layer = finder.create_simplified_output_layer(
                                       polylineThreshold)
        
        height_prof, slope_profile, _ = viewers.height_profile(
                finder.dtm["array"],
                finder.optimizer.waypoints_index(), 
                finder.parameters["max_slope_pct"]/100.0, 
                finder.converter.pixel_width)
        
        self.assertEqual(len(slope_profile) - 1, 
                         simplified_layer.dataProvider().featureCount())
        
        feats = simplified_layer.dataProvider().getFeatures()
        for row_id, vals in enumerate(zip(feats, slope_profile[1:])):
            f, s = vals
            
            for att_id, a in enumerate(f.attributes()):
                with self.assertRaises(AttributeError):
                    a.isNull()
            self.assertAlmostEqual(s*100.0, f.attribute("slope_p"))
            self.assertTrue(abs(f.attribute("slope_p")) <= parameters [
            "max_slope_pct"])
            self.assertTrue(abs(f.attribute("slope_p")) >= parameters [
            "min_slope_pct"])
            
    def test_empty_waypoints(self):
        """Test for empty layer
        """
        import tempfile
        outputFolder = tempfile.mkdtemp("frd")
               
        parameters = {
            "min_slope_pct": 0,
            "max_slope_pct": 10, 
            "semi_size": 2,
            "penalty_factor_xy": 40,
            "penalty_factor_z": 40
            }
        
        finder = oq.BestPathFinder(self.input_dtm, self.exclusion_areas_layer)
        finder.set_parameters(parameters)
        finder.set_output_folder(outputFolder)
        finder.create_raw_output_layer()
        simp_layer = finder.create_simplified_output_layer(5)
        self.assertEqual(simp_layer.featureCount(), 0)

    def testExclusionUtility(self):
        """Test if exclusion utility is working
        """
        import tempfile 
        from qgis.core import QGis
        outputFolder = tempfile.mkdtemp("frd") 
        
        parameters = {
            "min_slope_pct": 0,
            "max_slope_pct": 10, 
            "semi_size": 2,
            "penalty_factor_xy": 40,
            "penalty_factor_z": 40
            }
         
        finder = oq.BestPathFinder(self.input_dtm, self.exclusion_areas_layer) 
        finder.set_parameters(parameters)
        finder.set_output_folder(outputFolder)
        raw_layer = finder.create_raw_output_layer()
        for point_index in af.waypoints_list(self.input_v_layer):
            finder.add_segment_to(point_index)
        raw_layer = finder.create_raw_output_layer()
        self.assertTrue(raw_layer)
                
        provider = raw_layer.dataProvider().getFeatures()
        puntos_geom = []
        for elem in provider:
            geom2 = elem.geometry()
            if geom2.wkbType() == QGis.WKBPoint:
                puntos_geom.append(geom2)

        exc_provider = self.exclusion_areas_layer.dataProvider().getFeatures()
        exc_geoms = []
        for elem in exc_provider:
            geom1 = elem.geometry()
            exc_geoms.append(geom1)

        contenido = []
        for elem_exc in self.exclusion_areas_layer.dataProvider().getFeatures():
            for elem in raw_layer.dataProvider().getFeatures():
                geom2 = elem.geometry()
                geom1 = elem_exc.geometry()
                if geom1.contains(geom2):
                    contenido.append(geom2)
        self.assertEqual(contenido, [])
                
    def tearDown(self):
        QgsMapLayerRegistry.instance().removeMapLayer(self.input_v_layer)
        QgsMapLayerRegistry.instance().removeMapLayer(self.input_dtm)
        QgsMapLayerRegistry.instance().removeMapLayer(
                self.exclusion_areas_layer)
        
        
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