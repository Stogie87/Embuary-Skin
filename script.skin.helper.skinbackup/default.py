#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.skinbackup
    Kodi addon to backup skin settings
'''

import sys
import traceback

# Kodi core modules (sind beim Testen außerhalb von Kodi nicht vorhanden)
try:
    import xbmc
    import xbmcgui
    import xbmcvfs
    LOG_WARNING = xbmc.LOGWARNING
    LOG_ERROR = xbmc.LOGERROR
except ImportError:
    # Fallback-Loglevel für Tests außerhalb von Kodi
    LOG_WARNING = 30
    LOG_ERROR = 40

from resources.lib.backuprestore import BackupRestore
from resources.lib.colorthemes import ColorThemes
from resources.lib.utils import log_exception, log_msg


class Main:
    '''Main entry point for script'''

    def __init__(self):
        '''Initialization and main code run'''
        try:
            self.params = self.get_params()
            log_msg(f"called with parameters: {self.params}")
            action = self.params.get("action", "")
            if not action:
                # launch main backuprestore dialog
                BackupRestore().backuprestore()
            elif hasattr(self, action):
                # launch module for action provided by this script
                getattr(self, action)()
            else:
                log_msg(f"No such action: {action}", LOG_WARNING)
        except Exception as exc:
            log_msg(f"Exception occurred: {exc}\n{traceback.format_exc()}", LOG_ERROR)
            log_exception(__name__, exc)

    def backup(self):
        '''Backup skin settings to file'''
        backuprestore = BackupRestore()
        filters = self.params.get("filter")
        if filters:
            filters = filters.split("|")
        else:
            filters = []

        silent = self.params.get("silent", "")
        promptfilename = self.params.get("promptfilename", "").lower() == "true"

        if silent:
            silent_backup = True
            backup_file = silent
        else:
            silent_backup = False
            backup_file = backuprestore.get_backupfilename(promptfilename)

        backuprestore.backup(filters, backup_file, silent_backup)

    def restore(self):
        '''Restore skin settings from file'''
        backuprestore = BackupRestore()
        silent = self.params.get("silent", "")

        if silent and not xbmcvfs.exists(silent):
            log_msg(
                "ERROR while restoring backup! --> Filename invalid. "
                "Make sure you provide the FULL path, e.g., special://skin/extras/mybackup.zip",
                LOG_ERROR
            )
            return

        backuprestore.restore(silent)

    def reset(self):
        '''Reset skin settings'''
        backuprestore = BackupRestore()
        filters = self.params.get("filter")
        if filters:
            filters = filters.split("|")
        else:
            filters = []

        silent = self.params.get("silent", "").lower() == "true"
        backuprestore.reset(filters, silent)

        # Short delay to ensure settings are applied
        if 'xbmc' in sys.modules:
            xbmc.Monitor().waitForAbort(2)

            # Optional: Notify skin.helper.service to re-check settings
            if xbmc.getCondVisibility("System.HasAddon(script.skin.helper.service)"):
                xbmc.executebuiltin("RunScript(script.skin.helper.service,action=checkskinsettings)")

    def colorthemes(self):
        '''Open colorthemes dialog'''
        if self.params.get("daynight"):
            self.daynighttheme()
        else:
            ColorThemes().colorthemes()

    def daynighttheme(self):
        '''Select day/night theme'''
        daynight = self.params.get("daynight")
        if daynight:
            ColorThemes().daynightthemes(daynight)

    @staticmethod
    def createcolortheme():
        '''Create a color theme'''
        colorthemes = ColorThemes()
        colorthemes.createColorTheme()

    @staticmethod
    def restorecolortheme():
        '''Restore colortheme from backup'''
        colorthemes = ColorThemes()
        colorthemes.restoreColorTheme()

    @staticmethod
    def get_params():
        '''Extract parameters from script arguments'''
        params = {}
        for arg in sys.argv[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lower()
                if key == "action":
                    value = value.lower()
                params[key] = value
        return params


# MAIN
if __name__ == '__main__':
    Main()
