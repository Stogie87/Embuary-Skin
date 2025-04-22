import os
import re
import hashlib
import zipfile
from xml.dom.minidom import parseString
from urllib.parse import quote

BASE_URL = "https://stogie87.github.io/Embuary-2K-Skin/"
OUTPUT_ADDONS_XML = "addons.xml"
OUTPUT_MD5 = "addons.xml.md5"
OUTPUT_INDEX_HTML = "index.html"

def get_current_version(addon_xml_path):
    with open(addon_xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'<addon[^>]+version="(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        raise ValueError(f"⚠️ Keine gültige Versionsnummer in {addon_xml_path} gefunden!")
    return tuple(map(int, match.groups()))

def update_addon_version(addon_xml_path, new_version):
    with open(addon_xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(
        r'(<addon[^>]+version=")(\d+\.\d+\.\d+)(")',
        r'\g<1>' + new_version + r'\g<3>',
        content
    )

    with open(addon_xml_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def zip_addon(addon_folder, version):
    zip_name = f"{addon_folder}-{version}.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(addon_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(addon_folder))
                zipf.write(full_path, arcname=rel_path)
    print(f"📦 ZIP erstellt: {zip_name}")
    return zip_name

def get_folder_checksum(folder_path):
    checksums = []
    for root, _, files in os.walk(folder_path):
        for file in sorted(files):
            path = os.path.join(root, file)
            with open(path, 'rb') as f:
                data = f.read()
                checksums.append(hashlib.md5(data).hexdigest())
    return hashlib.md5("".join(checksums).encode()).hexdigest()

def get_last_zip_checksum(addon_id):
    zip_files = sorted([
        f for f in os.listdir()
        if f.startswith(addon_id + "-") and f.endswith(".zip")
    ])
    if not zip_files:
        return None
    latest = zip_files[-1]
    with zipfile.ZipFile(latest, 'r') as zipf:
        data = b''.join([zipf.read(name) for name in sorted(zipf.namelist())])
    return hashlib.md5(data).hexdigest()

def should_bump_version(addon_id, addon_folder):
    current_checksum = get_folder_checksum(addon_folder)
    last_checksum = get_last_zip_checksum(addon_id)
    return current_checksum != last_checksum

def find_addons():
    return [
        d for d in os.listdir()
        if os.path.isdir(d) and os.path.isfile(os.path.join(d, 'addon.xml'))
    ]

def create_addons_xml(addon_dirs):
    addons = ""
    for addon_dir in addon_dirs:
        addon_path = os.path.join(addon_dir, 'addon.xml')
        with open(addon_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'<\?xml.*?\?>', '', content).strip()
        addons += content + "\n\n"
    addons = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<addons>\n{addons}</addons>\n"
    dom = parseString(addons)
    return dom.toprettyxml(indent="  ")

def write_addons_xml(content):
    with open(OUTPUT_ADDONS_XML, 'w', encoding='utf-8') as f:
        f.write(content)
    print("📝 addons.xml geschrieben")

def write_md5(content):
    md5_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    with open(OUTPUT_MD5, 'w') as f:
        f.write(md5_hash)
    print(f"🔐 addons.xml.md5 geschrieben: {md5_hash}")

def generate_zip_index():
    zip_files = [f for f in os.listdir() if f.endswith('.zip')]
    with open(OUTPUT_INDEX_HTML, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Kodi ZIPs</title></head><body>\n")
        f.write("<h1>Kodi Addon ZIP-Dateien</h1><ul>\n")
        for zip_file in sorted(zip_files):
            f.write(f"<li><a href='{BASE_URL}{quote(zip_file)}'>{zip_file}</a></li>\n")
        f.write("</ul></body></html>\n")
    print(f"🌐 index.html geschrieben mit {len(zip_files)} ZIP-Dateien")

def main():
    addon_dirs = find_addons()

    for addon_dir in addon_dirs:
        addon_path = os.path.join(addon_dir, 'addon.xml')
        addon_id = os.path.basename(addon_dir)

        if should_bump_version(addon_id, addon_dir):
            major, minor, patch = get_current_version(addon_path)
            patch += 1
            new_version = f"{major}.{minor}.{patch}"
            update_addon_version(addon_path, new_version)
            zip_addon(addon_dir, new_version)
            print(f"🔢 Version erhöht für {addon_id}: {major}.{minor}.{patch - 1} → {new_version}")
        else:
            print(f"⏩ Keine Änderung an {addon_id}, Version bleibt gleich.")

    addons_xml = create_addons_xml(addon_dirs)
    write_addons_xml(addons_xml)
    write_md5(addons_xml)
    generate_zip_index()
    print("\n✅ Fertig! Repository aktualisiert.")

if __name__ == "__main__":
    main()
