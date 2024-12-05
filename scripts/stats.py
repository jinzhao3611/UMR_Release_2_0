import os
def count_valid_graphs(file_path):
    """
    Count the number of valid '# sentence level graph:' and
    '# document level annotation:' entries (where the next line is not empty).
    """
    valid_sentence_graph_count = 0
    valid_document_annotation_count = 0

    with open(file_path, 'r') as file:
        lines = file.readlines()

        for i, line in enumerate(lines):
            if line.strip().startswith("# sentence level graph:"):
                # Check if the next line exists and is not empty
                if i + 1 < len(lines) and lines[i + 1].strip():
                    valid_sentence_graph_count += 1
            elif line.strip().startswith("# document level annotation:"):
                # Check if the next line exists and is not empty
                if i + 1 < len(lines) and lines[i + 1].strip():
                    valid_document_annotation_count += 1

    return valid_sentence_graph_count, valid_document_annotation_count


def process_folder_with_valid_entries(folder_path):
    """
    Process all .txt files in the folder to count valid sentence-level graphs
    and document-level annotations.
    """
    txt_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.txt')]
    total_files = len(txt_files)

    total_valid_sentence_graph = 0
    total_valid_document_annotation = 0

    for txt_file in txt_files:
        valid_sentence_graph, valid_document_annotation = count_valid_graphs(txt_file)
        total_valid_sentence_graph += valid_sentence_graph
        total_valid_document_annotation += valid_document_annotation

    return total_files, total_valid_sentence_graph, total_valid_document_annotation


# Example usage
folder_path = "../english/formatted_data"  # Change this to your folder path

# Process the folder
total_files, total_valid_sentence_graph, total_valid_document_annotation = process_folder_with_valid_entries(
    folder_path)

# Print the results
print(f"Total .txt files in the folder: {total_files}")
print(f"Total valid '# sentence level graph:' count: {total_valid_sentence_graph}")
print(f"Total valid '# document level annotation:' count: {total_valid_document_annotation}")
