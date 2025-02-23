import os,re
import penman
from penman.exceptions import DecodeError
from tabulate import tabulate
from pathlib import Path


# Get the directory of the current script
current_script_dir = Path(__file__).parent

# Construct the path to the file
root = current_script_dir.parent

def parse_blocks_from_file(file_path):
    """
    Reads the .txt file and yields one 'block' at a time (list of lines).
    Each block is separated by lines starting with '################################################################################'.
    """
    blocks = []
    current_block = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith("################################################################################"):
                # If we hit the delimiter, store the current block (if not empty) and start a new one
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            else:
                current_block.append(line.rstrip('\n'))
        # Add the last block if file doesn't end with the delimiter
        if current_block:
            blocks.append(current_block)

    return blocks

def analyze_block(block_lines):
    """
    Analyze a single block and return a dictionary with:
      - is_partial: bool (True if :: type = partial_conversion)
      - word_count: int (# of words in the 'Words:' line)
      - has_sentence_graph: bool
      - has_doc_graph: bool (doc-level graph with >2 lines)
      - relations_count: int (# of relations in the sentence-level graph)
      - concepts_count: int (# of concepts in the sentence-level graph)
    """
    is_partial = False
    word_count = 0
    has_sentence_graph = False
    has_doc_graph = False
    relations_count = 0
    concepts_count = 0
    doc_relations_count = 0

    # Convert block lines to a single string for easy searching
    block_text = "\n".join(block_lines)

    # 1) Check if partial_conversion
    for line in block_lines:
        if line.startswith('# meta-info') and 'type = partial_conversion' in line:
            is_partial = True
            break

    # 2) Count words from the "Words:" line
    for line in block_lines:
        if line.startswith("Words:"):
            # Extract everything after "Words:"
            words_part = line.replace("Words:", "").strip()
            word_count = len(words_part.split())
            break

    # 3) Detect and parse the sentence-level graph
    #    We'll count "has_sentence_graph" if there's at least one line of graph text
    #    after '# sentence level graph:'.
    if "# sentence level graph:" in block_text:
        start_index = None
        for i, line in enumerate(block_lines):
            if line.strip().startswith("# sentence level graph:"):
                start_index = i + 1
                break

        if start_index is not None and start_index < len(block_lines):
            # Collect graph lines until we hit another '#' section or end of block
            graph_lines = []
            for j in range(start_index, len(block_lines)):
                if block_lines[j].strip().startswith("#"):
                    break
                graph_lines.append(block_lines[j])

            graph_text = "\n".join(graph_lines).strip()
            if graph_text:
                has_sentence_graph = True
                clean_graph_text = graph_text.replace("#", "") # czech has concepts starts with #
                clean_graph_text = re.sub(r"\((s\d+x\d+) / /\)", r"\1", clean_graph_text) # czech has nodes like (s234x21 / /)
                # Try to decode with Penman
                try:
                    g = penman.decode(clean_graph_text)
                    triples = g.triples
                    # Count concepts vs. relations
                    relations_count = sum(1 for triple in triples if triple[1] != ':instance')
                    concepts_count = sum(1 for triple in triples if triple[1] == ':instance')
                except DecodeError:
                    # Optional: print the failing graph or an error message
                    # (Only if you want to debug. Otherwise, you can silence it.)
                    print(f"DecodeError in block:\n{clean_graph_text}\n")


    # 4) Check for multi-line document-level graph
    #    We only count it if there are >2 lines after "# document level annotation:".
    if "# document level annotation:" in block_text:
        start_index = None
        for i, line in enumerate(block_lines):
            if line.strip().startswith("# document level annotation:"):
                start_index = i + 1
                break
        if start_index is not None:
            doc_graph_lines = []
            for j in range(start_index, len(block_lines)):
                line_j = block_lines[j].strip()
                if line_j.startswith("#"):
                    break
                if line_j:  # skip empty lines
                    doc_graph_lines.append(line_j)
            if len(doc_graph_lines) > 2:
                has_doc_graph = True
                doc_relations_count = len(doc_graph_lines) - 1


    return {
        "is_partial": is_partial,
        "word_count": word_count,
        "has_sentence_graph": has_sentence_graph,
        "has_doc_graph": has_doc_graph,
        "relations_count": relations_count,
        "concepts_count": concepts_count,
        "doc_relations_count": doc_relations_count
    }

