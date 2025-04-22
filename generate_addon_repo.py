import os
from urllib.parse import quote

# ⚠️ Hier deine GitHub Pages URL eintragen:
BASE_URL = "https://<username>.github.io/<repo-name>/"  # z. B. https://stogie87.github.io/Embuary-2K-Skin/


def find_zip_files(base_dir):
    zip_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".zip"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")
                zip_files.append(rel_path)
    return sorted(zip_files)


def generate_html(zip_files, output_file="index.html"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n<html><head><meta charset='UTF-8'><title>Addon-Zips</title></head><body>\n")
        f.write("<h1>Kodi Addon ZIP-Dateien</h1>\n<ul>\n")
        for zip_path in zip_files:
            link = BASE_URL + quote(zip_path)
            f.write(f"<li><a href='{link}'>{zip_path}</a></li>\n")
        f.write("</ul>\n</body></html>")
    print(f"✅ HTML-Datei erstellt: {output_file}")


if __name__ == "__main__":
    repo_dir = os.getcwd()
    zip_list = find_zip_files(repo_dir)

    if zip_list:
        generate_html(zip_list)
    else:
        print("⚠️ Keine ZIP-Dateien gefunden.")
