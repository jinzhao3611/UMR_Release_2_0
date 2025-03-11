import os, re, json, shutil, csv
from pathlib import Path
import spacy
from collections import defaultdict

# Load the English model
nlp = spacy.load("en_core_web_sm")

current_script_dir = Path(__file__).parent
root = current_script_dir.parent


def copy_folder_structure(src, dst):
    """
    Copies the folder structure from src to dst without copying the files.
    """
    for dirpath, dirnames, _ in os.walk(src):
        # Construct the target path
        relative_path = os.path.relpath(dirpath, src)
        target_path = os.path.join(dst, relative_path)

        # Create the directory in the destination
        os.makedirs(target_path, exist_ok=True)
        print(f"Created: {target_path}")


def pre_format(input_file_path, output_file_path):
    """
    Add a separator
    """
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        try:
            content = infile.read()
        except UnicodeDecodeError:
            print(f"Error reading file: {input_file_path}")
            return
    # Replace pattern
    updated_content = re.sub(r"# ::id", "################################################################################\n# ::id", content)

    # Save the updated content
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        outfile.write(updated_content)

    print(f"Updated content written to {output_file_path}")


def batch_pre_format(original_folder_path):
    for subdir, _, files in os.walk(original_folder_path):
        for file in files:
            original_file_path = os.path.join(subdir, file)
            formatted_file_path = original_file_path.replace("original_data", "formatted_data")
            formatted_file_path = formatted_file_path.replace(".txt", ".umr")
            print(f"Processing file: {original_file_path}")
            print(f"formatted file: {formatted_file_path}")
            pre_format(input_file_path=original_file_path, output_file_path=formatted_file_path)


def process_document_level_file(input_file_path, output_file_path):
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
        meta_info_match = re.search(r'# (::id .+)', block)
        if meta_info_match:
            try:
                data['meta_info'] = re.findall(r"::id ([\w.-]+)", meta_info_match.group(1).strip())[0]
            except IndexError:
                print("entry: ", block)
                data['meta_info'] = ""

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
        else:
            data['sentence_level_graph'] = ""

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


def process_full_conversion_file(input_file_path, output_file_path):
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
        meta_info_match = re.search(r'# (::id .+)', block)
        if meta_info_match:
            try:
                data['meta_info'] = re.findall(r"::id ([\w.-]+)", meta_info_match.group(1).strip())[0]
            except IndexError:
                print("entry: ", block)
                data['meta_info'] = ""

        # Extract sentence_id from :: sntX
        sentence_id_match = re.search(r'# :: snt(\d+)', block)
        if sentence_id_match:
            data['sentence_id'] = int(sentence_id_match.group(1))

        # Extract sentence
        sentence_match = re.search(r'# ::snt (.+) # ::save-date', block)
        if sentence_match:
            data['sentence'] = sentence_match.group(1).strip()
        else:
            data['sentence'] = ""

        # Extract index and words
        # index_match = re.search(r'Index: ([^\n]+)\nWords: (.+)', block) #TODO
        data['index'] = ""
        doc = nlp(data['sentence'])
        data['words'] = [token.text for token in doc]


        # Extract sentence level graph
        graph_match = re.search(r'# sentence level graph:\n(.+?)(?=\n# alignment:)', block, re.DOTALL)
        if graph_match:
            data['sentence_level_graph'] = graph_match.group(1).strip()
        else:
            data['sentence_level_graph'] = ""

        data['alignment'] = ""
        data['document_level_annotation'] = ""
        processed_data.append(data)
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(processed_data, file, ensure_ascii=False, indent=4)
    print(f"Processed data saved to {output_file_path}")
    return processed_data


def process_partial_conversion_file(input_file_path, output_file_path):
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
        meta_info_match = re.search(r'# (::id .+)', block)
        if meta_info_match:
            try:
                data['meta_info'] = re.findall(r"::id ([\w.-]+)", meta_info_match.group(1).strip())[0]
            except IndexError:
                print("entry: ", block)
                data['meta_info'] = ""

        data["conversion_type"] = "partial-conversion"

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
        else:
            data['sentence_level_graph'] = ""

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



