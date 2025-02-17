"""
SCRIPT TO BUILD PROXYSHOP AS EXE RELEASE
"""
import os
import sys
import zipfile
from glob import glob
from pathlib import Path
from shutil import copy2, copytree, rmtree, move
import PyInstaller.__main__

# Folder definitions
CWD = os.getcwd()
DIST = os.path.join(CWD, "dist")
MTG = os.path.join(os.getcwd(), "lib")
DIST_MTG = os.path.join(os.getcwd(), "dist/lib")

# All individual files that need to be copied upon pyinstaller completion
files = [
    # --- WORKING DIRECTORY
    {"src": os.path.join(CWD, "LICENSE"), "dst": os.path.join(DIST, "LICENSE")},
    {"src": os.path.join(CWD, "README.md"), "dst": os.path.join(DIST, "README.md")},
    {"src": os.path.join(CWD, "cards.txt"), "dst": os.path.join(DIST, "cards.txt")},
    {"src": os.path.join(CWD, "config.ini"), "dst": os.path.join(DIST, "config.ini")},
    # --- SOURCE DIRECTORY
    {
        "src": os.path.join(MTG, "codes.hjson"),
        "dst": os.path.join(DIST_MTG, "codes.hjson"),
    },
    {
        "src": os.path.join(MTG, "links.json"),
        "dst": os.path.join(DIST_MTG, "links.json"),
    },
    {
        "src": os.path.join(MTG, "scryfall.json"),
        "dst": os.path.join(DIST_MTG, "scryfall.json"),
    },
]

# Folders that need to be copied
folders: list = [
    # --- WORKING DIRECTORY
    # {'src': os.path.join(CWD, "lists"), 'dst': os.path.join(DIST, 'lists')}
]


def clear_build_files(clear_dist=True):
    """
    Clean out all PYCACHE files and Pyinstaller files
    """
    os.system("pyclean -v .")
    try:
        rmtree(os.path.join(os.getcwd(), "build"))
    except Exception as e:
        print(e)
    if clear_dist:
        try:
            rmtree(os.path.join(os.getcwd(), "dist"))
        except Exception as e:
            print(e)


def make_dirs():
    """
    Make sure necessary directories exist.
    """
    # Ensure folders exist
    Path(DIST).mkdir(mode=511, parents=True, exist_ok=True)
    Path(DIST_MTG).mkdir(mode=511, parents=True, exist_ok=True)
    Path(DIST_MTG).mkdir(mode=511, parents=True, exist_ok=True)


def move_data():
    """
    Move our data files into the release.
    """
    # Transfer our necessary files
    print("Transferring data files...")
    for f in files:
        copy2(f["src"], f["dst"])

    # Transfer our necessary folders
    print("Transferring data folders...")
    for f in folders:
        copytree(f["src"], f["dst"])


def build_zip(version):
    """
    Create a zip of this release.
    """
    print("Building ZIP...")
    ZIP = os.path.join(CWD, "mtg-art-downloader.{}.zip".format(version))
    ZIP_DIST = os.path.join(DIST, "mtg-art-downloader.{}.zip".format(version))
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for fp in glob(os.path.join(DIST, "**/*"), recursive=True):
            base = os.path.commonpath([DIST, fp])
            zipf.write(fp, arcname=fp.replace(base, ""))
    move(ZIP, ZIP_DIST)


if __name__ == "__main__":

    # Pre-build steps
    clear_build_files()
    make_dirs()

    # Run pyinstaller
    print("Starting PyInstaller...")
    PyInstaller.__main__.run(["main.spec", "--clean"])

    # Post-build steps
    move_data()
    build_zip(sys.argv[1])
    clear_build_files(False)
