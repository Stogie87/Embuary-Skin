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

def get_current_version(addon_path):
    with open(addon_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'version="(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        raise ValueError(f"❌ Keine gültige Versionsnummer in {addon_path}")
    return tuple(map(int, match.groups()))

def generate_zip_filename(addon_dir, version):
    return f"{os.path.basename(addon_dir)}-{version}.zip"

def calculate_folder_hash(folder_path):
    """Erzeugt einen Hash aller Dateien im Ordner, um Änderungen zu erkennen."""
    sha = hashlib.sha256()
    for root, _, files in sorted(os.walk(folder_path)):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha.update(chunk)
    return sha.hexdigest()

def get_latest_zip_hash(addon_dir):
    """Sucht die neueste ZIP für ein Addon und berechnet ihren Inhaltshash."""
    prefix = os.path.basename(addon_dir)
    zips = sorted(
        [f for f in os.listdir() if f.startswith(prefix) and f.endswith('.zip')],
        reverse=True
    )
    if not zips:
        return None
    latest_zip = zips[0]
    sha = hashlib.sha256()
    with zipfile.ZipFile(latest_zip, 'r') as zipf:
        for name in sorted(zipf.namelist()):
            sha.update(zipf.read(name))
    return sha.hexdigest()

def bump_version(version):
    major, minor, patch = version
    return f"{major}.{minor}.{patch + 1}"

def zip_addon(addon_folder, version):
    zip_name = generate_zip_filename(addon_folder, version)
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(addon_folder):
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
    zip_files = [
        os.path.relpath(os.path.join(root, file), ADDONS_DIR).replace("\\", "/")
        for root, dirs, files in os.walk(ADDONS_DIR)
        for file in files if file.endswith('.zip')
    ]
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

    for addon_dir in addon_dirs:
        addon_path = os.path.join(addon_dir, 'addon.xml')
        current_version = get_current_version(addon_path)
        folder_hash = calculate_folder_hash(addon_dir)
        zip_hash = get_latest_zip_hash(addon_dir)

        if folder_hash != zip_hash:
            new_version = bump_version(current_version)
            with open(addon_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = re.sub(
                r'version="\d+\.\d+\.\d+"',
                f'version="{new_version}"',
                content
            )
            with open(addon_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🔢 Version erhöht: {current_version} → {new_version}")
            zip_addon(addon_dir, new_version)
        else:
            print(f"⏩ Keine Änderung im Ordner {addon_dir}, ZIP bleibt unverändert.")

    addon_paths = find_addons()
    addons_xml = create_addons_xml(addon_paths)
    write_addons_xml(addons_xml)
    write_md5(addons_xml)
    generate_zip_index()

    print("\n✅ Fertig! Repository aktualisiert.")

if __name__ == "__main__":
    main()
