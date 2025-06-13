# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import os
import xml.etree.ElementTree as ET
from xbmcvfs import translatePath

# === Skin-Pfad und Style-Datei ===
skin_path = translatePath('special://skin/')
styles_xml_path = os.path.join(skin_path, "xml", "flag_styles.xml")

# === XML mit Styles einlesen ===
try:
    tree = ET.parse(styles_xml_path)
    root = tree.getroot()
    styles = [elem.text.strip() for elem in root.findall("style") if elem.text and elem.text.strip()]
except Exception as e:
    xbmcgui.Dialog().ok("Fehler", f"Datei 'xml/flag_styles.xml' nicht gefunden oder fehlerhaft!\n{e}")
    raise SystemExit

if not styles:
    xbmcgui.Dialog().ok("Fehler", "Keine Style-Einträge in 'xml/flag_styles.xml' gefunden!")
    raise SystemExit

def beautify(name):
    return " ".join(w.capitalize() for w in name.replace("_", " ").split())

options = [beautify(s) for s in styles]

# === Auswahl-Dialog anzeigen ===
dialog = xbmcgui.Dialog()
idx = dialog.select("Flaggen-Stil wählen", options)

# === Auswahl wurde getroffen ===
if idx >= 0:
    selected_style = styles[idx]

    # Verwende Pfade für flags
    skin_style_path = f"flags/{selected_style}"
    skin_style_path_slash = f"flags/{selected_style}/"

    # Setze beide Strings
    xbmc.executebuiltin("Skin.Reset(codeclogos_flag_path)")
    xbmc.executebuiltin(f"Skin.SetString(codeclogos_flag_path,{skin_style_path})")
    xbmc.executebuiltin(f"Skin.SetString(codeclogos_flag_path_slash,{skin_style_path_slash})")
    xbmc.executebuiltin(f"Skin.SetString(codeclogos_flag_name,{options[idx]})")
    xbmc.executebuiltin(f'Notification("Codec Flags", "Stil gesetzt: {options[idx]}")')

else:
    xbmc.log("[CodecFlags] Auswahl abgebrochen.", xbmc.LOGINFO)
