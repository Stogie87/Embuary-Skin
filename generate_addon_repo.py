import os
import re
import hashlib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).parent
ADDONS_XML_PATH = ROOT / "addons.xml"
MD5_PATH = ROOT / "addons.xml.md5"
INDEX_HTML_PATH = ROOT / "index.html"

# Addons, die wie ein Repository behandelt werden sollen
REPO_ID_PREFIX = "repository."

def get_current_version(addon_path):
    addon_xml = addon_path / "addon.xml"
    tree = ET.parse(addon_xml)
    root = tree.getroot()
    version = root.attrib.get("version", "")
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ValueError(f"⚠️ Keine gültige Versionsnummer in {addon_path} gefunden!")
    return list(map(int, version.split(".")))

def update_addon_version(addon_path, new_version):
    addon_xml = addon_path / "addon.xml"
    content = addon_xml.read_text(encoding="utf-8")

    def replace_version(match):
        return match.group(0).replace(match.group(1), new_version)

    new_content = re.sub(r'version="(\d+\.\d+\.\d+)"', replace_version, content, count=1)
    addon_xml.write_text(new_content, encoding="utf-8")

def has_changes(addon_path, zip_path):
    if not zip_path.exists():
        return True
    latest_zip_time = zip_path.stat().st_mtime
    for path in addon_path.rglob("*"):
        if path.is_file() and path.stat().st_mtime > latest_zip_time:
            return True
    return False

def zip_addon(addon_path, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for file in addon_path.rglob("*"):
            if file.is_file():
                z.write(file, file.relative_to(addon_path.parent))

def build_addons_xml(addon_dirs):
    addons = []
    for path in addon_dirs:
        addon_xml = path / "addon.xml"
        xml = addon_xml.read_text(encoding="utf-8").strip()
        xml = re.sub(r"<\?xml.*?\?>", "", xml, count=1).strip()
        addons.append(xml)
    return "<addons>\n" + "\n\n".join(addons) + "\n</addons>\n"

def write_md5(file_path, md5_path):
    md5_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
    md5_path.write_text(md5_hash)

def generate_index_html(zip_files):
    links = [f'<li><a href="{zip_path.name}">{zip_path.name}</a></li>' for zip_path in zip_files]
    html = f"""<html><body><h1>Kodi Add-ons</h1><ul>{''.join(links)}</ul></body></html>"""
    INDEX_HTML_PATH.write_text(html, encoding="utf-8")

def update_repository_xml(repo_path, addon_paths):
    addon_ids = [p.name for p in addon_paths if not p.name.startswith(REPO_ID_PREFIX)]
    repo_xml_path = repo_path / "addon.xml"
    tree = ET.parse(repo_xml_path)
    root = tree.getroot()

    # Setze children im repository automatisch
    extension = root.find("./extension[@point='xbmc.addon.repository']")
    if extension is not None:
        for child in extension.findall("dir"):
            extension.remove(child)

        dir_elem = ET.Element("dir", attrib={"minversion": "20.999.0"})
        ET.SubElement(dir_elem, "info", {"compressed": "false"}).text = "https://raw.githubusercontent.com/Teddyknuddel/embuary.omega/master/addons.xml"
        ET.SubElement(dir_elem, "checksum").text = "https://raw.githubusercontent.com/Teddyknuddel/embuary.omega/master/addons.xml.md5"
        ET.SubElement(dir_elem, "datadir", {"zip": "true"}).text = "https://raw.githubusercontent.com/Teddyknuddel/embuary.omega/master/"
        extension.append(dir_elem)

    repo_xml_str = ET.tostring(root, encoding="unicode")
    repo_xml_str = re.sub(r"^\s*\n", "", repo_xml_str, flags=re.MULTILINE)
    repo_xml_path.write_text(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n{repo_xml_str}', encoding="utf-8")

def main():
    addon_dirs = [d for d in ROOT.iterdir() if d.is_dir() and (d / "addon.xml").exists()]
    updated_zip_paths = []

    for addon_path in addon_dirs:
        addon_id = addon_path.name
        is_repo = addon_id.startswith(REPO_ID_PREFIX)

        major, minor, patch = get_current_version(addon_path)
        new_version = f"{major}.{minor}.{patch + 1}"

        zip_name = f"{addon_id}-{new_version}.zip"
        zip_path = (ROOT if is_repo else addon_path) / zip_name

        if has_changes(addon_path, zip_path):
            update_addon_version(addon_path, new_version)
            zip_addon(addon_path, zip_path)
            updated_zip_paths.append(zip_path)

    # repository.*-addon.xml anpassen
    for repo_path in [p for p in addon_dirs if p.name.startswith(REPO_ID_PREFIX)]:
        update_repository_xml(repo_path, addon_dirs)

    # addons.xml, .md5, index.html aktualisieren
    addons_xml = build_addons_xml(addon_dirs)
    ADDONS_XML_PATH.write_text(addons_xml, encoding="utf-8")
    write_md5(ADDONS_XML_PATH, MD5_PATH)
    generate_index_html(list(ROOT.glob("*.zip")) + [p / z for p in addon_dirs for z in p.glob("*.zip")])

if __name__ == "__main__":
    main()
