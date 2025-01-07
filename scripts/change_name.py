import os
import pandas as pd
from pathlib import Path


current_script_dir = Path(__file__).parent
root = current_script_dir.parent

def change_name(folder_path):
    rename_table = []

    # Get a sorted list of filenames to ensure deterministic renaming
    file_list = sorted([f for f in os.listdir(folder_path) if f.endswith('.txt')])

    # Iterate through the sorted list of files
    for i, filename in enumerate(file_list, start=1):
        old_file_path = os.path.join(folder_path, filename)
        new_filename = f"chinese_{i:03d}.umr"
        new_file_path = os.path.join(folder_path, new_filename)

        # Rename the file
        os.rename(old_file_path, new_file_path)

        # Add old and new filenames to the table
        rename_table.append([filename, new_filename])

    # Create a DataFrame and display it
    df = pd.DataFrame(rename_table, columns=["Original Filename", "Renamed Filename"])
    print(df)

    # Optionally save the table to a CSV file
    df.to_csv(os.path.join(folder_path, "rename_table.csv"), index=False)

if __name__ == '__main__':
    folder_path = Path(root) / 'chinese/copy'
    change_name(folder_path)
