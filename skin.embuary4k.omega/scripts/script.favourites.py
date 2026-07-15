# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import os
import xml.etree.ElementTree as ET
from xbmcvfs import translatePath

FAVOURITES_PATH = translatePath("special://profile/favourites.xml")

# Übersetzungs-IDs für Dialoge
STRID_FAV_VIEW = 31906
STRID_CAT_SELECT = 31909
STRID_PLAY = 31910
STRID_REMOVE = 31911
STRID_CANCEL = 31912
STRID_REMOVED = 31913
STRID_NO_FAVS = 31914
STRID_NO_CATS = 31915
STRID_ACTION_SELECT = 31916

CATEGORIES = ["Filme", "Serien", "Interpreten", "Musikalben", "Musiktitel"]

class FavouriteItem:
    def __init__(self, name, thumb, path):
        self.name = name
        self.thumb = thumb
        self.path = path

def localize(id, fallback):
    text = xbmc.getLocalizedString(id)
    return text if text and not text.startswith('Label') else fallback

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

def save_favourites(favs):
    root = ET.Element("favourites")
    for fav in favs:
        elem = ET.SubElement(root, "favourite", name=fav.name)
        if fav.thumb:
            elem.set("thumb", fav.thumb)
        elem.text = fav.path
    tree = ET.ElementTree(root)
    tree.write(FAVOURITES_PATH, encoding="utf-8", xml_declaration=True)

def classify_favourite(item: FavouriteItem):
    path = item.path.lower()
    if "type=mixed" in path:
        return "Filme"
    if "type=seasons" in path or "type=tvshows" in path:
        return "Serien"
    if any(x in path for x in ["/movies/", "videodb://movies/", "/movie/"]) or ("plugin.video.jellyfin" in path and "mode=play" in path and "tvshow" not in path):
        return "Filme"
    if any(x in path for x in ["/tvshows/", "/shows/", "videodb://tvshows/", "/series/", "/show/"]) or ("plugin.video.jellyfin" in path and "tvshow" in path):
        return "Serien"
    if any(x in path for x in ["/artist/", "musicdb://artists/", "/musicartists"]):
        return "Interpreten"
    if any(x in path for x in ["/album/", "musicdb://albums/", "/albums/", "/music/albums"]):
        return "Musikalben"
    if any(x in path for x in ["/track/", "/song/", "musicdb://songs/", "/file/music/", ".mp3", ".flac"]) or ("plugin.audio.jellyfin" in path and "track" in path):
        return "Musiktitel"
    return "Andere"

def extract_artist_from_name_or_path(name, path, thumb=None):
    if " - " in name:
        parts = name.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    if thumb:
        parts = thumb.replace("\\", "/").split("/")
        if len(parts) >= 3:
            return parts[-3], name
    parts = path.replace("\\", "/").split("/")
    if len(parts) >= 3:
        return parts[-3], name
    return "", name

def create_listitem(fav: FavouriteItem, category: str):
    label = fav.name
    if category in ["Musiktitel", "Musikalben"]:
        artist, title = extract_artist_from_name_or_path(fav.name, fav.path, fav.thumb)
        if artist and artist != title:
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

