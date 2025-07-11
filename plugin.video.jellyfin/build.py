#!/usr/bin/env python3

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime

import yaml

def indent(elem: ET.Element, level: int = 0) -> None:
    """Nicely format XML output for better readability."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def create_addon_xml(config: dict, source: Path, py_version: str) -> None:
    """Create addon.xml from template file."""
    template_path = source / ".build" / "template.xml"
    tree = ET.parse(template_path)
    root = tree.getroot()

    # Populate dependencies in template
    dependencies = config["dependencies"].get(py_version, [])
    for dep in dependencies:
        ET.SubElement(root.find("requires"), "import", attrib=dep)

    # Populate version string
    addon_version = config.get("version")
    root.attrib["version"] = f"{addon_version}+{py_version}"

    # Populate Changelog
    date = datetime.today().strftime("%Y-%m-%d")
    changelog = config.get("changelog", "")
    for section in root.findall("extension"):
        news = section.findall("news")
        if news:
            news[0].text = f"v{addon_version} ({date}):\n{changelog}"

    # Format xml tree
    indent(root)

    # Write addon.xml
    tree.write(str(source / "addon.xml"), encoding="utf-8", xml_declaration=True)

def zip_files(py_version: str, source: Path, target: Path, dev: bool) -> None:
    """Create installable addon zip archive."""
    archive_name = f"plugin.video.jellyfin+{py_version}.zip"
    archive_path = target / archive_name

    with zipfile.ZipFile(archive_path, "w") as z:
        for root, dirs, files in os.walk(source):
            for filename in filter(file_filter, files):
                file_path = Path(root) / filename
                if dev or folder_filter(file_path):
                    relative_path = Path("plugin.video.jellyfin") / file_path.relative_to(source)
                    z.write(str(file_path), str(relative_path))

def file_filter(file_name: str) -> bool:
    """True if file_name is meant to be included."""
    return (
        not (file_name.startswith("plugin.video.jellyfin") and file_name.endswith(".zip"))
        and not file_name.endswith((".pyo", ".pyc", ".pyd"))
    )

def folder_filter(file_path: Path) -> bool:
    """True if folder is meant to be included."""
    filters = [
        ".ci", ".git", ".github", ".build", ".mypy_cache", ".pytest_cache", "__pycache__"
    ]
    # Prüft, ob einer der Filter im Pfad vorkommt
    return not any(f in file_path.parts for f in filters)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build flags:")
    parser.add_argument("--version", type=str, choices=("py2", "py3"), default="py3")
    parser.add_argument("--source", type=Path, default=Path(__file__).absolute().parent)
    parser.add_argument("--target", type=Path, default=Path(__file__).absolute().parent)
    parser.add_argument("--dev", action="store_true", default=False)

    args = parser.parse_args()

    # Load config file
    config_path = args.source / "release.yaml"
    with open(config_path, "r", encoding="utf-8") as fh:
        release_config = yaml.safe_load(fh)

    create_addon_xml(release_config, args.source, args.version)
    zip_files(args.version, args.source, args.target, args.dev)
