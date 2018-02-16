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

from __future__ import unicode_literals

from qgis.core import (QgsSymbolV2, QgsRendererRangeV2, 
                       QgsGraduatedSymbolRendererV2)
from PyQt4 import QtGui, QtCore
import numpy as np

class AttributeLayerSymbology(QtCore.QObject):
    
    COLORS ={"outofbounds_2": QtGui.QColor(255,0,0), 
            "outofbounds_1": QtGui.QColor(200, 0, 0),
            "minallowedslope": QtGui.QColor(0, 255, 0),
            "zerominusslope": QtGui.QColor(0, 128, 0),
            "zeroslope": QtGui.QColor(255, 255, 255),
            "zeroplusslope": QtGui.QColor(0, 0, 128),
            "maxallowedslope": QtGui.QColor(0, 0, 255)}
        
    LINE_WIDTH_PIX = 1.5
    
    def __init__(self, layer, target_field,
                 max_allowed_value, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
                
        self.max_allowed_slope_p = max_allowed_value
        self.target_field = target_field        
        self.seminum_intervals = 5        
        self.top_lim= 1.20
        self.just_over_max_lim = 1.10
        self.setLayer(layer)
        
    def setLayer(self, layer):
        self._layer = layer
        if self._layer:
            self.updateSymbology()

    def _intervalValues(self, slopes=None):
        """Define intervalues for simbology
        """
        min_slope_p = min(slopes) if slopes else 0
        max_slope_p = max(slopes) if slopes else 0
        bottom_val_p = min(min_slope_p, 
                           -self.max_allowed_slope_p * self.top_lim)
        top_val_p = max(max_slope_p, self.max_allowed_slope_p * self.top_lim)
        just_under_min_val_p = (
                -self.max_allowed_slope_p * self.just_over_max_lim)
        just_over_max_val_p = (                
                self.max_allowed_slope_p * self.just_over_max_lim)
        
        intervals = [bottom_val_p, 
                    just_under_min_val_p]
        intervals.extend(np.linspace(-self.max_allowed_slope_p, 
                    self.max_allowed_slope_p, 
                    2 * self.seminum_intervals,
                    endpoint=True))
        
        intervals.extend([just_over_max_val_p,
                          top_val_p])
        return intervals
    
    @staticmethod
    def _colorRange(c_start, c_end, num):
        """Create a color range from c_start to c_end, both inclusive."""
        reds = np.linspace(c_start.red(), c_end.red(), num, endpoint=True)
        greens = np.linspace(
                c_start.green(), c_end.green(), num, endpoint=True)
        blues = np.linspace(c_start.blue(), c_end.blue(), num, endpoint=True)
        alphas = np.linspace(
                c_start.alpha(), c_end.alpha(), num, endpoint=True)
        
        colors = []
        for r, g, b, a in zip(reds, greens, blues, alphas):
            colors.append(QtGui.QColor(r, g, b, a))
        return colors
    
    def _colorValues(self):
        """Color values for a given number of intervals."""
        colors = [self.COLORS["outofbounds_2"],
                  self.COLORS["outofbounds_1"]]
        
        colors.extend(self._colorRange(self.COLORS["minallowedslope"],
                                       self.COLORS["zerominusslope"],
                                       self.seminum_intervals-1))
        
        colors.append(self.COLORS["zeroslope"])
        
        colors.extend(self._colorRange(self.COLORS["zeroplusslope"],
                                       self.COLORS["maxallowedslope"],
                                       self.seminum_intervals-1))
                
        colors.extend([self.COLORS["outofbounds_1"],
                      self.COLORS["outofbounds_2"]])
        return colors
    
    def updateSymbology(self):
        if self._layer and self._layer.isValid():
            att_values = [f[self.target_field] for f in self._layer.dataProvider().getFeatures()]
            
            intervs = self._intervalValues(att_values)
            colors = self._colorValues()
            range_list = []
            for v_min, v_max, col in zip(intervs[:-1], intervs[1:], colors):                
                symbol = QgsSymbolV2.defaultSymbol(self._layer.geometryType())
                symbol.setColor(col)
                symbol.setWidth(self.LINE_WIDTH_PIX)
                label = '{:0.2f}%->{:0.2f}%'.format(v_min, v_max)
                range_ = QgsRendererRangeV2(v_min, v_max, symbol, label)
                range_list.append(range_)
    
            renderer = QgsGraduatedSymbolRendererV2('', range_list)
            renderer.setMode(QgsGraduatedSymbolRendererV2.Custom)
            renderer.setClassAttribute(self.target_field)
            self._layer.setRendererV2(renderer)
            self._layer.triggerRepaint()