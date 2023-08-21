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

import os
import math
import logging
# logger = logging.getLogger("frd")
# logger.setLevel(logging.DEBUG)

import webbrowser
from pathlib import Path

from osgeo import gdal
from qgis.core import (QgsApplication, QgsMapLayer, QgsWkbTypes, QgsProject,
    Qgis, QgsUnitTypes)
from qgis.utils import iface

from qgis.PyQt import QtWidgets, QtGui, uic, QtCore
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox, QProgressBar
try:
    from . import optimizer_qgis
    from .frd_utils import array_funs as af
    from .frd_utils import inputs_checker
    from .frd_interactive_tool import FRDInteractiveTool
    from . import frd_profiles
except ImportError:
    import optimizer_qgis
    from frd_utils import array_funs as af
    from frd_utils import inputs_checker
    from frd_interactive_tool import FRDInteractiveTool
    import frd_profiles
try:
    from . import version
except ImportError:
    class version(object):
        VERSION = "devel"
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'forest_road_designer_dockwidget_base.ui'), resource_suffix='')

BASEPATH = os.path.dirname(os.path.realpath(__file__))
DOC_PATH = 'documentation'

        
def create_loging_file():
    """Crear y configura un fichero logger de registro
    """
    base_dir = os.path.join(os.path.dirname(__file__), 'logs')
    base_dir_path = Path(base_dir)
    base_dir_path.mkdir(exist_ok=True)
    log_filename = str(os.path.join(base_dir, 'logfile.log'))
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    print(f'log_filename FILE {log_filename} ')
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.DEBUG,   # Nivel de los eventos que se registran en el logger
        filename=log_filename,  # Fichero de  logs
        format=log_format      # Formato de registro
        )
    
logger = logging.getLogger("frd")
logger.setLevel(logging.DEBUG)



class ForestRoadDesignerDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

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
        self.basic_mode = True
        self.dtm_size = 1

        
        self.advanced_parameters_checkBox.clicked.connect(self.updateAdvancedCheckBox)
        self.basic_parameters_checkBox.clicked.connect(self.updateBasicCheckBox)

        self.basic_parameters_checkBox.setChecked(True)

        self.manual_help_pushButton.clicked.connect(self.read_help_manual)
        
        self.updateInteractiveWidgetTab()

        self.closeMessageBarWidgets()
        self.exclusionAreasCheckBox.setChecked(False)
        self.exclusionAreasComboBox.setEnabled(False)
        self.exclusionAreasTextLabel.setEnabled(False)
        self.activateRoadOptionsCheckBox.setChecked(False)
        self.updateRoadOptions()
        # self.waypointsLayerLabel.setEnabled(False)
        # self.waypointsLayerComboBox.setEnabled(False)
        self.stopInteractivePushButton.setEnabled(False)
        self.cancelProcessPushButton.setEnabled(False)
        self._updateMetersLabels()
        self.dtmLayerComboBox.currentIndexChanged.connect(
                self._updateMetersLabels)
        self.exclusionAreasCheckBox.clicked.connect(
                self.initExclusionAreasLayer)
        self.outputFolderToolButton.clicked.connect(self.chooseOutputFolder)
        self.startProcessPushButton.clicked.connect(
                    self.startInteractiveRouteOptimization)
        self.startBatchPushButton.clicked.connect(
                    self.launchRouteOptimization)
        self.stopInteractivePushButton.clicked.connect(
                    self.continueCancel_interactive_mode)
        self.maxSlopeDoubleSpinBox.valueChanged.connect(
                self._updateMaxSlopeDegreesValue)
        self.minSlopeDoubleSpinBox.valueChanged.connect(
                self._updateMinSlopeDegreesValue)
        self._updateMaxSlopeDegreesValue()
        self._updateMinSlopeDegreesValue()
        self._updateRadiusPenaltyFactor()
        self.minRadioDoubleSpinBox.valueChanged.connect(self._updateRadiusPenaltyFactor)        
        self.activateRoadOptionsCheckBox.clicked.connect(self.updateRoadOptions)
        self._updateCutPercentLabel()
        self._updateFillPercentLabel()        
        self.cutVerticalSpinBox.valueChanged.connect(self._updateCutPercentLabel)
        self.cutHorizontalSpinBox.valueChanged.connect(self._updateCutPercentLabel)
        self.fillVerticalSpinBox.valueChanged.connect(self._updateFillPercentLabel)
        self.fillHorizontalSpinBox.valueChanged.connect(self._updateFillPercentLabel)
        
        self.vehicle_profile_help_pushButton.clicked.connect(self._show_vehicle_profile_help)
        self.slope_direction_profile_help_pushButton.clicked.connect(self._show_slope_direction_profile_help)
        self.penalty_factor_profile_help_pushButton.clicked.connect(self._show_penalty_factor_profile_help)

        self.semiSizeDoubleSpinBox.valueChanged.connect(
                self._updateSemiSizeDoubleSpinBoxColor)
        self.minRadioDoubleSpinBox.valueChanged.connect(
                self._updateSemiSizeDoubleSpinBoxColor)

        self.semiSizeDoubleSpinBox.valueChanged.connect(
                self._updateMetersLabels)
        self.polylineThresholdDoubleSpinBox.valueChanged.connect(
                self._updateMetersLabels)

        self.slopeInteractiveDoubleSpinBox.valueChanged.connect(self.update_interactive_parameters)
        self.lenghtInteractiveDoubleSpinBox.valueChanged.connect(self.update_interactive_parameters)

        self.infoRadiusPushButton.clicked.connect(self.show_radius_info_visible_tab)
        self.closeRadiusInfoTabPushButton.clicked.connect(self.hide_radius_info_visible_tab)
        
        self.cancelProcessPushButton.clicked.connect(self.cancelProcess)
        # When a new layer is added/removed, update the comboboxes
        QgsProject.instance().layerWasAdded.connect(self.initLayers)
        QgsProject.instance().layersRemoved.connect(self.initLayers)
        self._initVersion()
        self.initLayers()
        self.update_interactive_parameters()
        self.updateBasicAdvancedTabs()
        self.updateNonInteractiveDialog(True)

        create_loging_file() 
        logger.info("--- START LOGGING ---")
        
    #DAVID Not in use
    # def launchProcess(self):
    #     if self.batchProcessCheckBox.isChecked():
    #         # Llamar a funcion por lotes
    #         self.launchRouteOptimization()
    #     else:
    #         # Llamar a funcion interactiva
    #         self.startInteractiveRouteOptimization()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def _initVersion(self):
        self.frdVersionLabel.setText("Forest Road Designer {}".format(
                version.VERSION))

    def _initComboBox(self, comboBox, layerType):
        """Init the value of Dtm layer QComboBox with loaded layers in Qgis
        interface.
        """
        loadedLayers = QgsProject.instance().mapLayers()
        checkType = lambda lyr, lt: lyr.type()==lt[0] and (
                lt[1] == "all" or lyr.wkbType() in lt[1])

        layerList = [
            layer.name() for layer in list(loadedLayers.values())
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
        minValue = self.minSlopeDoubleSpinBox.value()

        if maxValue < minValue:
            self.maxSlopeDoubleSpinBox.setValue(minValue)

        self.minSlopeDoubleSpinBox.setMinimum(0.0)
        self.minSlopeDoubleSpinBox.setMaximum(59998.0)
        self.maxSlopeDoubleSpinBox.setMinimum(2.0)
        self.maxSlopeDoubleSpinBox.setMaximum(60000.0)          

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
        maxValue = self.maxSlopeDoubleSpinBox.value()
        minValue = self.minSlopeDoubleSpinBox.value()

        if minValue > maxValue:
            self.minSlopeDoubleSpinBox.setValue(maxValue)

        self.minSlopeDoubleSpinBox.setMinimum(0.0)
        self.minSlopeDoubleSpinBox.setMaximum(59998.0)
        self.maxSlopeDoubleSpinBox.setMinimum(2.0)
        self.maxSlopeDoubleSpinBox.setMaximum(60000.0)         

        self._updateMinSlopeDegreesLabel(minValue)

    def _updateMinSlopeDegreesLabel(self, minValue=None):
        """Update the label with min slope in degrees according to value in
        pct."""

        min_slope_degrees = math.degrees(math.atan(
                minValue / 100.0))
        self.minSlopeDegreesLabel.setText("{:.2f}°".format(min_slope_degrees))    

    def _updateRadiusPenaltyFactor(self):
        """update radius penalty factor box"""
        if self.minRadioDoubleSpinBox.value() > 0:
            self.radFactorDoubleSpinBox.setEnabled(True)            
        else:
            self.radFactorDoubleSpinBox.setEnabled(False)

    def _updateSemiSizeDoubleSpinBoxColor(self):
        if self.minRadioDoubleSpinBox.value() <= self.semiSizeDoubleSpinBox.value():
            self.semiSizeDoubleSpinBox.setStyleSheet("background-color: #f0f0f0; color: black;")
        else:
            self.semiSizeDoubleSpinBox.setStyleSheet("background-color: mistyrose; color: darkred;")

    def _updateCutPercentLabel(self):
        """Update the label with cut percent"""
        cutPercent = math.degrees(math.atan((self.cutVerticalSpinBox.value()) /
                self.cutHorizontalSpinBox.value()))
        self.cutPercentLabel.setText("{:.2f} º".format(cutPercent))

    def _updateFillPercentLabel(self):
        """Update the label with cut percent"""
        fillPercent = math.degrees(math.atan((self.fillVerticalSpinBox.value()) /
                self.fillHorizontalSpinBox.value()))
        self.fillPercentLabel.setText("{:.2f} º".format(fillPercent))

    def _updateMetersLabels(self, semiSizeValue=None):
        """Update the label with the pixels number according the value in
        SemiSizeDoubleSpinBox"""
        semiSizeValue = int(self.semiSizeDoubleSpinBox.value())
        dtmLayerList = QgsProject.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())
        self.dtmMapUnit = "" #initialize dtmMapUnit
        self._updateSpinboxSuffix(self.dtmMapUnit)
        if dtmLayerList == []:
            # self.semiSizeMetersLabel.setText("")
            self.polylineErrorMetersLabel.setText("(-)")
        else:
            dtm_layer = dtmLayerList[0]
            raster = gdal.Open(dtm_layer.source())
            self.dtmMapUnit = self._updateMapUnits(dtm_layer) 
            try:
                raster.GetGeoTransform()
                geotransform = raster.GetGeoTransform()
                dtm_pixel_size = geotransform[1]
                self.dtm_size = dtm_pixel_size
                semi_size_m = int((semiSizeValue-1) * dtm_pixel_size)
                poly_error_m = (self.polylineThresholdDoubleSpinBox.value()
                                * dtm_pixel_size)
                # self.semiSizeMetersLabel.setText(f"({semi_size_m}{self.dtmMapUnit})")
                self.polylineErrorMetersLabel.setText("({:.1f}{}\xb2)".format(poly_error_m, self.dtmMapUnit))

                self._updateSpinboxSuffix(self.dtmMapUnit)

            except AttributeError:
                # self.semiSizeMetersLabel.setText("")
                self.polylineErrorMetersLabel.setText("(-)")

    def _updateMapUnits(self, dtmLayer):
        """ returns metric unit from the layer"""
        
        if dtmLayer.isValid():
            # dtmLayer is a QgsRasterLayer
            crs = dtmLayer.crs()
            # crs is a QgsCoordinateReferenceSystem 
            unit = crs.mapUnits()
            s_unit = QgsUnitTypes.toAbbreviatedString(unit)
        else:
            s_unit =""
        return s_unit
    
    def _updateSpinboxSuffix(self, suffix):
        """ update suffix of several SpinBoxes"""
        self.penaltyFactorDoubleSpinBox.setSuffix( "{}/180º".format(suffix))
        self.slopePenaltyDoubleSpinBox.setSuffix("{}/cambio máximo pendiente".format(suffix))
        self.wRoadDoubleSpinBox.setSuffix(" {}".format(suffix))
        self.minRadioDoubleSpinBox.setSuffix(" {}".format(suffix))
        self.semiSizeDoubleSpinBox.setSuffix(" {}".format(suffix))
        self.lenghtInteractiveDoubleSpinBox.setSuffix(" {}".format(suffix))

    def updateBasicCheckBox(self):
        """Update the checkboxes for advanced or basic mode."""
        self.basic_parameters_checkBox.setChecked(True)
        self.advanced_parameters_checkBox.setChecked(False)
        self.basic_mode = True
        self.updateBasicAdvancedTabs() 

    def updateAdvancedCheckBox(self):
        """Update the checkboxes for advanced or basic mode."""
        self.advanced_parameters_checkBox.setChecked(True)
        self.basic_parameters_checkBox.setChecked(False)
        self.basic_mode = False
        self.updateBasicAdvancedTabs()

    def updateBasicAdvancedTabs(self):
        """Update the enabled/disabled tabs for advanced or basic mode."""

        if self.basic_parameters_checkBox.isChecked():
            self.tabWidget.setTabVisible(0,True)
            self.tabWidget.setTabVisible(1,False)
            self.tabWidget.setTabVisible(2,False)
            self.tabWidget.setTabVisible(3,False)
            self.tabWidget.setTabVisible(4,False)
            self.tabWidget.setTabVisible(5,False)
        
        else:
            self.tabWidget.setTabVisible(0,False)
            self.tabWidget.setTabVisible(1,True)
            self.tabWidget.setTabVisible(2,True)
            self.tabWidget.setTabVisible(3,True)
            self.tabWidget.setTabVisible(4,True)
            self.tabWidget.setTabVisible(5,False)


    def updateInteractiveWidgetTab(self):
        """Update the interactive_mode_tabWidget for batch or interactive mode."""
        self.interactive_mode_tabWidget.setCurrentIndex(0)        
        self.interactive_mode = True

    def updateNoneInteractiveWidgetTab(self):
        """Update the interactive_mode_tabWidget for batch or interactive mode."""
        self.interactive_mode_tabWidget.setCurrentIndex(1)        
        self.interactive_mode = False    

    def updateDialog(self):
        """Update the enabled/disabled widgets according to interactive mode.
        """
        # Elements disabled during interactive mode

        self.dtmLabel.setEnabled(not self.interactive_mode)
        self.dtmLayerComboBox.setEnabled(not self.interactive_mode)

        self.outputFolderLabel.setEnabled(not self.interactive_mode)
        self.outputFolderLineEdit.setEnabled(not self.interactive_mode)
        self.outputFolderToolButton.setEnabled(not self.interactive_mode)

        self.exclusionAreasCheckBox.setEnabled(not self.interactive_mode)
        self.exclusionAreasTextLabel.setEnabled(not self.interactive_mode)
        self.exclusionAreasComboBox.setEnabled(not self.interactive_mode)

        # self.designParametersGroupBox.setEnabled(not self.interactive_mode)
        self.design_parameter_label.setEnabled(not self.interactive_mode)
        self.basic_parameters_checkBox.setEnabled(not self.interactive_mode)
        self.advanced_parameters_checkBox.setEnabled(not self.interactive_mode)
        # self.interactive_mode_tab.setEnabled(self.interactive_mode)
        self.profiles_tab.setEnabled(not self.interactive_mode)
        self.basic_tab.setEnabled(not self.interactive_mode)
        self.cutfill_tab.setEnabled(not self.interactive_mode)
        self.direction_tab.setEnabled(not self.interactive_mode)
        self.optimization_tab.setEnabled(not self.interactive_mode)

        self.stopInteractivePushButton.setEnabled(self.interactive_mode)
        self.non_interactive_mode_tab.setEnabled(not self.interactive_mode)
        self.startProcessPushButton.setEnabled(not self.interactive_mode)
        self.cancelProcessPushButton.setEnabled(self.interactive_mode)
        self.updateDialogBatchProcess()
    
    def updateNonInteractiveDialog(self, active):
        """Update the enabled/disabled widgets according to interactive mode.
        """
        # Elements disabled during interactive mode

        self.dtmLabel.setEnabled(active)
        self.dtmLayerComboBox.setEnabled(active)

        self.outputFolderLabel.setEnabled(active)
        self.outputFolderLineEdit.setEnabled(active)
        self.outputFolderToolButton.setEnabled(active)

        self.exclusionAreasCheckBox.setEnabled(active)
        self.exclusionAreasTextLabel.setEnabled(active)
        self.exclusionAreasComboBox.setEnabled(active)

        self.interactive_mode_tab.setEnabled(active)
        self.designParametersGroupBox.setEnabled(active)

        self.basic_parameters_checkBox.setEnabled(active)
        self.advanced_parameters_checkBox.setEnabled(active)
        self.design_parameter_label.setEnabled(active)

        self.waypointsLayerComboBox.setEnabled(active)
        self.waypointsLayerLabel.setEnabled(active)
        self.startBatchPushButton.setEnabled(active)
        self.batch_processing_status_label.setStyleSheet("color: green")
        if not active:
            self.batch_processing_status_label.setText("PROCESANDO")            
        else:
            self.batch_processing_status_label.setText("")

    def updateDialogBatchProcess(self):
        """Update the GUI if batch process is selected
        """
        self.batch_process = self.non_interactive_mode_tab.isEnabled()

        self.waypointsLayerComboBox.setEnabled(self.batch_process)
        self.waypointsLayerLabel.setEnabled(self.batch_process)

    def updateRoadOptions(self):
        """Update the GUI if cut/fill checkBox is selected
        """
        if self.activateRoadOptionsCheckBox.isChecked():
            self.wRoadDoubleSpinBox.setEnabled(True)
            self.cutVerticalSpinBox.setEnabled(True)
            self.cutHorizontalSpinBox.setEnabled(True)
            self.cutHmaxDoubleSpinBox.setEnabled(True)
            self.fillVerticalSpinBox.setEnabled(True)
            self.fillHorizontalSpinBox.setEnabled(True)
            self.fillHmaxDoubleSpinBox.setEnabled(True)
            self.cutFillFactorDoubleSpinBox.setEnabled(True)
        else:
            self.wRoadDoubleSpinBox.setEnabled(False)
            self.cutVerticalSpinBox.setEnabled(False)
            self.cutHorizontalSpinBox.setEnabled(False)
            self.cutHmaxDoubleSpinBox.setEnabled(False)
            self.fillVerticalSpinBox.setEnabled(False)
            self.fillHorizontalSpinBox.setEnabled(False)
            self.fillHmaxDoubleSpinBox.setEnabled(False)
            self.cutFillFactorDoubleSpinBox.setEnabled(False)
    
    def initLayers(self):
        """Init the three input layers that intervenes in the process"""
        self.initDtmLayer()
        self.initWaypointLayer()
        self.initExclusionAreasLayer()

    def initDtmLayer(self):
        """Init the value of Dtm layer QComboBox with loaded layers in Qgis
        interface."""
        try:
            self._initComboBox(self.dtmLayerComboBox,
                               (QgsMapLayer.RasterLayer, "all"))
        except AttributeError:
            # Sometimes we get a NoneType has no attribute RasterLayer (?)
            pass

    def initWaypointLayer(self):
        """Init the value of Waypoint layers in QComboBox with loaded
        layers in Qgis interface."""
        try:
            self._initComboBox(
                    self.waypointsLayerComboBox,
                    (QgsMapLayer.VectorLayer, [QgsWkbTypes.LineString,
                                               QgsWkbTypes.MultiLineString]))
        except AttributeError:
            # Sometimes we get a NoneType has no attribute VectorLayer (?)
            pass

    def initExclusionAreasLayer(self):
        """Init the value of Waypoint layers in QComboBox with loaded layers
        in Qgis interface."""
        if self.exclusionAreasCheckBox.isChecked():
            self.exclusionAreasComboBox.setEnabled(True)
            self.exclusionAreasTextLabel.setEnabled(True)
            try:
                self._initComboBox(self.exclusionAreasComboBox,
                               (QgsMapLayer.VectorLayer,
                                [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon]))
            except AttributeError:
                # Sometimes we get a NoneType has no attribute VectorLayer (?)
                pass
        else:
            self.exclusionAreasComboBox.clear()
            self.exclusionAreasComboBox.setEnabled(False)
            self.exclusionAreasTextLabel.setEnabled(False)

    def chooseOutputFolder(self):
        outputFolder = QtWidgets.QFileDialog.getExistingDirectory(self,
            'Seleccione el directorio de salida',
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
        dtmLayerList = QgsProject.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())
        if not dtmLayerList:
            self.showMessageBox("Error: ¡No se ha seleccionado un DTM!\n" +
                                "Por favor seleccione uno.")
            return False
        if not interactive_mode:
            waypointsLayerList = QgsProject.instance(
                    ).mapLayersByName(
                            self.waypointsLayerComboBox.currentText())
            if not waypointsLayerList:
                self.showMessageBox(
                        "Error: ¡No se ha seleccionado ninguna capa con" +
                        " los puntos de paso!\nPor favor seleccione una.")
                return False

        if self.exclusionAreasCheckBox.isChecked():
            exclusionAreasLayerList = QgsProject.instance(
                    ).mapLayersByName(
                self.exclusionAreasComboBox.currentText())
            if not exclusionAreasLayerList \
                    and self.exclusionAreasCheckBox.isChecked():
                self.showMessageBox(
                        "Error: ¡No se ha seleccionado ninguna capa con " +
                        "las zonas de exclusion para el trazado!\nPor " +
                        "favor seleccione una o desactive la opción.")
                return False        

        if not self.outputFolderLineEdit.text():

            self.showMessageBox(
                    "Error: ¡No se ha seleccionado directorio para" +
                    " los resultados!, por favor seleccione uno")
            return False

        if self.basic_mode: #we don't need to go any furter
            return True
        
        checkStar = self.checkStarRadius()
        if not checkStar:
            return False

        if self.activateRoadOptionsCheckBox.isChecked() :
            if (self.cutVerticalSpinBox.value() == 0 or
                    self.fillVerticalSpinBox.value() == 0 or
                    self.cutHmaxDoubleSpinBox.value() == 0.0 or
                    self.fillHmaxDoubleSpinBox.value() == 0.0 or
                    self.wRoadDoubleSpinBox.value() == 0.0):

                self.showMessageBox(
                    "Error: ¡Error en las opciones de pista!" +
                    "Por favor revise los valores o desactive la opción" )
                return False

        return True

    def checkInteractiveParameters(self, interactive_mode):
        """Check that input parameters are fine:

            dtm list contains at least one layer
            waypoints list contains at least one layer
            waypoints layer contains at least one line or two points
            the selected dtm and waypoint layer share the same CRS
            the scale of the dtm in both axes is the same

            Output is set

        """
        dtmLayerList = QgsProject.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())
        if not dtmLayerList:
            self.showMessageBox("Error: ¡No se ha seleccionado un DTM!\n" +
                                "Por favor seleccione uno.")
            return False
        
        if self.exclusionAreasCheckBox.isChecked():
            exclusionAreasLayerList = QgsProject.instance(
                    ).mapLayersByName(
                self.exclusionAreasComboBox.currentText())
            if not exclusionAreasLayerList \
                    and self.exclusionAreasCheckBox.isChecked():
                self.showMessageBox(
                        "Error: ¡No se ha seleccionado ninguna capa con " +
                        "las zonas de exclusion para el trazado!\nPor " +
                        "favor seleccione una o desactive la opción.")
                return False        

        if not self.outputFolderLineEdit.text():

            self.showMessageBox(
                    "Error: ¡No se ha seleccionado directorio para" +
                    " los resultados!, por favor seleccione uno")
            return False

        return True


    def main_parameters(self):
        cut_angle_tan = self.cutVerticalSpinBox.value() / self.cutHorizontalSpinBox.value()
        fill_angle_tan = self.fillVerticalSpinBox.value() / self.fillHorizontalSpinBox.value()
        semi_size = self.semiSizeDoubleSpinBox.value() / self.dtm_size
        parameters = {
                "min_slope_pct": self.minSlopeDoubleSpinBox.value(),
                "max_slope_pct": self.maxSlopeDoubleSpinBox.value(),
                "semi_size": semi_size,
                "penalty_factor_xy": self.penaltyFactorDoubleSpinBox.value(),
                "penalty_factor_z": self.slopePenaltyDoubleSpinBox.value(),
                "activated_road_options": self.activateRoadOptionsCheckBox.isChecked(),
                "cut_angle_tan": cut_angle_tan,            
                "fill_angle_tan": fill_angle_tan,
                "cut_hmax_m": self.cutHmaxDoubleSpinBox.value(),
                "fill_hmax_m": self.fillHmaxDoubleSpinBox.value(),
                "min_curve_radio_m": self.minRadioDoubleSpinBox.value(),
                "w_road_m": self.wRoadDoubleSpinBox.value(),
                "slope_penalty_factor": self.slopeFactorDoubleSpinBox.value(),
                "radius_penalty_factor": self.radFactorDoubleSpinBox.value(),
                "cutfill_penalty_factor": self.cutFillFactorDoubleSpinBox.value() 
        }  
        return parameters
    
    def interactive_main_parameters(self):
        
        semi_size = self.semiSizeDoubleSpinBox.value() / self.dtm_size
        parameters = {
                "inter_slope_pct": self.slopeInteractiveDoubleSpinBox.value(),
                "inter_length": self.lenghtInteractiveDoubleSpinBox.value(),                
        }
        print(f"interactive_main_parameters {parameters} ")  
        return parameters

    def update_interactive_parameters(self):
        
        parameters = self.interactive_main_parameters()
        inter_hight = parameters["inter_length"] * (parameters["inter_slope_pct"]/100)
        str_inter_hight_m = " {:.2f} {}".format(inter_hight, self.dtmMapUnit)
        self.interactiveSlopeLabel.setText(str_inter_hight_m)        
        if self.finder is not None and type(self.finder) == optimizer_qgis.BestInteractivePathFinder:
            print(f"FINDER {type(self.finder)}")
            self.finder.set_parameters(parameters)

    def initRouteOptimization(self, interactive_mode):

        if not self.outputFolderLineEdit.text():
            self.chooseOutputFolder()

        if not self.checkParameters(interactive_mode=interactive_mode):
            return False

        dtmLayer = QgsProject.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())[0]

        if self.exclusionAreasCheckBox.isChecked():
            try:
                exclusionAreasLayer = \
                    QgsProject.instance().mapLayersByName(
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
            self.showMessageBox(str(e), "Error del optimizador")
            self.showMessageBar(
                    "Forest Road Designer: ha fallado la optimización",
                    'Error', Qgis.Warning)
            return False
        return True

    def processRouteOptimization(self):

        iface.messageBar().clearWidgets()
        progressMessageBar = iface.messageBar()
        progress = QProgressBar()
        #Maximum is set to 100, making it easy to work with percentage of completion
        progress.setMaximum(100)
        #pass the progress bar to the message Bar
        progressMessageBar.pushWidget(progress)


        waypointsLayer = QgsProject.instance().mapLayersByName(
                    self.waypointsLayerComboBox.currentText())[0]

        try:
            ok, message = inputs_checker.check_layers(
                        self.finder.dtm["layer"],
                        waypointsLayer,
                        self.finder.exclusion_areas["layer"])
            if not ok:
                    raise ValueError(message)
            # Process line point by point:
            waypoints = af.waypoints_list(waypointsLayer)
            for idx, point_coords in enumerate(waypoints):

                def updateProgress(value, current_best_path_index=None):
                    # Take the fact that there are different semgents into
                    # account, Value set by finder goes from to 0 to 100 for
                    # each new segment.
                    progress.setValue(max(0,
                            float(value)/(len(waypoints)-1)
                            + (idx-1)*100.0/(len(waypoints)-1)))
                    progress.repaint()
                    if current_best_path_index:
                        # print(current_best_path)
                        # self.finder.raw_layer.setPoints(current_best_waypoints)
                        self.finder._update_output_layer(current_best_path_index)                        
                        self.iface.mapCanvas().refresh()
                        for _ in range(1000):
                            QgsApplication.instance().processEvents()
                self.finder.optimizer.progress_callback = updateProgress

                self.finder.add_segment_to(point_coords)
                # force update of gui, not nice but multithreading on python
                # would not get it much better.
                for _ in range(10):
                    QgsApplication.instance().processEvents()
                self.finder.raw_layer.triggerRepaint()
                self.iface.mapCanvas().refresh()
                for _ in range(10):
                    QgsApplication.instance().processEvents()

        except ValueError as e:
            self.showMessageBox(str(e), "Error del optimizador")

            self.showMessageBar(
                    "Forest Road Designer: ha fallado la optimización",
                    "Error", Qgis.Warning)
            return False
        return True

    def createRawRouteOptimization(self):
        self.outputDirectory = self.outputFolderLineEdit.text()
        self.finder.set_output_folder(self.outputDirectory)
        self.raw_layer = self.finder.create_raw_output_layer()
        self.root = QgsProject.instance().layerTreeRoot()
        QgsProject.instance().addMapLayers([self.raw_layer], False)
        for layer in [self.raw_layer]:
            self.root.insertLayer(0, layer)
        
        self.iface.mapCanvas().refresh()

    def remove_empty_raw_layer(self):
        QgsProject.instance().removeMapLayer(self.raw_layer)

    def importSimplifiedRouteOptimization(self):

        polylineThreshold = self.polylineThresholdDoubleSpinBox.value()
        simplified_layer, summary_layer = self.finder.create_simplified_output_layer(
                polylineThreshold)

        self.showMessageBar("Forest Road Designer: Simplificando...",
                            "Info", Qgis.Info, 20)

        self.output_layer = simplified_layer
        QgsProject.instance().addMapLayers([simplified_layer], False)
        for layer in [simplified_layer]:
            self.root.insertLayer(0, layer)
        self.setCanvasExtent(simplified_layer)

        return summary_layer       

    def launchRouteOptimization(self):
        """Launch batch route optimization using vector layer as input.
            Batch processing mode
        """
        self.showMessageBar("Forest Road Designer: procesando...")
        num_options = 1
        params = {}
        msg = ""
        
        try:
            logger.info("--- NONE INTERACTIVE MODE --- START ---")
            if self.basic_mode:
                frd_profile, num_options = self.set_frd_profile()
            self.interactive_mode = False
            self.updateNonInteractiveDialog(False)        

            for option in range(num_options):
                if num_options > 1:
                    params = self.params_frd_profile(frd_profile, option)
                else:
                    params = self.main_parameters()

                if not self.initProfileRouteOptimization(params, interactive_mode=False):
                    self.updateNonInteractiveDialog(True)
                    return False
                self.createRawRouteOptimization()
                if not self.processRouteOptimization():
                    self.updateNonInteractiveDialog(True)
                    return False
            
                # self.importSimplifiedRouteOptimization()
                summary_layer = self.importSimplifiedRouteOptimization()
                msg = msg + self.create_sumary_message_profile(summary_layer)

            self.profileMensagge("resultado obtenido", summary_layer, msg )
            self.updateNonInteractiveDialog(True)
            logger.info("--- NONE INTERACTIVE MODE --- DONE ---")
        except RuntimeError as rte:
            self.updateNonInteractiveDialog(True)
            logger.error(f"ERROR TYPE {type(rte)}")
            logger.error(f"ERROR ARGS {rte.args}")
            logger.error(f"ERROR {str(rte)}")
        except Exception as ex:
            logger.error(f"ERROR TYPE {type(ex)}")
            logger.error(f"ERROR ARGS {ex.args}")
            logger.error(f"ERROR {str(ex)}")


    def startInteractiveRouteOptimization2(self):
        """Launch online/interactive route optimization using mouse input.
        """
        self.updateAdvancedCheckBox()
        information_msg = "Modo interactivo"
        interactive_msg = ('Se aplicarán los valores de los parámetros de diseño avanzados\n' +
                        'Se han desactivado las opciones de radio de giro y desmonte/terraplén\n' +
                        'Para detener el proceso pulse Cancelar. Para continuar pulse Aceptar')
        msg_selection = self.questionMessageBox(interactive_msg, information_msg )
        if not msg_selection == 'continue':
            return False
        self.showMessageBar(
                "Forest Road Designer: entrando en modo interactivo...")
        params = self.main_parameters()
        # if not self.initRouteOptimization(interactive_mode=True):
        if not self.initProfileRouteOptimization(params, interactive_mode=True):
            self.showMessageBar(
                    "No se ha podido iniciar el modo interactivo.",
                    'Error', Qgis.Warning)
            return False

        self.createRawRouteOptimization()
        # Disable interface elements
        self._previously_active_tool = self.iface.mapCanvas().mapTool()
        self.interactive_mode = True
        interactive_tool = FRDInteractiveTool(self.iface.mapCanvas(),
                                   self.finder)
        interactive_tool.finished.connect(
                        self.stopInteractiveRouteOptimization)
        self.iface.mapCanvas().setMapTool(interactive_tool)
        self.updateDialog()
        # set map tool

    def startInteractiveRouteOptimization(self):
        """Launch online/interactive route optimization using mouse input.
        """
        # self.updateAdvancedCheckBox()
        # information_msg = "Modo interactivo"
        # interactive_msg = ('Se aplicarán los valores de los parámetros de diseño avanzados\n' +
        #                 'Se han desactivado las opciones de radio de giro y desmonte/terraplén\n' +
        #                 'Para detener el proceso pulse Cancelar. Para continuar pulse Aceptar')
        # msg_selection = self.questionMessageBox(interactive_msg, information_msg )
        # if not msg_selection == 'continue':
        #     return False
        self.showMessageBar(
                "Forest Road Designer: entrando en modo interactivo...")
        # params = self.main_parameters()
        # if not self.initRouteOptimization(interactive_mode=True):
        try:
            logger.info("--- INTERACTIVE MODE --- START ---")
            params = self.interactive_main_parameters()
            if not self.initInteractiveRouteOptimization(params, interactive_mode=True):
                self.showMessageBar(
                    "No se ha podido iniciar el modo interactivo.",
                    'Error', Qgis.Warning)
                return False

            self.createRawRouteOptimization()
            # Disable interface elements
            self._previously_active_tool = self.iface.mapCanvas().mapTool()
            self.interactive_mode = True
            interactive_tool = FRDInteractiveTool(self.iface.mapCanvas(),
                                   self.finder)
            # interactive_tool.finished.connect(
            #                 self.stopInteractiveRouteOptimization)
            interactive_tool.finished.connect(
                        self.activateContinue_button)
            self.iface.mapCanvas().setMapTool(interactive_tool)
            self.updateDialog()

        except Exception as ex:
            logger.error(f"ERROR TYPE {type(ex)}")
            logger.error(f"ERROR ARGS {ex.args}")
            logger.error(f"ERROR {str(ex)}")

    def activateContinue_button(self):
        if self.interactive_mode:
            self.startProcessPushButton.setEnabled(True)
            self.startProcessPushButton.setText("Continuar Proceso")
            self.startProcessPushButton.clicked.disconnect(self.startInteractiveRouteOptimization)
            self.startProcessPushButton.clicked.connect(self.continueInteractiveRouteOptimization)
            print("activateContinue_button")
    
    def deactivateContinue_button(self):
        if self.interactive_mode:
            
            self.startProcessPushButton.setText("Iniciar el proceso de diseño")
            self.startProcessPushButton.clicked.disconnect(self.continueInteractiveRouteOptimization)
            self.startProcessPushButton.clicked.connect(self.startInteractiveRouteOptimization)
            self.startProcessPushButton.setEnabled(False)
        
    def continueInteractiveRouteOptimization(self):
        if self.interactive_mode:
            interactive_tool = FRDInteractiveTool(self.iface.mapCanvas(), self.finder)
            self.iface.mapCanvas().setMapTool(interactive_tool)
            interactive_tool.finished.connect(
                        self.activateContinue_button)
            interactive_tool.activate()                     
            self.deactivateContinue_button()


    def continueCancel_interactive_mode(self):
        print(f"self.raw_layer.featureCount() {self.raw_layer.featureCount()}")
        if self.raw_layer.featureCount() < 1:
            
            msg_selection = self.questionMessageBox(('Es necesario dar' +
                            ' al menos dos puntos a la ruta.\nPulse Ok' +
                            ' para seguir añadiendo puntos.\nPulse' +
                            ' Cancel para finalizar'), 'Mensaje')

            if not msg_selection == 'continue':
                self.remove_empty_raw_layer()
                self.stopInteractiveRouteOptimization(
                        simplify_raw_layer = False)
                self.closeMessageBarWidgets()
            else:
                return

        # else:
        #     self.remove_empty_raw_layer()
        #     self.stopInteractiveRouteOptimization(
        #                 simplify_raw_layer = False)
        #     self.closeMessageBarWidgets()
        #     return

        else:
            self.stopInteractiveRouteOptimization()
            self.closeMessageBarWidgets()

    def cancelProcess(self):
        msg_selection = self.questionMessageBox(('Ha pulsado cancelar el proceso.\nSe perderán' +
                                'los datos obtenidos hasta ahora. \nPulse Aceptar' +
                                ' para cancelar el proceso.\nPulse' +
                                ' Cancelar para continuar'), 'Mensaje')
        if msg_selection == 'continue':
            self.remove_empty_raw_layer()
            self.stopInteractiveRouteOptimization(simplify_raw_layer = False)
            self.closeMessageBarWidgets()
        else:
            return

    def stopInteractiveRouteOptimization(self, simplify_raw_layer = True):
        try:
            if self.interactive_mode:
                self.interactive_mode = False
                self.iface.mapCanvas().setMapTool(self._previously_active_tool)
                interactive_tool = FRDInteractiveTool(self.iface.mapCanvas(),
                                   self.finder)
                interactive_tool.delete_Points()
                interactive_tool.delete_Rubberbands()
                if simplify_raw_layer == True:
                    summary_layer = self.importSimplifiedRouteOptimization()        
                    # msg = self.create_sumary_message_profile(summary_layer)
                    msg = self.interactive_create_sumary_message_profile(summary_layer)
                    self.profileMensagge("modo interactivo", summary_layer, msg )
                # self.interactive_mode = False
                # Enable interface elements
            
                self.updateDialog()
                logger.info("--- INTERACTIVE MODE --- FINISH ---")
        except Exception as ex:
            logger.error(f"ERROR TYPE {type(ex)}")
            logger.error(f"ERROR ARGS {ex.args}")
            logger.error(f"ERROR {str(ex)}")


    def setCanvasExtent(self, layer):
        """Set the canvas extent with the given layer extent
        """
        self.iface.mapCanvas().setExtent(layer.extent())
        self.iface.mapCanvas().refresh()

    def closeMessageBarWidgets(self):
        import time
        time.sleep(2)
        self.iface.messageBar().clearWidgets()

    def showMessageBar(self, message, msg_level= 'Info',
                       Qgslevel=Qgis.Info, msg_duration=0):
        """This function shows the messageBars with the given message text
        """
        self.iface.messageBar().pushMessage(msg_level, message,
                             Qgslevel, msg_duration)

    def showMessageBox(self, message, msg_level = 'Error'):
        """This function shows the messageBoxes with the given message text
        """
        QMessageBox.warning(self, msg_level, message)

    def showInformationMessageBox(self, message, msg_information ):
        """This function shows the messageBoxes with the given message text
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle(msg_information)
        msg.setStandardButtons(QMessageBox.Ok)   
        retval = msg.exec_()      

    def questionMessageBox(self, message, msg_level):
       msg = QMessageBox()
       msg.setIcon(QMessageBox.Question)
       msg.setText(message)
       msg.setWindowTitle(msg_level)
       msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
       retval = msg.exec_()
       if retval == QMessageBox.Ok:
           return 'continue'
       else:
           return 'finish'
    def create_sumary_message(self, summary_dic):
        """Create a message to show the sumay results"""
       
        msg_gen = """    Distancia origen-destino {:.2f}{}
    Distancia recorrido total {:.2f}{}
    Desnivel neto {:.2f}{}
    Desnivel acumulado {:.2f}{}
    Desnivel medio neto {:.2f}{}
    Desnivel medio acumulado {:.2f}{}
    Número penalizaciones pendiente {}""".format(
                    summary_dic["straight_distance"], self.dtmMapUnit,
                    summary_dic["total_cumsum"], self.dtmMapUnit,
                    summary_dic["raw_slope"], self.dtmMapUnit,
                    summary_dic["total_acumulative_slope"], self.dtmMapUnit,
                    summary_dic["average_slope"], self.dtmMapUnit,
                    summary_dic["average_acum_slope"], self.dtmMapUnit,                    
                    summary_dic["total_slope_pen"]
                )

        msg_radius = """\n   Número penalizaciones radio {}""".format(
                    summary_dic["total_rad_pen"]) if self.minRadioDoubleSpinBox.value() > 0 else ""

        msg_cutfill = """\n   Número penalizaciones desmonte/terraplén {}""".format(
                    summary_dic["tota_cutfill_pen"]) if self.activateRoadOptionsCheckBox.isChecked() else "" 

        msg = msg_gen + msg_radius + msg_cutfill

        return msg

    def initProfileRouteOptimization(self, parameters, interactive_mode,):

        if not self.outputFolderLineEdit.text():
            self.chooseOutputFolder()

        if not self.checkParameters(interactive_mode=interactive_mode):
            return False

        dtmLayer = QgsProject.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())[0]

        if self.exclusionAreasCheckBox.isChecked():
            try:
                exclusionAreasLayer = \
                    QgsProject.instance().mapLayersByName(
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
            # raise ValueError(parameters)
            self.finder.set_parameters(parameters)            

        except ValueError as e:
            self.showMessageBox(str(e), "Error del optimizador")
            self.showMessageBar(
                    "Forest Road Designer: ha fallado la optimización",
                    'Error', Qgis.Warning)
            return False
        return True
    
    def initInteractiveRouteOptimization(self, parameters, interactive_mode,):

        if not self.outputFolderLineEdit.text():
            self.chooseOutputFolder()

        if not self.checkInteractiveParameters(interactive_mode=interactive_mode):
            return False

        dtmLayer = QgsProject.instance().mapLayersByName(
                self.dtmLayerComboBox.currentText())[0]

        if self.exclusionAreasCheckBox.isChecked():
            try:
                exclusionAreasLayer = \
                    QgsProject.instance().mapLayersByName(
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

            # self.finder = optimizer_qgis.BestPathFinder(
            #         dtmLayer, exclusionAreasLayer)
            self.finder = optimizer_qgis.BestInteractivePathFinder(
                    dtmLayer, exclusionAreasLayer)
            # raise ValueError(parameters)
            self.finder.set_parameters(parameters)            

        except ValueError as e:
            self.showMessageBox(str(e), "Error del optimizador")
            self.showMessageBar(
                    "Forest Road Designer: ha fallado la optimización",
                    'Error', Qgis.Warning)
            return False
        return True


    def profileMensagge(self,mode_msg,summary_layer, msg):

        self.closeMessageBarWidgets()
        self.showMessageBar("summary_layer {}".format(summary_layer),
                            "Info", Qgis.Info, 20)
        
        self.closeMessageBarWidgets()

        self.showMessageBar("Forest Road Designer ha finalizado el proceso",
                            "Info", Qgis.Info, 20)       
        head_msg = self.head_summary_message(summary_layer)
        # summary_msg = self.create_sumary_message(summary_layer)
        summary_msg = head_msg + '\n' + msg
        information_msg = mode_msg
        self.showInformationMessageBox(summary_msg, information_msg )

    def set_frd_profile(self):
        vehicle_profile = self.vehicle_profile_comboBox.currentIndex()
        directon_profile = self.slope_direction_profile_comboBox.currentIndex()
        penalty_profile = self.penalty_factor_profile_label_comboBox.currentIndex()
        frd_profile = frd_profiles.frd_profiles(vehicle_profile, directon_profile, penalty_profile, self.dtm_size)
        num_options = frd_profile.num_options
        return frd_profile, num_options

    def params_frd_profile(self, frd_profile, option):
        frd_profile.slope_radius_params(option)
        frd_profile.direc_params()
        frd_profile.penalty_params()

        return frd_profile.params

    def _show_vehicle_profile_help(self):
        """Create a message to show the vehicle profile parameters"""
        information_msg = """Parámetros """ + self.vehicle_profile_comboBox.currentText()
        profile, option = self.set_frd_profile()
        params = self.params_frd_profile(profile, 0)
        semi_s = 2 * params["semi_size"]
        msg = """Radio mínimo de giro {:.2f}{} \nTamaño mínimo de segmento {}{} \nPendiente mínima {:.2f}% \n\n """.format(params["min_curve_radio_m"], self.dtmMapUnit, semi_s, self.dtmMapUnit, params["min_slope_pct"])
        msg += """ Resultado 1\n Pendiente máxima {:.2f}%\n """.format(params["max_slope_pct"])
        for op in range(1,option):
            param = self.params_frd_profile(profile, op)
            msg += """ Resultado {} \nPendiente máxima {:.2f}%\n """.format(op+1, params["max_slope_pct"])
        
        self.showInformationMessageBox(msg, information_msg )
        return msg, information_msg

    def _show_slope_direction_profile_help(self):
        """Create a message to show the slope_direction profile parameters"""
        information_msg = """Parámetros """ + self.slope_direction_profile_comboBox.currentText()
        profile, option = self.set_frd_profile()
        params = self.params_frd_profile(profile, 0)        
        msg = """Penalización cambio de dirección {}{}/180º \nPenalización cambio de rasante {}{}/cambio máximo pendiente """.format(params["penalty_factor_xy"], self.dtmMapUnit, params["penalty_factor_z"], self.dtmMapUnit)
                
        self.showInformationMessageBox(msg, information_msg )
        return msg, information_msg

    def _show_penalty_factor_profile_help(self):
        """Create a message to show the penalty_factor profile parameters"""
        information_msg = """Parámetros """ + self.penalty_factor_profile_label_comboBox.currentText()
        profile, option = self.set_frd_profile()
        params = self.params_frd_profile(profile, 0)        
        msg = """Factor de pendiente {} \nFactor de radio {} """.format(params["slope_penalty_factor"], params["radius_penalty_factor"])
                
        self.showInformationMessageBox(msg, information_msg )
        return msg, information_msg

    def checkStarRadius(self):
        if self.minRadioDoubleSpinBox.value() > self.semiSizeDoubleSpinBox.value():
            msg_selection = self.questionMessageBox(('El radio de giro es mayor \n' +
                                    'que la longitud de segmento mínima.\n' +
                                    'Puede producir un resultado de poca utilidad . \nPulse OK' +
                                    ' para continuar el proceso.\nPulse' +
                                    ' Cancel para finalizar'), 'Mensaje')
            if not msg_selection == 'continue':
                self.tabWidget.setCurrentIndex(4)
                self.semiSizeDoubleSpinBox.setFocus()            
                self.closeMessageBarWidgets()
                return False
            else:
                return True
        else:
            return True

    def head_summary_message(self, summary_dic):
        """Create a message to show the sumay results"""
       
        msg_head = """    Distancia origen-destino: {:.2f} {}
    Desnivel neto: {:.2f} {}""".format(
                    summary_dic["straight_distance"], self.dtmMapUnit,
                    summary_dic["raw_slope"], self.dtmMapUnit,)

        return msg_head

    def create_sumary_message_profile(self, summary_dic):
        """Create a message to show the sumay results"""
       
        msg_gen = """ 
    Distancia recorrido total: {:.2f} {}
    Desnivel acumulado: {:.2f}{}
    Desnivel acumulado medio: {:.2f} {}
    Número penalizaciones pendiente: {}""".format(
                    summary_dic["total_cumsum"], self.dtmMapUnit,
                    summary_dic["total_acumulative_slope"], self.dtmMapUnit,
                    summary_dic["average_acum_slope"], self.dtmMapUnit,                    
                    summary_dic["total_slope_pen"]
                )

        msg_radius = """\n   Número penalizaciones radio: {}""".format(
                    summary_dic["total_rad_pen"]) if (self.minRadioDoubleSpinBox.value() > 0 or self.basic_mode) else ""

        msg_cutfill = """\n   Número penalizaciones desmonte/terraplén: {}""".format(
                    summary_dic["tota_cutfill_pen"]) if (self.activateRoadOptionsCheckBox.isChecked() and not self.basic_mode) else "" 

        msg_twist_number = """\n   Número de giros: {}""".format(
                    summary_dic["twist_number"])

        msg_track_quality = """\n   Indice de calidad de trazado: {:.2f}""".format(
                    summary_dic["track_quality"])

        msg = msg_gen + msg_radius + msg_cutfill + msg_twist_number + msg_track_quality + '\n'

        return msg

    def read_help_manual(self):
        "open help manual .pdf"
        new_path = Path(BASEPATH, DOC_PATH)
        filelist = sorted(new_path.glob('*frd_manual*.pdf'))
        webbrowser.open_new_tab(filelist[0])
        return
    
    def interactive_create_sumary_message_profile(self, summary_dic):
        """Create a message to show the sumay results"""
       
        msg_gen = """ 
    Distancia recorrido total: {:.2f} {}
    Desnivel acumulado: {:.2f} {}
    Desnivel acumulado medio: {:.2f} {}
    """.format(
                    summary_dic["total_cumsum"], self.dtmMapUnit,
                    summary_dic["total_acumulative_slope"], self.dtmMapUnit,
                    summary_dic["average_acum_slope"], self.dtmMapUnit,
                )
        
        msg_twist_number = """\n   Número de giros: {}""".format(
                    summary_dic["twist_number"])

        msg_track_quality = """\n   Indice de calidad de trazado: {:.2f}""".format(
                    summary_dic["track_quality"])

        msg = msg_gen + msg_twist_number + msg_track_quality + '\n'

        return msg
    
    def show_radius_info_visible_tab(self):
        self.radius_info(True)

    def hide_radius_info_visible_tab(self):
        self.radius_info(False)

    def radius_info(self, active):                     
        self.tabWidget.setTabVisible(0,False)
        self.tabWidget.setTabVisible(1,not active)
        self.tabWidget.setTabVisible(2,not active)
        self.tabWidget.setTabVisible(3,not active)
        self.tabWidget.setTabVisible(4,not active)
        self.tabWidget.setTabVisible(5,active)
        if not active:
            self.tabWidget.setCurrentIndex(1)       
