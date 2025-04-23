import os
import hashlib
import zipfile
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

REPO_ID = "repository.embuary"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_all_addons():
    return [
        d for d in os.listdir(ROOT_DIR)
        if os.path.isdir(os.path.join(ROOT_DIR, d)) and os.path.isfile(os.path.join(ROOT_DIR, d, "addon.xml"))
    ]

def get_current_version(addon_path):
    with open(os.path.join(addon_path, "addon.xml"), encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'version="(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        raise ValueError(f"⚠️ Keine gültige Versionsnummer in {addon_path} gefunden!")
    return tuple(map(int, match.groups()))

def update_addon_version(addon_path, new_version):
    xml_path = os.path.join(addon_path, "addon.xml")
    with open(xml_path, encoding="utf-8") as f:
        content = f.read()

    new_content = re.sub(
        r'(id="[^"]+"[^>]*version=")\d+\.\d+\.\d+(")',
        rf'\g<1>{new_version}\g<2>',
        content,
        count=1
    )

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def has_changes_since_last_zip(addon_path, zip_path):
    if not os.path.exists(zip_path):
        return True
    zip_mtime = os.path.getmtime(zip_path)
    for root, _, files in os.walk(addon_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            if os.path.getmtime(fpath) > zip_mtime:
                return True
    return False

def create_zip(addon_id, addon_path, zip_path, version):
    bak_path = zip_path + ".bak"
    if os.path.exists(zip_path):
        if os.path.exists(bak_path):
            os.remove(bak_path)
        shutil.move(zip_path, bak_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(addon_path):
            for file in files:
                if file.endswith(".zip"):
                    continue  # ZIP-Dateien überspringen
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, addon_path)
                zipf.write(full_path, os.path.join(addon_id, rel_path))

        # ✅ Füge addons.xml und .md5 in Repository-ZIP ein
        if addon_id.startswith("repository."):
            addons_xml_path = os.path.join(ROOT_DIR, "addons.xml")
            md5_path = addons_xml_path + ".md5"
            zipf.write(addons_xml_path, os.path.join(addon_id, "addons.xml"))
            zipf.write(md5_path, os.path.join(addon_id, "addons.xml.md5"))
            print("📝 addons.xml und MD5 in Repository-ZIP eingefügt.")

def generate_addons_xml(addon_dirs):
    addons = []
    for d in addon_dirs:
        addon_xml = os.path.join(ROOT_DIR, d, "addon.xml")
        with open(addon_xml, encoding="utf-8") as f:
            addons.append(f.read().strip())
    return "<addons>\n\n" + "\n\n".join(addons) + "\n\n</addons>"

def write_addons_files(addons_xml):
    addons_xml_path = os.path.join(ROOT_DIR, "addons.xml")
    with open(addons_xml_path, "w", encoding="utf-8") as f:
        f.write(addons_xml)

    md5 = hashlib.md5(addons_xml.encode("utf-8")).hexdigest()
    with open(addons_xml_path + ".md5", "w") as f:
        f.write(md5)

def update_repository_addon(addon_dirs, repo_path, version):
    xml_path = os.path.join(repo_path, "addon.xml")
    with open(xml_path, encoding="utf-8") as f:
        tree = ET.parse(f)
        root = tree.getroot()
        root.set("version", version)

    # Entferne alten Repository-Abschnitt
    for elem in root.findall("extension"):
        if elem.attrib.get("point") == "xbmc.addon.repository":
            root.remove(elem)

    # Füge aktualisierten Repository-Abschnitt ein
    repo_ext = ET.SubElement(root, "extension", {
        "point": "xbmc.addon.repository",
        "name": "Embuary Skins Repository"
    })

    dir_elem = ET.SubElement(repo_ext, "dir", {
        "minversion": "20.999.0"
    })
    ET.SubElement(dir_elem, "info", {"compressed": "false"}).text = "https://raw.githubusercontent.com/Stogie87/Embuary-Skin/master/addons.xml"
    ET.SubElement(dir_elem, "checksum").text = "https://raw.githubusercontent.com/Stogie87/Embuary-Skin/master/addons.xml.md5"
    ET.SubElement(dir_elem, "datadir", {"zip": "true"}).text = "https://raw.githubusercontent.com/Stogie87/Embuary-Skin/master/"

    ET.indent(tree, space="    ", level=0)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

def generate_index_html():
    zips_by_folder = {}

    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".zip"):
                folder = os.path.relpath(root, ROOT_DIR)
                if folder == ".":
                    addon_name = file.split("-")[0]
                    folder = addon_name
                zips_by_folder.setdefault(folder, []).append(os.path.join(folder, file) if folder != "." else file)

    html_path = os.path.join(ROOT_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Embuary Addons</title></head><body>\n")
        f.write("<h1>Embuary Addon ZIP-Dateien</h1>\n")

        for folder, zip_files in sorted(zips_by_folder.items()):
            f.write(f"<h2>{folder}</h2>\n<ul>\n")
            for zip_path in sorted(zip_files):
                file_name = os.path.basename(zip_path)
                file_href = zip_path.replace("\\", "/")
                f.write(f'<li><a href="{file_href}">{file_name}</a></li>\n')
            f.write("</ul>\n")

        f.write("</body></html>\n")

    print("✅ index.html mit Ordnerstruktur aktualisiert.")

def main():
    all_addons = get_all_addons()
    addons_xml_sources = []

    for addon in all_addons:
        addon_path = os.path.join(ROOT_DIR, addon)
        addon_id = addon
        is_repo = addon.startswith("repository.")

        try:
            major, minor, patch = get_current_version(addon_path)
        except ValueError as e:
            print(e)
            continue

        if is_repo:
            patch += 1
            new_version = f"{major}.{minor}.{patch}"
            update_addon_version(addon_path, new_version)
            update_repository_addon(
                [a for a in all_addons if not a.startswith("repository.")],
                addon_path,
                new_version
            )
            zip_filename = f"{addon}-{new_version}.zip"
            zip_target_folder = os.path.join(addon_path, zip_filename)
            create_zip(addon_id, addon_path, zip_target_folder, new_version)
            print(f"✅ Repository ZIP erstellt: {zip_target_folder}")
        else:
            zip_target = os.path.join(addon_path, f"{addon}-{major}.{minor}.{patch}.zip")
            if has_changes_since_last_zip(addon_path, zip_target):
                patch += 1
                new_version = f"{major}.{minor}.{patch}"
                update_addon_version(addon_path, new_version)
                zip_target = os.path.join(addon_path, f"{addon}-{new_version}.zip")
                create_zip(addon_id, addon_path, zip_target, new_version)
                print(f"📦 ZIP für {addon} erstellt: {zip_target}")
            else:
                print(f"⏩ Keine Änderungen an {addon}, keine neue ZIP erstellt.")

        addons_xml_sources.append(addon)

    addons_xml = generate_addons_xml(addons_xml_sources)
    write_addons_files(addons_xml)
    generate_index_html()
    print("✅ addons.xml, MD5 und index.html aktualisiert.")

if __name__ == "__main__":
    main()
