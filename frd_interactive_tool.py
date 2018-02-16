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

from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QCursor, QPixmap, QMessageBox  
from qgis.gui import QgsMapTool

class FRDInteractiveTool(QgsMapTool):

    finished = pyqtSignal()

    def __init__(self, canvas, finder, max_dist_m=100):
        QgsMapTool.__init__(self, canvas)
        self.finder = finder        
                
        self.mCtrl = None
        self.max_dist_m = max_dist_m
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

    def canvasPressEvent(self, event):
        pass    

    def canvasMoveEvent(self, event):
        pass

    def addVertex(self, pos):
        
        if self.finder.raw_layer is None:
            return
        
        point = self.toLayerCoordinates(self.finder.raw_layer, pos)
        point_type_list = [point.x(), point.y()]
        try:
            if self.mCtrl:       
                self.finder.add_segment_to(point_type_list, 
                                           force=True)
            else:          
                self.finder.add_segment_to(point_type_list, 
                                           max_dist_m = self.max_dist_m)
        except ValueError as e:
            QMessageBox.warning(None, unicode('Error'), unicode(e))
            
    def canvasReleaseEvent(self, event):            

        if event.button() == Qt.LeftButton:
           self.addVertex(event.pos())
        elif event.button() == Qt.RightButton:
           self.finder.remove_last_segment()

    def showSettingsWarning(self):
        pass

    def activate(self):
        self._old_cursor = self.canvas().cursor()
        self.canvas().setCursor(self.cursor)      

    def deactivate(self):
        self.finder = None
        self.canvas().setCursor(self._old_cursor)
        self.finished.emit()
        
    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True