# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import os
import xml.etree.ElementTree as ET
from xbmcvfs import translatePath

# Skin-Pfad
skin_path = translatePath('special://skin/')
styles_xml_path = os.path.join(skin_path, "xml", "codec_styles.xml")

# XML mit Styles einlesen
try:
    tree = ET.parse(styles_xml_path)
    root = tree.getroot()
    styles = [elem.text.strip() for elem in root.findall("style") if elem.text and elem.text.strip()]
except Exception as e:
    xbmcgui.Dialog().ok("Fehler", f"Datei 'xml/codec_styles.xml' nicht gefunden oder fehlerhaft!\n{e}")
    raise SystemExit

if not styles:
    xbmcgui.Dialog().ok("Fehler", "Keine Style-Einträge in 'xml/codec_styles.xml' gefunden!")
    raise SystemExit

def beautify(name):
    return " ".join(w.capitalize() for w in name.replace("_", " ").split())

options = [beautify(s) for s in styles]

dialog = xbmcgui.Dialog()
idx = dialog.select("Codec-Logo-Style wählen", options)

if idx >= 0:
    selected_style = styles[idx]
    # Baue explizit OHNE Slash am Ende!
    skin_style_path = f"codecs/{selected_style}"
    # Auch mit Slash, für Tests
    skin_style_path_slash = f"codecs/{selected_style}/"

    # Setze beide Strings für Kompatibilität mit alten XML-Definitionen
    xbmc.executebuiltin("Skin.Reset(codeclogos_path)")
    xbmc.executebuiltin(f"Skin.SetString(codeclogos_path,{skin_style_path})")
    xbmc.executebuiltin(f"Skin.SetString(codeclogos_path_slash,{skin_style_path_slash})")
    xbmc.executebuiltin(f"Skin.SetString(codeclogos_name,{options[idx]})")
    xbmc.executebuiltin('Notification("Codec Logos", "Style gesetzt: {}")'.format(options[idx]))

else:
    xbmc.log("[CodecLogos] Auswahl abgebrochen.", xbmc.LOGINFO)
