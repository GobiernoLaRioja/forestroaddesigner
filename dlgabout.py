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
        
        repo_url = (u'<address><b>https://github.com/GobiernoLaRioja/' +
                    u'forestroaddesigner</address></b>')
        tracker_url = (u'<address><b>https://github.com/GobiernoLaRioja/' +
                       u'forestroaddesigner/issues</address></b><br>')
        panoi_url = u'<address><b>www.panoimagen.com</address></b><br>'
        
        repository_info = (u'Code repository: {}<br>Bug Tracker: {}'.format(
                repo_url, tracker_url))
        
        contact_info = (u'<h3>Copyright (C) 2017  by PANOimagen S.L.</h3>' +
                        u'PANOimagen S.L. La Rioja (Spain) -- {}'.format(
                                panoi_url))

        plugin_description = (u'This plugin has been funded by the Dirección' +
                              u' General de Tecnologías de la Información' +
                              u' y la Comunicación\ndel Gobierno de La Rioja'+
                              u' and developed by PANOimagen S.L. at the' +
                              u' request of the Dirección General\ndel' +
                              u' Gobierno de La Rioja.\n\nForest Road' +
                              u' Designer serves as support of foresters'+
                              u' in the design of forest roads.\n' +
                              u'For more information, please, read metadata/' +
                              u'readme and/or contact the author.')
        
        license_info = (u'<h3>License:' +
                        u'</h3>This program is free software' +
                        u' you can redistribute it and/or modify it under' +
                        u' the terms of the GNU General<br>Public License as' +
                        u' published by the Free Software Foundation, either' +
                        u' version 3 of the License, or (at your<br>option)' +
                        u' any later version.<br><br>This program is' +
                        u' distributed in the hope that it will be useful,' +
                        u' but WITHOUT ANY WARRANTY; without even<br>the' +
                        u' implied warranty of MERCHANTABILITY or FITNESS' +
                        u' FOR A PARTICULAR PURPOSE.  See the GNU General' +
                        u'<br>Public License for more details.<br><br>' +
                        u'You should have received a copy of the GNU' +
                        u' General Public License along with this program.' +
                        u' If not, see:<br><address><b>https://www.gnu.org/' +
                        u'licenses/</address></b>.')
        
        self.codeRepoLabel.setText(repository_info)
        self.contactLabel.setText(contact_info)
        self.descriptionLabel.setText(plugin_description)
        self.licenseLabel.setText(license_info)
        self.versionLabel.setText(u'<h2>Forest Road Designer<\h2>' +
                                  u' Version {}'.format(
                                          version.VERSION))