def analyze_folder(folder_path):
    """
    Go through each .txt file in the folder, parse blocks, categorize partial vs. non-partial,
    and accumulate stats (including relations & concepts).
    """
    all_docs = 0
    # PARTIAL counters
    partial_docs = 0
    partial_sentences = 0
    partial_words = 0
    partial_sentence_graphs = 0
    partial_doc_graphs = 0
    partial_relations = 0
    partial_concepts = 0
    partial_doc_relations = 0

    # NON-PARTIAL counters
    nonpartial_docs = 0
    nonpartial_sentences = 0
    nonpartial_words = 0
    nonpartial_sentence_graphs = 0
    nonpartial_doc_graphs = 0
    nonpartial_relations = 0
    nonpartial_concepts = 0
    nonpartial_doc_relations = 0

    # Iterate over each .txt file
    for fname in os.listdir(folder_path):
        if not fname.endswith(".umr"):
            continue

        all_docs += 1
        file_path = os.path.join(folder_path, fname)
        blocks = parse_blocks_from_file(file_path)

        # Track if this file had partial or non-partial blocks
        file_has_partial = False
        file_has_nonpartial = False

        for block in blocks:
            info = analyze_block(block)

            if info["is_partial"]:
                file_has_partial = True
                partial_sentences += 1
                partial_words += info["word_count"]
                if info["has_sentence_graph"]:
                    partial_sentence_graphs += 1
                if info["has_doc_graph"]:
                    partial_doc_graphs += 1
                partial_relations += info["relations_count"]
                partial_concepts += info["concepts_count"]
                partial_doc_relations += info["doc_relations_count"]
            else:
                file_has_nonpartial = True
                nonpartial_sentences += 1
                nonpartial_words += info["word_count"]
                if info["has_sentence_graph"]:
                    nonpartial_sentence_graphs += 1
                if info["has_doc_graph"]:
                    nonpartial_doc_graphs += 1
                nonpartial_relations += info["relations_count"]
                nonpartial_concepts += info["concepts_count"]
                nonpartial_doc_relations += info["doc_relations_count"]

        if file_has_partial:
            partial_docs += 1
        if file_has_nonpartial:
            nonpartial_docs += 1


    all_data = [
        ["Documents", all_docs],
    ]
    # Prepare table data for partial
    partial_data = [
        ["Documents", partial_docs],
        ["Sentences (Blocks)", partial_sentences],
        ["Words", partial_words],
        ["Sentence-level Graphs", partial_sentence_graphs],
        ["Doc-level Graphs", partial_doc_graphs],
        ["Relations (Sentence-level)", partial_relations],
        ["Concepts (Sentence-level)", partial_concepts],
        ["Relations (Document-level)", partial_doc_relations],
    ]

    # Prepare table data for non-partial
    nonpartial_data = [
        ["Documents", nonpartial_docs],
        ["Sentences (Blocks)", nonpartial_sentences],
        ["Words", nonpartial_words],
        ["Sentence-level Graphs", nonpartial_sentence_graphs],
        ["Doc-level Graphs", nonpartial_doc_graphs],
        ["Relations (Sentence-level)", nonpartial_relations],
        ["Concepts (Sentence-level)", nonpartial_concepts],
        ["Relations (Document-level)", nonpartial_doc_relations],
    ]
    print("=== Stats for ALL ===")
    print(tabulate(all_data, headers=["Metric", "Count"], tablefmt="grid"))

    print("\n=== Stats for PARTIAL-CONVERSION ===")
    print(tabulate(partial_data, headers=["Metric", "Count"], tablefmt="grid"))

    print("\n=== Stats for NON-PARTIAL-CONVERSION Blocks ===")
    print(tabulate(nonpartial_data, headers=["Metric", "Count"], tablefmt="grid"))

def print_explanation():

    all_data = [
        ["Documents", "Total documents of this language"],
    ]
    # Prepare table data for partial
    partial_data = [
        ["Documents", "Documents that contain at least one partial annotation"],
        ["Sentences (Blocks)", "Sentences that have partially converted annotation"],
        ["Words", "Total words of sentences that have partially converted annotation"],
        ["Sentence-level Graphs", "partially converted sentence level annotations"],
        ["Doc-level Graphs", "partially converted document level annotations"],
        ["Relations (Sentence-level)", "Total relations in partially converted sentence level annotation"],
        ["Concepts (Sentence-level)", "Total concepts in partially converted annotation"],
        ["Relations (Document-level)", "Total relations in partially converted document level annotation"],
    ]

    # Prepare table data for non-partial
    nonpartial_data = [
        ["Documents", "Documents that contain at least one non-partial annotation"],
        ["Sentences (Blocks)", "Sentences that have non-partially converted annotation"],
        ["Words", "Total words of sentences that have non-partially converted annotation"],
        ["Sentence-level Graphs", "non-partially converted sentence level annotations"],
        ["Doc-level Graphs", "non-partially converted document level annotations"],
        ["Relations (Sentence-level)", "Total relations in non-partially converted sentence level annotation"],
        ["Concepts (Sentence-level)", "Total concepts in non-partially converted annotation"],
        ["Relations (Document-level)", "Total relations in non-partially converted document level annotation"],
    ]
    print("=== Stats for ALL ===")
    print(tabulate(all_data, headers=["Metric", "Count"], tablefmt="grid"))

    print("\n=== Stats for PARTIAL-CONVERSION ===")
    print(tabulate(partial_data, headers=["Metric", "Count"], tablefmt="grid"))

    print("\n=== Stats for NON-PARTIAL-CONVERSION Blocks ===")
    print(tabulate(nonpartial_data, headers=["Metric", "Count"], tablefmt="grid"))


if __name__ == "__main__":
    # lang = 'english'
    # folder_path = Path(root) / f'{lang}/merged_output_data/'
    # analyze_folder(folder_path)

    # lang = 'czech'
    # folder_path = Path(root) / f'{lang}/original_data/'
    # analyze_folder(folder_path)

    lang = 'chinese'
    folder_path = Path(root) / f'{lang}/formatted_data/'
    analyze_folder(folder_path)

    # print_explanation()
