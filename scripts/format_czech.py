import os
from pathlib import Path
current_script_dir = Path(__file__).parent
root = current_script_dir.parent

def replace_sent_id(folder_path):
    # Create the output directory if it doesn't exist
    output_folder = str(folder_path).replace("original_data", "formatted_data")
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        if not filename.endswith(".umr"):
            continue

        # Path to the original file
        file_path = os.path.join(folder_path, filename)

        # Read the file line by line
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Modify lines in memory
        new_lines = []
        for line in lines:
            # If line starts with "# sent_id =", replace with "# meta-info :: type = partial_conversion :: sent_id ="
            if line.strip().startswith("# sent_id ="):
                line = line.replace(
                    "# sent_id =",
                    "# meta-info :: type = partial_conversion :: sent_id =",
                    1
                )
            new_lines.append(line)

        # Build output path in the "formatted_data" folder
        output_file_path = os.path.join(output_folder, filename)

        # Write the updated lines to the new file
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    print(f"Files processed and saved in {output_folder}")



if __name__ == "__main__":
    folder = Path(root) / 'czech/original_data/'
    replace_sent_id(folder)

