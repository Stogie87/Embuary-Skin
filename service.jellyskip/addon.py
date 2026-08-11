import xbmcaddon
import xbmcgui
import xbmc

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')

language = xbmc.getLanguage(xbmc.ISO_639_1)

if language == "de":
    line1 = (
        "Jellyskip ist ein Kodi-Plugin für Jellyfin-Mediensegmente. Intro, Outro, Rückblick, Vorschau und Werbung "
        "können in den Einstellungen getrennt aktiviert oder deaktiviert werden. Die Segmenterkennung erfolgt zuverlässig "
        "über Jellyfin-Metadaten. Das Plugin springt präzise zum Segmentende oder beim Outro direkt zur nächsten Folge. "
        "Die Skip-Buttons passen sich dynamisch an die gewählten Skin-Farben und die Kodi-Sprache an."
    )
else:
    line1 = (
        "Jellyskip is a Kodi plugin for Jellyfin media segments. Intro, Outro, Recap, Preview and Commercial can be "
        "enabled or disabled independently in the settings. Segment detection uses Jellyfin metadata. The plugin accurately "
        "skips to the segment end or, for outros, directly to the next episode. Skip buttons adapt to the skin colors and Kodi UI language."
    )

xbmcgui.Dialog().ok(addonname, line1)
