import re
import os
from glob import glob
from pathlib import Path
from unidecode import unidecode
import numpy as np
import shutil
from colorama import Style, Fore

upArtDir = Path("C:\\git-helixvita\\MTG-Art-Downloader\\downloaded-premodern\\3-upscaled-felix-chainner\\Upscales-Final-Selection")

# ==============
# Debug options
# ==============
# Dry run? Setting this option to True will run every single part of the program as normal, except the shutil.copy() command which copies the files.
dry_run = True

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
# Perform preliminary checks and assertions
# ==================================================
assert upArtDir.exists(), f"Could not find {upArtDir}. Please ensure the path provided is correct."

# ==============================================================================
# -- Normalize filenames --
# Normalize or standardize the filenames of the upFiles AND scryFiles in order
# to avoid that minor differences in formatting prevent files from being found.
# ==============================================================================

scryDownDir = Path("C:\\git-helixvita\\MTG-Art-Downloader\\downloaded-premodern\\0-scryfall-artcrops-do-not-touch")
# File extensions to include
extensions = [".png", ".jpg", ".tif", ".jpeg"]

# Obtain a list of all files in scryDownDir with applicable file extensions
scryFiles = [_ for _ in os.listdir(scryDownDir) if Path(_).suffix in extensions]

# Obtain a list of all files in upArtDir
upFiles = [_ for _ in os.listdir(upArtDir) if Path(_).suffix in extensions]

# Create normalized, de-apostrophized, and regex-normalized versions of the list of your files downloaded with MTG-Art-Downloader
scryFilesNormalized = [normalize_filename(_) for _ in scryFiles]
scryFilesNormNoApo = [replace_apostrophes(_) for _ in scryFilesNormalized]
scryFilesRegexed = [regex_filter(_) for _ in scryFilesNormNoApo]
scryFilesRegexedNoArtist = [regex_filter(_, includeArtist=False) for _ in scryFilesNormNoApo]
scryCount = len(scryFilesRegexed)

# Create normalized, de-apostrophized, and regex-normalized versions of the list of upscaled files
upFilesNormalized = [normalize_filename(_) for _ in upFiles]
upFilesNormNoApo = [replace_apostrophes(_) for _ in upFilesNormalized]
upFilesRegexed = [regex_filter(_) for _ in upFilesNormNoApo]
upFilesRegexedNoArtist = [regex_filter(_, includeArtist=False) for _ in upFilesNormNoApo]
upCount = len(upFilesRegexed)

# Check whether there exist files for which someone has forgotten to replace apostrophes in the google drive:
for i, file in enumerate(upFilesNormalized):
    if file != upFilesNormNoApo[i]:
        print(i, file)
        print(i, upFilesNormNoApo[i])
        break

# ================================================================================
# -- Compare filenames in upFiles to scryFiles --
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
        up_idxs = np.where(np.array([upFilesRegexed]) == scryFilesRegexedNoArtist[i])
        matchingFiles = np.array([upFiles])[up_idxs].tolist()
        if matchingFiles:
            # Add those to a separate list
            ambiguousArtistFiles.extend(matchingFiles)
            ambiguousArtistCount += 1
        else:
            # If no matching files were found, then track this using the missingFiles list
            missingFiles.append(Path(scryFiles[i]).name)
            missingCount += 1

# ========================================
# Create dirs if they don't exist
# ========================================

# Dir into which the upscaled art will be copied (and into which the #MissingFiles.txt will be created)
upDestinationDir = scryDownDir / "UpscaledArt"
if not upDestinationDir.is_dir():
    upDestinationDir.mkdir(parents=True, exist_ok=True)

# Dir into which ambiguous artist art will be copied
ambigDestinationDir = scryDownDir / "UpscaledArt" / "AmbiguousArtist"
if not ambigDestinationDir.is_dir():
    ambigDestinationDir.mkdir(parents=True, exist_ok=True)

# =============================
# Missing files
# =============================
print(f"\n==== MISSING UPSCALE ({missingCount}/{scryCount}) - Art for which no matching cardname was found: ===={Fore.RED}{Style.BRIGHT}")
if missingFiles:
    # Print list of missing files
    for _ in missingFiles:
        print(_)
else:
    print("None.")
print(f"{Style.RESET_ALL}", end='')

if missingFiles:
    # Save a list of missing files (i.e. scryFiles for which no matching cardname was found in upFiles)
    missingFilesTxt = scryDownDir / "UpscaledArt" / "#MissingFiles.txt"
    with open(missingFilesTxt, 'w') as f:
        for _ in missingFiles:
            try:
                f.write(f"{_}\n")
            except UnicodeEncodeError:
                line = unidecode(_)
                f.write(f"{line}\n")
        print(f"Saved list of missing files to {missingFilesTxt}\n")

# =============================
# Ambiguous artist files
# =============================
# Copy files files with ambiguous artist (i.e. upFiles with same cardname but with no artist name)
print(f"==== AMBIGUOUS ARTIST UPSCALE ({ambiguousArtistCount}/{scryCount}) - Art for which a matching cardname was found but was lacking an artist name: ===={Fore.YELLOW}{Style.BRIGHT}")
if ambiguousArtistFiles:
    for _ in ambiguousArtistFiles:
        print(_, end=' ')
        destination = ambigDestinationDir / Path(_).name
        print(" --- Copying...", end=' ')
        if not dry_run:
            shutil.copy(_, destination)
            print("Done.")
        else:
            print("Skipped (dry run).")
else:
    print("None.")
print(f"{Style.RESET_ALL}")

# =============================
# Full match files
# =============================
print(f"==== FULL MATCH UPSCALE ({foundCount}/{scryCount}) - Art for which a matching cardname AND artist were found: ===={Fore.GREEN}{Style.BRIGHT}")
if foundFiles:
    for _ in foundFiles:
        print(_, end=' ')
        destination = upDestinationDir / Path(_).name
        print(" --- Copying...", end=' ')
        if not dry_run:
            shutil.copy(_, destination)
            print("Done.")
        else:
            print("Skipped (dry run).")
else:
    print("None.")
print(f"{Style.RESET_ALL}")

print(f'Finished running upscaled-art-finder.py')
