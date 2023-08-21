# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Batch_Hillshader
                                 A QGIS plugin  to generate a three light
                                 exposure hillshade (shaded relief by
                                 combining three light exposures)

    For more information, see the program documentation.

    If you uses as input LiDAR data, note that plugin uses LASTools library.
        See LASTools License at  <https://rapidlasso.com/lastools/>

    Plugin also use in LiDAR data mode FUSION LDV.
        See FUSION LDV License at <http://forsys.cfr.washington.edu/fusion.html>
                              -------------------
        begin                : 2016-07-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by PANOimagen S.L.
        email                : info@panoimagen.com
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


from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

import platform
import os

try:
    from . import version
except ImportError:
    class version(object):
        VERSION = "devel"

import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dlgabout.ui'), resource_suffix='')


class DlgAbout(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        repository_info = ('Code repository: PENDIENTE\nBug Tracker: PENDIENTE')

        contact_info = ('Copyright: (C) 2017 by PANOimagen S.L.\nPANOimagen S.L. La Rioja (Spain)\nwww.panoimagen.com')

        plugin_description = ('This plugin has been funded by the Dirección General de Medio Natural del Gobierno de La Rioja and developed by PANOimagen S.L.\nForest Road Designer serve as support of foresters in the design of forest roads.\nFor more information, please, read metadata/readme and/or contact the author.')

        license_info = 'This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License\nas published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.'

        self.codeRepoLabel.setText(repository_info)
        self.contactLabel.setText(contact_info)
        self.descriptionLabel.setText(plugin_description)
        self.licenseLabel.setText(license_info)
        self.versionLabel.setText('Forest Road Designer version {}'.format(
                version.VERSION))
