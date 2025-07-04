# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, unicode_literals

#################################################################################################

import binascii
import json
import os
import sys
import re
import threading

import unicodedata
from uuid import uuid4
from urllib.parse import quote_plus, urlparse, urlunparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from . import LazyLogger

#################################################################################################

LOG = LazyLogger(__name__)


#################################################################################################


def addon_id():
    return "service.jellyskip"


def kodi_version():
    # Kodistubs returns empty string, causing Python 3 tests to choke on int()
    # TODO: Make Kodistubs version configurable for testing purposes
    if sys.version_info.major == 2:
        default_versionstring = "18"
    else:
        default_versionstring = "19.1 (19.1.0) Git:20210509-85e05228b4"

    version_string = xbmc.getInfoLabel("System.BuildVersion") or default_versionstring
    return int(version_string.split(" ", 1)[0].split(".", 1)[0])


def window(key, value=None, clear=False, window_id=10000):
    """Get or set window properties."""
    window = xbmcgui.Window(window_id)

    if clear:

        LOG.debug("--[ window clear: %s ]", key)
        window.clearProperty(key.replace(".json", "").replace(".bool", ""))
    elif value is not None:
        if key.endswith(".json"):

            key = key.replace(".json", "")
            value = json.dumps(value)

        elif key.endswith(".bool"):

            key = key.replace(".bool", "")
            value = "true" if value else "false"

        window.setProperty(key, value)
    else:
        result = window.getProperty(key.replace(".json", "").replace(".bool", ""))

        if result:
            if key.endswith(".json"):
                result = json.loads(result)
            elif key.endswith(".bool"):
                result = result in ("true", "1")

        return result


def settings(setting, value=None):
    """Get or add add-on settings.
    getSetting returns unicode object.
    """
    addon = xbmcaddon.Addon(addon_id())

    if value is not None:
        if setting.endswith(".bool"):
            setting = setting.replace(".bool", "")
            value = "true" if value else "false"

        addon.setSetting(setting, value)
    else:
        result = addon.getSetting(setting.replace(".bool", ""))

        if result and setting.endswith(".bool"):
            result = result in ("true", "1")

        return result


def create_id():
    return uuid4()


def find(dict, item):
    # FIXME: dead code
    """Find value in dictionary."""
    if item in dict:
        return dict[item]

    for key, value in sorted(dict.items(), key=lambda kv: (kv[1], kv[0])):

        if re.match(key, item, re.I):
            return dict[key]


def translate_path(path):
    """
    Use new library location for translate path starting in Kodi 19
    """
    version = kodi_version()

    if version > 18:
        return xbmcvfs.translatePath(path)
    else:
        return xbmc.translatePath(path)


def run_threaded(target, delay=None, args=None, kwargs=None):
    """Executes the target in a separate thread or timer"""

    if args is None:
        args = ()

    if kwargs is None:
        kwargs = {}

    if delay is not None:
        thread = threading.Timer(delay, target, args=args, kwargs=kwargs)
    else:
        thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    # Daemon threads may not work in Kodi, but enable it anyway
    thread.daemon = True
    thread.start()
    return thread


def from_bytes(text, encoding='utf-8', errors='strict'):
    """Force bytes to str/unicode"""

    if isinstance(text, bytes):
        return text.decode(encoding, errors)
    return text


def from_unicode(text, encoding='utf-8', errors='strict'):
    """Force unicode to bytes"""

    if sys.version_info.major == 2 and isinstance(text,
                                                  unicode):  # noqa: F821; pylint: disable=undefined-variable,useless-suppression
        return text.encode(encoding, errors)
    return text
