# -*- coding: utf-8 -*-
import xbmc
import xbmcgui

def get_localized_text(key):
    return xbmc.getLocalizedString(key)

def toggle_favourites_view():
    # Hole aktuelle Ansicht
    view = xbmc.getInfoLabel('Skin.String(favourites_view)').lower()
    # Zyklisches Umschalten zwischen landscape → portrait → standard
    if view == "landscape":
        new_view = "portrait"
        text = get_localized_text(31907)  # vertikal
    elif view == "portrait":
        new_view = "standard"
        text = get_localized_text(31917)  # standard
    else:  # standard oder ungültig
        new_view = "landscape"
        text = get_localized_text(31908)  # horizontal

    xbmc.executebuiltin(f'Skin.SetString(favourites_view,{new_view})')
    xbmc.executebuiltin(f'Skin.SetString(favourites_view_localized,{text})')
    xbmcgui.Dialog().notification(get_localized_text(31906), f"{get_localized_text(31906)} {text}", xbmcgui.NOTIFICATION_INFO, 1500)

    # Optional: Direkt zu MyFavourites.xml wechseln, falls Standard gewählt wird
    if new_view == "standard":
        xbmc.executebuiltin('ActivateWindow(MyFavourites.xml)')

if __name__ == '__main__':
    toggle_favourites_view()
