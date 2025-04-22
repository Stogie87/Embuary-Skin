#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon
import sys
from typing import Optional, Dict, Any
from resources.lib import ColorPicker as cp

ADDON_ID = "script.skin.helper.colorpicker"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo('path')
MONITOR = xbmc.Monitor()

class Main:
    '''Main entrypoint for our colorpicker'''
    def __init__(self):
        params = self._get_params()
        if params:
            color_picker = cp.ColorPicker("script-skin_helper_service-ColorPicker.xml", ADDON_PATH, "Default", "1080i")
            color_picker.skinstring = params.get("SKINSTRING", "")
            color_picker.win_property = params.get("WINPROPERTY", "")
            color_picker.active_palette = params.get("PALETTE", "")
            color_picker.header_label = params.get("HEADER", "")
            propname = params.get("SHORTCUTPROPERTY", "")
            color_picker.shortcut_property = propname
            color_picker.doModal()

            # special action when we want to set our chosen color into a skinshortcuts property
            if propname and not isinstance(color_picker.result, int):
                self._wait_for_skinshortcuts_window()
                xbmc.sleep(400)
                current_window = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
                current_window.setProperty("customProperty", propname)
                current_window.setProperty("customValue", color_picker.result[0])
                xbmc.executebuiltin("SendClick(404)")
                xbmc.sleep(250)
                current_window.setProperty("customProperty", f"{propname}.name")
                current_window.setProperty("customValue", color_picker.result[1])
                xbmc.executebuiltin("SendClick(404)")
            del color_picker

    @staticmethod
    def _get_params() -> Dict[str, str]:
        '''Extract the parameters from the called script path.'''
        params: Dict[str, str] = {}
        for arg in sys.argv:
            if arg in ('script.skin.helper.colorpicker', 'default.py'):
                continue
            elif "=" in arg:
                param_name, param_value = arg.split('=', 1)
                params[param_name] = param_value
                params[param_name.upper()] = param_value
        return params

    @staticmethod
    def _wait_for_skinshortcuts_window() -> None:
        '''Wait until skinshortcuts is active window (because of any animations that may have been applied)'''
        while not MONITOR.abortRequested() and not xbmc.getCondVisibility(
            "Window.IsActive(DialogSelect.xml) | "
            "Window.IsActive(script-skin_helper_service-ColorPicker.xml) | "
            "Window.IsActive(DialogKeyboard.xml)"
        ):
            MONITOR.waitForAbort(0.1)


# MAIN ENTRY POINT
if __name__ == "__main__":
    Main()
