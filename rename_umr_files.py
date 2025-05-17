#!/usr/bin/env python3
import os
import re
import glob
from collections import defaultdict

"""# UMR File Renaming Tool

This script renames UMR (Uniform Meaning Representation) files from UMR 2.0 Release to follow the naming convention established in UMR 1.0 Release.

## How it works

The script:

1. Processes Czech and Latin files (UMR 2.0 only) by renaming them to the format `{language}_umr-NNNN.umr` starting from 0001.

2. For Chinese and English (present in both UMR 1.0 and UMR 2.0):
   - Keeps existing UMR 1.0 files untouched
   - Renames UMR 2.0 files continuing the numbering from where UMR 1.0 left off

3. Generates a mapping file (`umr_file_mapping.txt`) that records the original filename to new filename mapping.

4. Asks for confirmation before actually renaming files.

## Usage

Run the script from the root directory of the UMR_Release_2_0 repository:

```bash
python rename_umr_files.py
```

The script will:
1. Show you what files will be renamed
2. Create a mapping file
3. Ask for confirmation before actual renaming

## Requirements

- Python 3.6+
- The UMR_Release_2_0 directory structure with the language subdirectories """



def main():
    # Define the root directory
    root_dir = "ready_to_release"
    
    # Languages that were already in UMR 1.0 (don't need renaming)
    umr_1_0_only_langs = ["arapaho", "kukama", "navajo", "sanapana"]
    
    # Languages that are in UMR 2.0 only (need complete renaming)
    umr_2_0_only_langs = ["czech", "latin"]
    
    # Languages that are in both releases (need partial renaming)
    mixed_langs = ["english", "chinese"]
    
    # Initialize the mapping dictionary
    mapping = {}
    
    # Process UMR 2.0 only languages (rename all files)
    for lang in umr_2_0_only_langs:
        umr_data_dir = os.path.join(root_dir, lang, "umr_data")
        if not os.path.exists(umr_data_dir):
            print(f"Directory not found: {umr_data_dir}")
            continue
        
        # Get all .umr files that don't already follow the pattern
        pattern = re.compile(f"^{lang}_umr-\d{{4}}\.umr$")
        files_to_rename = []
        
        for filename in os.listdir(umr_data_dir):
            if filename.endswith(".umr") and not pattern.match(filename):
                files_to_rename.append(filename)
        
        # Sort files to ensure consistent numbering
        files_to_rename.sort()
        
        # Rename the files
        for i, old_name in enumerate(files_to_rename, 1):
            new_name = f"{lang}_umr-{i:04d}.umr"
            old_path = os.path.join(umr_data_dir, old_name)
            new_path = os.path.join(umr_data_dir, new_name)
            
            # Check if the new filename already exists
            if os.path.exists(new_path):
                print(f"Warning: {new_name} already exists, skipping {old_name}")
                continue
                
            # Save the mapping
            mapping[old_path] = new_path
            
            # Don't actually rename yet, just collect the mapping
            print(f"Will rename: {old_path} -> {new_path}")
    
    # Process languages in both UMR 1.0 and 2.0
    for lang in mixed_langs:
        umr_data_dir = os.path.join(root_dir, lang, "umr_data")
        if not os.path.exists(umr_data_dir):
            print(f"Directory not found: {umr_data_dir}")
            continue
        
        # Find the highest numbered UMR 1.0 file
        pattern = re.compile(f"^{lang}_umr-(\d{{4}})\.umr$")
        max_number = 0
        
        for filename in os.listdir(umr_data_dir):
            match = pattern.match(filename)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
        
        print(f"Highest existing number for {lang}: {max_number}")
        
        # Get all .umr files that don't follow the pattern
        files_to_rename = []
        
        for filename in os.listdir(umr_data_dir):
            if filename.endswith(".umr") and not pattern.match(filename):
                files_to_rename.append(filename)
        
        # Sort files to ensure consistent numbering
        files_to_rename.sort()
        
        # Rename the files starting from max_number + 1
        for i, old_name in enumerate(files_to_rename, max_number + 1):
            new_name = f"{lang}_umr-{i:04d}.umr"
            old_path = os.path.join(umr_data_dir, old_name)
            new_path = os.path.join(umr_data_dir, new_name)
            
            # Check if the new filename already exists
            if os.path.exists(new_path):
                print(f"Warning: {new_name} already exists, skipping {old_name}")
                continue
                
            # Save the mapping
            mapping[old_path] = new_path
            
            # Don't actually rename yet, just collect the mapping
            print(f"Will rename: {old_path} -> {new_path}")
    
    # Write the mapping to a file
    with open("umr_file_mapping.txt", "w") as f:
        f.write("Original Path\tNew Path\n")
        for old_path, new_path in mapping.items():
            f.write(f"{old_path}\t{new_path}\n")
    
    # Ask for confirmation before actually renaming
    confirmation = input("\nDo you want to proceed with the renaming? (yes/no): ")
    if confirmation.lower() in ["yes", "y"]:
        for old_path, new_path in mapping.items():
            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")
            except Exception as e:
                print(f"Error renaming {old_path}: {e}")
        print("Renaming completed.")
    else:
        print("Renaming aborted. You can check the mapping in umr_file_mapping.txt")

if __name__ == "__main__":
    main() 