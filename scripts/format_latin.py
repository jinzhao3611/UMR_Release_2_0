from pathlib import Path
current_script_dir = Path(__file__).parent
root = current_script_dir.parent

def pre_format(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    modified_lines = []
    for line in lines:
        # Example modification: Adjust comments or merge lines for sentence gloss
        if line.startswith("# sent_id ="):
            # Add separator before the # sent_id line
            modified_lines.append("################################################################################\n")
            modified_lines.append(line.replace("# sent_id =", "# meta-info :: sent_id ="))
        else:
            modified_lines.append(line)

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        outfile.writelines(modified_lines)

lang = "latin"
original_file_path = Path(root) / 'umr_2_0/latin/original_data/latin_umr-0001.txt'
formatted_file_path = Path(root) / 'umr_2_0/latin/formatted_data/latin_umr-0001.umr'
# step 1:
pre_format(input_file_path=original_file_path, output_file_path=formatted_file_path)



