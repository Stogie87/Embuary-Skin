#!/usr/bin/python

########################

import sys
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
        self.params = {}
        self._parse_argv()

        if self.action:
            self.getactions()
        else:
            DIALOG.ok(ADDON.getLocalizedString(32000), ADDON.getLocalizedString(32001))

    def _parse_argv(self):
        args = sys.argv

        for arg in args:
            if arg == ADDON_ID:
                continue
            if arg.startswith('action='):
                self.action = arg[7:].lower()
            else:
                try:
                    self.params[arg.split("=")[0].lower()] = "=".join(arg.split("=")[1:]).strip()
                except Exception:
                    self.params = {}

    def getactions(self):
        if self.action in globals():
            util = globals()[self.action]
            util(self.params)
        else:
            DIALOG.ok("Fehler", f"Ungültige Aktion: {self.action}")

if __name__ == '__main__':
    Main()
