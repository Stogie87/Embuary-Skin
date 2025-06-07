# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import re

INCLUDE_ID = 'codeclogos_include'
SCALE_ID = 'codeclogos_scale'
BG1_ID = 'codeclogos_bg1'
BG2_ID = 'codeclogos_bg2'
BAR_INCLUDE_ID = 'bar_position_include'  # Neu: Variable für Balken-Include

size_steps = [x for x in range(100, 301, 10)]  # Jetzt bis 300%

def extract_current_percent(current_include):
    try:
        percent = int(re.sub(r'\D', '', current_include))
        return percent if percent in size_steps else 100
    except Exception:
        return 100

current_include = xbmc.getInfoLabel(f'Skin.String({INCLUDE_ID})') or "CodecLogoSize_100"
current_percent = extract_current_percent(current_include)
try:
    current_idx = size_steps.index(current_percent)
except Exception:
    current_idx = 0

options = [f"{x}%" for x in size_steps]
dialog = xbmcgui.Dialog()
idx = dialog.select("Codec Logo Größe wählen", options, preselect=current_idx)
if idx == -1:
    xbmcgui.Dialog().notification("Abgebrochen", "Keine Änderung vorgenommen.", xbmcgui.NOTIFICATION_INFO, 2000)
    exit(0)

new_percent = size_steps[idx]
new_include = f"CodecLogoSize_{new_percent}"

# Hintergrund-Includes passend setzen
bg1_include = f"CodecLogoBG1_{new_percent}"
bg2_include = f"CodecLogoBG2_{new_percent}"

# NEU: Bar-Position-Include passend setzen
bar_include = f"BarPosition_{new_percent}"

# Setzen der Skin-Variablen
xbmc.executebuiltin(f'Skin.SetString({INCLUDE_ID},{new_include})')
xbmc.executebuiltin(f'Skin.SetString({SCALE_ID},{new_percent})')
xbmc.executebuiltin(f'Skin.SetString({BG1_ID},{bg1_include})')
xbmc.executebuiltin(f'Skin.SetString({BG2_ID},{bg2_include})')
xbmc.executebuiltin(f'Skin.SetString({BAR_INCLUDE_ID},{bar_include})')

# Nur noch den Prozentsatz anzeigen
xbmcgui.Dialog().notification(
    "Logo-Größe",
    f"{new_percent}% gesetzt",
    xbmcgui.NOTIFICATION_INFO,
    3000
)
