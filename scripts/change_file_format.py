import os, re, json
from pathlib import Path

# Get the directory of the current script
current_script_dir = Path(__file__).parent

# Construct the path to the file
root = current_script_dir.parent


def split_document_by_workset(input_file, file_name):
    # Define the input file path and delimiter
    # input_file = Path.joinpath(root, 'original_data/english/full_conversion/Document_Level_Graphs.txt')
    output_directory = Path.joinpath(root, 'english/splitted_data')
    delimiter1 = '# ::workset'
    delimiter2 = "***********************************************************************************************"

    # Initialize variables
    current_file_number = 1
    current_document_content = []
    file_prefix = f"{file_name}_"


    with open(input_file, 'r') as infile:
        # break the source file into documents
        for line in infile:
            # if '*' in line:
            #     print(repr(line))
            if line.startswith(delimiter1):
                print("workset name: ", line)
                if current_document_content:
                    output_file = os.path.join(output_directory, f"{file_prefix}{current_file_number}.txt")
                    with open(output_file, 'w') as outfile:
                        outfile.writelines(current_document_content)
                    current_file_number += 1
                    current_document_content = []
                continue # do not include the workset line in documents
            if line.strip() == delimiter2:
                continue # do not include the ending delimiter
            current_document_content.append(line)

        # Save the last file if there is any content
        if current_document_content:
            output_file = os.path.join(output_directory, f"{file_prefix}{current_file_number}.txt")
            with open(output_file, 'w') as outfile:
                outfile.writelines(current_document_content)

def split_full_conversion_documents_by_workset():
    full_conversion_path = Path(root) / 'english/original_data/full_conversion'
    # Iterate over all .txt files in the directory
    for file_path in full_conversion_path.iterdir():
        if file_path.suffix == '.txt':  # Ensure the file has a .txt extension
            print(f"Processing file: {file_path}")
            print(file_path)
            print(file_path.name)
            try:
                split_document_by_workset(file_path, file_path.name[:-4])
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

def extract_sentence_id(graph):
    """
    Extract the sentence ID (e.g., '4' from 's4') from the given sentence graph.
    """
    # Use a regular expression to find variables starting with 's' followed by a number
    matches = re.findall(r'\(s(\d+)', graph)

    # Return the first unique sentence ID found, if any
    return matches[0] if matches else None

def remove_empty_strings_before_sentence_graph(input_list):
    """
    Removes empty strings from the list if the next item is "sentence".
    """
    result = []
    for i in range(len(input_list)):
        # Check if the current item is an empty string and the next item is "sentence"
        if input_list[i] == "\n" and i + 1 < len(input_list) and input_list[i + 1].startswith("# sentence level graph:"):
            continue  # Skip adding this item to the result
        result.append(input_list[i])
    return result

def format_full_document_level_graphs_document(input_file):
    """
    1. changed format of sentence meta info comment line
    2. ensure one empty line between blocks and two empty lines between sentences
    3. change alignments to alignment for consistency (though alignments may make more sense )
    """
    output = []
    with open(input_file, 'r') as infile:
        lines = infile.readlines()
        # print("before:", lines)
        lines = remove_empty_strings_before_sentence_graph(lines) #document 4,5,6,7,8 have different line break rules with 1,2,3
        # print("after:", lines)
        blocks = ''.join(lines).strip().split("\n\n")
        for block in blocks:
            for i, line in enumerate(block.split('\n')):
                if line.startswith("# ::snt"):
                    # Extract the sentence
                    sentence = line.split("::snt", 1)[1].strip()
                    words = sentence.split()

                    # Create indexed representation
                    indices = [f"{j + 1:5}" for j in range(len(words))]
                    index_line = f"Index:   {'  '.join(indices)}\n"
                    words_line = f"Words:   {'  '.join(words)}\n\n"

                    sent_id = extract_sentence_id(block)
                    # Write the original line
                    output.append(f"# :: snt{sent_id}\n")

                    # Write the index and words table
                    output.append(index_line)
                    output.append(words_line)
                elif line.startswith("# alignments:"):
                    output.append("# alignment:\n")
                elif line.startswith("# document level graph:"):
                    output.append('# document level annotation:\n')
                else:
                    # Write the line as is
                    output.append(line+'\n')
            if block.startswith('# document level graph:'):
                output.append('\n\n')
            else:
                output.append('\n')
    return output

def format_full_ldc_document(input_file):
    """
    1. changed format of sentence meta info comment line
    2. ensure one empty line between blocks and two empty lines between sentences
    3. change alignments to alignment for consistency (though alignments may make more sense )
    """
    output = []
    blocks = full_ldc2document_level_graphs(input_file).strip().split("\n\n")
    for block in blocks:
        for i, line in enumerate(block.split('\n')):
            if line.startswith("# ::snt"):
                # Extract the sentence
                sentence = line.split("::snt", 1)[1].strip()
                words = sentence.split()

                # Create indexed representation
                indices = [f"{j + 1:5}" for j in range(len(words))]
                index_line = f"Index:   {'  '.join(indices)}\n"
                words_line = f"Words:   {'  '.join(words)}\n\n"

                sent_id = extract_sentence_id(block)
                # Write the original line
                output.append(f"# :: snt{sent_id}\n")

                # Write the index and words table
                output.append(index_line)
                output.append(words_line)
            elif line.startswith("# alignments:"):
                output.append("# alignment:\n")
            elif line.startswith("# document level graph:"):
                output.append('# document level annotation:\n')
            else:
                # Write the line as is
                output.append(line+'\n')
        if block.startswith('# document level graph:'):
            output.append('\n\n')
        else:
            output.append('\n')
    return output

def full_ldc2document_level_graphs(input_file):
    with open(input_file, "r") as f:
        input_text = f.read()

    sections = input_text.strip().split("\n\n")
    output = []

    for section in sections:
        lines = section.strip().split("\n")
        metadata = []
        graph_lines = []
        sentence = ""

        for line in lines:
            if line.startswith("#"):
                metadata.append(line.strip())
                if line.startswith("# ::snt"):
                    sentence = line.split("# ::snt", 1)[-1].strip()
            else:
                graph_lines.append(line)

        # Build output
        formatted_metadata = " ".join(metadata)
        sentence_graph = "\n".join(graph_lines)
        formatted_section = (
            f"{formatted_metadata}\n"
            f"# ::snt {sentence}\n"
            f"# sentence level graph:\n{sentence_graph}\n\n"
            "# alignments:\n\n"
            "# document level graph:\n\n"
        )
        output.append(formatted_section.strip())
    return "\n\n".join(output)

def format_english():
    input_folder_path = Path(root) / 'english/splitted_data/'
    output_folder_path = Path(root) / 'english/formatted_data/'
    # Iterate over all .txt files in the directory
    for file_path in input_folder_path.iterdir():
        if file_path.suffix == '.txt':  # Ensure the file has a .txt extension
            try:
                if file_path.name.startswith("Document_Level_Graphs"):
                    print(f"Processing file: {file_path}")
                    output_list = format_full_document_level_graphs_document(file_path)
                else:
                    print(f"Processing file: {file_path}")
                    output_list = format_full_ldc_document(file_path)
                with open(Path.joinpath(output_folder_path, file_path.name), 'w') as outfile:
                    outfile.writelines(output_list)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

if __name__ == '__main__':
    split_full_conversion_documents_by_workset()
    format_english()
