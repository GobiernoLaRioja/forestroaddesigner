# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from math import floor, pi, sqrt
# from .frd_utils import logging_qgis as logging
# import logging
# logger = logging.getLogger("frd")

#Factors fixed to allow painting different kind of penalties
PREDET_PENALTY_FACT ={"slope": 100,
                      "radius": 10000,
                      "cutfill": 1E+12}

def remove_undef(dtm_m, dtm_no_data_value):
    """Remove undef values from lidar dtms (usually -XXXXX height value)."""
    try:
        min_val = np.min(dtm_m[dtm_m > dtm_no_data_value])
    except ValueError:
        min_val = 0
    dtm_m[dtm_m <= dtm_no_data_value] = min_val
    return dtm_m


def height_profile(dtm_m, waypoints, min_slope, max_slope, scale_m_per_pix):
    # force int type as they will be used as indices to dtm_m
    waypoints = np.array(waypoints)

    height_prof = [dtm_m[int(y),int(x)] for y, x in waypoints]
    dist_xy = [scale_m_per_pix*np.linalg.norm(p1-p0) for p0, p1 in
               zip(waypoints[:-1], waypoints[1:]) ]
    slope = np.diff(height_prof)/dist_xy
    dist_xy = np.hstack((0, dist_xy))
    slope = np.hstack((0, slope))

    cumdist_xy = np.cumsum(dist_xy)

    slope_pen_max =[100*abs(slo-max_slope)/abs(max_slope) if (max_slope < slo or -max_slope > slo) else 0 for slo in slope]

    slope_pen_min =[100*(1 -abs(slo-min_slope)/abs(min_slope)) if (slo > -min_slope and slo < min_slope)  else 0 for slo in slope]
    
    slope_pen = []
    for smax,smin in zip(slope_pen_max,slope_pen_min):
        slope_pen.append(max(smax,abs(smin)))

    return height_prof, slope, cumdist_xy, slope_pen

def radius_profile(dtm_m, waypoints, scale_m_per_pix, min_radius):
    # force int type as they will be used as indices to dtm_m
    waypoints = np.array(waypoints)
    row_rad = []
    for p0, p1, p2 in zip(waypoints[:-2], waypoints[1: -1], waypoints[2:]):
        way0 = p1-p0
        way1 = p2-p1
        angle0 = np.arctan2(way0[0], way0[1])
        angle1 = np.arctan2(way1[0], way1[1])
        if abs(angle1 - angle0) >= np.pi:            
            if angle0 >= 0:
                angle1 = 2*np.pi + angle1
            else:
                angle1 = angle1 - 2*np.pi
        anglevar = angle1 - angle0
        angle = abs(anglevar)
        angle2 = np.arccos(min(max(np.dot(p1-p0, p2-p1)/(np.linalg.norm(p1-p0)* np.linalg.norm(p2-p1)),-1),1))

        lon0 = np.linalg.norm(way0)
        lon1 = np.linalg.norm(way1)
        suma_arc = lon0 + lon1

        if angle > 1E-06:
                rad = scale_m_per_pix * 0.5 * suma_arc / angle if angle < np.pi else 94906265.2485031
        else:
            rad = 0
        # print(f"p0 {p0[0]} p0 {p0[1]} p1 {p1[0]} p1 {p1[1]} p2 {p2[0]} p2 {p2[1]}")
        # print(f"p0 {p0[0]} p0 {p0[1]}")   
        # print(f"angle {np.degrees(angle)} angle2 {np.degrees(angle2)} rad {rad}")
        row_rad.append(rad)
    row_rad = np.hstack((0, row_rad, 0))
    min_rad_allowed = min_radius*(1 - 1E-06)
    row_rad_pen = []
    for rad in row_rad:
        rad_pen = 100*(1-rad/min_radius) if 0 < rad < min_rad_allowed else 0
        row_rad_pen.append(rad_pen)
    
    return row_rad, row_rad_pen

