# -*- coding: utf-8 -*-
import xbmc
import xbmcgui

def get_localized_text(key):
    return xbmc.getLocalizedString(key)

def toggle_favourites_view():
    # Hole aktuelle Ansicht
    view = xbmc.getInfoLabel('Skin.String(favourites_view)').lower()
    # Umschalten
    new_view = "landscape" if view == "portrait" else "portrait"
    xbmc.executebuiltin(f'Skin.SetString(favourites_view,{new_view})')
    # Lokalisierte Bezeichnung holen und als neue Variable setzen
    if new_view == "landscape":
        text = get_localized_text(42009)  # horizontal
    else:
        text = get_localized_text(42008)  # vertikal
    xbmc.executebuiltin(f'Skin.SetString(favourites_view_localized,{text})')
    # Optionale Notification
    xbmcgui.Dialog().notification(get_localized_text(42007), f"{get_localized_text(42007)} {text}", xbmcgui.NOTIFICATION_INFO, 1500)

if __name__ == '__main__':
    toggle_favourites_view()
