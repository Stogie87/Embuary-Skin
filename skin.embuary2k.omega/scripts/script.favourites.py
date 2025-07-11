# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import os
import re
import xml.etree.ElementTree as ET
from xbmcvfs import translatePath

FAVOURITES_PATH = translatePath("special://profile/favourites.xml")

class FavouriteItem:
    def __init__(self, name, thumb, path):
        self.name = name
        self.thumb = thumb
        self.path = path

def load_favourites():
    if not os.path.exists(FAVOURITES_PATH):
        xbmc.log("[Embuary-Favourites] favourites.xml not found", xbmc.LOGWARNING)
        return []

    tree = ET.parse(FAVOURITES_PATH)
    root = tree.getroot()
    items = []

    for fav in root.findall("favourite"):
        name = fav.get("name")
        thumb = fav.get("thumb", "DefaultAudio.png")
        path = fav.text.strip()
        items.append(FavouriteItem(name, thumb, path))

    return items

def classify_favourite(item: FavouriteItem):
    path = item.path.lower()

    if any(x in path for x in ["/movies/", "videodb://movies/", "/movie/"]) \
       or ("plugin.video.jellyfin" in path and "mode=play" in path and "tvshow" not in path):
        return "Filme"

    if any(x in path for x in ["/tvshows/", "/shows/", "videodb://tvshows/", "/series/", "/show/"]) \
       or ("plugin.video.jellyfin" in path and "tvshow" in path):
        return "Serien"

    if any(x in path for x in ["/artist/", "musicdb://artists/", "/musicartists"]):
        return "Interpreten"

    if any(x in path for x in ["/album/", "musicdb://albums/", "/albums/", "/music/albums"]):
        return "Musikalben"

    if any(x in path for x in ["/track/", "/song/", "musicdb://songs/", "/file/music/", ".mp3", ".flac"]) \
       or ("plugin.audio.jellyfin" in path and "track" in path):
        return "Musiktitel"

    return "Andere"

def extract_artist_from_name_or_path(name, path, thumb=None):
    # 1. Aus Titel-String
    if " - " in name:
        parts = name.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()

    # 2. Aus Thumb (z. B. /Music/Artist/Album/folder.jpg)
    if thumb:
        parts = thumb.replace("\\", "/").split("/")
        if len(parts) >= 3:
            return parts[-3], name

    # 3. Aus Pfad: /Music/Artist/Album/track.mp3
    path_parts = path.replace("\\", "/").split("/")
    if len(path_parts) >= 3:
        return path_parts[-3], name

    return "", name  # fallback

def create_listitem(fav: FavouriteItem, category: str):
    label = fav.name

    if category in ["Musiktitel", "Musikalben"]:
        artist, title = extract_artist_from_name_or_path(fav.name, fav.path, fav.thumb)
        if artist:
            label = f"{artist} – {title}"
        else:
            label = title

    li = xbmcgui.ListItem(label=label)
    li.setArt({
        "thumb": fav.thumb,
        "poster": fav.thumb,
        "icon": fav.thumb
    })
    li.setProperty("IsPlayable", "true")
    li.setPath(fav.path)
    return li

def show_favourites():
    all_favs = load_favourites()
    if not all_favs:
        xbmcgui.Dialog().notification("Embuary", "Keine Favoriten gefunden", xbmcgui.NOTIFICATION_INFO, 3000)
        return

    grouped = {
        "Filme": [],
        "Serien": [],
        "Interpreten": [],
        "Musikalben": [],
        "Musiktitel": [],
        "Andere": []
    }

    for fav in all_favs:
        category = classify_favourite(fav)
        grouped[category].append(fav)

    ordered = [k for k in ["Filme", "Serien", "Interpreten", "Musikalben", "Musiktitel", "Andere"] if grouped[k]]
    if not ordered:
        xbmcgui.Dialog().notification("Embuary", "Keine erkennbaren Favoriten gefunden", xbmcgui.NOTIFICATION_INFO, 3000)
        return

    cat_index = xbmcgui.Dialog().select("Favoriten-Kategorie", ordered)
    if cat_index == -1:
        return

    selected_cat = ordered[cat_index]
    items = grouped[selected_cat]
    listitems = [create_listitem(i, selected_cat) for i in items]
    labels = [i.getLabel() for i in listitems]
    item_index = xbmcgui.Dialog().select(f"{selected_cat}", labels)

    if item_index == -1:
        return

    action = items[item_index].path.strip()
    xbmc.executebuiltin(action)

if __name__ == '__main__':
    show_favourites()