def cutfill_profile(dtm_m, waypoints, scale_m_per_pix, activated_road_options, cut_angle, fill_angle, cut_hmax, fill_hmax, w_road):
    
    if not activated_road_options or len(waypoints) < 2:
        return [0]*len(waypoints), [0]*len(waypoints), [0]*len(waypoints)

    # force int type as they will be used as indices to dtm_m
    waypoints = np.array(waypoints)
    orto_points = precalc_orto_array(waypoints)
    height_diff =[]
    cutfill_tans = []
    cutfill_penalties_dif = []

    for w_point, o_point_list in zip(waypoints[:-1], orto_points):
        pen_orto_list = []
        cutfill_tag_orto_list = []
        h_dif_list = []
        h_dif = 0
        pen_dif = 0
        cutfill_tag = 0
        for o_point_rel in o_point_list:
            o_point = o_point_rel + w_point
            pen_orto = 0
            cutfill_tag_orto = 0
            h_dif_orto = 0
            if (0 <= o_point[0] < dtm_m.shape[0] and 0<= o_point[1] < dtm_m.shape[1] ):
                h_orto_cut = cut_angle*abs(np.linalg.norm(o_point - w_point)* scale_m_per_pix - w_road/2)
                h_orto_fill = fill_angle*abs(np.linalg.norm(o_point - w_point)* scale_m_per_pix - w_road/2)
                hmax = min(cut_hmax, h_orto_cut)
                hmin = min(fill_hmax, h_orto_fill)
                h_dif_orto = dtm_m[o_point[0],o_point[1]] - dtm_m[w_point[0],w_point[1]]
                if (0 <= h_dif_orto < hmax or 0 >= h_dif_orto > -hmin ):
                    cutfill_tag_orto = max(abs(h_dif_orto - hmax)/abs(np.linalg.norm(o_point - w_point)-w_road/2),
                                    abs(h_dif_orto - hmin)/abs(np.linalg.norm(o_point - w_point)-w_road/2)) 
                    pass
                else:
                    pen_dif_max = abs(1 - h_dif_orto/hmax) if h_dif_orto > 1E-2 else 0
                    pen_dif_min = abs(1 - abs(h_dif_orto/hmin)) if h_dif_orto < -1E-2 else 0
                    pen_orto = max(pen_dif_max, pen_dif_min)
                    cutfill_tag_orto = abs(h_dif_orto - hmax)/(np.linalg.norm(o_point - w_point)*scale_m_per_pix) \
                                    if pen_dif_max >= pen_dif_min else abs(h_dif_orto - hmin)/(np.linalg.norm(o_point - w_point)*scale_m_per_pix)

            pen_orto_list.append(pen_orto)
            cutfill_tag_orto_list.append(cutfill_tag_orto)
            h_dif_list.append(h_dif_orto)

        pen_dif= max(pen_orto_list)
        cutfill_tag = cutfill_tag_orto_list[0] if pen_orto_list[0]>= pen_orto_list[1] else cutfill_tag_orto_list[1]
        h_dif = h_dif_list[0] if pen_orto_list[0]>= pen_orto_list[1] else h_dif_list[1]
        cutfill_penalties_dif.append(100*pen_dif)
        height_diff.append(h_dif)
        cutfill_tans.append(cutfill_tag)

    height_diff.append(0)
    cutfill_tans.append(0)
    cutfill_penalties_dif.append(0)
    return height_diff, cutfill_tans , cutfill_penalties_dif


def precalc_orto_array(waypoints):
    
    orto_waypoints = [w_p1-w_p0 for w_p1, w_p0 in zip(waypoints[1:], waypoints[:-1])]
    orto_coords = orto_waypoints@np.array(([0,1],[-1,0])).T
    orto_points = [[-c ,c ] for c in orto_coords] 
    return orto_points

