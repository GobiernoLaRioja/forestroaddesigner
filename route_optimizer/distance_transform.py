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

Simple distance transform function using Chamfer metrics
DT(x,y) with integer or fractional metric (Borgefors/Butt and Maragos) and 5x5 template, 101x101 cells
Programd yields a symmetric (hexadecagon) surface about the sampled point (50,50)
M J de Smith - 5/12/08 for Python (as a template prog)

Libraries required:
Numpy - Numerical Python - see dtm_mtp://numpy.scipy.org/
Modificado según dtm_mtp://www.desmith.eu/MJdS/PDFS/desmith.pdf
"""
from __future__ import division

import numpy as np

def constrained_distance_transform(dtm_m, target_points, max_slope, 
                                   scale_m_per_pix = 1):
    """Distance transform constrained to max slope value"

    "Determination of gradient and curvature constrained optimal paths."
    Dr Michael J de Smith, Computer-Aided Civil and Infrastruture Engineering.

    dtm_m: elevation map.
    target_points : ((starting_y, starting_x), (end_y, end_x))
    max_slope : max allowed slope in the distance transform.
    """
    # XV, YV: matriz que indicará el siguiente punto a recorrer (?)
    XV = np.zeros(dtm_m.shape, dtype=np.int)
    YV = np.zeros(dtm_m.shape, dtype=np.int)
       
    DT = np.prod(dtm_m.shape) ** 2 * np.ones(dtm_m.shape, dtype=np.float)

    for cy, cx in target_points:
        DT[cy, cx] = 0.0 # target point in centre of array

    # Local Distance Metric (LDM) and mask arrays
    N, M = dtm_m.shape

    # define chamfer values
    a1,a2,a3 = 2.2062, 1.4141, 0.9866

    # forward scan
    DX = [-2., -2., -1., -1., -1., -1., -1.,  0.,  0.]
    DY = [-1.,  1., -2., -1.,  0.,  1.,  2., -1.,  0.]
    # LDM = [a1, a1, a1, a2, a3, a2, a1, a3, 0]
    LDM = np.hypot(DX, DY)

    for i in range(2, N-2):
        for j in range(2, M-2):
            d0 = DT[i,j]
            for k in range(len(DX)):
                    r = int(i+DX[k])
                    c = int(j+DY[k])
                    d = DT[r,c]
                    if LDM[k] > 0:
                        slope = abs(dtm_m[i,j]-dtm_m[r,c]) / (
                                scale_m_per_pix * LDM[k])
                    else:
                        slope = 0
                        
                    d_tentative = d + LDM[k]
                    if d_tentative < d0 and slope < max_slope:
                        d0 = d_tentative
                        XV[i, j] = DX[k]
                        YV[i, j] = DY[k]

            DT[i,j] = d0
  
    DX = [ 0.,  0.,  1.,  1.,  1.,  1.,  1.,  2.,  2.]
    DY = [-1.,  1., -2., -1.,  0.,  1.,  2., -1.,  0.]

    LDM = np.hypot(DX, DY)
    for i in range(N-3,1,-1):
        for j in range(M-3,1,-1):
            d0=DT[i,j]
            for k in range(len(DX)):
                    r=int(i + DX[k])
                    c=int(j + DY[k])
                    d=DT[r,c] #+LDM[k]

                    if LDM[k]>0:
                        slope = abs(dtm_m[i,j]-dtm_m[r,c]) / (
                                scale_m_per_pix*LDM[k])
                    else:
                        slope = 0
                    if ((d+LDM[k]) < d0) and (slope < max_slope):
                        d0 = d + LDM[k]
                        XV[i, j] = DX[k]
                        YV[i, j] = DY[k]

            DT[i, j]=d0
    
    return DT

def least_constrained_path(dtm_m, target_points, max_slope, scale_m_per_pix):
    
    dt = constrained_distance_transform(dtm_m, target_points, max_slope, 
                                        scale_m_per_pix=scale_m_per_pix)
    return dt

if __name__ == "__main__":
    """Inicialización de datos para prueba"""
    N = 101

    perfil = np.linspace(0, 9, N)
    dtm_m = np.tile(perfil,[len(perfil), 1]).T   # Vertical slope
            
    dtm_m[40:60,40:51] = 1    # with a bump somewhere in the middle
    target_points_index = [(75, 75)]   # list of target points
    max_slope = 0.1          # max allowed slope
    scale_m_per_pix = 1
    
    """Cálculo"""    
    dt = least_constrained_path(dtm_m, 
                           target_points_index, 
                           max_slope, 
                           scale_m_per_pix)