#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Helper service and scripts for Kodi skins
    skinshortcuts.py
    Methods to connect skinhelper to skinshortcuts for smartshortcuts, widgets and backgrounds
'''

import os
import sys
from resources.lib.utils import kodi_json, log_msg, urlencode, ADDON_ID, getCondVisibility, try_encode, try_decode
from metadatautils import MetadataUtils
import xbmc
import xbmcvfs
import xbmcplugin
import xbmcgui
import xbmcaddon

# extendedinfo has some login-required widgets, these must not be probed without login details
EXTINFO_CREDS = False
if getCondVisibility("System.Hasaddon(script.extendedinfo)"):
    exinfoaddon = xbmcaddon.Addon(id="script.extendedinfo")
    if exinfoaddon.getSetting("tmdb_username") and exinfoaddon.getSetting("tmdb_password"):
        EXTINFO_CREDS = True
    del exinfoaddon


def add_directoryitem(entry, is_folder=True, widget=None, widget2=None):
    '''helper to create a listitem for our smartshortcut node'''
    label = "$INFO[Window(Home).Property(%s.title)]" % entry
    path = "$INFO[Window(Home).Property(%s.path)]" % entry
    content = "$INFO[Window(Home).Property(%s.content)]" % entry
    image = "$INFO[Window(Home).Property(%s.image)]" % entry
    mediatype = "$INFO[Window(Home).Property(%s.type)]" % entry

    if is_folder:
        path = sys.argv[0] + "?action=SMARTSHORTCUTS&path=" + entry
        listitem = xbmcgui.ListItem(label, path=path)
        listitem.setArt({"icon": 'DefaultFolder.png'})
    else:
        listitem = xbmcgui.ListItem(label, path=path)
        props = {}
        props["list"] = content
        if not xbmc.getInfoLabel(mediatype):
            mediatype = "media"
        props["type"] = mediatype
        props["background"] = "$INFO[Window(Home).Property(%s.image)]" % entry
        props["backgroundName"] = "$INFO[Window(Home).Property(%s.title)]" % entry

        if widget:
            widget_type = "$INFO[Window(Home).Property(%s.type)]" % widget
            if not xbmc.getInfoLabel(mediatype):
                widget_type = mediatype
            widget_target = "music" if widget_type in ["albums", "artists", "songs"] else "video"
            props["widget"] = "addon"
            props["widgetName"] = "$INFO[Window(Home).Property(%s.title)]" % widget
            props["widgetType"] = widget_type
            props["widgetTarget"] = widget_target
            props["widgetPath"] = "$INFO[Window(Home).Property(%s.content)]" % widget
            if "plugin:" in xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.content)]" % widget):
                props["widgetPath"] = props["widgetPath"] + \
                    "&reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]"

        if widget2:
            widget_type = "$INFO[Window(Home).Property(%s.type)]" % widget2
            if not xbmc.getInfoLabel(mediatype):
                widget_type = mediatype
            widget_target = "music" if widget_type in ["albums", "artists", "songs"] else "video"
            props["widget.1"] = "addon"
            props["widgetName.1"] = "$INFO[Window(Home).Property(%s.title)]" % widget2
            props["widgetType.1"] = widget_type
            props["widgetTarget.1"] = widget_target
            props["widgetPath.1"] = "$INFO[Window(Home).Property(%s.content)]" % widget2
            if "plugin:" in xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.content)]" % widget2):
                props["widgetPath.1"] = props["widgetPath.1"] + \
                    "&reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]"

        # InfoTag-API nutzen
        info_tag = listitem.getVideoInfoTag()
        info_tag.setTitle("smartshortcut")
        info_tag.setMediaType("video")
        info_tag.setMpaa(repr(props))

        listitem.setArt({"icon": "special://home/addons/script.skin.helper.service/fanart.jpg", "thumb": image})

    listitem.setArt({"fanart": image})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=is_folder)


def smartshortcuts_sublevel(entry):
    if "emby" in entry:
        content_strings = ["", ".recent", ".inprogress", ".unwatched", ".recentepisodes", ".inprogressepisodes", ".nextepisodes", ".recommended"]
    elif "plex" in entry:
        content_strings = ["", ".ondeck", ".recent", ".unwatched"]
    elif "netflix.generic.suggestions" in entry:
        content_strings = ["", ".0", ".1", ".2", ".3", ".4", ".5", ".6", ".7", ".8", ".9", ".10"]
    elif "netflix" in entry:
        content_strings = ["", ".mylist", ".recent", ".inprogress", ".suggestions", ".genres", ".recommended", ".trending"]
    else:
        content_strings = [""]

    for content_string in content_strings:
        key = entry + content_string
        widget = None
        widget2 = None
        if content_string == "":
            mediatype = xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.type)]" % entry)
            if "plex" in entry:
                widget = entry + ".ondeck"
                widget2 = entry + ".recent"
            elif mediatype in ["movies", "movie", "artist"] or "netflix" in entry:
                widget = entry + ".recent"
                widget2 = entry + ".inprogress"
            elif mediatype == "tvshows" and "emby" in entry:
                widget = entry + ".nextepisodes"
                widget2 = entry + ".recent"
            elif mediatype in ["homevideos", "photos"] and "emby" in entry:
                widget = entry + ".recent"
                widget2 = entry + ".recommended"
            else:
                widget = entry
        if xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.path)]" % key):
            add_directoryitem(key, False, widget, widget2)


def get_smartshortcuts(sublevel=None):
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    if sublevel:
        smartshortcuts_sublevel(sublevel)
    else:
        all_smartshortcuts = xbmc.getInfoLabel("Window(Home).Property(all_smartshortcuts)")
        win = xbmcgui.Window(10000)
        all_smartshortcuts = win.getProperty("all_smartshortcuts")
        if all_smartshortcuts:
            for node in eval(all_smartshortcuts):
                if "emby" in node or "plex" in node or "netflix" in node:
                    add_directoryitem(node, True)
                else:
                    add_directoryitem(node, False, node)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def smartshortcuts_widgets():
    widgets = []
    all_smartshortcuts = xbmc.getInfoLabel("Window(Home).Property(all_smartshortcuts)")
    if all_smartshortcuts:
        for node in eval(all_smartshortcuts):
            label = xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.title)]" % node)
            if "emby" in node or "plex" in node or "netflix" in node:
                path = sys.argv[0] + "?action=SMARTSHORTCUTS&path=%s" % node
                widgets.append([label, path, "folder", True])
            else:
                content = xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.content)]" % node)
                media_type = xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.type)]" % node)
                widgets.append([label, content, media_type])
    return widgets


def item_filter_mapping():
    mappings = []
    mappings.append(("scriptwidgets", xbmc.getInfoLabel("System.AddonTitle(script.skin.helper.widgets)")))
    mappings.append(("librarydataprovider", xbmc.getInfoLabel("System.AddonTitle(service.library.data.provider)")))
    mappings.append(("extendedinfo", xbmc.getInfoLabel("System.AddonTitle(script.extendedinfo)")))
    mappings.append(("smartshortcuts", "Smart Shortcuts"))
    mappings.append(("skinplaylists", "Playlists"))
    mappings.append(("favourites", "Favourites"))
    mappings.append(("static", "Static widgets"))
    return mappings


def get_item_filter_label(filterkey):
    label = ""
    for item in item_filter_mapping():
        if item[0] == filterkey:
            label = item[1]
    return label


def get_widgets(item_filter="", sublevel=""):
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    if item_filter:
        item_filters = item_filter.split(",")
    else:
        item_filters = [mapping[0] for mapping in item_filter_mapping()]

    for item_filter in item_filters:
        if item_filter == "smartshortcuts":
            widgets = smartshortcuts_widgets()
        elif item_filter == "skinplaylists":
            widgets = playlists_widgets()
        elif item_filter == "favourites":
            widgets = favourites_widgets()
        elif item_filter == "static":
            widgets = static_widgets()
        elif sublevel:
            widgets = plugin_widgetlisting(item_filters[0], sublevel)
        elif item_filter == "scriptwidgets":
            widgets = plugin_widgetlisting("script.skin.helper.widgets")
        elif item_filter == "librarydataprovider":
            widgets = plugin_widgetlisting("service.library.data.provider")
        elif item_filter == "extendedinfo":
            widgets = plugin_widgetlisting("script.extendedinfo")
        else:
            continue

        if not sublevel and len(item_filters) > 1 and item_filter != "static":
            if widgets:
                label = get_item_filter_label(item_filter)
                listitem = xbmcgui.ListItem(label)
                listitem.setArt({"icon": 'DefaultFolder.png'})
                url = "plugin://script.skin.helper.service?action=widgets&path=%s" % item_filter
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True)
        else:
            for widget in widgets:
                media_type = widget[2]
                if media_type == "folder":
                    is_folder = True
                elif len(widget) > 3:
                    is_folder = widget[3]
                else:
                    is_folder = False
                if media_type == "movies":
                    image = "DefaultMovies.png"
                    media_library = "Videos"
                    target = "video"
                elif media_type == "pvr":
                    media_library = "TvChannels"
                    image = "DefaultTVShows.png"
                    target = "pvr"
                elif media_type == "tvshows":
                    image = "DefaultTVShows.png"
                    media_library = "Videos"
                    target = "video"
                elif media_type == "episodes":
                    image = "DefaultTVShows.png"
                    media_library = "Videos"
                    target = "video"
                elif media_type == "albums":
                    image = "DefaultMusicAlbums.png"
                    media_library = "Music"
                    target = "music"
                elif media_type == "songs":
                    image = "DefaultMusicSongs.png"
                    media_library = "Music"
                    target = "music"
                elif media_type == "artists":
                    image = "DefaultMusicArtists.png"
                    media_library = "Music"
                    target = "music"
                elif media_type == "musicvideos":
                    image = "DefaultMusicVideos.png"
                else:
                    image = "Defaultaddon.png"
                    media_library = "Videos"
                    target = "video"

                if is_folder:
                    listitem = xbmcgui.ListItem(widget[0])
                    listitem.setArt({"icon": "DefaultFolder.png"})
                    xbmcplugin.addDirectoryItem(
                        handle=int(sys.argv[1]),
                        url=widget[1],
                        listitem=listitem, isFolder=True)
                else:
                    widgetpath = "ActivateWindow(%s,%s,return)" % (media_library, widget[1].split("&")[0])
                    listitem = xbmcgui.ListItem(widget[0], path=widgetpath)
                    props = {}
                    props["list"] = widget[1]
                    props["type"] = widget[2]
                    props["background"] = image
                    props["backgroundName"] = ""
                    props["widgetPath"] = widget[1]
                    props["widgetTarget"] = target
                    props["widgetName"] = widget[0]
                    props["widget"] = item_filter
                    info_tag = listitem.getVideoInfoTag()
                    info_tag.setTitle("smartshortcut")
                    info_tag.setMpaa(repr(props))
                    listitem.setArt({"fanart": image, "thumb": image})
                    xbmcplugin.addDirectoryItem(
                        handle=int(
                            sys.argv[1]),
                        url=widgetpath,
                        listitem=listitem,
                        isFolder=False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_skinhelper_backgrounds():
    result = []
    backgrounds = xbmc.getInfoLabel("Window(Home).Property(SkinHelper.AllBackgrounds)")
    if backgrounds:
        backgrounds = eval(backgrounds)
        win = xbmcgui.Window(10000)
        for key, value in backgrounds:
            label = value
            image = "$INFO[Window(Home).Property(%s)]" % key
            if win.getProperty(key):
                result.append((label, image))
            wall_props = [".Wall", ".Poster.Wall", ".Wall.BW", ".Poster.Wall.BW"]
            for wall_prop in wall_props:
                image = "$INFO[Window(Home).Property(%s%s)]" % (key, wall_prop)
                if win.getProperty("%s%s" % (key, wall_prop)):
                    if ".Poster" in wall_prop:
                        newlabel = "%s: %s" % (xbmc.getInfoLabel("$ADDON[script.skin.helper.backgrounds 32030]"), label)
                    else:
                        newlabel = "%s: %s" % (xbmc.getInfoLabel("$ADDON[script.skin.helper.backgrounds 32029]"), label)
                    if ".BW" in wall_prop:
                        newlabel = "%s (%s)" % (newlabel, xbmc.getInfoLabel(
                            "$ADDON[script.skin.helper.backgrounds 32031]"))
                    result.append((newlabel, image))
                else:
                    break
        del win
    return result


def get_backgrounds():
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    for label, image in get_skinhelper_backgrounds():
        listitem = xbmcgui.ListItem(label, path=image)
        listitem.setArt({"fanart": image, "thumb": image})
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=image, listitem=listitem, isFolder=False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playlists_widgets():
    widgets = []
    import xml.etree.ElementTree as xmltree
    for playlist_path in ["special://skin/playlists/",
                          "special://skin/extras/widgetplaylists/", "special://skin/extras/playlists/"]:
        if xbmcvfs.exists(playlist_path):
            log_msg("skinshortcuts widgets processing: %s" % playlist_path)
            media_array = kodi_json('Files.GetDirectory', {"directory": playlist_path, "media": "files"})
            for item in media_array:
                if item["file"].endswith(".xsp"):
                    playlist = item["file"]
                    contents = xbmcvfs.File(item["file"], 'r')
                    contents_data = try_decode(contents.read())
                    contents.close()
                    xmldata = xmltree.fromstring(try_encode(contents_data))
                    media_type = ""
                    label = item["label"]
                    for line in xmldata.iter():
                        if line.tag == "smartplaylist":
                            media_type = line.attrib.get('type', '')
                        if line.tag == "name":
                            label = line.text
                    try:
                        languageid = int(label)
                        label = xbmc.getLocalizedString(languageid)
                    except Exception:
                        pass
                    if not media_type:
                        mutils = MetadataUtils()
                        media_type = mutils.detect_plugin_content(playlist)
                        del mutils
                    widgets.append([label, playlist, media_type])
    return widgets


def plugin_widgetlisting(pluginpath, sublevel=""):
    widgets = []
    if sublevel:
        media_array = kodi_json('Files.GetDirectory', {"directory": pluginpath, "media": "files"})
    else:
        if not getCondVisibility("System.HasAddon(%s)" % pluginpath):
            return []
        media_array = kodi_json('Files.GetDirectory', {"directory": "plugin://%s" % pluginpath, "media": "files"})
    for item in media_array:
        log_msg("skinshortcuts widgets processing: %s" % (item["file"]))
        content = item["file"]
        label = item["label"]
        if ("script.extendedinfo" in pluginpath and not EXTINFO_CREDS and (
                "info=starred" in content or "info=rated" in content or "info=account" in content)):
            continue
        if item.get("filetype", "") == "file":
            continue
        mutils = MetadataUtils()
        media_type = mutils.detect_plugin_content(item["file"])
        del mutils
        if media_type == "empty":
            continue
        if media_type == "folder":
            content = "plugin://script.skin.helper.service?action=widgets&path=%s&sublevel=%s" % (
                urlencode(item["file"]), label)
        if "reload=" not in content:
            if "movies" in content:
                reloadstr = "&reload=$INFO[Window(Home).Property(widgetreload-movies)]"
            elif "episodes" in content:
                reloadstr = "&reload=$INFO[Window(Home).Property(widgetreload-episodes)]"
            elif "tvshows" in content:
                reloadstr = "&reload=$INFO[Window(Home).Property(widgetreload-tvshows)]"
            elif "musicvideos" in content:
                reloadstr = "&reload=$INFO[Window(Home).Property(widgetreload-musicvideos)]"
            elif "albums" in content or "songs" in content or "artists" in content:
                reloadstr = "&reload=$INFO[Window(Home).Property(widgetreload-music)]"
            else:
                reloadstr = "&reload=$INFO[Window(Home).Property(widgetreload)]"\
                    "$INFO[Window(Home).Property(widgetreload2)]"
            content = content + reloadstr
        content = content.replace("&limit=100", "&limit=25")
        widgets.append([label, content, media_type])
        if pluginpath == "script.extendedinfo" and not sublevel:
            widgets += extendedinfo_youtube_widgets()
    return widgets


def favourites_widgets():
    favourites = kodi_json('Favourites.GetFavourites',
                           {"type": None, "properties": ["path", "thumbnail", "window", "windowparameter"]})
    widgets = []
    if favourites:
        for fav in favourites:
            if "windowparameter" in fav:
                content = fav["windowparameter"]
                if ("script://" not in content.lower() and "mode=9" not in content.lower() and
                        "search" not in content.lower() and "play" not in content.lower()):
                    label = fav["title"]
                    log_msg("skinshortcuts widgets processing favourite: %s" % label)
                    mutils = MetadataUtils()
                    mediatype = mutils.detect_plugin_content(content)
                    del mutils
                    if mediatype and mediatype != "empty":
                        widgets.append([label, content, mediatype])
    return widgets


def static_widgets():
    widgets = []
    addon = xbmcaddon.Addon(ADDON_ID)
    widgets.append([xbmc.getLocalizedString(8), "$INCLUDE[WeatherWidget]", "static"])
    widgets.append([xbmc.getLocalizedString(130), "$INCLUDE[SystemInfoWidget]", "static"])
    widgets.append([addon.getLocalizedString(32025), "$INCLUDE[skinshortcuts-submenu]", "static"])
    if getCondVisibility("System.Hasaddon(script.games.rom.collection.browser)"):
        widgets.append([addon.getLocalizedString(32026), "$INCLUDE[RCBWidget]", "static"])
    del addon
    return widgets


def extendedinfo_youtube_widgets():
    widgets = []
    entrypoints = [
        "plugin://script.extendedinfo?info=youtubeusersearch&&id=Eurogamer",
        "plugin://script.extendedinfo?info=youtubeusersearch&&id=Engadget",
        "plugin://script.extendedinfo?info=youtubeusersearch&&id=MobileTechReview"]
    for entry in entrypoints:
        content = entry
        label = entry.split("id=")[1]
        widgets.append([label, content, "episodes"])
    return widgets


def set_skinshortcuts_property(property_name="", value="", label=""):
    if value or label:
        wait_for_skinshortcuts_window()
        xbmc.sleep(250)
        xbmc.executebuiltin("SetProperty(customProperty,%s)" % try_encode(property_name))
        xbmc.executebuiltin("SetProperty(customValue,%s)" % try_encode(value))
        xbmc.executebuiltin("SendClick(404)")
        xbmc.sleep(250)
        xbmc.executebuiltin("SetProperty(customProperty,%s.name)" % try_encode(property_name))
        xbmc.executebuiltin("SetProperty(customValue,%s)" % try_encode(label))
        xbmc.executebuiltin("SendClick(404)")
        xbmc.sleep(250)
        xbmc.executebuiltin("SetProperty(customProperty,%sName)" % try_encode(property_name))
        xbmc.executebuiltin("SetProperty(customValue,%s)" % try_encode(label))
        xbmc.executebuiltin("SendClick(404)")


def wait_for_skinshortcuts_window():
    for i in range(40):
        if not (getCondVisibility(
                "Window.IsActive(DialogSelect.xml) | "
                "Window.IsActive(script-skin_helper_service-ColorPicker.xml) | "
                "Window.IsActive(DialogKeyboard.xml)")):
            break
        else:
            xbmc.sleep(100)

# Einstiegspunkt für das Plugin
if __name__ == "__main__":
    # Parse Arguments
    import urllib.parse

    params = {}
    if len(sys.argv) > 2 and sys.argv[2]:
        params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    action = params.get('action', '').lower()

    if action == "widgets":
        get_widgets(params.get("path", ""), params.get("sublevel", ""))
    elif action == "backgrounds":
        get_backgrounds()
    elif action == "smartshortcuts":
        get_smartshortcuts(params.get("path", ""))
    elif action == "setproperty":
        set_skinshortcuts_property(params.get("property_name", ""), params.get("value", ""), params.get("label", ""))
    else:
        # Standardmäßig: SmartShortcuts anzeigen
        get_smartshortcuts(params.get("path", ""))
