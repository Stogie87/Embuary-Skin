from xml.dom.minidom import parse
import os
import sys
import math
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from traceback import format_exc
from contextlib import contextmanager

ADDON_ID = "script.skin.helper.colorpicker"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo('path')
COLORFILES_PATH = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}/colors/")
SKINCOLORFILES_PATH = xbmcvfs.translatePath(f"special://profile/addon_data/{xbmc.getSkinDir()}/colors/")
SKINCOLORFILE = xbmcvfs.translatePath("special://skin/extras/colors/colors.xml")
WINDOW = xbmcgui.Window(10000)
SUPPORTS_PIL = False
PYTHON3 = sys.version_info.major == 3

# HELPERS ###########################################

def log_msg(msg, level=xbmc.LOGDEBUG):
    xbmc.log(f"Skin Helper Service ColorPicker --> {msg}", level=level)

def log_exception(modulename, exceptiondetails):
    log_msg(f"Exception in {modulename} ! --> {exceptiondetails}", xbmc.LOGERROR)

@contextmanager
def busy_dialog():
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

# IMPORT PIL/PILLOW ###################################

try:
    from PIL import Image
    img = Image.new("RGB", (1, 1))
    del img
    SUPPORTS_PIL = True
except Exception as exc:
    log_exception(__name__, exc)
    try:
        import Image
        img = Image.new("RGB", (1, 1))
        del img
        SUPPORTS_PIL = True
    except Exception as exc:
        log_exception(__name__, exc)

