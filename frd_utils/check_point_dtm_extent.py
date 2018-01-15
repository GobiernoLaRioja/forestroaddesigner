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

from __future__ import unicode_literals

from PyQt4.QtGui import QMessageBox
from qgis.core import QgsPoint

def check_point_at_dtm(dtm_layer, point):
    """This function checks if given point as list isn't in dtm layer extension
    """
    if not dtm_layer.extent().contains(QgsPoint(point[0], point[-1])):
        QMessageBox.warning(None, "ERROR",
                    u"Error: ¡No se admiten puntos fuera de la extensión\n" +
                    " del Modelo Digital del Terreno!.")
        return 'out'
    
    else:
        return 'in'