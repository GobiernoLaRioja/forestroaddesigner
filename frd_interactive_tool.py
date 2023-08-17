# -*- coding: utf-8 -*-
"""
Forest Road Designer - Interactive tool

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QCursor, QPixmap
from qgis.PyQt.QtWidgets import QMessageBox, QApplication
from qgis.core import Qgis, QgsPoint, QgsPointXY, QgsWkbTypes
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand
from PyQt5.QtGui import QColorConstants, QPen


class FRDInteractiveTool(QgsMapTool):

    finished = pyqtSignal()

    def __init__(self, canvas, finder, max_dist_m=100):
        super().__init__(canvas)
        self.finder = finder

                # create and setup the rubber band to display the line
        self.rubberBand = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)  
        self.rubberBand.setColor(QColorConstants.Green)
        self.rubberBand.setWidth(1)
        self.start_point = None
        self.mCtrl = None
        self.max_dist_m = max_dist_m
        self.goal_result = None

        #our own fancy cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                       "      c None",
                                       ".     c #FF0000",
                                       "+     c #faed55",
                                       "                ",
                                       "       +.+      ",
                                       "      ++.++     ",
                                       "     +.....+    ",
                                       "    +.  .  .+   ",
                                       "   +..  .  ..+  ",
                                       "  +.  . . .  .+ ",
                                       " ++.    .    .++",
                                       " ... ...+... ...",
                                       " ++.    .    .++",
                                       "  +.  . . .  .+ ",
                                       "   +..  .  ..+  ",
                                       "   ++.  .  .+   ",
                                       "    ++.....+    ",
                                       "      ++.++     ",
                                       "       +.+      "]))
        self.ctrl_cursor = QCursor(QPixmap(["16 16 3 1",
                                       "      c None",
                                       ".     c #0000FF",
                                       "+     c #55edfa",
                                       "                ",
                                       "       +.+      ",
                                       "      ++.++     ",
                                       "     +.....+    ",
                                       "    +.  .  .+   ",
                                       "   +..  .  ..+  ",
                                       "  +.  . . .  .+ ",
                                       " ++.    .    .++",
                                       " ... ...+... ...",
                                       " ++.    .    .++",
                                       "  +.  . . .  .+ ",
                                       "   +..  .  ..+  ",
                                       "   ++.  .  .+   ",
                                       "    ++.....+    ",
                                       "      ++.++     ",
                                       "       +.+      "]))

        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True
            self.canvas().setCursor(self.ctrl_cursor)


    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False
            self.canvas().setCursor(self.cursor)

    #DAVID
    def addVertex2(self, pos):
        if self.finder.raw_layer is None:
            return
        
        point = self.toLayerCoordinates(self.finder.raw_layer, pos)
        point_type_list = [point.x(), point.y()]
        try:
            if self.mCtrl:
                # finder.go_to(point, force_straight=True)            
                self.finder.add_segment_to(point_type_list, 
                                           force=True)
            else:
                # TODO: point coordinates vs pointMap??            
                self.finder.add_segment_to(point_type_list, 
                                           max_dist_m = self.max_dist_m)
        except ValueError as e:
            QMessageBox.warning(None, str('Error'), str(e))

    
    def addVertex(self, pos):
        if self.finder.raw_layer is None:
            return
        
        point = self.toLayerCoordinates(self.finder.raw_layer, pos)
        point_type_list = [point.x(), point.y()]
        # print(f"MODO INTERACTIVO addVertex {point_type_list}")
        # print(f"MODO INTERACTIVO addVertex {self.finder.parameters}")
        try:
            if self.mCtrl:
                # finder.go_to(point, force_straight=True)            
                self.finder.add_segment_to(point_type_list, 
                                           force=True)
            else:
                # TODO: point coordinates vs pointMap??            
                self.finder.add_segment_to(point_type_list)
        except ValueError as e:
            QMessageBox.warning(None, str('Error'), str(e))

    def showLine(self, start, pos):
        if start is not None:                        
            end = self.toLayerCoordinates(self.finder.raw_layer, pos)
            end_type_list = [end.x(), end.y()]
            goal_result, up_down = self.finder.search_segment_to(end_type_list)
            # print("----------")
            # print(f"SHAW LINE START {start} TYPE {type(start)} END {end} GOAL {goal_result} TYPE {type(goal_result)}")
            if goal_result is not None:
                self.rubberBandColor(up_down)
                self.draw_Line(start, goal_result)
            else:
                self.delete_Line()

    def rubberBandColor(self, up_down = True):
        if up_down:
            self.rubberBand.setColor(QColorConstants.Green)
        else:
            self.rubberBand.setColor(QColorConstants.Magenta)

    def canvasReleaseEvent(self, event):            
        if event.button() == Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                self.mCtrl = True
            else:
                self.mCtrl = False
            self.addVertex(event.pos())
            self.draw_Point()
            self.delete_Line()
            # self.draw_Line(event)
        elif event.button() == Qt.RightButton:
            # print(f"self.finder.raw_layer {self.finder.raw_layer}")
            if self.finder.raw_layer is None:
                return
            self.finder.remove_last_segment()
            self.draw_Point()
        try:
            start = self.finder.raw_path_coords_last_point
            self.showLine( start, event.pos())
        except:
            print("----------")
            print(f"EXCEPT")
            pass
        

    def canvasMoveEvent(self, event):
        try:
            start = self.finder.raw_path_coords_last_point
        except:
            start = None
        if start is not None:            
            self.showLine(start, event.pos())
       

    def draw_Point(self):
        self.delete_Points()
        if self.finder.raw_path_coords_last_point is not None:
            point = self.finder.raw_path_coords_last_point
            # print(f"DRAW POINT {point}")
            vertex_marker = QgsVertexMarker(self.canvas())
            vertex_marker.setCenter(QgsPointXY(point[0], point[1]))
            vertex_marker.setColor(QColorConstants.Green)
            vertex_marker.setIconSize(7)
            vertex_marker.setIconType(QgsVertexMarker.ICON_BOX)  # ICON_BOX, ICON_CROSS, ICON_X
            vertex_marker.setPenWidth(2)
            self.start_point = point
        else:
            self.delete_Line()

    def delete_Points(self):
        vertex_items = [ i for i in self.canvas().scene().items() if issubclass(type(i), QgsVertexMarker)]
        for ver in vertex_items:
            if ver in self.canvas().scene().items():
                self.canvas().scene().removeItem(ver)

    def draw_Line(self, start, end):
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        self.rubberBand.addPoint(QgsPointXY(start[0], start[1]))
        self.rubberBand.addPoint(QgsPointXY(end[0], end[1]))
        self.rubberBand.show()

    def delete_Line(self):
        try:
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        except:
            pass
    
    def delete_Rubberbands(self):
        rubber_items = [ i for i in self.canvas().scene().items() if issubclass(type(i), QgsRubberBand)]
        for rub in rubber_items:
            if rub in self.canvas().scene().items():
                self.canvas().scene().removeItem(rub)
   
    def check_point_pos(self, goal_coords):
        """Check that the target point is not out of the map and that it does not 
        lie within an exclusion zone."""

        if not self.dtm['layer'].extent().contains(
                QgsPointXY(goal_coords[0], goal_coords[-1])):
            print(f'check_point_pos Point at {goal_coords} not in DTM.')
            self.activate()

        if self.exclusion_areas["layer"]:
            if self.optimizer._waypoints_index == []:
                for elem in self.exclusion_areas[
                        "layer"].dataProvider().getFeatures():
                    if elem.geometry().contains(
                            QgsPointXY(goal_coords[0], goal_coords[-1])):
                        print(f'check_point_pos Point at {goal_coords} lies within the exclusion zone!!!! Avoiding.')
                        self.activate()
                    else:
                        print(f'Point at {goal_coords} OK.')

    def getFinder(self):
        return self.finder

    def showSettingsWarning(self):
        pass

    def activate(self):
        super().activate()
        print("ACTIVATE")
        self._old_cursor = self.canvas().cursor()
        self.canvas().setCursor(self.cursor)
        # Check whether Geometry is a Line or a Polygon 
            

    def deactivate(self):
        # self.finder = None
        print("DEACTIVATE")
        self.delete_Line()
        self.canvas().setCursor(self._old_cursor)
        self.finished.emit()
        

    def isZoomTool(self):
        return False


    def isTransient(self):
        return False


    def isEditTool(self):
        return True


    def flags(self):
        return QgsMapTool.EditTool