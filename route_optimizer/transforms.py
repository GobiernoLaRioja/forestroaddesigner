# -*- coding: utf-8 -*-
"""
Created on Wed Feb  8 19:10:40 2017

@author: Javier
"""

# Simple distance transform function using Chamfer metrics
# DT(x,y) with integer or fractional metric (Borgefors/Butt and Maragos) and 5x5 template, 101x101 cells
# Programd yields a symmetric (hexadecagon) surface about the sampled point (50,50)
# M J de Smith - 5/12/08 for Python (as a template prog)

# Libraries required:
# Numpy - Numerical Python - see dtm_mtp://numpy.scipy.org/
# Modificado según dtm_mtp://www.desmith.eu/MJdS/PDFS/desmith.pdf



import numpy as np

#
# dtm_m: mapa de elevación
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
    XV = np.zeros(dtm_m.shape, dtype=int)
    YV = np.zeros(dtm_m.shape, dtype=int)

    # Escala del MDT
    # define arrays and dimensions

    # Used to initialize the data, greater than any distance that can be
    # found within the search domain
    # (max would be np.sqrt(np.sum(dtm_m.shape ** 2)))
    
       
    DT = np.prod(dtm_m.shape) ** 2 * np.ones(dtm_m.shape, dtype=float)
    print(("Valor máximo: {}".format(np.max(DT))))

    for cy, cx in target_points:
        print(("Target point: {}".format((cx, cy))))
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
                        # if slope != 0:
                        #    print(i,j,r,c,abs(dtm_m[i,j]-dtm_m[r,c]), slope)
                    else:
                        slope = 0
                        
                    d_tentative = d + LDM[k]
                    if d_tentative < d0 and slope < max_slope:
                        d0 = d_tentative
                        XV[i, j] = DX[k]
                        YV[i, j] = DY[k]
                # k
            DT[i,j] = d0
        # j
    # i
    # backwards scan
  
    DX = [ 0.,  0.,  1.,  1.,  1.,  1.,  1.,  2.,  2.]
    DY = [-1.,  1., -2., -1.,  0.,  1.,  2., -1.,  0.]
    # LDM= [0, a3, a1, a2, a3, a2, a1, a1, a1]
    LDM = np.hypot(DX, DY)
    for i in range(N-3,1,-1):
        for j in range(M-3,1,-1):
            d0=DT[i,j]
            for k in range(len(DX)):
                    r=int(i + DX[k])
                    c=int(j + DY[k])
                    d=DT[r,c] #+LDM[k]
                    # d0=min(d,d0) Not in gradient constrained?
                    if LDM[k]>0:
                        slope = abs(dtm_m[i,j]-dtm_m[r,c]) / (
                                scale_m_per_pix*LDM[k])
                    else:
                        slope = 0
                    if ((d+LDM[k]) < d0) and (slope < max_slope):
                        d0 = d + LDM[k]
                        XV[i, j] = DX[k]
                        YV[i, j] = DY[k]
                 # k
            DT[i, j]=d0
        # j
    # i
    
    return DT



def least_constrained_path(dtm_m, target_points, max_slope, scale_m_per_pix, 
                           show_graphics=False):
    
    dt = constrained_distance_transform(dtm_m, target_points, max_slope, 
                                        scale_m_per_pix=scale_m_per_pix)
    
    
    if show_graphics:
        
        from matplotlib import pyplot as plt
        # path_ima = dtm_m[2:-2, 2:-2].copy()        
        
        plt.figure()
        plt.imshow(dt)
        plt.colorbar()
        plt.clim(0, np.sqrt(np.sum(np.array(dt.shape) ** 2)))
        # Get firat and last point in path, and swap x and y order
                
        plt.title('Distance transform constrained.')

    return dt
