import os
from pathlib import Path
current_script_dir = Path(__file__).parent
root = current_script_dir.parent

def replace_sent_id(folder_path):
    for filename in os.listdir(folder_path):
        if not filename.endswith(".umr"):
            continue

        file_path = os.path.join(folder_path, filename)

        # Read the file line by line
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Modify lines in memory
        new_lines = []
        for line in lines:
            # If line starts with "# sent_id =", replace with "# meta-info :: sent_id ="
            if line.strip().startswith("# sent_id ="):
                # Replace the *first* occurrence in the line
                line = line.replace("# sent_id =", "# meta-info :: sent_id =", 1)
            new_lines.append(line)

        # Write the updated lines back to the same file (or to a new file if you prefer)
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)


if __name__ == "__main__":
    folder = Path(root) / 'czech/original_data/'
    replace_sent_id(folder)
