# -*- coding: utf-8 -*-
"""
Created on Mon May 08 16:09:44 2017

@author: Javier
"""



from matplotlib.pyplot import colormaps
from numpy.lib.function_base import hamming
from qgis.core import *
from qgis.PyQt import QtGui, QtCore
import numpy as np
import logging

class AttributeLayerSymbology(QtCore.QObject):
    
    COLORS ={# really out of bounds
            "outofbounds_2": QtGui.QColor(255,0,0), 
            # out of bounds, close to the max
            "outofbounds_1": QtGui.QColor(200, 0, 0),
            "minallowedslope": QtGui.QColor(0, 255, 0),
            "zerominusslope": QtGui.QColor(0, 128, 0),
            "zeroslope": QtGui.QColor(255, 255, 255),
            "zeroplusslope": QtGui.QColor(0, 255, 255),
            "maxallowedslope": QtGui.QColor(0, 0, 255),
            "minallowedslope_minusslope": QtGui.QColor(200, 255, 240),
            "minallowedslope_zerominusslope": QtGui.QColor(230, 255, 240),
            "minallowedslope_zeroplusslope": QtGui.QColor(230, 240, 255),
            "minallowedslope_plusslope": QtGui.QColor(200, 240, 255),
            "minallowedradius": QtGui.QColor(100,0,100),
            "zeroradius": QtGui.QColor(200,0,200),
            "zerocutfill": QtGui.QColor(255,150,0),
            "hundredcutfill": QtGui.QColor(255,70,0),
            "outcutfill": QtGui.QColor(255,50,0),
            "color_blank_interval":QtGui.QColor(0,0,0)}

    LINE_WIDTH_PIX = 1.5

    PARAMS = {
            "radius": 10000,
            "cutfill": 1E+12 }
    
    SEMINUM_INTERVALS = 5
    
    def __init__(self, layer, target_field, target_field_radius, target_field_penalties,
                target_field_cutfill, target_field_height_cutfill, target_field_cutfill_pen,    
                min_allowed_value, max_allowed_value, min_allowed_radius_value, activated_road_options, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
                
        self.max_allowed_slope_p = max_allowed_value
        self.min_allowed_slope_p = min_allowed_value
        self.target_field = target_field
        
        self.min_allowed_radius_m = min_allowed_radius_value
        self.target_field_radius = target_field_radius
        self.param_rad = self.PARAMS["radius"]

        self.target_field_cutfill = target_field_cutfill
        self.target_field_height_cutfill = target_field_height_cutfill        
        self.target_field_cutfill_pen = target_field_cutfill_pen
        self.activated_road_options = activated_road_options        
        self.param_cutfill = self.PARAMS["cutfill"]

        self.target_field_penalties = target_field_penalties
        self.seminum_intervals = 5
        
        #Default last interval 1.20*slope_max
        self.top_lim= 1.20
        #Default over the max interval equals 1.10*slope_max
        self.just_over_max_lim = 1.10        
        self.setLayer(layer)
        
        
    def setLayer(self, layer):
        self._layer = layer
        if self._layer:
            self.updateSymbology()

    
    def _intervalValues(self, slopes=None):
        
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
    
    def _intervalValues_minSlope(self, slopes=None):
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
                    -self.min_allowed_slope_p, 
                    self.seminum_intervals,
                    endpoint=True))
        intervals.extend(np.linspace(-self.min_allowed_slope_p,
                    self.min_allowed_slope_p, 
                    int(self.seminum_intervals / 2) * 2 + 1,
                    endpoint=True)[1:-1])
        intervals.extend(np.linspace(self.min_allowed_slope_p,
                    self.max_allowed_slope_p, 
                    self.seminum_intervals,
                    endpoint=True))

        intervals.extend([just_over_max_val_p,
                          top_val_p])
        
        return intervals

    def _intervalValues_radius(self, param):
        intervals=[]
        intervals.extend(np.linspace(0,
                        100,
                        self.seminum_intervals+1,
                        endpoint=True )*param)
        return intervals 


    def _intervalValues_cutfill(self, cutfill_pen, param):
        intervals = []
        max_cutfill_pen = max(cutfill_pen) if cutfill_pen else 0
        intervals.extend(np.linspace(0,
                        100,
                        self.seminum_intervals+1,
                        endpoint=True )*param)
        if max_cutfill_pen > 100:
            intervals.append(max_cutfill_pen*100*param)
        return intervals 


    def _intervalValues_tot(self, slopes=None, radius_pen=None, cutfill_pen=None, param_rad=0, param_cutfill=0):

        if self.min_allowed_slope_p > 0:
            intervals = self._intervalValues_minSlope(slopes)
        else:
            intervals = self._intervalValues(slopes)
        if self.min_allowed_radius_m:
            intervals.extend(self._intervalValues_radius(param_rad))
        
        if self.activated_road_options:
            intervals.extend(self._intervalValues_cutfill(cutfill_pen, param_cutfill))
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
            colors.append(QtGui.QColor(round(r), round(g), round(b),round(a)))
        return colors
    
    def _colorValues(self):
        """Color values for a given number of intervals."""
        colors = [self.COLORS["outofbounds_2"],
                  self.COLORS["outofbounds_1"]]

        colors.extend(self._colorRange(self.COLORS["zerominusslope"],
                                       self.COLORS["minallowedslope"],
                                       self.seminum_intervals-1))
        
        colors.append(self.COLORS["zeroslope"])
        
        colors.extend(self._colorRange(self.COLORS["zeroplusslope"],
                                       self.COLORS["maxallowedslope"],
                                       self.seminum_intervals-1))
                
        colors.extend([self.COLORS["outofbounds_1"],
                      self.COLORS["outofbounds_2"]])
        return colors
    
    def _colorValues_MinSlope(self):
        """Color values for a given number of intervals."""

        colors = [self.COLORS["outofbounds_2"],
                  self.COLORS["outofbounds_1"]]
        
        colors.extend(self._colorRange(self.COLORS["zerominusslope"],
                                       self.COLORS["minallowedslope"],
                                       self.seminum_intervals-1))
        
        colors.extend(self._colorRange(self.COLORS["minallowedslope_minusslope"],
                                       self.COLORS["minallowedslope_zerominusslope"],
                                       int(self.seminum_intervals /2)))

        ##colors.append(self.COLORS["zeroslope"])

        colors.extend(self._colorRange(self.COLORS["minallowedslope_zeroplusslope"],
                                       self.COLORS["minallowedslope_plusslope"],
                                       int(self.seminum_intervals /2)))

        colors.extend(self._colorRange(self.COLORS["zeroplusslope"],
                                       self.COLORS["maxallowedslope"],
                                       self.seminum_intervals-1))
                
        colors.extend([self.COLORS["outofbounds_1"],
                      self.COLORS["outofbounds_2"]])
        # logging.info('COLORS..{}'.format(len(colors)))
        return colors

    def _colorValues_rad(self):

        colors=[]
        colors.extend(self._colorRange(self.COLORS["zeroradius"],
                                       self.COLORS["minallowedradius"],                                      
                                       self.seminum_intervals))
        return colors


    def _colorValues_cutfill(self):

        colors=[]
        colors.extend(self._colorRange(self.COLORS["zerocutfill"],
                                       self.COLORS["hundredcutfill"],                                      
                                       self.seminum_intervals+1))
        colors.append(self.COLORS["outcutfill"])                               
        return colors


    def _colorValues_tot(self):
        colors = []
        if self.min_allowed_slope_p > 0:
            colors = self._colorValues_MinSlope()
        else:
            colors = self._colorValues()

        if self.min_allowed_radius_m:
            colors.append(self.COLORS["color_blank_interval"])
            colors.extend(self._colorValues_rad())
            colors.append(self.COLORS["color_blank_interval"])
            
        if self.activated_road_options:
            colors.extend(self._colorValues_cutfill())
        return colors


    def updateSymbology(self):
        if self._layer and self._layer.isValid():
            att_values = [f[self.target_field] for f in self._layer.dataProvider().getFeatures()]
            
            att_values_rad = [f[self.target_field_radius] for f in self._layer.dataProvider().getFeatures()]
            att_values_cutfill= [f[self.target_field_cutfill_pen] for f in self._layer.dataProvider().getFeatures()]
            intervs = self._intervalValues_tot( att_values, att_values_rad, att_values_cutfill, self.param_rad, self.param_cutfill)
            colors = self._colorValues_tot()
            range_list = []
            for v_min, v_max, col in zip(intervs[:-1], intervs[1:], colors[:-1]):
                if col==self.COLORS["color_blank_interval"]:
                    continue
                symbol = QgsSymbol.defaultSymbol(self._layer.geometryType())
                symbol.setColor(col)
                symbol.setWidth(self.LINE_WIDTH_PIX)
                # mySymbol1.setAlpha(myOpacity) set by color?
                if v_max < self.param_rad/self.seminum_intervals:
                    label = '{:0.2f}%->{:0.2f}%'.format(v_min, v_max)
                elif v_max < self.param_cutfill/self.seminum_intervals:
                    v_lab_min =  v_min/(self.param_rad)
                    v_lab_max =  v_max/(self.param_rad)
                    label = '{:0.2f}%'.format(v_lab_min) + u'\u2264' + ' dif rad < {:0.2f}%'.format( v_lab_max)
                else:
                    v_lab_min_ct =  v_min/self.param_cutfill
                    v_lab_max_ct =  v_max/self.param_cutfill
                    label = '{:0.2f}%'.format(v_lab_min_ct) +'< dif cut/fill ' + u'\u2264' + ' {:0.2f}%'.format( v_lab_max_ct)
                range_ = QgsRendererRange(v_min, v_max, symbol, label)
                range_list.append(range_)

            renderer = QgsGraduatedSymbolRenderer('', range_list)
            renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
            renderer.setClassAttribute(self.target_field_penalties)
            self._layer.setRenderer(renderer)
            # QgsMapLayerRegistry.instance().addMapLayer(myVectorLayer)
            self._layer.triggerRepaint()

class InteractiveAttributeLayerSymbology(QtCore.QObject):

    COLORS ={"simple_color": QtGui.QColor(0,0,255), 
            }

    LINE_WIDTH_PIX = 1.5

    def __init__(self, layer, target_field, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)                
        
        self.target_field = target_field
                
        #Default last interval 1.20*slope_max
        self.top_lim= 1.20
        #Default over the max interval equals 1.10*slope_max
        self.just_over_max_lim = 1.10        
        self.setLayer(layer)
        
        
    def setLayer(self, layer):
        self._layer = layer
        if self._layer:
            self.updateSymbology()

    
    def updateSymbology(self):
        if self._layer and self._layer.isValid():

            att_values = [f[self.target_field] for f in self._layer.dataProvider().getFeatures()]

            symbol = QgsSymbol.defaultSymbol(self._layer.geometryType())
            symbol.setColor(self.COLORS["simple_color"])
            symbol.setWidth(self.LINE_WIDTH_PIX)
            self._layer.renderer().setSymbol(symbol)
            self._layer.triggerRepaint()