class ColorPicker(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.colors_list = None
        self.skinstring = None
        self.win_property = None
        self.shortcut_property = None
        self.colors_path = None
        self.saved_color = None
        self.current_window = None
        self.header_label = None
        self.colors_file = None
        self.all_colors = {}
        self.all_palettes = []
        self.active_palette = None
        self.action_exitkeys_id = [10, 13]
        self.win = xbmcgui.Window(10000)
        self.build_colors_list()
        self.result = -1

        if xbmcvfs.exists(SKINCOLORFILE) and not xbmcvfs.exists(SKINCOLORFILES_PATH):
            xbmcvfs.mkdirs(SKINCOLORFILES_PATH)
        if not xbmcvfs.exists(COLORFILES_PATH):
            xbmcvfs.mkdirs(COLORFILES_PATH)

    def add_color_to_list(self, colorname, colorstring):
        if not colorname:
            colorname = colorstring
        color_image_file = self.create_color_swatch_image(colorstring)
        listitem = xbmcgui.ListItem(label=colorname)
        listitem.setArt({'icon': color_image_file})
        listitem.setProperty("colorstring", colorstring)
        self.colors_list.addItem(listitem)

    def build_colors_list(self):
        if xbmcvfs.exists(SKINCOLORFILE):
            colors_file = SKINCOLORFILE
            self.colors_path = SKINCOLORFILES_PATH
        else:
            colors_file = os.path.join(ADDON_PATH, 'resources', 'colors', 'colors.xml')
            self.colors_path = COLORFILES_PATH

        doc = parse(colors_file)
        palette_listing = doc.documentElement.getElementsByTagName('palette')
        if palette_listing:
            for item in palette_listing:
                palette_name = item.attributes['name'].nodeValue
                self.all_colors[palette_name] = self.get_colors_from_xml(item)
                self.all_palettes.append(palette_name)
        else:
            self.all_colors["all"] = self.get_colors_from_xml(doc.documentElement)
            self.all_palettes.append("all")

    def load_colors_palette(self, palette_name=""):
        self.colors_list.reset()
        if not palette_name:
            palette_name = self.all_palettes[0]
        if palette_name != "all":
            self.current_window.setProperty("palettename", palette_name)
        if not self.all_colors.get(palette_name):
            log_msg(f"No palette exists with name {palette_name}", xbmc.LOGERROR)
            return
        for item in self.all_colors[palette_name]:
            self.add_color_to_list(item[0], item[1])

    def onInit(self):
        with busy_dialog():
            self.current_window = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
            self.colors_list = self.getControl(3110)
            try:
                self.getControl(1).setLabel(self.header_label)
            except Exception:
                pass

            curvalue = ""
            curvalue_name = ""
            if self.skinstring:
                curvalue = xbmc.getInfoLabel(f"Skin.String({self.skinstring})")
                curvalue_name = xbmc.getInfoLabel(f"Skin.String({self.skinstring}.name)")
            if self.win_property:
                curvalue = WINDOW.getProperty(self.win_property)
                curvalue_name = xbmc.getInfoLabel(f"{self.win_property}.name")
            if curvalue:
                self.current_window.setProperty("colorstring", curvalue)
                if curvalue != curvalue_name:
                    self.current_window.setProperty("colorname", curvalue_name)
                self.current_window.setProperty("current.colorstring", curvalue)
                if curvalue != curvalue_name:
                    self.current_window.setProperty("current.colorname", curvalue_name)

            self.load_colors_palette(self.active_palette)

            if self.current_window.getProperty("colorstring"):
                self.current_window.setFocusId(3010)
            else:
                self.current_window.setFocusId(3110)
                self.colors_list.selectItem(0)
                self.current_window.setProperty("colorstring",
                                                self.colors_list.getSelectedItem().getProperty("colorstring"))
                self.current_window.setProperty("colorname",
                                                self.colors_list.getSelectedItem().getLabel())

            if self.current_window.getProperty("colorstring"):
                self.set_opacity_slider()

    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448):
            self.save_color_setting(restoreprevious=True)
            self.close_dialog()

    def close_dialog(self):
        self.close()

    def set_opacity_slider(self):
        colorstring = self.current_window.getProperty("colorstring")
        try:
            if colorstring and colorstring.lower() != "none":
                a, r, g, b = [int(colorstring[i:i+2], 16) for i in range(0, 8, 2)]
                a = 100.0 * a / 255
                self.getControl(3015).setPercent(float(a))
        except Exception:
            pass

    def save_color_setting(self, restoreprevious=False):
        if restoreprevious:
            colorname = self.current_window.getProperty("current.colorname")
            colorstring = self.current_window.getProperty("current.colorstring")
        else:
            colorname = self.current_window.getProperty("colorname")
            colorstring = self.current_window.getProperty("colorstring")

        if not colorname:
            colorname = colorstring

        self.create_color_swatch_image(colorstring)

        if self.skinstring and (not colorstring or colorstring == "None"):
            xbmc.executebuiltin(f"Skin.SetString({self.skinstring}.name, {ADDON.getLocalizedString(32013)})")
            xbmc.executebuiltin(f"Skin.SetString({self.skinstring}, None)")
            xbmc.executebuiltin(f"Skin.Reset({self.skinstring}.base)")
        elif self.skinstring and colorstring:
            xbmc.executebuiltin(f"Skin.SetString({self.skinstring}.name, {colorname})")
            xbmc.executebuiltin(f"Skin.SetString({self.skinstring}, {colorstring})")
            colorbase = "ff" + colorstring[2:]
            xbmc.executebuiltin(f"Skin.SetString({self.skinstring}.base, {colorbase})")
        elif self.win_property:
            WINDOW.setProperty(self.win_property, colorstring)
            WINDOW.setProperty(self.win_property + ".name", colorname)

    def onClick(self, controlID):
        if controlID == 3110:
            item = self.colors_list.getSelectedItem()
            colorstring = item.getProperty("colorstring")
            self.current_window.setProperty("colorstring", colorstring)
            self.current_window.setProperty("colorname", item.getLabel())
            self.set_opacity_slider()
            self.current_window.setFocusId(3012)
            self.current_window.setProperty("color_chosen", "true")
            self.save_color_setting()
        elif controlID == 3010:
            dialog = xbmcgui.Dialog()
            colorstring = dialog.input(ADDON.getLocalizedString(32012),
                                       self.current_window.getProperty("colorstring"), type=xbmcgui.INPUT_ALPHANUM)
            self.current_window.setProperty("colorname", ADDON.getLocalizedString(32050))
            self.current_window.setProperty("colorstring", colorstring)
            self.set_opacity_slider()
            self.save_color_setting()
        elif controlID == 3011:
            self.current_window.setProperty("colorstring", "")
            self.save_color_setting()

        if controlID in (3012, 3011):
            if self.skinstring or self.win_property:
                self.close_dialog()
            elif self.shortcut_property:
                self.result = (self.current_window.getProperty("colorstring"),
                               self.current_window.getProperty("colorname"))
                self.close_dialog()
        elif controlID == 3015:
            try:
                colorstring = self.current_window.getProperty("colorstring")
                opacity = self.getControl(3015).getPercent()
                a = int(round(opacity / 100.0 * 255))
                r, g, b = [int(colorstring[i:i+2], 16) for i in (2, 4, 6)]
                colorstringvalue = f"{a:02x}{r:02x}{g:02x}{b:02x}"
                self.current_window.setProperty("colorstring", colorstringvalue)
                self.save_color_setting()
            except Exception:
                pass
        elif controlID == 3030:
            ret = xbmcgui.Dialog().select(ADDON.getLocalizedString(32141), self.all_palettes)
            self.load_colors_palette(self.all_palettes[ret])

    def create_color_swatch_image(self, colorstring):
        color_image_file = None
        if colorstring:
            paths = [
                f"{COLORFILES_PATH}{colorstring}.png",
                f"{SKINCOLORFILES_PATH}{colorstring}.png" if xbmcvfs.exists(SKINCOLORFILE) else ""
            ]
            for color_image_file in filter(None, paths):
                if not xbmcvfs.exists(color_image_file):
                    if SUPPORTS_PIL:
                        try:
                            colorstring = colorstring.strip().lstrip('#')
                            a, r, g, b = [int(colorstring[i:i+2], 16) for i in range(0, 8, 2)]
                            img = Image.new("RGBA", (16, 16), (r, g, b, a))
                            img.save(color_image_file)
                            del img
                        except Exception as exc:
                            log_exception(__name__, exc)
                    else:
                        xbmcvfs.copy(f"https://dummyimage.com/16/{colorstring[2:]}/{colorstring[2:]}.png", color_image_file)
                        log_msg("Local PIL module not available, generating color swatch image with online service", xbmc.LOGWARNING)
        return color_image_file

    def get_colors_from_xml(self, xmlelement):
        items = []
        listing = xmlelement.getElementsByTagName('color')
        for color in listing:
            name = color.attributes['name'].nodeValue.lower()
            colorstring = color.childNodes[0].nodeValue.lower()
            items.append((name, colorstring))
        return items
