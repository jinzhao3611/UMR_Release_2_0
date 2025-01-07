import os, re, json
from pathlib import Path
import spacy

# Load the English model
nlp = spacy.load("en_core_web_sm")

current_script_dir = Path(__file__).parent
root = current_script_dir.parent

def pre_format(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    modified_lines = []
    for line in lines:
        # Example modification: Adjust comments or merge lines for sentence gloss
        if line.startswith("# ::id") or line.startswith("# ::workset"):
            # Add separator before the # sent_id line
            modified_lines.append("################################################################################\n")
            modified_lines.append(line)
        elif line.startswith("Sentence:"):
            continue         # skip #TODO: make this line on meta info
        elif line.startswith("Sentence Gloss"):
            continue  # Skip #TODO: make this line on meta info
        else:
            modified_lines.append(line)

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        outfile.writelines(modified_lines)

def batch_pre_format(original_folder_path):
    for subdir, _, files in os.walk(original_folder_path):
        for file in files:
            original_file_path = os.path.join(subdir, file)
            formatted_file_path = original_file_path.replace("original_data", "formatted_data")
            formatted_file_path = formatted_file_path.replace(".txt", ".umr")
            print(f"Processing file: {original_file_path}")
            print(f"formatted file: {formatted_file_path}")

            # Perform any operation on the file (e.g., read, parse, etc.)
            with open(original_file_path, 'r', encoding='utf-8') as f:
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
            data['meta_info'] = meta_info_match.group(1).strip()

        # Extract sentence_id from :: sntX
        sentence_id_match = re.search(r'# :: snt(\d+)', block)
        if sentence_id_match:
            data['sentence_id'] = int(sentence_id_match.group(1))

        # Extract sentence
        sentence_match = re.search(r'# ::snt (.+) # ::save-date', block)
        if sentence_match:
            data['sentence'] = sentence_match.group(1).strip()

        # Extract index and words
        # index_match = re.search(r'Index: ([^\n]+)\nWords: (.+)', block) #TODO
        data['index'] = ""
        try:
            doc = nlp(data['sentence'])
            data['words'] = [token.text for token in doc]
        except KeyError:
            print("something wrong with sentence ", data['sentence_id'])
            data['words'] = []

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
            data['meta_info'] = meta_info_match.group(1).strip()

        # Extract sentence_id from :: sntX
        sentence_id_match = re.search(r'# :: snt(\d+)', block)
        if sentence_id_match:
            data['sentence_id'] = int(sentence_id_match.group(1))

        # Extract sentence
        sentence_match = re.search(r'# ::snt (.+) # ::save-date', block)
        if sentence_match:
            data['sentence'] = sentence_match.group(1).strip()

        # Extract index and words
        # index_match = re.search(r'Index: ([^\n]+)\nWords: (.+)', block) #TODO
        data['index'] = ""
        try:
            doc = nlp(data['sentence'])
            data['words'] = [token.text for token in doc]
        except KeyError:
            print("something wrong with sentence ", data['sentence_id'])
            data['words'] = []

        # Extract sentence level graph
        graph_match = re.search(r'# sentence level graph:\n(.+?)(?=\n alignment:)', block, re.DOTALL)
        if graph_match:
            data['sentence_level_graph'] = graph_match.group(1).strip()
        else:
            data['sentence_level_graph'] = ""


        data['alignment'] = []
        data['document_level_annotation'] = []

        processed_data.append(data)
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(processed_data, file, ensure_ascii=False, indent=4)
    print(f"Processed data saved to {output_file_path}")
    return processed_data


def batch_process_file(formatted_folder_path):
    for subdir, _, files in os.walk(formatted_folder_path):
        for file in files:
            original_file_path = os.path.join(subdir, file)
            temp = original_file_path.replace("formatted_data/document_level/", "jsons/")
            temp = temp.replace("formatted_data/full_conversion/", "jsons/full_conversion_")
            temp = temp.replace("formatted_data/partial_conversion/", "jsons/partial_conversion_")
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

lang = "english"
original_folder_path = Path(root) / f'{lang}/original_data/'
formatted_folder_path = Path(root) / f'{lang}/formatted_data/'
# jsons_folder_path = Path(root) / f'{lang}/jsons/'

#step 1:
# batch_pre_format(original_folder_path)
# step 2:
batch_process_file(formatted_folder_path)