# --- Portrait Dialog ---
class FavouritesPortraitDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.items_by_type = kwargs.get("items_by_type", {})
        self.categories = list(self.items_by_type.keys())
        self.selected = None
        self.closed = False

    def close(self):
        self.closed = True
        super().close()

    def get_safe_control(self, cid):
        try:
            return self.getControl(cid)
        except Exception:
            xbmc.log(f"[Embuary-Favourites] Control {cid} nicht gefunden!", xbmc.LOGERROR)
            return None

    def onInit(self):
        if self.closed:
            return
        try:
            cat_ctrl = self.get_safe_control(9000)
            if not cat_ctrl:
                return
            cat_ctrl.reset()
            for cat in self.categories:
                cat_ctrl.addItem(xbmcgui.ListItem(label=cat))
            cat_ctrl.selectItem(0)
            self.update_vertical_list(0)
            self.setFocusId(9001)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onInit Exception: {e}", xbmc.LOGERROR)

    def onFocus(self, controlId):
        if self.closed:
            return
        try:
            if controlId == 9000:
                self.setFocusId(9001)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onFocus Exception: {e}", xbmc.LOGERROR)

    def onAction(self, action):
        if self.closed:
            return
        if action in (10, 92):  # ACTION_PREVIOUS_MENU, ACTION_NAV_BACK
            self.close()
            return
        try:
            cat_ctrl = self.get_safe_control(9000)
            fav_ctrl = self.get_safe_control(9001)
            if not cat_ctrl or not fav_ctrl:
                return
            focus_id = self.getFocusId()
            pos = cat_ctrl.getSelectedPosition()
            if focus_id == 9001:
                if action == 1:  # LEFT
                    if pos > 0:
                        cat_ctrl.selectItem(pos - 1)
                        self.update_vertical_list(pos - 1)
                        fav_ctrl.selectItem(0)
                        self.setFocusId(9001)
                elif action == 2:  # RIGHT
                    if pos < len(self.categories) - 1:
                        cat_ctrl.selectItem(pos + 1)
                        self.update_vertical_list(pos + 1)
                        fav_ctrl.selectItem(0)
                        self.setFocusId(9001)
                else:
                    return super().onAction(action)
            else:
                self.setFocusId(9001)
                return super().onAction(action)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onAction Exception: {e}", xbmc.LOGERROR)

    def onClick(self, controlId):
        if self.closed:
            return
        try:
            cat_ctrl = self.get_safe_control(9000)
            fav_ctrl = self.get_safe_control(9001)
            if not cat_ctrl or not fav_ctrl:
                return
            if controlId == 9001:
                cat_pos = cat_ctrl.getSelectedPosition()
                cat = self.categories[cat_pos]
                sel = fav_ctrl.getSelectedPosition()
                if sel is not None and sel >= 0 and sel < fav_ctrl.size():
                    item = fav_ctrl.getListItem(sel)
                    if item.getLabel() == "Keine Favoriten" and not item.getProperty("IsPlayable") == "true":
                        return
                    self.selected = (cat, sel)
                    self.close()
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onClick Exception: {e}", xbmc.LOGERROR)

    def update_vertical_list(self, cat_index):
        if self.closed:
            return
        try:
            cat = self.categories[cat_index]
            fav_ctrl = self.get_safe_control(9001)
            cat_label = self.get_safe_control(9002)
            if not fav_ctrl or not cat_label:
                return
            fav_ctrl.reset()
            cat_label.setLabel(cat)
            items = self.items_by_type[cat]
            if items:
                for li in items:
                    fav_ctrl.addItem(li)
                fav_ctrl.selectItem(0)
                self.setFocusId(9001)
            else:
                dummy = xbmcgui.ListItem(label='Keine Favoriten')
                dummy.setProperty("IsPlayable", "false")
                fav_ctrl.addItem(dummy)
                fav_ctrl.selectItem(0)
                self.setFocusId(9001)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] update_vertical_list Exception: {e}", xbmc.LOGERROR)

# --- Landscape Dialog ---
class FavouritesLandscapeDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.items_by_type = kwargs.get("items_by_type", {})
        self.categories = list(self.items_by_type.keys())
        self.selected = None
        self.closed = False

    def close(self):
        self.closed = True
        super().close()

    def get_safe_control(self, cid):
        try:
            ctrl = self.getControl(cid)
            return ctrl
        except Exception:
            xbmc.log(f"[Embuary-Favourites] Control {cid} nicht gefunden!", xbmc.LOGERROR)
            return None

    def onInit(self):
        if self.closed:
            return
        try:
            cat_ctrl = self.get_safe_control(9000)
            if not cat_ctrl:
                return
            cat_ctrl.reset()
            for cat in self.categories:
                cat_ctrl.addItem(xbmcgui.ListItem(label=cat))
            cat_ctrl.selectItem(0)
            self.update_horizontal_list(0)
            self.setFocusId(9001)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onInit Exception: {e}", xbmc.LOGERROR)

    def onFocus(self, controlId):
        if self.closed:
            return
        try:
            if controlId == 9000:
                self.setFocusId(9001)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onFocus Exception: {e}", xbmc.LOGERROR)

    def onAction(self, action):
        if self.closed:
            return
        if action in (10, 92):  # ACTION_PREVIOUS_MENU, ACTION_NAV_BACK
            self.close()
            return
        try:
            cat_ctrl = self.get_safe_control(9000)
            fav_ctrl = self.get_safe_control(9001)
            if not cat_ctrl or not fav_ctrl:
                return
            focus_id = self.getFocusId()
            if focus_id == 9001:
                pos = cat_ctrl.getSelectedPosition()
                if action == 3:  # UP
                    if pos > 0:
                        cat_ctrl.selectItem(pos - 1)
                        self.update_horizontal_list(pos - 1)
                        self.setFocusId(9001)
                elif action == 4:  # DOWN
                    if pos < len(self.categories) - 1:
                        cat_ctrl.selectItem(pos + 1)
                        self.update_horizontal_list(pos + 1)
                        self.setFocusId(9001)
                else:
                    return super().onAction(action)
            else:
                self.setFocusId(9001)
                return super().onAction(action)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onAction Exception: {e}", xbmc.LOGERROR)

    def onClick(self, controlId):
        if self.closed:
            return
        try:
            cat_ctrl = self.get_safe_control(9000)
            fav_ctrl = self.get_safe_control(9001)
            if not cat_ctrl or not fav_ctrl:
                return
            if controlId == 9001:
                cat_pos = cat_ctrl.getSelectedPosition()
                cat = self.categories[cat_pos]
                sel = fav_ctrl.getSelectedPosition()
                if sel is not None and sel >= 0 and sel < fav_ctrl.size():
                    item = fav_ctrl.getListItem(sel)
                    if item.getLabel() == "Keine Favoriten" and not item.getProperty("IsPlayable") == "true":
                        return
                    self.selected = (cat, sel)
                    self.close()
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] onClick Exception: {e}", xbmc.LOGERROR)

    def update_horizontal_list(self, cat_index):
        if self.closed:
            return
        try:
            cat = self.categories[cat_index]
            fav_ctrl = self.get_safe_control(9001)
            cat_label = self.get_safe_control(9002)
            if not fav_ctrl or not cat_label:
                return
            fav_ctrl.reset()
            cat_label.setLabel(cat)
            items = self.items_by_type[cat]
            if items:
                for li in items:
                    fav_ctrl.addItem(li)
                fav_ctrl.selectItem(0)
                self.setFocusId(9001)
            else:
                dummy = xbmcgui.ListItem(label='Keine Favoriten')
                dummy.setProperty("IsPlayable", "false")
                fav_ctrl.addItem(dummy)
                fav_ctrl.selectItem(0)
                self.setFocusId(9001)
        except Exception as e:
            xbmc.log(f"[Embuary-Favourites] update_horizontal_list Exception: {e}", xbmc.LOGERROR)

