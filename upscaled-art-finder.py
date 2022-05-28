import re
import os
from glob import glob
from pathlib import Path
from unidecode import unidecode
import numpy as np
import shutil
from colorama import Style, Fore

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
# Note 1: The file missingFiles.txt will contain a list of art for which no corresponding art was found in upArtDir.
# Note 2: If you wish to simply find any upscaled art regardless of artist, then remove the artist from the filenames of your scryfall art files (or change the config.ini to Naming.Convention = NAME).
# ==== END OF INSTRUCTIONS ====

# ========
# To do's
# ========
# TODO: Implement finding of art for double-sided cards
# TODO: Implement finding of art for sagas
# TODO: Implement finding of art for planeswalkers
# TODO: Implement finding of art for lands

# ==============
# Debug options
# ==============
# Dry run? Setting this option to True will run every single part of the program as normal, except the shutil.copy() command which copies the files.
dry_run = False

# =================
# Helper functions
# =================

def normalize_filename(filename: str):
    """
    Takes a filename or filepath and does the following:
    1. Trim away all parts of the filepath except the filename. (Also removes file extension).
    2. Removes most types of punctuation, including comma, period, exclamation mark, quotation marks, etc.
    3. Replaces hyphens with a space
    4. Turns everything into lower case
    5. Replaces accented characters with the closest character in a-z
    """
    stem = Path(filename).stem
    punctuationToRemove = list(".,-—!\",/")
    for punc in punctuationToRemove:
        replacement = " " if punc == "-" else ""
        stem = stem.replace(punc, replacement)
    lower = stem.lower()
    normalized = unidecode(lower)
    return normalized

def replace_apostrophes(myStr: str):
    """Replaces all instances of the apostrophe (aka the single quote character) with an underscore character."""
    return myStr.replace("'", "_")

def regex_filter(scryFile: str, includeArtist = True, includeSetcode = False):
    """Normalize a filename via a method of regular expression pattern matching that looks for and isolates three patterns per filename:
    1. Cardname (always assumed to be present).
    2. Artist name (not neccesarily present, but always assumed to be enclosed in parentheses () if it is).
    3. Setcode (not necessarily present, but always assumed to be enclosed in angle brackets [] if it is).
    The filter contains two optional variables which control what is included in the string output by the function:
    includeArtist : When True, it will include the artist name (enclosed in parentheses) in the returned string.
    includeSetcode : When True, it will include the set code [enclosed in angle brackets] in the returned string.
    """
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

# ==================================================
# Step 0: Perform preliminary checks and assertions
# ==================================================
assert upArtDir.exists, f"Could not find {upArtDir}. Please ensure the path provided is correct."

# ==============================================================================
# Step 1: Normalize filenames
# Normalize or standardize the filenames of the upFiles AND scryFiles in order
# to avoid that minor differences in formatting prevent files from being found.
# ==============================================================================

# Location of your files downloaded with MTG-Art-Downloader (henceforth referred to as the files in scryDownDir).
scryDownDir = Path("downloaded2\\scryfall")
# File extensions to include
extensions = ["*.png", "*.jpg", "*.tif", "*.jpeg"]

# Obtain a list of all files in scryDownDir with applicable file extensions
scryFiles = []
scryFilesSubdirs = ["Land", "Planeswalker", "Saga", "TF Back", "TF Front"]
for ext in extensions:
    scryFiles.extend(glob(os.path.join(scryDownDir, ext)))
    for subdir in scryFilesSubdirs:
        scryFiles.extend(glob(os.path.join(scryDownDir / subdir, ext)))

# Obtain a list of all files in upArtDir
upFiles = []
for ext in extensions:
    upFiles.extend(glob(os.path.join(upArtDir,"**", ext)))

# Create normalized, de-apostrophized, and regex-normalized versions of the list of your files downloaded with MTG-Art-Downloader
scryFilesNormalized = [normalize_filename(_) for _ in scryFiles]
scryFilesNormNoApo = [replace_apostrophes(_) for _ in scryFilesNormalized]
scryFilesRegexed = [regex_filter(_) for _ in scryFilesNormNoApo]
scryFilesRegexedNoArtist = [regex_filter(_, includeArtist=False) for _ in scryFilesNormNoApo]

# Create normalized, de-apostrophized, and regex-normalized versions of the list of upscaled files
upFilesNormalized = [normalize_filename(_) for _ in upFiles]
upFilesNormNoApo = [replace_apostrophes(_) for _ in upFilesNormalized]
upFilesRegexed = [regex_filter(_) for _ in upFilesNormNoApo]
upFilesRegexedNoArtist = [regex_filter(_, includeArtist=False) for _ in upFilesNormNoApo]

