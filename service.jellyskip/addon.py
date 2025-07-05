import xbmcaddon
import xbmcgui
import xbmc

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')

language = xbmc.getLanguage(xbmc.ISO_639_1)

if language == "de":
    line1 = (
        "Jellyskip ist ein Kodi-Plugin, das während der Wiedergabe von Serienepisoden aus Jellyfin automatisch "
        "einen 'Intro überspringen'- und 'Outro überspringen'-Button anzeigt. Die Segmenterkennung erfolgt zuverlässig "
        "über Jellyfin-Metadaten. Das Plugin springt präzise zum Segmentende oder direkt zur nächsten Folge. "
        "Das Design des Skip-Buttons passt sich dynamisch an die gewählten Skin-Farben an und unterstützt mehrere Sprachen."
    )
else:
    line1 = (
        "Jellyskip is a Kodi plugin that automatically displays 'Skip Intro' and 'Skip Outro' buttons during playback of "
        "TV episodes from Jellyfin. Segment detection is reliable via Jellyfin metadata. The plugin accurately skips to "
        "the segment end or directly to the next episode. The button design dynamically adapts to your chosen skin colors and supports multiple languages."
    )

xbmcgui.Dialog().ok(addonname, line1)
