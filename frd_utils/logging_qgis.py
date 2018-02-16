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

from qgis.core import QgsMessageLog

class QgsLogging(object):
    DEBUG = -1
    INFO = QgsMessageLog.INFO
    WARNING = QgsMessageLog.WARNING
    CRITICAL = QgsMessageLog.CRITICAL
    NONE = 100
    
    def __init__(self, tag):
        self._tag = tag
        self._level = QgsMessageLog.INFO
        
        self.debug = lambda msg: self._message(msg, self.DEBUG)
        self.info = lambda msg: self._message(msg, self.INFO)
        self.warning = lambda msg: self._message(msg, self.WARNING)
        self.critical = lambda msg: self._message(msg, self.CRITICAL)
        self.error = lambda msg: self._message(msg, self.CRITICAL)
    
    def setLevel(self, level):
        self._level = level
        
    def _message(self, message, level):
        if level >= self._level:
            QgsMessageLog.logMessage(message, self._tag, level)

class defaultdictfromkey(dict):
    def __init__(self, factory):
        self.factory = factory
    def __missing__(self, key):
        self[key] = self.factory(key)
        return self[key]

LOGGERS = defaultdictfromkey(QgsLogging)

def getLogger(tag):
    return LOGGERS[tag]


ROOT = getLogger("root")

def basicConfig(*args, **kwargs):
    pass

setLevel = lambda level: ROOT.setLevel(level)
debug = lambda msg: ROOT.debug(msg)
info = lambda msg: ROOT.info(msg)
warning = lambda msg: ROOT.warning(msg)
critical = lambda msg: ROOT.critical(msg)
error = lambda msg: ROOT.critical(msg)

    