def penalty_profile(dtm_m, waypoints, min_slope, max_slope, scale_m_per_pix, min_radius,
                    activated_road_options, cut_angle,
                    fill_angle, cut_hmax, fill_hmax,
                    w_road):

    height_prof, slope, cumdist_xy, slope_pen = height_profile(dtm_m, waypoints, min_slope, max_slope, scale_m_per_pix)
    min_radius_profile = min_radius if min_radius else 0
    # row_rad, row_rad_pen = radius_profile(dtm_m, waypoints, scale_m_per_pix, min_radius_profile)
    row_rad, row_rad_pen = radius_profile(dtm_m, waypoints, scale_m_per_pix, min_radius_profile)

    height_diff_prof, cutfill_tan_prof, cutfill_pen_prof = cutfill_profile(dtm_m, waypoints, scale_m_per_pix,
                                    activated_road_options, cut_angle,
                                    fill_angle, cut_hmax, fill_hmax, w_road)

    row_rad_pen_prev = row_rad_pen[1:] + [0]
    penalty_slope_radius_cutfill = [pen_sl_rd(sl, sl_pen, rd_pen, rd_pen_prev, cutfill_pen,
                                             PREDET_PENALTY_FACT['slope'],
                                             PREDET_PENALTY_FACT['radius'],
                                             PREDET_PENALTY_FACT['cutfill']) for sl, sl_pen, rd_pen, rd_pen_prev, cutfill_pen in zip(slope[1:], slope_pen[1:], row_rad_pen[:-1], row_rad_pen_prev[:-1], cutfill_pen_prof[:-1])]

    return height_prof, slope, cumdist_xy, slope_pen, row_rad, row_rad_pen, height_diff_prof, cutfill_tan_prof, cutfill_pen_prof,  penalty_slope_radius_cutfill


def pen_sl_rd(sl, sl_pen, rd_pen, rd_pen_prev, cutfill_pen, param_sl= None, param_rad=None, param_cutfill=None):
    """ Devolvemos el máximo de penalización entre cutfill_pen, rd_pen, rd_pen_prev, sl_pen
        (multiplicado por un factor predeterminado (100, 10000, 1e12) ?"""
    
    max_pen = max(cutfill_pen, rd_pen, rd_pen_prev, sl_pen)
    if sl_pen == max_pen:
        return sl*param_sl
    elif cutfill_pen == max_pen:
        return cutfill_pen*param_cutfill
    elif rd_pen_prev == max_pen:
        return rd_pen_prev*param_rad
    elif rd_pen == max_pen:
        return rd_pen*param_rad
    else:
        return 0

def summary(waypoints, scale_m_per_pix, height_prof, slope_pen, row_rad, row_rad_pen, cutfill_penalties_dif):

    summary = {}
    waypoints = np.array(waypoints)
    if waypoints is None or len(waypoints) <2 :
        return summary
        
    summary["straight_distance"] = scale_m_per_pix*np.linalg.norm(waypoints[-1]-waypoints[0])

    w_start_x = [p[0] for p in waypoints[:-1]]
    w_arri_x = [p[0] for p in waypoints[1:]]
    w_start_y = [p[1] for p in waypoints[:-1]]
    w_arri_y = [p[1] for p in waypoints[1:]]
    w_start_z = height_prof[:-1]
    w_arri_z = height_prof[1:]
    real_d_m = np.sqrt(
            ((np.array(w_arri_x)
             - np.array(w_start_x))*scale_m_per_pix) ** 2 +
            ((np.array(w_arri_y)
             - np.array(w_start_y))*scale_m_per_pix)  ** 2 +
            (np.array(w_arri_z)
             - np.array(w_start_z)) ** 2)
    
    summary["total_cumsum"] = (np.cumsum(np.array(real_d_m)))[-1]    
    summary["total_acumulative_slope"] = np.cumsum(abs(np.diff(height_prof)))[-1]
    summary["raw_slope"] = height_prof[-1] - height_prof[0]    
    summary["average_slope"] = abs(height_prof[-1] -height_prof[0])/ summary["straight_distance"]
    summary["average_acum_slope"] = summary["total_acumulative_slope"] / summary["total_cumsum"]
    summary["total_curves"] = np.count_nonzero(row_rad)
    summary["total_slope_pen"] = np.count_nonzero(slope_pen)
    summary["total_rad_pen"] = np.count_nonzero(row_rad_pen)
    summary["tota_cutfill_pen"] = np.count_nonzero(cutfill_penalties_dif)

    track_quality, twist_num, turn_number_list = get_track_quality(waypoints, height_prof, scale_m_per_pix)
    summary["twist_number"] = twist_num
    summary["track_quality"] = track_quality

    return summary, turn_number_list

# METHODS FOR TRACK QUALITY

