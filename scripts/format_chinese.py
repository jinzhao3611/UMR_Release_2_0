import os, re, json
from pathlib import Path
from tabulate import tabulate
import penman
from penman.exceptions import DecodeError
current_script_dir = Path(__file__).parent
root = current_script_dir.parent

with open(Path(root) / 'chinese/role_mappings.json', 'r') as file:
    replacements = json.load(file)

def add_modal_triple(doc_text, new_triple="(author :full-affirmative s3z)"):
    """
    Given the text of a document-level annotation (AMR-like),
    add `new_triple` to the :modal block if it doesn't already exist.
    1) If there is no :modal block, create one.
    2) If there is a :modal block, insert the new triple before the final ')'.
    3) If `new_triple` (exact line match ignoring indentation) is already present, do nothing.
    """
    lines = doc_text.split("\n")

    # 0) Check if `new_triple` is already present (line-by-line)
    new_triple_stripped = new_triple.strip()
    for line in lines:
        if line.strip() == new_triple_stripped:
            # This exact triple line is already present
            return doc_text  # do nothing, return original

    # 1) Find if there's a :modal block
    found_modal_block = False
    modal_start_index = None

    for i, line in enumerate(lines):
        if line.strip().startswith(":modal ("):
            found_modal_block = True
            modal_start_index = i
            break

    if found_modal_block:
        # We already have a :modal block. Let's find its matching close.
        bracket_count = 0
        start = modal_start_index

        # Count parentheses from the start line until the block ends
        for j in range(start, len(lines)):
            bracket_count += lines[j].count("(")
            bracket_count -= lines[j].count(")")
            if bracket_count == 0:
                # j is the line where the :modal block closes
                # Insert our new triple just before this line.
                indent = " " * 8
                insertion_line = indent + new_triple
                lines.insert(j, insertion_line)
                break
    else:
        # No :modal block found => create a brand-new one.
        modal_block_lines = [
            "    :modal ((root :modal author)",
            f"        {new_triple})"  # close the parentheses
        ]

        # Insert near the end of the doc (just before the final line).
        insert_idx = len(lines) - 1
        # If you need a more precise spot, do a search for the top-level closing parenthesis.
        lines[insert_idx:insert_idx] = modal_block_lines

    # Return updated text
    return "\n".join(lines)

def create_aligned_lines(words):
    """
    Takes a list of words and returns two lines:
      1) An index line: "Index: 1  2  3  ..."
      2) A words line: "Words: w1 w2 w3 ..."
    using tabulate for alignment.
    """
    # Prepare a 2-row table where the first row has "Index:" + each index
    # and the second row has "Words:" + each word.
    data = [
        ["Index:"] + [str(i + 1) for i in range(len(words))],
        ["Words:"] + words
    ]

    # Generate a plain table with left alignment
    table_str = tabulate(data, tablefmt="plain", stralign="left")

    # Split the table into lines
    lines = table_str.split("\n")
    index_line = lines[0]
    words_line = lines[1]

    return index_line, words_line


def fix_closing_paren_format(text):
    # Split the text into lines
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        stripped = line.strip()
        # Check if the line (ignoring whitespace) consists solely of one or more closing parentheses
        if re.match(r'^\)+$', stripped):
            # If this line is just closing parentheses
            if new_lines:
                # Append these parentheses to the previous line
                new_lines[-1] = new_lines[-1].rstrip() + stripped
            else:
                # If there's no previous line, just add it as is
                new_lines.append(line)
        else:
            # Just a normal line, keep it
            new_lines.append(line)

    # Join the lines back together
    return '\n'.join(new_lines)

