# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import os
import sys
import xml.etree.ElementTree as ET
from xbmcvfs import translatePath

FAVOURITES_PATH = translatePath("special://profile/favourites.xml")

def get_favourite_action(label):
    if not os.path.exists(FAVOURITES_PATH):
        return None
    try:
        tree = ET.parse(FAVOURITES_PATH)
        root = tree.getroot()
        for fav in root.findall("favourite"):
            name = fav.get("name", "")
            if name == label:
                return fav.text.strip()
    except Exception as e:
        xbmc.log(f"[PlayContent] Fehler beim Lesen der favourites.xml: {e}", xbmc.LOGERROR)
    return None

def close_window():
    xbmc.executebuiltin('Dialog.Close(all,true)')

def run_favourite_action(action_cmd):
    # Known commands
    if not action_cmd:
        xbmc.executebuiltin('ActivateWindow(10060)')
        return

    action = action_cmd.strip()

    # 1. Bekannte Favoriten-Kommandos
    if action.startswith("PlayMedia("):
        cmd = action[len("PlayMedia("):-1]
        close_window()
        xbmc.executebuiltin(f'PlayMedia({cmd})')
    elif action.startswith("ActivateWindow("):
        cmd = action[len("ActivateWindow("):-1]
        close_window()
        xbmc.executebuiltin(f'ActivateWindow({cmd})')
    elif action.startswith("RunScript("):
        cmd = action[len("RunScript("):-1]
        close_window()
        xbmc.executebuiltin(f'RunScript({cmd})')
    elif action.startswith("RunPlugin("):
        cmd = action[len("RunPlugin("):-1]
        close_window()
        xbmc.executebuiltin(f'RunPlugin({cmd})')
    elif action.startswith("XBMC.RunScript("):  # Legacy
        cmd = action[len("XBMC.RunScript("):-1]
        close_window()
        xbmc.executebuiltin(f'RunScript({cmd})')
    else:
        # 2. Erkennung Datenbank-Pfade (Serienordner, Filmordner etc.)
        if action.lower().startswith("videodb://tvshows"):
            close_window()
            xbmc.executebuiltin(f'ActivateWindow(10025,"{action}",return)')
        elif action.lower().startswith("videodb://movies"):
            close_window()
            xbmc.executebuiltin(f'ActivateWindow(10025,"{action}",return)')
        elif action.lower().startswith("musicdb://"):
            close_window()
            xbmc.executebuiltin(f'ActivateWindow(10501,"{action}",return)')
        # 3. Plugin-URL (z.B. Play von Jellyfin/Emby)
        elif action.lower().startswith("plugin://"):
            close_window()
            xbmc.executebuiltin(f'PlayMedia({action})')
        # 4. Sonstige Befehle (als Builtin probieren)
        else:
            close_window()
            try:
                xbmc.executebuiltin(action)
            except Exception as e:
                xbmc.log(f"[PlayContent] Nicht ausführbar: {action}: {e}", xbmc.LOGERROR)
                xbmc.executebuiltin('ActivateWindow(10060)')

def main():
    if len(sys.argv) < 2:
        xbmc.executebuiltin('ActivateWindow(10060)')
        return

    fav_label = sys.argv[1]
    action_cmd = get_favourite_action(fav_label)
    if action_cmd:
        run_favourite_action(action_cmd)
    else:
        xbmc.executebuiltin('ActivateWindow(10060)')

if __name__ == '__main__':
    main()