# --- Standard Dialog ---
class FavouritesStandardDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.closed = False

    def close(self):
        self.closed = True
        super().close()

    def onInit(self):
        pass

    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        if action in (10, 92):  # ACTION_PREVIOUS_MENU, ACTION_NAV_BACK
            self.close()
        else:
            super().onAction(action)

    def onClick(self, controlId):
        pass

    def update_standard_list(self, cat_index):
        pass

# --- Hauptdialog-Funktion ---
def show_favourites():
    while True:
        all_favs = load_favourites()
        if not all_favs:
            xbmcgui.Dialog().notification("Embuary", localize(STRID_NO_FAVS, "Keine Favoriten gefunden"), xbmcgui.NOTIFICATION_INFO, 3000)
            return

        grouped = {cat: [] for cat in CATEGORIES}
        grouped["Andere"] = []
        for fav in all_favs:
            category = classify_favourite(fav)
            if category in grouped:
                grouped[category].append(fav)
            else:
                grouped["Andere"].append(fav)

        skin_path = translatePath("special://skin/xml/")
        view = xbmc.getInfoLabel('Skin.String(favourites_view)').lower() or "portrait"

        if view != "standard":
            items_by_type = {cat: [create_listitem(i, cat) for i in grouped[cat]] for cat in CATEGORIES}
            items_by_type["Andere"] = [create_listitem(i, "Andere") for i in grouped["Andere"]]
        else:
            items_by_type = {cat: [] for cat in CATEGORIES}
            items_by_type["Andere"] = []

        if view == "portrait":
            win = FavouritesPortraitDialog("DialogFavouritesPortrait.xml", skin_path, "default",
                                           items_by_type=items_by_type)
        elif view == "landscape":
            win = FavouritesLandscapeDialog("DialogFavouritesLandscape.xml", skin_path, "default",
                                            items_by_type=items_by_type)
        elif view == "standard":
            win = FavouritesStandardDialog("MyFavourites.xml", skin_path, "default")
            win.doModal()
            del win
            return
        else:
            win = FavouritesPortraitDialog("DialogFavouritesPortrait.xml", skin_path, "default",
                                           items_by_type=items_by_type)

        win.selected = None
        win.doModal()
        sel = win.selected
        del win
        if not sel:
            return  # Fenster wurde explizit geschlossen

        if view == "standard":
            return

        cat, idx = sel
        items = grouped[cat]
        if idx < 0 or idx >= len(items):
            return
        selected_item = items[idx]
        action = xbmcgui.Dialog().select(
            localize(STRID_ACTION_SELECT, "Aktion wählen"),
            [localize(STRID_PLAY, "Wiedergabe starten"),
             localize(STRID_REMOVE, "Aus Favoriten entfernen"),
             localize(STRID_CANCEL, "Abbrechen")]
        )
        if action == -1:
            return  # Dialog wurde per ESC/BACK geschlossen – Schleife und Fenster beenden!
        if action == 0:
            xbmc.executebuiltin(selected_item.path.strip())
            return
        elif action == 1:
            all_favs.remove(selected_item)
            save_favourites(all_favs)
            xbmcgui.Dialog().notification(localize(STRID_REMOVED, "Favorit entfernt"), selected_item.name,
                                          xbmcgui.NOTIFICATION_INFO, 2000)
            continue
        elif action == 2:
            continue
        else:
            return

if __name__ == '__main__':
    show_favourites()
