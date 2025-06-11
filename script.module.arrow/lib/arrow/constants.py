"""Constants used internally in arrow."""

import sys

# Defensive import: ensure 'datetime' really is the datetime.datetime class,
# even if another addon/script has globally poisoned the name.
try:
    from datetime import datetime as _orig_datetime
except ImportError:
    import importlib
    _orig_datetime = importlib.import_module("datetime").datetime

datetime = _orig_datetime  # Reset local reference just to be safe

if sys.version_info < (3, 8):  # pragma: no cover
    from typing_extensions import Final
else:
    from typing import Final  # pragma: no cover

# Platform-independent max timestamp calculation
try:
    # Try real max; fails on some platforms/32bit/Windows
    _MAX_TIMESTAMP = datetime.max.timestamp()
except Exception:
    # Fallback for systems that don't support datetime.max.timestamp()
    is_64bits = sys.maxsize > 2**32
    try:
        _MAX_TIMESTAMP = (
            datetime(3000, 1, 1, 23, 59, 59, 999999).timestamp()
            if is_64bits
            else datetime(2038, 1, 1, 23, 59, 59, 999999).timestamp()
        )
    except Exception:
        # Last resort fallback: Use 2038 for 32-bit, 3000 for 64-bit, UNIX epoch otherwise
        _MAX_TIMESTAMP = 2145916799 if not is_64bits else 32503679999

MAX_TIMESTAMP: "Final[float]" = _MAX_TIMESTAMP
MAX_TIMESTAMP_MS: "Final[float]" = MAX_TIMESTAMP * 1000
MAX_TIMESTAMP_US: "Final[float]" = MAX_TIMESTAMP * 1_000_000

try:
    MAX_ORDINAL: "Final[int]" = datetime.max.toordinal()
except Exception:
    MAX_ORDINAL: "Final[int]" = 3652059  # Fallback for datetime.max.toordinal()

MIN_ORDINAL: "Final[int]" = 1

DEFAULT_LOCALE: "Final[str]" = "en-us"

# Supported dehumanize locales (unverändert)
DEHUMANIZE_LOCALES = {
    "en", "en-us", "en-gb", "en-au", "en-be", "en-jp", "en-za", "en-ca", "en-ph",
    "fr", "fr-fr", "fr-ca", "it", "it-it", "es", "es-es", "el", "el-gr", "ja", "ja-jp",
    "se", "se-fi", "se-no", "se-se", "sv", "sv-se", "fi", "fi-fi", "zh", "zh-cn", "zh-tw", "zh-hk",
    "nl", "nl-nl", "be", "be-by", "pl", "pl-pl", "ru", "ru-ru", "af", "bg", "bg-bg", "ua", "uk", "uk-ua",
    "mk", "mk-mk", "de", "de-de", "de-ch", "de-at", "nb", "nb-no", "nn", "nn-no", "pt", "pt-pt", "pt-br",
    "tl", "tl-ph", "vi", "vi-vn", "tr", "tr-tr", "az", "az-az", "da", "da-dk", "ml", "hi", "cs", "cs-cz",
    "sk", "sk-sk", "fa", "fa-ir", "mr", "ca", "ca-es", "ca-ad", "ca-fr", "ca-it", "eo", "eo-xx", "bn",
    "bn-bd", "bn-in", "rm", "rm-ch", "ro", "ro-ro", "sl", "sl-si", "id", "id-id", "ne", "ne-np", "ee",
    "et", "sw", "sw-ke", "sw-tz", "la", "la-va", "lt", "lt-lt", "ms", "ms-my", "ms-bn", "or", "or-in",
    "lb", "lb-lu", "zu", "zu-za", "sq", "sq-al", "ta", "ta-in", "ta-lk", "ur", "ur-pk", "ka", "ka-ge",
    "kk", "kk-kz", "am", "am-et", "hy-am", "hy", "uz", "uz-uz",
}
