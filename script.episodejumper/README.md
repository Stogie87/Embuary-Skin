# Episode Jumper

![Kodi](https://img.shields.io/badge/platform-Kodi-blue) ![MIT License](https://img.shields.io/badge/license-MIT-green)

---

## 📺 Übersicht | Overview

**Episode Jumper** ist ein Kodi Addon, das dir das bequeme Springen zur nächsten oder vorherigen Episode einer Serie ermöglicht – für Kodi-Bibliothek, Jellyfin, Emby und EmbyCon.  
Das Addon **ist kein eigenständiges OSD**: Die Buttons müssen manuell in dein Skin (z.B. in die `VideoOSD.xml`) integriert werden.

**Episode Jumper** is a Kodi addon for easy jumping to the next or previous episode of a series.  
It works with the Kodi library, Jellyfin, Emby, and EmbyCon.  
**Note:** The addon is *not* a standalone OSD. You must manually add the buttons to your skin (e.g., in `VideoOSD.xml`).

---

## ✨ Features

- Nächstes/vorheriges Serienepisode abspielen  
  Jump to next/previous TV episode
- Unterstützt Kodi, Jellyfin, Emby, EmbyCon  
  Works with Kodi library, Jellyfin, Emby, EmbyCon
- Leicht in eigene Skins integrierbar  
  Easily integratable into your custom skin

---

## ⚡️ Schnellstart / Quick Start

### 1. Addon herunterladen / Download

Lade das Addon von GitHub herunter.  
Download the addon from GitHub.

### 2. Installation in Kodi

- Öffne Kodi, gehe zu **Addons > Aus ZIP-Datei installieren**
- Installiere das heruntergeladene ZIP
- Open Kodi, go to **Add-ons > Install from ZIP file**
- Install the downloaded ZIP

### 3. Integration ins Skin / Skin Integration

Füge die folgenden Buttons für **"Nächste Episode"** und **"Vorherige Episode"** in deine `VideoOSD.xml` (oder das OSD-Layout deines Skins) ein:

Add the following buttons for **"Next Episode"** and **"Previous Episode"** to your skin's `VideoOSD.xml` (or OSD layout):

```xml
<control type="button" id="620">
    <label>$LOCALIZE["Next Episode"]</label>
    <onclick>RunScript(script.episodejumper,next)</onclick>
    <visible>Player.HasMedia + VideoPlayer.Content(episodes)</visible>
</control>
<control type="button" id="621">
    <label>$LOCALIZE["Previous Episode"]</label>
    <onclick>RunScript(script.episodejumper,previous)</onclick>
    <visible>Player.HasMedia + VideoPlayer.Content(episodes)</visible>
</control>
```

> **Hinweis / Note:**  
> Die Buttons erscheinen und funktionieren erst, wenn du sie manuell in dein OSD eingefügt hast.  
> Buttons will only be visible and usable after you add them yourself.

**Lokalisierung:**  
Übersetzungen funktionieren automatisch, wenn du die richtigen `$LOCALIZE[]`-Einträge verwendest.  
Localization works automatically if you use the proper `$LOCALIZE[]` entries.

---

## ℹ️ Hinweise & Support / Notes & Support

- Das Addon funktioniert nur in Verbindung mit einem angepassten Skin/OSD.  
  This addon requires manual skin/OSD integration.
- Kompatibel mit gängigen Mediatheken (Kodi, Jellyfin, Emby, EmbyCon).  
  Compatible with Kodi, Jellyfin, Emby, EmbyCon libraries/playlists.
- Keine eigene Benutzeroberfläche.  
  No standalone user interface.

---

## 📄 Lizenz / License

Dieses Projekt steht unter der [MIT License](LICENSE).  
This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Beitrag & Feedback / Contribute & Feedback

Fragen, Fehler oder Wünsche? Erstelle ein [Issue](../../issues) oder öffne einen Pull-Request!  
Questions or ideas? Please [open an issue](../../issues) or send a pull request!

---