def fix_parentheses(input_text):
    pattern = re.compile(r'\((\S+)\)')

    # For each match, we replace '(token)' with 'token)'
    # i.e., remove only the opening parenthesis
    output_lines = []
    for line in input_text.split('\n'):
        new_line = pattern.sub(r'\1)', line)
        output_lines.append(new_line)

    output_text = "\n".join(output_lines)
    return output_text

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
                sentence_id = None
                if match:
                    sentence_id = int(match.group(1))
                else:
                    print("ERROR: there is no sentence_id extracted. ")
                if "\t" not in line: #lin bin's file
                    line = re.sub(r"(# :: snt\d+) ", r"\1\t", line)
                current_annotation = {
                    "meta_info": "",
                    "sentence_id": sentence_id,
                    "sentence": line.split("\t", 1)[1],
                    "index":"",
                    "words":line.split("\t", 1)[1].split(),
                    "sentence_level_graph": "",
                    "alignments": "", #TODO: change the alignment from string to dictionary
                    "document_level_annotation": "",
                }
            elif line.startswith("# ::snt"): #lin bin's file
                sent_level_annot = False
                alignment_annot = False
                doc_level_annot = False
                if current_annotation:
                    parsed_data["annotations"].append(current_annotation)
                match = re.search(r"# ::snt(\d+)Sentence:", line)
                sentence_id = None
                if match:
                    sentence_id = int(match.group(1))
                else:
                    print("ERROR: there is no sentence_id extracted. ")
                current_annotation = {
                    "meta_info": "",
                    "sentence_id": sentence_id,
                    "sentence": line.split("Sentence:", 1)[1],
                    "index":"",
                    "words":line.split("Sentence:", 1)[1].strip().split(),
                    "sentence_level_graph": "",
                    "alignments": "", #TODO: change the alignment from string to dictionary
                    "document_level_annotation": "",
                }
                current_annotation["conversion_type"] = "partial-conversion"
            elif current_annotation and line.startswith("# sentence level graph:"):
                sent_level_annot = True
                alignment_annot = False
                doc_level_annot = False
                current_annotation["sentence_level_graph"] = ""
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
                        current_annotation["sentence_level_graph"] += line
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


    for annot in parsed_data["annotations"]:
        sent_level_graph = annot["sentence_level_graph"]
        doc_level_graph = annot["document_level_annotation"]
        if doc_level_graph.strip() and not "ROOT" in doc_level_graph:
            doc_level_graph = add_modal_triple(doc_level_graph, "(ROOT :modal AUTH)")
        try:
            g = penman.decode(sent_level_graph)
            triples = g.triples
            for triple in triples:
                if triple[1] == ":MODSTR" or triple[1] == ":modal-strength":
                    if doc_level_graph.strip():
                        doc_level_graph = add_modal_triple(doc_level_graph, f"(AUTH :{triple[2]} {triple[0]})")
            # 2) Filter out any triple whose relation is ':MODSTR'
            filtered_triples = [t for t in triples if t[1] != ':MODSTR' and t[1] != ":modal-strength"]

            # 3) Build a new Graph with the filtered triples
            new_graph = penman.Graph(filtered_triples, epidata=g.epidata)

            # 4) Encode back to AMR-like text
            sent_level_graph = penman.encode(new_graph)
        except DecodeError:
            print(f"DecodeError in block:\n{sent_level_graph}\n")

        annot["sentence_level_graph"] = sent_level_graph
        annot["document_level_annotation"] = doc_level_graph

    # Save the parsed output as JSON for review
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(parsed_data["annotations"], output_file, ensure_ascii=False, indent=4)

    print(f"Parsed data saved to {output_file_path}")

def folder_umr_writer_txt2json():
    input_folder_path = Path(root) / 'chinese/original_data/'
    output_folder_path = Path(root) / 'chinese/jsons/'
    for file_path in input_folder_path.iterdir():
        if file_path.suffix == '.txt':  # Ensure the file has a .txt extension
            umr_writer_txt2json(file_path, Path.joinpath(output_folder_path, file_path.name.replace(".txt", ".json")))

            # try:
            # except Exception as e:
            #     print(f"Error processing {file_path}: {e}")


def json2txt(json_file_path, output_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    with open(output_file_path, 'w', encoding='utf-8') as out_file:
        for entry in data:
            # Prepare content for each entry
            id_info = entry.get("meta_info", "")
            conversion_type = entry.get("conversion_type", "")
            sentence_id = entry.get("sentence_id", "No sentence ID")
            words = entry.get("words", [])
            sent_annot = entry.get("sentence_level_graph", "No graph")
            alignment = entry.get("alignment", {})
            doc_annot = entry.get("document_level_annotation", "")
            for key, value in replacements.items():
                sent_annot = re.sub(re.escape(key), value, sent_annot, flags=re.IGNORECASE)
                doc_annot = re.sub(re.escape(key), value, doc_annot, flags=re.IGNORECASE)
            doc_annot = fix_closing_paren_format(doc_annot)
            doc_annot = fix_parentheses(doc_annot)

            if sentence_id != "No sentence ID":
                out_file.write("################################################################################\n")
                # Write the content to the file
                if id_info:
                    if conversion_type:
                        out_file.write(f"# meta-info :: sent_id = {id_info} :: type = partial_conversion\n")
                    else:
                        out_file.write(f"# meta-info :: sent_id = {id_info}\n")
                else:
                    if conversion_type:
                        out_file.write(f"# meta-info :: type = partial_conversion\n")
                    else:
                        out_file.write(f"# meta-info\n")

                out_file.write(f"# :: snt{sentence_id}\n")

                # Calculate the maximum width of the words for alignment
                if words:
                    index_str, words_str = create_aligned_lines(words)

                    out_file.write(index_str + "\n")
                    out_file.write(words_str + "\n")
                    out_file.write("\n")

                out_file.write(f"# sentence level graph:\n{sent_annot}\n\n")
                out_file.write(f"# alignment:\n")
                if alignment:
                    for v, i in alignment.items():
                        out_file.write(f"{v}: {i}\n")
                out_file.write(f"\n")
                out_file.write(f"# document level annotation:\n{doc_annot.strip()}\n\n\n")
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

if __name__ == '__main__':
    # step 1:
    # folder_umr_writer_txt2json()
    # step 2:
    batch_json2txt(Path(root) / 'chinese/jsons', Path(root) / 'chinese/formatted_data')
