import os, re, json
from pathlib import Path

current_script_dir = Path(__file__).parent
root = current_script_dir.parent

with open(Path(root) / 'chinese/role_mappings.json', 'r') as file:
    replacements = json.load(file)

def umr_writer_txt2json(input_file_path, output_file_path):
    parsed_data = {
        "meta": {},
        "annotations": [],
        "source_file": []
    }

    # Helper variables
    current_annotation = None
    source_file_start = False
    sent_level_annot = False
    alignment_annot = False
    doc_level_annot = False
    with open(input_file_path, "r", encoding="utf-8") as file:
        for line in file:

            # Parse meta information
            if line.startswith("user name:"):
                parsed_data["meta"]["user_name"] = line.split(":")[1].strip()
            elif line.startswith("user id:"):
                parsed_data["meta"]["user_id"] = int(line.split(":")[1].strip())
            elif line.startswith("file language:"):
                parsed_data["meta"]["file_language"] = line.split(":")[1].strip()
            elif line.startswith("file format:"):
                parsed_data["meta"]["file_format"] = line.split(":")[1].strip()
            elif line.startswith("Doc ID in database:"):
                parsed_data["meta"]["doc_id"] = int(line.split(":")[1].strip())
            elif line.startswith("export time:"):
                parsed_data["meta"]["export_time"] = line.split(":", 1)[1].strip()

            # Parse annotations
            elif line.startswith("# :: snt"):
                sent_level_annot = False
                alignment_annot = False
                doc_level_annot = False
                if current_annotation:
                    parsed_data["annotations"].append(current_annotation)
                match = re.search(r"# :: snt(\d+)", line)
                if match:
                    sentence_id = int(match.group(1))
                else:
                    print("ERROR: there is no sentence_id extracted. ")
                if "\t" not in line: #lin bin's file
                    line = re.sub(r"(# :: snt\d+) ", r"\1\t", line)
                current_annotation = {
                    "sentence_id": sentence_id,
                    "sentence": line.split("\t", 1)[1],
                    "sentence_graph": "",
                    "alignments": "",
                    "document_level_annotation": ""
                }
            elif current_annotation and line.startswith("# sentence level graph:"):
                sent_level_annot = True
                alignment_annot = False
                doc_level_annot = False
                current_annotation["sentence_graph"] = ""
            elif current_annotation and line.startswith("# alignment:"):
                sent_level_annot = False
                alignment_annot = True
                doc_level_annot = False
                current_annotation["alignments"] += line.split(":", 1)[1]
            elif current_annotation and line.startswith("# document level annotation:"):
                sent_level_annot = False
                alignment_annot = False
                doc_level_annot = True
                current_annotation["document_level_annotation"] = ""
            elif current_annotation and not line.startswith("#") and not source_file_start:
                if sent_level_annot:
                    if line.strip():
                        current_annotation["sentence_graph"] += line
                elif alignment_annot:
                    if line.strip():
                        current_annotation["alignments"] += line
                elif doc_level_annot:
                    if line.strip():
                        current_annotation["document_level_annotation"] += line
                else:
                    print("ERROR: ", line)

            # Capture the source file text
            elif line.startswith("# Source File:"):
                sent_level_annot = False
                alignment_annot = False
                doc_level_annot = False
                if current_annotation:
                    parsed_data["annotations"].append(current_annotation)
                source_file_start = True
            elif source_file_start:
                sent_level_annot = False
                alignment_annot = False
                doc_level_annot = False
                parsed_data["source_file"].append(line)

    # Finalize if the last annotation was not added
    if current_annotation:
        parsed_data["annotations"].append(current_annotation)

    # Save the parsed output as JSON for review
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(parsed_data, output_file, ensure_ascii=False, indent=4)

    print(f"Parsed data saved to {output_file_path}")

def folder_umr_writer_txt2json():
    input_folder_path = Path(root) / 'chinese/original_data/'
    output_folder_path = Path(root) / 'chinese/jsons/'
    for file_path in input_folder_path.iterdir():
        if file_path.suffix == '.txt':  # Ensure the file has a .txt extension
            try:
                umr_writer_txt2json(file_path, Path.joinpath(output_folder_path, file_path.name.replace(".txt", ".json")))
            except Exception as e:
                print(f"Error processing {file_path}: {e}")



def json2txt(input_file_path, output_file_path):
    # input_file_path = "/Users/jinzhao/schoolwork/UMR_Release_2_0/chinese/jsons/coldwave_jingyi.json"
    # output_file_path = "/Users/jinzhao/schoolwork/UMR_Release_2_0/chinese/formatted_data/coldwave_jingyi.txt"
    with open(input_file_path, 'r') as file:
        data = json.load(file)

    output = ""
    for annotation in data["annotations"]:
        indices = "\t".join(map(str, range(1, len(annotation["sentence"].strip().split()) + 1)))
        output += f"""# :: snt{annotation["sentence_id"]}\nIndex:\t{indices}\nWords:\t{annotation["sentence"].strip()}\n\n"""
        sent_annot = annotation["sentence_graph"]
        doc_annot = annotation["document_level_annotation"]
        for key, value in replacements.items():
            sent_annot = re.sub(re.escape(key), value, sent_annot, flags=re.IGNORECASE)
            doc_annot = re.sub(re.escape(key), value, doc_annot, flags=re.IGNORECASE)

        output += f"""# sentence level graph:\n{sent_annot}\n"""
        output += f"""# alignment:\n{annotation["alignments"]}\n"""
        output += f"""# document level annotation:\n{doc_annot}\n\n"""


    with open(output_file_path, 'w') as file:
        file.write(output)

def folder_json2txt():
    input_folder_path = Path(root) / 'chinese/jsons/'
    output_folder_path = Path(root) / 'chinese/formatted_data/'
    for file_path in input_folder_path.iterdir():
        if file_path.suffix == '.json':  # Ensure the file has a .txt extension
            try:
                json2txt(file_path, Path.joinpath(output_folder_path, file_path.name.replace(".json", ".txt")))
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

if __name__ == '__main__':
    # folder_umr_writer_txt2json()
    folder_json2txt()