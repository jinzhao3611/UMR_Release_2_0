import json, os, re
from pathlib import Path
# Get the directory of the current script
current_script_dir = Path(__file__).parent

# Construct the path to the file
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

def process_file(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the file into blocks using the delimiter
    blocks = content.split('################################################################################')
    processed_data = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        data = {}

        # Capture the entire meta-info line
        meta_info_match = re.search(r'# (sent_id = .+)', block)
        if meta_info_match:
            data['meta_info'] = meta_info_match.group(1).strip()

        # Extract sentence_id from :: sntX
        sentence_id_match = re.search(r'# :: snt(\d+)', block)
        if sentence_id_match:
            data['sentence_id'] = int(sentence_id_match.group(1))

        # Extract sentence
        sentence_match = re.search(r'# :: (snt\d+)\nIndex: [^\n]+\nWords: (.+)', block)
        if sentence_match:
            data['sentence'] = sentence_match.group(2).strip()

        # Extract index and words
        index_match = re.search(r'Index: ([^\n]+)\nWords: (.+)', block)
        if index_match:
            data['index'] = index_match.group(1).strip()
            data['words'] = index_match.group(2).strip().split()

        # Extract sentence level graph
        graph_match = re.search(r'# sentence level graph:\n(.+?)(?=\n# alignment:)', block, re.DOTALL)
        if graph_match:
            data['sentence_level_graph'] = graph_match.group(1).strip()

        # Extract alignment
        alignment_match = re.search(r'# alignment:\n(.+?)(?=\n# document level annotation:)', block, re.DOTALL)
        if alignment_match:
            alignment_lines = alignment_match.group(1).strip().split('\n')
            alignment = {}
            for line in alignment_lines:
                key, value = line.split(':')
                alignment[key.strip()] = value.strip()
            data['alignment'] = alignment

        # Extract document level annotation
        doc_annot_match = re.search(r'# document level annotation:\n(.+)', block, re.DOTALL)
        if doc_annot_match:
            data['document_level_annotation'] = doc_annot_match.group(1).strip()

        processed_data.append(data)
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(processed_data, file, ensure_ascii=False, indent=4)
    print(f"Processed data saved to {output_file_path}")
    return processed_data

def batch_process_file(input_folder, output_folder):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.umr'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename.replace('.umr', '.json'))
            # Process the file
            process_file(input_path, output_path)

lang = "latin"
original_file_path = Path(root) / 'latin/original_data/latin_umr-0001.txt'
formatted_file_path = Path(root) / 'latin/formatted_data/latin_umr-0001.umr'
# step 1:
pre_format(input_file_path=original_file_path, output_file_path=formatted_file_path)

# step 2: This step is not needed for publishing
# batch_process_file(input_folder= Path(root) / f'{lang}/formatted_data/', output_folder= Path(root) / f'{lang}/jsons/')


