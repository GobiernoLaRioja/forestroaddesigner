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
import os
import math
import logging
logger = logging.getLogger("frd")
logger.setLevel(logging.DEBUG)

from osgeo import gdal
from qgis.core import (QgsApplication, QgsMapLayerRegistry, QgsMapLayer, QGis,
                       QgsProject)
from qgis.gui import QgsMessageBar
from qgis.utils import iface

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QMessageBox, QProgressBar

import optimizer_qgis
import frd_utils.array_funs as af
from frd_utils import inputs_checker
from frd_interactive_tool import FRDInteractiveTool
try:
    import version
except ImportError:
    class version(object):
        VERSION = "devel"

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'forest_road_designer_dockwidget_base.ui'))


class ForestRoadDesignerDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(ForestRoadDesignerDockWidget, self).__init__(parent)
        self.iface = iface
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        # The object responsible of the optimization.
        self.finder = None
        self.interactive_mode = False
        self._previously_active_tool = None

        self.exclusionAreasCheckBox.setChecked(False)
        self.exclusionAreasComboBox.setEnabled(False)
        self.exclusionAreasTextLabel.setEnabled(False)
        self.waypointsLayerLabel.setEnabled(False)
        self.waypointsLayerComboBox.setEnabled(False)
        self.stopInteractivePushButton.setEnabled(False)
        self.dtmLayerComboBox.currentIndexChanged.connect(
                self._updateMetersLabels)
        self.exclusionAreasCheckBox.clicked.connect(
                self.initExclusionAreasLayer)
        self.outputFolderToolButton.clicked.connect(self.chooseOutputFolder)
        self.startProcessPushButton.clicked.connect(
                    self.launchProcess)
        self.stopInteractivePushButton.clicked.connect(
                    self.continueCancel_interactive_mode)
        self.maxSlopeDoubleSpinBox.valueChanged.connect(
                self._updateMaxSlopeDegreesValue)
        self.maxSlopeDoubleSpinBox.valueChanged.connect(
                self._updateMinSlopeDegreesValue)
        self.minSlopeDoubleSpinBox.valueChanged.connect(
                self._updateMinSlopeDegreesValue)
        self._updateMaxSlopeDegreesValue()
        self._updateMinSlopeDegreesValue()
        self.semiSizeDoubleSpinBox.valueChanged.connect(
                self._updateMetersLabels)
        self.polylineThresholdDoubleSpinBox.valueChanged.connect(
                self._updateMetersLabels)
        self.batchProcessCheckBox.clicked.connect(
                self.updateDialogBatchProcess)
        QgsMapLayerRegistry.instance().layerWasAdded.connect(self.initLayers)
        QgsMapLayerRegistry.instance().layersRemoved.connect(self.initLayers)
        self._initVersion()
        self.initLayers()
    
    def launchProcess(self):
        """Defines porcess acording bath_process checkBox
        """
        if self.batchProcessCheckBox.isChecked():
            self.launchRouteOptimization()
        else:
            self.startInteractiveRouteOptimization()
    
    def closeEvent(self, event):
        """Closes plugin GUI
        """
        self.closingPlugin.emit()
        event.accept()

    def _initVersion(self):
        """Init versionLabel with plugin info in module version.py
        """
        self.frdVersionLabel.setText(u"Forest Road Designer {}".format(
                version.VERSION))

    def _initComboBox(self, comboBox, layerType):
        """Init the value of Dtm layer QComboBox with loaded layers in QGis
        interface.
        """
        loadedLayers = QgsMapLayerRegistry.instance().mapLayers()
        checkType = lambda lyr, lt: lyr.type()==lt[0] and (
                lt[1] == "all" or lyr.wkbType() in lt[1])

        layerList = [
            layer.name() for layer in loadedLayers.values()
            if checkType(layer, layerType)]
        previous_selection = comboBox.currentText()
        comboBox.clear()
        comboBox.addItems(layerList)
        try:
            comboBox.setCurrentIndex(layerList.index(previous_selection))
        except ValueError:
            pass

    def _updateMaxSlopeDegreesValue(self):
        """Update the label with max slope in degrees according to value in
        pct."""
        maxValue = self.maxSlopeDoubleSpinBox.value()

        self._updateMaxSlopeDegreesLabel(maxValue)

    def _updateMaxSlopeDegreesLabel(self, maxValue=None):
        """Update the label with max slope in degrees according to value in
        pct."""

        max_slope_degrees = math.degrees(math.atan(
                maxValue / 100.0))
        self.maxSlopeDegreesLabel.setText("{:.2f}°".format(max_slope_degrees))

    def _updateMinSlopeDegreesValue(self):
        """Update the label with min slope in degrees according to value in
        pct."""
        minValue = self.minSlopeDoubleSpinBox.value()

        self.minSlopeDoubleSpinBox.setMaximum(
                self.maxSlopeDoubleSpinBox.value() - 2.0)
        self.minSlopeDoubleSpinBox.setMinimum(0.0)

        self._updateMinSlopeDegreesLabel(minValue)

    def _updateMinSlopeDegreesLabel(self, minValue=None):
        """Update the label with min slope in degrees according to value in
        pct."""

        min_slope_degrees = math.degrees(math.atan(
                minValue / 100.0))
        self.minSlopeDegreesLabel.setText(u"{:.2f}°".format(min_slope_degrees))

    def _updateMetersLabels(self, semiSizeValue=None):
        """Update the label with the pixels number according the value in
        SemiSizeDoubleSpinBox"""
        semiSizeValue = int(self.semiSizeDoubleSpinBox.value())
        dtmLayerList = QgsMapLayerRegistry.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())

        if dtmLayerList == []:
            self.semiSizeMetersLabel.setText(u"- x - metros")
            self.polylineErrorMetersLabel.setText(u"(-)")
        else:
            dtm_layer = dtmLayerList[0]
            raster = gdal.Open(dtm_layer.source())

            try:
                raster.GetGeoTransform()
                geotransform = raster.GetGeoTransform()
                dtm_pixel_size = geotransform[1]
                semi_size_m = int(((2 * semiSizeValue) + 1) * dtm_pixel_size)
                poly_error_m = (self.polylineThresholdDoubleSpinBox.value()
                                * dtm_pixel_size)
                self.semiSizeMetersLabel.setText(u"({}m x {}m)".format(
                        semi_size_m, semi_size_m))
                self.polylineErrorMetersLabel.setText(u"({:.1f}m^2)".format(
                        poly_error_m))
            except AttributeError:
                self.semiSizeMetersLabel.setText(u"(- x -)")
                self.polylineErrorMetersLabel.setText(u"(-)")
                
    def updateDialog(self):
        """Update the enabled/disabled widgets according to interactive mode.
        """
            
        self.dtmLabel.setEnabled(not self.interactive_mode)
        self.dtmLayerComboBox.setEnabled(not self.interactive_mode)

        self.outputFolderLabel.setEnabled(not self.interactive_mode)
        self.outputFolderLineEdit.setEnabled(not self.interactive_mode)
        self.outputFolderToolButton.setEnabled(not self.interactive_mode)
        
        self.exclusionAreasCheckBox.setEnabled(not self.interactive_mode)
        self.exclusionAreasTextLabel.setEnabled(not self.interactive_mode)
        self.exclusionAreasComboBox.setEnabled(not self.interactive_mode)
        
        self.designParametersGroupBox.setEnabled(not self.interactive_mode)
        
        self.stopInteractivePushButton.setEnabled(self.interactive_mode)
        self.batchProcessCheckBox.setEnabled(not self.interactive_mode)
        self.startProcessPushButton.setEnabled(not self.interactive_mode)       
        
        self.updateDialogBatchProcess()
        
    def updateDialogBatchProcess(self):
        """Update the GUI if batch process is selected 
        """
        self.batch_process = self.batchProcessCheckBox.isChecked()
                   
        self.waypointsLayerComboBox.setEnabled(self.batch_process)
        self.waypointsLayerLabel.setEnabled(self.batch_process)
        
    def initLayers(self):
        """Init the three input layers that intervenes in the process"""
        self.initDtmLayer()
        self.initWaypointLayer()
        self.initExclusionAreasLayer()

    def initDtmLayer(self):
        """Init the value of Dtm layer QComboBox with loaded layers in QGis
        interface."""
        try:
            self._initComboBox(self.dtmLayerComboBox,
                               (QgsMapLayer.RasterLayer, "all"))
        except AttributeError:
            pass

    def initWaypointLayer(self):
        """Init the value of Waypoint layers in QComboBox with loaded
        layers in QGis interface."""
        try:
            self._initComboBox(
                    self.waypointsLayerComboBox,
                    (QgsMapLayer.VectorLayer, [QGis.WKBLineString,
                                               QGis.WKBMultiLineString]))
        except AttributeError:
            pass

    def initExclusionAreasLayer(self):
        """Init the value of Waypoint layers in QComboBox with loaded layers
        in QGis interface."""
        if self.exclusionAreasCheckBox.isChecked():
            self.exclusionAreasComboBox.setEnabled(True)
            self.exclusionAreasTextLabel.setEnabled(True)
            try:
                self._initComboBox(self.exclusionAreasComboBox,
                               (QgsMapLayer.VectorLayer, [QGis.WKBPolygon]))
            except AttributeError:
                pass
        else:
            self.exclusionAreasComboBox.clear()
            self.exclusionAreasComboBox.setEnabled(False)
            self.exclusionAreasTextLabel.setEnabled(False)

    def chooseOutputFolder(self):
        """Chooses the output folder with a QFileDialog
        """
        outputFolder = QtGui.QFileDialog.getExistingDirectory(self,
            u'Seleccione el directorio de salida',
            self.outputFolderToolButton.text())
        self.outputDirectory = os.path.join(outputFolder, 'salidas_FRD')
        if not os.path.exists(self.outputDirectory):
            os.makedirs(self.outputDirectory)
        if outputFolder:
            self.outputFolderLineEdit.setText(self.outputDirectory)

    def checkParameters(self, interactive_mode):
        """Check that input parameters are fine:

            dtm list contains at least one layer
            waypoints list contains at least one layer
            waypoints layer contains at least one line or two points
            the selected dtm and waypoint layer share the same CRS
            the scale of the dtm in both axes is the same

            Output is set
        """
        dtmLayerList = QgsMapLayerRegistry.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())
        if not dtmLayerList:
            self.showMessageBox(u"Error: ¡No se ha seleccionado un DTM!\n" +
                                u"Por favor seleccione uno.")
            return False
        if not interactive_mode:
            waypointsLayerList = QgsMapLayerRegistry.instance(
                    ).mapLayersByName(
                            self.waypointsLayerComboBox.currentText())
            if not waypointsLayerList:
                self.showMessageBox(
                        u"Error: ¡No se ha seleccionado ninguna capa con" +
                        u" los puntos de paso!\nPor favor seleccione una.")
                return False

        if self.exclusionAreasCheckBox.isChecked():
            exclusionAreasLayerList = QgsMapLayerRegistry.instance(
                    ).mapLayersByName(
                self.exclusionAreasComboBox.currentText())
            if not exclusionAreasLayerList \
                    and self.exclusionAreasCheckBox.isChecked():
                self.showMessageBox(
                        u"Error: ¡No se ha seleccionado ninguna capa con " +
                        u"las zonas de exclusion para el trazado!\nPor " +
                        u"favor seleccione una o desactive la opción.")
                return False

        if not self.outputFolderLineEdit.text():
            
            self.showMessageBox(
                    u"Error: ¡No se ha seleccionado directorio para" +
                    u" los resultados!, por favor seleccione uno")
            return False

        return True

    def main_parameters(self):
        """Connect the GUI parameters with processing parameters
        """
        return {
            "min_slope_pct": self.minSlopeDoubleSpinBox.value(),
            "max_slope_pct": self.maxSlopeDoubleSpinBox.value(),
            "semi_size": int(self.semiSizeDoubleSpinBox.value()),
            "penalty_factor_xy": self.penaltyFactorDoubleSpinBox.value(),
            "penalty_factor_z": self.slopePenaltyDoubleSpinBox.value()
            }

    def initRouteOptimization(self, interactive_mode):
        """Conect the process options and calls the optimizer module
        """
        if not self.outputFolderLineEdit.text():
            self.chooseOutputFolder()

        if not self.checkParameters(interactive_mode=interactive_mode):
            return False

        dtmLayer = QgsMapLayerRegistry.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())[0]

        if self.exclusionAreasCheckBox.isChecked():
            try:
                exclusionAreasLayer = \
                    QgsMapLayerRegistry.instance().mapLayersByName(
                        self.exclusionAreasComboBox.currentText())[0]
            except (ValueError, IndexError):
                exclusionAreasLayer = None
        else:
            exclusionAreasLayer = None
            
        try:
            ok, message = inputs_checker.check_layers(
                        dtmLayer,
                        None,
                        exclusionAreasLayer)
            if not ok:
                    raise ValueError(message)
            if interactive_mode == True:
                if not self.iface.mapCanvas().extent().intersects(
                        dtmLayer.extent()):
                    self.setCanvasExtent(dtmLayer)
                
            self.finder = optimizer_qgis.BestPathFinder(
                    dtmLayer, exclusionAreasLayer)
            self.finder.set_parameters(self.main_parameters())

        except ValueError as e:
            self.showMessageBox(unicode(e), u"Error del optimizador")
            self.showMessageBar(
                    u"Forest Road Designer: ha fallado la optimización",
                    u'Error', QgsMessageBar.WARNING)
            return False
        return True

    def processRouteOptimization(self):
        """This function manages the progressBar
        """
        iface.messageBar().clearWidgets()
        progressMessageBar = iface.messageBar()
        progress = QProgressBar()
        progress.setMaximum(100)
        progressMessageBar.pushWidget(progress)

        waypointsLayer = QgsMapLayerRegistry.instance().mapLayersByName(
                    self.waypointsLayerComboBox.currentText())[0]

        try:
            ok, message = inputs_checker.check_layers(
                        self.finder.dtm["layer"],
                        waypointsLayer,
                        self.finder.exclusion_areas["layer"])
            if not ok:
                    raise ValueError(message)
            waypoints = af.waypoints_list(waypointsLayer)
            for idx, point_coords in enumerate(waypoints):

                def updateProgress(value):
                    progress.setValue(max(0,
                            float(value)/(len(waypoints)-1)
                            + (idx-1)*100.0/(len(waypoints)-1)))
                    progress.repaint()
                self.finder.optimizer.progress_callback = updateProgress

                self.finder.add_segment_to(point_coords)
                for _ in range(10):
                    QgsApplication.instance().processEvents()
                self.finder.raw_layer.triggerRepaint()
                self.iface.mapCanvas().refresh()
                for _ in range(10):
                    QgsApplication.instance().processEvents()

        except ValueError as e:
            self.showMessageBox(unicode(e), u"Error del optimizador")
            
            self.showMessageBar(
                    u"Forest Road Designer: ha fallado la optimización", 
                    u"Error", QgsMessageBar.WARNING)
            return False
        return True

    def createRawRouteOptimization(self):
        """Creates the raw points layer and loads it into canvas
        """
        self.outputDirectory = self.outputFolderLineEdit.text()
        self.finder.set_output_folder(self.outputDirectory)
        self.raw_layer = self.finder.create_raw_output_layer()

        self.root = QgsProject.instance().layerTreeRoot()
        QgsMapLayerRegistry.instance().addMapLayers([self.raw_layer], False)
        for layer in [self.raw_layer]:
            self.root.insertLayer(0, layer)

        self.iface.mapCanvas().refresh()
    
    def remove_empty_raw_layer(self):
        """Removes the empity raw layer when process is not completed
        """
        QgsMapLayerRegistry.instance().removeMapLayer(self.raw_layer)
        
    def importSimplifiedRouteOptimization(self):
        """This function imports the simplified layer and loads it in the top
        position of QgisLayers. 
        """
        polylineThreshold = self.polylineThresholdDoubleSpinBox.value()
        simplified_layer = self.finder.create_simplified_output_layer(
                polylineThreshold)
        
        self.showMessageBar(u"Forest Road Designer: Simplificando...",
                            u"Info", QgsMessageBar.INFO, 20)
        
        self.output_layer = simplified_layer
        QgsMapLayerRegistry.instance().addMapLayers([simplified_layer], False)
        for layer in [simplified_layer]:
            self.root.insertLayer(0, layer)
        self.setCanvasExtent(simplified_layer)
        
        self.closeMessageBarWidgets()
        
        self.showMessageBar(u"Forest Road Designer ha finalizado el proceso",
                            u"Info", QgsMessageBar.INFO, 20)

    def launchRouteOptimization(self):
        """Launch batch route optimization using vector layer as input.
            Batch processing mode
        """
        self.showMessageBar(u"Forest Road Designer: procesando...")
        
        if not self.initRouteOptimization(interactive_mode=False):
            return False
        self.createRawRouteOptimization()
        if not self.processRouteOptimization():
            return False

        self.importSimplifiedRouteOptimization()

    def startInteractiveRouteOptimization(self):
        """Launch online/interactive route optimization using mouse input.
        """
        self.showMessageBar(
                u"Forest Road Designer: entrando en modo interactivo...")
        
        if not self.initRouteOptimization(interactive_mode=True):
            self.showMessageBar(
                    u"No se ha podido iniciar el modo interactivo.",
                    u'Error', QgsMessageBar.WARNING)
            return False

        self.createRawRouteOptimization()
        self._previously_active_tool = self.iface.mapCanvas().mapTool()
        self.interactive_mode = True
        interactive_tool = FRDInteractiveTool(self.iface.mapCanvas(),
                                   self.finder)
        interactive_tool.finished.connect(
                        self.stopInteractiveRouteOptimization)
        self.iface.mapCanvas().setMapTool(interactive_tool)
        self.updateDialog()
    
    def continueCancel_interactive_mode(self):
        """When user finished the interactive mode without finishing edition
        Also removes the empity raw layer
        """
        if self.raw_layer.featureCount() < 2:
            if self.raw_layer.featureCount() > 0:
                msg_selection = self.questionMessageBox((u'Es necesario dar' +
                                u' más de dos puntos a la ruta.\nPulse Ok' +
                                u' para seguir añadiendo puntos.\nPulse' +
                                u' Cancel para finalizar'), u'Mensaje')
            
                if not msg_selection == 'continue':
                    self.remove_empty_raw_layer()
                    self.stopInteractiveRouteOptimization(
                            simplify_raw_layer = False)
                else:
                    return

            else:
                self.remove_empty_raw_layer()
                self.stopInteractiveRouteOptimization(
                        simplify_raw_layer = False)

                return
                
        else:
            self.stopInteractiveRouteOptimization()
    
    def stopInteractiveRouteOptimization(self, simplify_raw_layer = True):
        """Clear the MapTool, imports the simplified layer when process
        is finished and updates the dialog
        """
        if self.interactive_mode:
            self.interactive_mode = False
            self.iface.mapCanvas().setMapTool(self._previously_active_tool)
            if simplify_raw_layer == True:
                self.importSimplifiedRouteOptimization()
            self.updateDialog()

    def setCanvasExtent(self, layer):
        """Set the canvas extent with the given layer extent
        """
        self.iface.mapCanvas().setExtent(layer.extent())
        self.iface.mapCanvas().refresh()
    
    def closeMessageBarWidgets(self):
        """Closes the all QgsMessages 
        """
        import time
        time.sleep(2)
        self.iface.messageBar().clearWidgets()
        
    def showMessageBar(self, message, msg_level= u'Info', 
                       Qgslevel=QgsMessageBar.INFO, msg_duration=0):
        """This function shows the messageBars with the given message text
        """
        self.iface.messageBar().pushMessage(msg_level, message, 
                             Qgslevel, msg_duration)
    
    def showMessageBox(self, message, msg_level = u'Error'):
        """This function shows the messageBoxes with the given message text
        """
        QMessageBox.warning(self, msg_level, message)
    
    def questionMessageBox(self, message, msg_level):
        """Define the messageBoxDialog Object and buttons
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText(message)
        msg.setWindowTitle(msg_level)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()
        if retval == QMessageBox.Ok:
            return u'continue'
        else:
            return u'finish'