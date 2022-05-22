import re
import os
from glob import glob
from pathlib import Path
from unidecode import unidecode
import numpy as np
import shutil

# ==== INSTRUCTIONS ====
# 1. Get your hands on a bunch of upscaled art, for example from the mpcproxies google drive.
# 2. If the content is online, download a local copy of it and place in a folder on your computer, henceforth referred to as the "upArtDir"
# 3. Replace the path below with the path to the upArtDir
upArtDir = Path("D:\\mpcproxies\\Upcaled Arts")
# 4. Open config.ini and set Only.Download.Scryfall = true
# 5. Add some cards to the cards.txt as per the README.md
# 6. Run the MTG-Art-Downloader "main.py" program
# 7. Run this "upscaled-art-finder.py" program
# 8. Done!
# If any upscaled versions were found in upArtDir, then they have now been copied into MTG-Art-Downloader/downloaded/scryfall/UpscaledArt
# The file missingFiles.txt will contain a list of art for which no corresponding art was found in upArtDir.
# ==== END OF INSTRUCTIONS ====

scryFiles = []
scryDownDir = Path("downloaded\\scryfall")

extensions = ["*.png", "*.jpg", "*.tif", "*.jpeg"]
for ext in extensions:
    scryFiles.extend(glob(os.path.join(scryDownDir, ext)))

upFiles = []
for ext in extensions:
    upFiles.extend(glob(os.path.join(upArtDir,"**", ext)))

def normalize_filename(filename: str):
    stem = Path(filename).stem
    punctuationToRemove = list(".,-—!\",/")
    for punc in punctuationToRemove:
        replacement = " " if punc == "-" else ""
        stem = stem.replace(punc, replacement)
    lower = stem.lower()
    normalized = unidecode(lower)
    return normalized

def replace_apostrophes(myStr: str):
    return myStr.replace("'", "_")

upFilesNormalized = [normalize_filename(_) for _ in upFiles]
upFilesNormNoApo = [replace_apostrophes(_) for _ in upFilesNormalized]

# # Check whether there exist files for which someone has forgotten to replace apostrophes in the google drive:
# for i, file in enumerate(upFilesNormalized):
#     if file != upFilesNormNoApo[i]:
#         print(i, file)
#         print(i, upFilesNormNoApo[i])
#         break

scryFilesNormalized = [normalize_filename(_) for _ in scryFiles]
scryFilesNormNoApo = [replace_apostrophes(_) for _ in scryFilesNormalized]


def regex_filter(scryFile: str, includeArtist = True, includeSetcode = False):
    match = re.match(r"([\w\s]+)\s?(?:\(([\w ]*)\))?(?:\s\[(\w{3})\])?", scryFile)
    if match:
        cardname, artist, setcode = match.groups()
        output = f"{cardname.lstrip().rstrip()}"
        if includeArtist and artist:
            output += f" ({artist.lstrip().rstrip()})"
        if includeSetcode and setcode:
            output += f" [{setcode.lstrip().rstrip()}]"
        return output
    else:
        return None

scryFilesRegexed = [regex_filter(_) for _ in scryFilesNormNoApo]
upFilesRegexed = [regex_filter(_) for _ in upFilesNormNoApo]
upFilesRegexedNoArtist = [regex_filter(_, includeArtist=False) for _ in upFilesNormNoApo]

missingFiles = []
foundFiles = []
count = 0
for i, scryFile in enumerate(scryFilesRegexed):
    up_idxs = np.where(np.array([upFilesRegexed]) == scryFile)
    matchingFiles = np.array([upFiles])[up_idxs].tolist()
    foundFiles.extend(matchingFiles)
    if not foundFiles:
        up_idxs = np.where(np.array([upFilesRegexedNoArtist]) == scryFile)
        matchingFiles = np.array([upFiles])[up_idxs]
        foundFiles.extend(matchingFiles)
    if foundFiles:
        count += 1
    else:
        missingFiles.append(Path(scryFiles[i]).name)
print(f"Files found: {count}/{len(scryFilesRegexed)}")


# Print list of missingFiles
print("==== Missing files: ====")
for _ in missingFiles:
    print(_)

# Copy foundFiles (will overwrite any existing files with same name in UpscaledArt dir)
print("==== Upscaled art found and copied: ====")
for _ in foundFiles:
    destinationDir = scryDownDir / "UpscaledArt"
    if not destinationDir.is_dir():
        destinationDir.mkdir(parents=True, exist_ok=True)
    destination = destinationDir / Path(_).name
    print(_)
    shutil.copy(_, destination)

missingFilesTxt = destinationDir / "missingFiles.txt"
with open(missingFilesTxt, 'w') as f:
    for _ in missingFiles:
        f.write(f"{_}\n")

print('Done')

# TODO: Implement finding of art for double-sided cards
