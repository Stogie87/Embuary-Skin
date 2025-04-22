import os
import hashlib
from xml.dom.minidom import parse, parseString

# Der Pfad, wo die Addon-Ordner liegen (meist das Repo-Root)
ADDONS_DIR = os.getcwd()


def find_addons():
    """Finde alle addon.xml Dateien in Unterordnern"""
    addon_paths = []
    for item in os.listdir(ADDONS_DIR):
        full_path = os.path.join(ADDONS_DIR, item)
        if os.path.isdir(full_path):
            addon_xml = os.path.join(full_path, 'addon.xml')
            if os.path.isfile(addon_xml):
                addon_paths.append(addon_xml)
    return addon_paths


def create_addons_xml(addon_paths):
    addons = []
    for addon_path in addon_paths:
        with open(addon_path, 'r', encoding='utf-8') as f:
            data = f.read()
            dom = parseString(data)
            addon_element = dom.documentElement
            pretty_xml = addon_element.toprettyxml(indent="  ")
            addons.append(pretty_xml)

    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    addons_xml += '\n'.join(addons)
    addons_xml += '\n</addons>\n'
    return addons_xml


def write_addons_xml(xml_data):
    with open('addons.xml', 'w', encoding='utf-8') as f:
        f.write(xml_data)
    print("addons.xml wurde erstellt.")


def write_md5(xml_data):
    m = hashlib.md5()
    m.update(xml_data.encode('utf-8'))
    with open('addons.xml.md5', 'w') as f:
        f.write(m.hexdigest())
    print("addons.xml.md5 wurde erstellt.")


def create_index_html():
    content = '''<!DOCTYPE html>
<html>
<head><title>Kodi Repository</title></head>
<body>
  <h1>Kodi Repository</h1>
  <p>Wichtige Dateien:</p>
  <ul>
    <li><a href="addons.xml">addons.xml</a></li>
    <li><a href="addons.xml.md5">addons.xml.md5</a></li>
  </ul>
</body>
</html>'''
    with open('index.html', 'w') as f:
        f.write(content)
    print("index.html wurde erstellt.")


if __name__ == '__main__':
    addons = find_addons()
    if not addons:
        print("⚠️ Keine Addons gefunden.")
    else:
        xml = create_addons_xml(addons)
        write_addons_xml(xml)
        write_md5(xml)
        create_index_html()
        print("✅ Repository-Dateien erfolgreich erstellt.")