#!/usr/bin/python

########################

import sys  # FEHLTE
import xbmcgui
import xbmcaddon

from resources.lib.helper import *
from resources.lib.utils import *
from resources.lib.cinema_mode import *

########################

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
DIALOG = xbmcgui.Dialog()

class Main:
    def __init__(self):
        self.action = False
        self.params = {}  # FEHLTE
        self._parse_argv()

        if self.action:
            self.getactions()
        else:
            DIALOG.ok(ADDON.getLocalizedString(32000), ADDON.getLocalizedString(32001))

    def _parse_argv(self):
        # Kodi übergibt bei Skriptaufrufen üblicherweise sys.argv[1] als Query-String.
        if len(sys.argv) > 1 and sys.argv[1]:
            import urllib.parse
            args = sys.argv[1]
            params = dict(urllib.parse.parse_qsl(args))
            for k, v in params.items():
                if k.lower() == 'action':
                    self.action = v.lower()
                else:
                    self.params[k.lower()] = v

    def getactions(self):
        # Direkt aus dem globalen Namensraum aufrufbar machen, falls Funktion existiert
        if self.action in globals():
            util = globals()[self.action]
            util(self.params)
        else:
            DIALOG.ok(ADDON.getLocalizedString(32000), "Ungültige Aktion: %s" % self.action)


if __name__ == '__main__':
    Main()