def get_angles_distances(waypoints, scale_m_per_pix):
    
    dist_xy = [scale_m_per_pix * np.linalg.norm(p1-p0) for p0, p1 in zip(waypoints[:-1], waypoints[1:])]
    angles = []
    for p0, p1, p2 in zip(waypoints[:-2], waypoints[1: -1], waypoints[2:]):
        way0 = p1-p0
        way1 = p2-p1
        angle0 = np.degrees(np.arctan2(way0[0], way0[1]))
        angle1 = np.degrees(np.arctan2(way1[0], way1[1]))
        if abs(angle1 - angle0) >= 180:            
            if angle0 >= 0:
                angle1 = 360 + angle1
            else:
                angle1 = angle1 -360
        angle = angle1 - angle0
        angles.append(angle)
    angles.append(0)
    return dist_xy, angles

def get_track_elements(waypnt, scale_m_per_pix):
    
    # waypoints_array = np.array(waypnt)
    dist_xy, angles = get_angles_distances(waypnt, scale_m_per_pix)
    sum_ang = 0 # sum of angles of twists
    num_curv = 0 # amount of twists of the track
    same_curve = False # Whether or not we are in the same curve
    cont = 0 # index of angle
    curve_index = [0] # index of the angle in a change of twist
    num_strline = 0 # number of consecutive straight segments
    for ang  in angles:
        if ang < 0:
            num_strline = 0
            if sum_ang <= 0:
                sum_ang = sum_ang + ang
            if sum_ang > 0 :                    
                same_curve = False
                sum_ang = ang
                curve_index.append(cont)
            if sum_ang <= -30 and not same_curve:
                    same_curve = True
                    num_curv +=1
                    
        elif ang > 0:
            num_strline = 0
            if sum_ang >= 0:
                sum_ang = sum_ang + ang
            if sum_ang < 0 : 
                same_curve = False
                
                sum_ang = ang
                curve_index.append(cont)
                
            if sum_ang >= 30 and not same_curve:
                    same_curve = True
                    num_curv +=1
        else:
            if num_strline > 1:
                same_curve = False
                curve_index.append(cont)
                sum_ang = ang
            else:
                num_strline +=1      
        cont +=1        
    curve_index.append(cont)
    
    return dist_xy, angles, num_curv, curve_index

def get_track_quality(waypointlist, height_prof, scale_m_per_pix):
    wayplist = []
    wx = [p[0] for p in waypointlist]
    wy = [p[1] for p in waypointlist]

    for x,y,z in zip(wx, wy, height_prof):
        wayplist.append([x,y,z])
    wayp = np.array(wayplist)
    dist_xy, angles, num_curv, curve_index = get_track_elements(wayp, scale_m_per_pix)
    radius_list =[]
    turn_number_list = [(0,0,0)]*len(waypointlist) 
    turn_number =0
    if num_curv == 0: 
        return [100], 0, turn_number_list
    
    for i in range(0, len(curve_index) -1):
        suma_ang = sum([an for an in angles[curve_index[i] : curve_index[i+1]]])
        suma_arc = sum([ar for ar in dist_xy[curve_index[i] : curve_index[i+1]]])
        if abs(suma_ang) >= 30:
            if curve_index[i +1] - curve_index[i] ==1 and curve_index[i+1] +1 < len(waypointlist): # The curve only contains two segments
                suma_arc = sum([ar for ar in dist_xy[curve_index[i] -1 : curve_index[i+1]]]) #We take the arc adding the previous and the next segments
            if curve_index[i + 1] - curve_index[i] == 1 and curve_index[i+1] +1 >= len(waypointlist): # The curve only contains two segments
                suma_arc = sum([ar for ar in dist_xy[curve_index[i] -1 : curve_index[i+1]]]) #We take the arc adding the previous and the next segments

            curv = suma_arc * 180 / (abs(suma_ang) * pi)
            radius_list.append(curv)

            turn_number += 1
            for j in range(curve_index[i], curve_index[i +1] +1) :
                turn_number_list[j] = (j,turn_number,curv)
    radio_medio = sum(radius_list)/len(radius_list) if len(radius_list) > 0 else 0   
    total_distxy_km = sum(dist_xy) / 1000
    calidad_trazado = radio_medio / (len(radius_list) /total_distxy_km)
    
    return  calidad_trazado, num_curv, turn_number_list