# # Check whether there exist files for which someone has forgotten to replace apostrophes in the google drive:
# for i, file in enumerate(upFilesNormalized):
#     if file != upFilesNormNoApo[i]:
#         print(i, file)
#         print(i, upFilesNormNoApo[i])
#         break

# ================================================================================
# Step 2: Compare filenames in upFiles to scryFiles
# To figure out which scryFiles have a corresponding upscaled version in upFiles.
# ================================================================================

# Compare the regex-normalized lists of upFiles and scryFiles
foundFiles = []
missingFiles = []
ambiguousArtistFiles = []
foundCount = 0
missingCount = 0
ambiguousArtistCount = 0
for i, scryFile in enumerate(scryFilesRegexed):
    # Find all the regex-normalized upFiles that match the regex-normalized scryFile
    up_idxs = np.where(np.array([upFilesRegexed]) == scryFile)
    matchingFiles = np.array([upFiles])[up_idxs].tolist()
    if matchingFiles:
        # Add those to the list of found files
        foundFiles.extend(matchingFiles)
        foundCount += 1
    else:
        # Then, instead look to see if there are any upFiles that match the cardname but lack an artist name.
        up_idxs = np.where(np.array([upFilesRegexedNoArtist]) == scryFilesRegexedNoArtist[i])
        matchingFiles = np.array([upFiles])[up_idxs].tolist()
        if matchingFiles:
            # Add those to a separate list
            ambiguousArtistFiles.extend(matchingFiles)
            ambiguousArtistCount += 1
        else:
            # If no matching files were found, then track this using the missingFiles list
            missingFiles.append(Path(scryFiles[i]).name)
            missingCount += 1

# ======================
# Step 3: Print results
# ======================

scryCount = len(scryFilesRegexed)

# Print list of missing files
print(f"\n==== No matching cardname found for {missingCount}/{scryCount} scryfall files: ===={Fore.RED}{Style.BRIGHT}")
if missingFiles:
    for _ in missingFiles:
        print(_)
else:
    print("None.")
print(f"{Style.RESET_ALL}")

# Print list of files with ambiguous artist (i.e. upFiles with same cardname but with no artist name)
print(f"==== Files with matching cardname but missing artist name found for {ambiguousArtistCount}/{scryCount} scryfall files: ===={Fore.YELLOW}{Style.BRIGHT}")
if ambiguousArtistFiles:
    for _ in ambiguousArtistFiles:
        print(_)
else:
    print("None.")
print(f"{Style.RESET_ALL}")

# Print list of files found
print(f"==== Matching cardname AND artist found for {foundCount}/{scryCount} scryfall files: ===={Fore.GREEN}{Style.BRIGHT}")
if foundFiles:
    for _ in foundFiles:
        print(_)
else:
    print("None.")
print(f"{Style.RESET_ALL}")

# ===============================================================
# Step 4: Copy files from upFiles to a subfolder in scryDownDir.
# ===============================================================

# Copy foundFiles (will overwrite any existing files with same name in UpscaledArt dir)
print("Copying files...")
for _ in foundFiles:
    destinationDir = scryDownDir / "UpscaledArt"
    if not destinationDir.is_dir():
        destinationDir.mkdir(parents=True, exist_ok=True)
    destination = destinationDir / Path(_).name
    if not dry_run:
        shutil.copy(_, destination)
# Similarly, copy any ambiguous artist files to a separate dir within the UpscaledArt dir
for _ in ambiguousArtistFiles:
    destinationDir = scryDownDir / "UpscaledArt" / "AmbiguousArtist"
    if not destinationDir.is_dir():
        destinationDir.mkdir(parents=True, exist_ok=True)
    destination = destinationDir / Path(_).name
    if not dry_run:
        shutil.copy(_, destination)
print("Done.")


# =====================
# Step 5: Produce logs
# =====================

# Save a list of missing files (i.e. scryFiles for which no matching cardname was found in upFiles)
if missingFiles:
    missingFilesTxt = scryDownDir / "UpscaledArt" / "#MissingFiles.txt"
    with open(missingFilesTxt, 'w') as f:
        for _ in missingFiles:
            f.write(f"{_}\n")
        print(f"Saved list of missing files to {missingFilesTxt}")

print(f'Finished running upscaled-art-finder.py')
