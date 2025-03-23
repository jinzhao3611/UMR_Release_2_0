import os
import re
from pathlib import Path
from tabulate import tabulate
import penman
from penman.exceptions import DecodeError
current_script_dir = Path(__file__).parent
root = current_script_dir.parent


def align_rows(rows):
    """
    Given a list of rows, each row a list of strings, compute the max width
    of each column and pad so columns are aligned.
    Returns a list of joined strings (one per row).
    """
    if not rows:
        return []
    # Number of columns in the widest row
    max_cols = max(len(r) for r in rows)

    # Compute max width of each column
    col_widths = [0] * max_cols
    for r in rows:
        for c, cell in enumerate(r):
            col_widths[c] = max(col_widths[c], len(cell))

    # Build each row as a padded string
    aligned = []
    for r in rows:
        padded_cells = []
        for c in range(max_cols):
            cell = r[c] if c < len(r) else ""
            # left-justify to col_widths[c]
            padded_cells.append(cell.ljust(col_widths[c]))
        # Join with a single space (or tab if you prefer)
        aligned.append(" ".join(padded_cells))
    return aligned


def extract_variables_and_concepts(graph_text):
    """
    Extract variables and their associated concepts from the graph using penman.
    
    Args:
        graph_text: The sentence level graph text
        
    Returns:
        dict: A dictionary mapping variables to their concepts
    """
    try:
        g = penman.decode(graph_text)
        var_concepts = {}
        for instance in g.instances():
            # Remove any -01, -02 etc. suffixes from concepts
            base_concept = re.sub(r'-\d+$', '', instance.target)
            var_concepts[instance.source] = base_concept
        return var_concepts
    except Exception as e:
        print(f"Error parsing graph with penman: {e}")
        return {}

def find_token_for_concept(concept, words):
    """
    Find the token that best matches the concept.
    
    Args:
        concept: The concept to match
        words: List of tokens in the sentence
        
    Returns:
        int: The 1-based index of the matching token, or 0 if no match found
    """
    # Convert concept to base form (remove hyphens and numbers)
    base_concept = concept.lower().replace('-', '')
    
    # First try exact match
    for i, word in enumerate(words, 1):
        if word.lower() == base_concept:
            return i
            
    # Then try stem/substring matching
    for i, word in enumerate(words, 1):
        word_lower = word.lower()
        # Check if either is a substring of the other
        if (base_concept in word_lower or 
            word_lower in base_concept or
            # Handle common variations (e.g., "take" matching "takes", "taking", etc.)
            word_lower.startswith(base_concept) or
            base_concept.startswith(word_lower)):
            return i
    
    return 0

def generate_alignments_from_graph(graph_text, words, num_tokens):
    """
    Generate alignments from the graph by matching variables' concepts with tokens.
    Uses penman to properly parse the graph structure.
    Always returns either a valid token index or 0-0, never -1--1.
    
    Args:
        graph_text: The sentence level graph text
        words: List of tokens in the sentence
        num_tokens: Number of tokens in the sentence
        
    Returns:
        dict: A dictionary mapping variables to alignment spans
    """
    alignments = {}
    try:
        # Extract variables and their concepts using penman
        var_concepts = extract_variables_and_concepts(graph_text)
        
        # For each variable, try to find a matching token
        for var, concept in var_concepts.items():
            token_idx = find_token_for_concept(concept, words)
            
            # Assign alignment
            if token_idx > 0 and token_idx <= num_tokens:
                alignments[var] = f"{token_idx}-{token_idx}"
            else:
                alignments[var] = "0-0"
                
        return alignments
    except Exception as e:
        print(f"Error generating alignments: {e}")
        return {}