def batch_process_file(formatted_folder_path):
    for subdir, _, files in os.walk(formatted_folder_path):
        for file in files:
            original_file_path = os.path.join(subdir, file)
            temp = original_file_path.replace("formatted_data/", "jsons/")
            jsons_file_path = temp.replace(".umr", ".json")

            print(f"Processing file: {original_file_path}")
            print(f"json file: {jsons_file_path}")

            if original_file_path.endswith('.umr'):
                if 'document_level' in original_file_path:
                    process_document_level_file(input_file_path=original_file_path, output_file_path=jsons_file_path)
                if 'full_conversion' in original_file_path:
                    process_full_conversion_file(input_file_path=original_file_path, output_file_path=jsons_file_path)
                if 'partial_conversion' in original_file_path:
                    process_partial_conversion_file(input_file_path=original_file_path, output_file_path=jsons_file_path)


def json2txt(json_file_path, output_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Open the output file to write
    with open(output_file_path, 'w', encoding='utf-8') as out_file:
        for entry in data:
            # Prepare content for each entry
            id_info = entry.get("meta_info", "")
            conversion_type = entry.get("conversion_type", "")
            sentence_id = entry.get("sentence_id", "No sentence ID")
            words = entry.get("words", [])
            sentence_graph = entry.get("sentence_level_graph", "No graph")
            alignment = entry.get("alignment", {})
            document_annotation = entry.get("document_level_annotation", "")

            if sentence_id != "No sentence ID":
                out_file.write("################################################################################\n")
                # Write the content to the file
                if conversion_type:
                    out_file.write(f"# meta-info :: sent_id = {id_info} :: type = partial_conversion\n")
                else:
                    out_file.write(f"# meta-info :: sent_id = {id_info}\n")
                out_file.write(f"# :: snt{sentence_id}\n")

                # Calculate the maximum width of the words for alignment
                if words:
                    max_width = max(len(word) for word in words)
                    # Generate aligned indices and words
                    indices = "Index: " + "".join(f"{i + 1:<{max_width + 1}}" for i in range(len(words)))  # Align indices
                    words_line = "Words: " + "".join(f"{word:<{max_width + 1}}" for word in words)  # Align words
                    out_file.write(indices + "\n")
                    out_file.write(words_line + "\n")
                    out_file.write("\n")

                out_file.write(f"# sentence level graph:\n{sentence_graph}\n\n")
                out_file.write(f"# alignment:\n")
                if alignment:
                    for v, i in alignment.items():
                        out_file.write(f"{v}: {i}\n")
                out_file.write(f"\n")
                out_file.write(f"# document level annotation:\n{document_annotation.strip()}\n\n\n")
    print(f"Entries have been written to {output_file_path}")

def batch_json2txt(json_folder_path, output_folder_path):
    output_folder_path.mkdir(parents=True, exist_ok=True)
    for subdir, _, files in os.walk(json_folder_path):
        for file in files:
            if file.endswith(".json"):
                json_file_path = os.path.join(subdir, file)
                output_file_path = os.path.join(output_folder_path, file)
                output_file_path = output_file_path.replace(".json", ".umr")
                print(f"Processing file: {json_file_path}")
                json2txt(json_file_path, output_file_path)


def flatten_directory_structure(src_dir, dest_dir, prefix="english"):
    """
    Flattens a multi-level directory into a single level directory, renames files,
    and keeps a mapping of original paths to new file names.

    Args:
    - src_dir (str): Path to the source directory.
    - dest_dir (str): Path to the destination directory.
    - prefix (str): Prefix for the new file names (default: "english").

    Returns:
    - map_dict (dict): A dictionary mapping original file paths to new file names.
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Counter for sequential file naming
    file_counter = 1
    map_dict = {}

    # Walk through the directory tree
    for dirpath, _, filenames in os.walk(src_dir):
        for filename in filenames:
            # Skip non-files
            if not filename.endswith(".umr"):
                continue

            # Construct original file path
            original_path = os.path.join(dirpath, filename)

            # Create a new file name
            new_file_name = f"{prefix}_{file_counter:04d}.umr"
            new_file_path = os.path.join(dest_dir, new_file_name)

            # Copy the file to the new directory with the new name
            shutil.copy2(original_path, new_file_path)

            # Add the mapping to the dictionary
            map_dict[original_path] = new_file_name

            # Increment the counter
            file_counter += 1

    # Save the mapping to a file (optional)
    with open(os.path.join(Path(root) / f'{prefix}/', f"{prefix}_file_mapping.txt"), "w") as f:
        for original, new_name in sorted(map_dict.items(), key=lambda item: item[0]):
            f.write(f"{new_name} -> {os.path.basename(original)}\n")

    print(f"Flattening complete! Mapping saved in {Path(root) / f'{prefix}/'}/{prefix}_file_mapping.txt")


def flatten_copy_directory(source_folder, destination_folder):
    # Create the destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    # Walk through the source folder and find all JSON files
    for root, _, files in os.walk(source_folder):
        if "full_conversion" in root:  # Skip any paths containing "full_conversion"
            continue
        for file in files:
            if file.endswith(".json"):
                # Get the relative path of the file from the source folder
                relative_path = os.path.relpath(os.path.join(root, file), source_folder)

                # Replace "/" with "-" in the relative path to create a flat filename
                flattened_name = relative_path.replace("/", "-").replace("partial_conversion-", "").replace("document_level_conversion-", "")

                # Construct the full destination path
                destination_path = os.path.join(destination_folder, flattened_name)

                # Copy the JSON file to the destination folder with the flattened name
                shutil.copy2(os.path.join(root, file), destination_path)

    print(f"All JSON files (excluding 'full_conversion') have been flattened into '{destination_folder}'!")


def get_full_conversion_sents_dict():
    tsv_file_path = Path(root) / "english/original_data/directory_by_sentence.tsv"
    full_converison_sents = defaultdict(list)
    with open(tsv_file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter="\t")  # Specify tab as the delimiter
        next(reader)  # Skip the first row (header)
        for row in reader:
            conversion_status = row[4]
            if conversion_status == "full_conversion":
                umr_id = row[3]
                path = row[5]
                full_converison_sents[path].append(umr_id)
    return full_converison_sents

def merge_full_conversion_into_partial_conversion_jsons():
    full_conversion_sents = get_full_conversion_sents_dict()
    # print(full_conversion_sents)
    for full_conversion_file_path in full_conversion_sents:
        print(full_conversion_file_path)
        full_conversion_json_path = Path(root) / f"english/jsons{full_conversion_file_path.replace('.txt','.json')}"
        partial_conversion_json_path = Path(root) / f"english/jsons{full_conversion_file_path.replace('full_conversion', 'partial_conversion').replace('.txt', '.json')}"

        with open(full_conversion_json_path, "r", encoding="utf-8") as file:
            full_conversion_data = json.load(file)

        try:
            with open(partial_conversion_json_path, "r", encoding="utf-8") as file:
                partial_conversion_data = json.load(file)

            for i, item in enumerate(partial_conversion_data):
                for sent_id in full_conversion_sents[full_conversion_file_path]:
                    full_dict = next((item for item in full_conversion_data if item.get("meta_info") == sent_id), None)
                    if item.get("meta_info") == sent_id:  # Check the target ID
                        partial_conversion_data[i] = full_dict  # Replace the dictionary
                        break  # Stop after replacing
        except FileNotFoundError as e:
            print(
                f"Error: The file '{e.filename}' was not found. Please check the path: {partial_conversion_json_path}")

        output_path = Path(root) / f"english/merged_jsons/{full_conversion_file_path.replace('/full_conversion/', '').replace('/', '-').replace('.txt', '.json')}"
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(partial_conversion_data, file, indent=4, ensure_ascii=False)


lang = "english"
original_folder_path = Path(root) / f'{lang}/original_data/'
formatted_folder_path = Path(root) / f'{lang}/formatted_data/'
jsons_folder_path = Path(root) / f'{lang}/jsons/'
merged_jsons_folder_path = Path(root) / f'{lang}/merged_jsons/'
output_folder_path = Path(root) / f'{lang}/merged_output_data/'
release_folder_path = Path(root) / f'{lang}/release_data/'

# step 1:
# copy_folder_structure(original_folder_path, formatted_folder_path)
# step 2: add separator
# batch_pre_format(original_folder_path)


# step 3:
# copy_folder_structure(formatted_folder_path, jsons_folder_path)
# step 4: save to json files
# batch_process_file(formatted_folder_path)

# step 5: flatten copy document_level_conversion and partial_conversion
# flatten_copy_directory(source_folder=jsons_folder_path, destination_folder=merged_jsons_folder_path)
# step 6: merge full conversion into partial conversion files
# merge_full_conversion_into_partial_conversion_jsons()

#todo: running above: Error: The file '/Users/jinzhao/schoolwork/UMR_Release_2_0/english/jsons/partial_conversion/ldc/dfb/bolt-eng-DF-170-181103-8883028_0147.json' was not found.

# step 6: write to standard lindakat format from merged jsons
batch_json2txt(merged_jsons_folder_path, output_folder_path)

# step 7:change file names to standards
# flatten_directory_structure(output_folder_path, release_folder_path)


