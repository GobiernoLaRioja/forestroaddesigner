# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ForestRoadDesigner
                                 A QGIS plugin
 This plugin serve as support of foresters in the design of forest roads
                             -------------------
        begin                : 2017-02-08
        copyright            : (C) 2017 by PANOimagen S.L.
        email                : info@panoimagen.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
This module manages the about information of the plugin
"""

from __future__ import unicode_literals
from PyQt4 import uic
from PyQt4.QtGui import QDialog

import platform
import os

try:
    import version
except ImportError:
    class version(object):
        VERSION = "devel"

uiFilePath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'dlgabout.ui'))
FormClass = uic.loadUiType(uiFilePath)[0]

class DlgAbout(QDialog, FormClass):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        repository_info = (u'Code repository: PENDIENTE\nBug Tracker: PENDIENTE')
        
        contact_info = (u'Copyright: (C) 2017 by PANOimagen S.L.\nPANOimagen' +
                        u' S.L. La Rioja (Spain)\nwww.panoimagen.com')
        
        plugin_description = (u'This plugin has been funded by the Dirección' +
                              u' General de Medio Natural del Gobierno de La' +
                              u' Rioja and developed by PANOimagen S.L.\n'+
                              u'Forest Road Designer serve as support of'+
                              u' foresters in the design of forest roads.\n' +
                              u'For more information, please, read metadata/' +
                              u'readme and/or contact the author.')
        
        license_info = (u'This program is free software: you can' +
                        u' redistribute it and/or modify it under the terms' +
                        u' of the GNU General Public License\nas published' +
                        u' by the Free Software Foundation, either version 3' +
                        u' of the License, or (at your option) any later' +
                        u' version.')
        
        self.codeRepoLabel.setText(repository_info)
        self.contactLabel.setText(contact_info)
        self.descriptionLabel.setText(plugin_description)
        self.licenseLabel.setText(license_info)
        self.versionLabel.setText(u'Forest Road Designer version {}'.format(
                version.VERSION))