import os
import re
import hashlib
import zipfile
from xml.dom.minidom import parseString
from urllib.parse import quote

BASE_URL = "https://stogie87.github.io/Embuary-2K-Skin/"

ADDONS_DIR = os.getcwd()
OUTPUT_ADDONS_XML = "addons.xml"
OUTPUT_MD5 = "addons.xml.md5"
OUTPUT_INDEX_HTML = "index.html"
TARGET_ADDON_ID = "skin.embuary2k.omega"

def bump_version_in_addon(addon_path):
    with open(addon_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if f'id="{TARGET_ADDON_ID}"' not in content:
        return None, None  # Nicht das gewünschte Addon

    version_match = re.search(rf'id="{TARGET_ADDON_ID}"\s+version="(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        raise ValueError("⚠️ Keine gültige Versionsnummer im Ziel-Addon gefunden!")

    major, minor, patch = map(int, version_match.groups())
    patch += 1
    new_version = f'{major}.{minor}.{patch}'

    new_content = re.sub(
        rf'(id="{TARGET_ADDON_ID}"\s+version=")\d+\.\d+\.\d+(")',
        rf'\g<1>{new_version}\g<2>',
        content
    )

    with open(addon_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"🔢 Version erhöht für {TARGET_ADDON_ID}: {major}.{minor}.{patch - 1} → {new_version}")
    return new_version, addon_path

def zip_addon(addon_folder, version):
    zip_name = f"{os.path.basename(addon_folder)}-{version}.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(addon_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(addon_folder))
                zipf.write(full_path, arcname=rel_path)
    print(f"📦 ZIP erstellt: {zip_name}")

def find_addons():
    addon_paths = []
    for root, dirs, files in os.walk(ADDONS_DIR):
        if 'addon.xml' in files:
            addon_paths.append(os.path.join(root, 'addon.xml'))
    return addon_paths

def create_addons_xml(addon_paths):
    addons = ""
    for addon_file in addon_paths:
        with open(addon_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'<\?xml.*?\?>', '', content).strip()
        addons += content + "\n\n"
    addons = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<addons>\n{addons}</addons>\n"
    dom = parseString(addons)
    return dom.toprettyxml(indent="  ")

def write_addons_xml(content):
    with open(OUTPUT_ADDONS_XML, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📝 addons.xml geschrieben")

def write_md5(content):
    md5_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    with open(OUTPUT_MD5, 'w') as f:
        f.write(md5_hash)
    print(f"🔐 addons.xml.md5 geschrieben: {md5_hash}")

def generate_zip_index():
    zip_files = []
    for root, dirs, files in os.walk(ADDONS_DIR):
        for file in files:
            if file.endswith('.zip'):
                rel_path = os.path.relpath(os.path.join(root, file), ADDONS_DIR).replace("\\", "/")
                zip_files.append(rel_path)

    with open(OUTPUT_INDEX_HTML, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Kodi ZIPs</title></head><body>\n")
        f.write("<h1>Kodi Addon ZIP-Dateien</h1><ul>\n")
        for zip_file in sorted(zip_files):
            f.write(f"<li><a href='{BASE_URL}{quote(zip_file)}'>{zip_file}</a></li>\n")
        f.write("</ul></body></html>\n")

    print(f"🌐 index.html geschrieben mit {len(zip_files)} ZIP-Dateien")

def main():
    addon_dirs = [
        d for d in os.listdir()
        if os.path.isdir(d) and os.path.isfile(os.path.join(d, 'addon.xml'))
    ]

    if not addon_dirs:
        print("⚠️ Kein Addon-Ordner mit addon.xml gefunden.")
        return

    version = None
    for addon_dir in addon_dirs:
        addon_path = os.path.join(addon_dir, 'addon.xml')
        bumped_version, bumped_path = bump_version_in_addon(addon_path)
        if bumped_version:
            version = bumped_version
            zip_addon(addon_dir, version)

    addon_paths = find_addons()
    addons_xml = create_addons_xml(addon_paths)
    write_addons_xml(addons_xml)
    write_md5(addons_xml)
    generate_zip_index()

    print("\n✅ Fertig! Repository aktualisiert.")

if __name__ == "__main__":
    main()