# DAVID NOT IN USE
def radius_profile_old(dtm_m, waypoints, scale_m_per_pix, min_radius):
    # force int type as they will be used as indices to dtm_m
    waypoints = np.array(waypoints)
    row_rad = []
    for p0, p1, p2 in zip(waypoints[:-2], waypoints[1: -1], waypoints[2:]):
        angle = np.arccos(min(max(np.dot(p1-p0, p2-p1)/(np.linalg.norm(p1-p0)* np.linalg.norm(p2-p1)),-1),1))
        # print(f"angle {angle} angle_degrees {np.degrees(angle)}")
        if angle > 1E-06:
                rad = scale_m_per_pix / ((np.tan(angle / 2))) if angle <= np.pi/2 else scale_m_per_pix / ((np.tan((np.pi - angle) / 2))) if angle < np.pi else 94906265.2485031
        else:
            rad = 0
        row_rad.append(rad)
    row_rad = np.hstack((0, row_rad, 0))
    min_rad_allowed = min_radius*(1 - 1E-06)
    row_rad_pen = []
    for rad in row_rad:
        rad_pen = 100*(1-rad/min_radius) if 0 < rad < min_rad_allowed else 0
        row_rad_pen.append(rad_pen)
    
    return row_rad, row_rad_pen

# INTERACTIVE MODE

def interactive_height_profile(interpolator, waypoints, scale_m_per_pix):
    # force int type as they will be used as indices to dtm_m
    waypoints = np.array(waypoints)
    # print(f"------------------------------------")
    # print(f"interactive_height_profile waypoints {waypoints}")
    height_prof = [scale_m_per_pix*interpolator([y,x]) for y, x in waypoints]
    # print(f"------------------------------------")
    # print(f"interactive_height_profile height_prof {height_prof}")
    diffe = [h1-h0 for h0, h1 in
               zip(height_prof[:-1], height_prof[1:]) ]   
    # print(f"------------------------------------")
    # print(f"interactive_height_profile diff {diffe}")
    dist_xy = [scale_m_per_pix*np.linalg.norm(p1-p0) for p0, p1 in
               zip(waypoints[:-1], waypoints[1:]) ]    
    # print(f"------------------------------------")
    # print(f"interactive_height_profile dist_XY {dist_xy}")

    slope = [h[0]/d for h,d in zip(diffe, dist_xy)]
    # print(f"------------------------------------")
    # print(f"interactive_height_profile slope {slope}")
    # slope = np.diff(height_prof)/np.array(dist_xy)
    dist_xy = np.hstack((0, dist_xy))
    slope = np.hstack((0, slope))
    
    cumdist_xy = np.cumsum(dist_xy)
    return height_prof, slope, cumdist_xy

def interactive_summary(waypoints, scale_m_per_pix, height_prof):

    summary = {}
    waypoints = np.array(waypoints)
    if waypoints is None or len(waypoints) <2 :
        return summary
        
    summary["straight_distance"] = scale_m_per_pix*np.linalg.norm(waypoints[-1]-waypoints[0])

    w_start_x = [p[0] for p in waypoints[:-1]]
    w_arri_x = [p[0] for p in waypoints[1:]]
    w_start_y = [p[1] for p in waypoints[:-1]]
    w_arri_y = [p[1] for p in waypoints[1:]]
    w_start_z = [h[0] for h in height_prof[:-1]]
    w_arri_z = [h[0] for h in height_prof[1:]]
    real_d_m = np.sqrt(
            ((np.array(w_arri_x)
             - np.array(w_start_x))*scale_m_per_pix) ** 2 +
            ((np.array(w_arri_y)
             - np.array(w_start_y))*scale_m_per_pix)  ** 2 +
            (np.array(w_arri_z)
             - np.array(w_start_z)) ** 2)
    
    summary["total_cumsum"] = (np.cumsum(np.array(real_d_m)))[-1]       
    height_prof_list = [h[0] for h in height_prof]
    summary["total_acumulative_slope"] = np.cumsum(abs(np.diff(height_prof_list)))[-1]    
    summary["raw_slope"] = height_prof_list[-1] - height_prof_list[0]
    summary["average_slope"] = abs(height_prof_list[-1] -height_prof_list[0])/ summary["straight_distance"]
    summary["average_acum_slope"] = summary["total_acumulative_slope"] / summary["total_cumsum"]
    track_quality, twist_num, turn_number_list = get_track_quality(waypoints, height_prof_list, scale_m_per_pix)
    summary["twist_number"] = twist_num
    summary["track_quality"] = track_quality
    print("SUMARY")
    print(summary)

    return summary, turn_number_list