def reformat_file(old_path, new_path):
    """
    Read an input file, parse it into blocks starting at '# :: snt',
    and produce a new-format file.
    """
    with open(old_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # We'll hold multiple 'blocks', each block is lines from
    # a '# :: snt' up to the next '# :: snt'.
    blocks = []
    current_block = []

    for line in lines:
        if line.strip().startswith("# :: snt"):
            # new block
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)
    # add final block if non-empty
    if current_block:
        blocks.append(current_block)

    reformatted = []
    for block in blocks:
        # We'll gather:
        # 1) The "# :: sntX" line
        # 2) The tokens for the sentence
        # 3) The sentence-level graph
        # 4) The alignment lines
        # 5) The doc-level annotation

        snt_line = None
        sentence_tokens = []
        sentence_level_graph = []
        alignment_lines = []
        doc_level_annotation = []

        in_graph = False
        in_alignment = False
        in_doc_annot = False

        for ln in block:
            line = ln.rstrip("\n")

            # detect "# :: sntX"
            if line.startswith("# :: snt"):
                # Extract just the snt number part
                match = re.match(r"# :: (snt\d+)", line)
                if match:
                    snt_number = match.group(1)
                    snt_line = f"# :: {snt_number}"
                else:
                    snt_number = "sntX"
                    snt_line = "# :: sntX"
                
                # Parse the sentence tokens if they exist
                line_split = line.split(None, 2)  # up to 3 parts
                if len(line_split) > 2:
                    third_part = line_split[2].strip()
                    match = re.match(r"(snt\d+)\s+(.*)", third_part)
                    if match:
                        tokens_str = match.group(2)  # "该 周报 综合 ..."
                        sentence_tokens = tokens_str.split()
                    else:
                        if "\t" in third_part:
                            parts2 = third_part.split("\t", 1)
                            if len(parts2) > 1:
                                sentence_tokens = parts2[1].split()

                # done reading this line, move on
                in_graph = False
                in_alignment = False
                in_doc_annot = False
                continue

            if line.startswith("# sentence level graph"):
                in_graph = True
                in_alignment = False
                in_doc_annot = False
                continue
            elif line.startswith("# alignment"):
                in_alignment = True
                in_graph = False
                in_doc_annot = False
                continue
            elif line.startswith("# document level annotation") or line.startswith("# document level graph"):
                in_doc_annot = True
                in_graph = False
                in_alignment = False
                continue

            # If we're inside the graph
            if in_graph:
                sentence_level_graph.append(line)
            # If we're inside alignment
            elif in_alignment:
                alignment_lines.append(line)
            # If we're inside doc-level annotation
            elif in_doc_annot:
                doc_level_annotation.append(line)

        # Now we build the new format
        reformatted.append("################################################################################")
        reformatted.append("# meta-info")

        if snt_line:
            reformatted.append(snt_line)  # This will now only contain "# :: sntX" without the sentence

        # Build an "Index:" row and "Words:" row
        # We'll align them in columns
        if sentence_tokens:
            index_row = ["Index:"]
            for i in range(len(sentence_tokens)):
                index_row.append(str(i + 1))
            words_row = ["Words:"] + sentence_tokens

            # We can align these 2 rows with align_rows
            aligned = align_rows([index_row, words_row])
            reformatted.extend(aligned)

        # Print the sentence-level graph
        if sentence_level_graph:
            reformatted.append("")
            reformatted.append("# sentence level graph:")
            reformatted.extend(sentence_level_graph)

        # Generate new alignments from the graph
        if sentence_level_graph and sentence_tokens:
            graph_text = "\n".join(sentence_level_graph)
            num_tokens = len(sentence_tokens)
            generated_alignments = generate_alignments_from_graph(graph_text, sentence_tokens, num_tokens)
            
            # Add the generated alignments
            if generated_alignments:
                reformatted.append("")
                reformatted.append("# alignment:")
                for var in sorted(generated_alignments.keys()):
                    reformatted.append(f"{var}: {generated_alignments[var]}")

        # Print doc-level annotation
        if doc_level_annotation:
            reformatted.append("")
            reformatted.append("# document level annotation:")
            reformatted.extend(doc_level_annotation)

        reformatted.append("")

    # Finally, write them out
    with open(new_path, "w", encoding="utf-8") as out:
        for ln in reformatted:
            out.write(ln + "\n")


def reformat_folder(input_folder, output_folder):
    """Process all files in 'input_folder' and write reformatted files to 'output_folder'."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for fname in os.listdir(input_folder):
        # If you only want to process .txt:
        if not fname.endswith(".txt"):
            continue
        old_path = os.path.join(input_folder, fname)
        new_path = os.path.join(output_folder, fname).replace(".txt", ".umr")
        reformat_file(old_path, new_path)
        print(f"Reformatted {old_path} -> {new_path}")


if __name__ == "__main__":
    input_dir = Path(root) / "umr_1_0/chinese/original_data"
    output_dir = Path(root) / "umr_1_0/chinese/formatted_data"
    reformat_folder(input_dir, output_dir)
