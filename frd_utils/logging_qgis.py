# -*- coding: utf-8 -*-
"""
This module provides a logging compatible interface to Qgis messages

@author: panoimagen
"""

from qgis.core import Qgis, QgsMessageLog

class QgsLogging(object):
    DEBUG = -1
    INFO = Qgis.Info
    WARNING = Qgis.Warning
    CRITICAL = Qgis.Critical
    NONE = 100
    
    def __init__(self, tag):
        self._tag = tag
        self._level = Qgis.Info
        
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

    