import os, re, json
from pathlib import Path
from tabulate import tabulate
import penman
from penman.exceptions import DecodeError
current_script_dir = Path(__file__).parent
root = current_script_dir.parent

import re

def align_rows(rows):
    """
    Given a list of rows, each row a list of strings, preserve the exact spacing
    from the original file format. Each token should maintain its original width
    and spacing.
    """
    if not rows:
        return []

    # Get the maximum width needed for each column
    num_cols = max(len(row) for row in rows)
    col_widths = []
    
    # First column (labels) needs special handling
    col_widths.append(max(len(row[0]) for row in rows))
    
    # For remaining columns, find max width including all spaces
    for col in range(1, num_cols):
        width = 0
        for row in rows:
            if col < len(row):
                # Use the full token width including all spaces
                token = row[col] if col < len(row) else ""
                width = max(width, len(token))
        col_widths.append(width)

    # Format each row
    aligned = []
    for row in rows:
        # Handle label column specially
        parts = [row[0].ljust(col_widths[0])]
        
        # Handle remaining columns, preserving original content
        for i in range(1, num_cols):
            if i < len(row):
                token = row[i]
                # Keep original spacing but ensure minimum width
                parts.append(token.ljust(col_widths[i]))
            else:
                # Add empty space for missing columns
                parts.append(" " * col_widths[i])
        
        # Join with tabs
        aligned_row = '\t'.join(parts)
        aligned.append(aligned_row)
    
    return aligned

def reformat_file(old_path, new_path):
    """
    Read an input file, parse it into blocks starting at '# :: snt',
    and produce a new-format file.
    """
    with open(old_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = []
    current_block = []
    in_block = False

    # Define titles with consistent width
    TITLE_WIDTH = len("Translation(English):")  # Use longest title as standard
    TITLES = {
        "tx": "Words:".ljust(TITLE_WIDTH) + "\t",
        "mb": "Morphemes:".ljust(TITLE_WIDTH) + "\t",
        "ge": "Morphemes(English):".ljust(TITLE_WIDTH) + "\t",
        "ps": "Part of Speech:".ljust(TITLE_WIDTH) + "\t"
    }
    INDEX_TITLE = "Index:".ljust(TITLE_WIDTH) + "\t"
    TRANSLATION_TITLE = "Translation(English):".ljust(TITLE_WIDTH) + "\t"

    def split_into_tokens(text):
        """Split text into tokens, handling both whitespace and punctuation."""
        # First split by whitespace
        whitespace_tokens = text.split()
        
        # Then handle punctuation in each token
        final_tokens = []
        for token in whitespace_tokens:
            current = ""
            for char in token:
                if char in ",.\"!":  # Punctuation marks are individual tokens
                    if current:
                        final_tokens.append(current)
                        current = ""
                    final_tokens.append(char)
                else:
                    current += char
            if current:
                final_tokens.append(current)
        
        return final_tokens

    for line in lines:
        if line.strip().startswith("# :: snt"):
            if current_block:
                blocks.append(current_block)
            current_block = []
            in_block = True
        if in_block:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)

    reformatted = []
    first_block = True
    # Add sentence counter
    sentence_counter = 1
    for block in blocks:
        if not first_block:
            reformatted.append("################################################################################")
        else:
            reformatted.append("################################################################################")
        first_block = False

        snt_line = None
        tx_line = None  # Keep the entire original line
        mb_line = None
        ge_line = None
        ps_line = None
        tr_text = ""    # full translation
        sentence_level_graph = []
        alignment_lines = []
        doc_level_annotation = []

        in_graph = False
        in_alignment = False
        in_doc_annot = False

        for ln in block:
            line = ln.rstrip("\n")
            
            # 1) First check the "section" markers
            if line.strip() == "# sentence level graph:":
                in_graph = True
                in_alignment = False
                in_doc_annot = False
                sentence_level_graph.append(line)  # Include the header
                continue

            elif line.strip() == "# alignment:" or line.strip() == "# alignments:":
                in_graph = False
                in_alignment = True
                in_doc_annot = False
                alignment_lines.append(line)  # Include the header
                continue

            elif line.strip() in ["# document level annotation:", "# document level graph:"]:
                in_graph = False
                in_alignment = False
                in_doc_annot = True
                doc_level_annotation.append(line)  # Include the header
                continue

            # 2) If we are *currently* in one of those sections, append lines accordingly
            if in_graph:
                sentence_level_graph.append(line)
                continue
            if in_alignment:
                alignment_lines.append(line)
                continue
            if in_doc_annot:
                doc_level_annotation.append(line)
                continue

            # 3) If we're in *none* of those sections, then we parse morphological lines
            parts = line.split(None, 1)
            if len(parts) >= 2:
                tag, content = parts[0], parts[1]
                if tag == "tx":
                    tx_line = content
                elif tag == "mb":
                    mb_line = content
                elif tag == "ge":
                    ge_line = content
                elif tag == "ps":
                    ps_line = content
                elif tag == "tr":
                    tr_text = content.strip()
                # If none of those, just ignore or do something else...
                continue


            # Handle section headers and content
            if line.strip() == "# sentence level graph:":
                in_graph = True
                in_alignment = False
                in_doc_annot = False
                sentence_level_graph.append(line)  # Include the header
            elif line.strip() == "# alignment:":
                in_graph = False
                in_alignment = True
                in_doc_annot = False
                alignment_lines.append(line)  # Include the header
            elif line.strip() == "# document level annotation:":
                in_graph = False
                in_alignment = False
                in_doc_annot = True
                doc_level_annotation.append(line)  # Include the header
            # Add content to appropriate section, including empty lines and preserving original line
            elif in_graph:
                sentence_level_graph.append(line)
            elif in_alignment:
                alignment_lines.append(line)
            elif in_doc_annot:
                doc_level_annotation.append(line)

        # Build the reformatted output
        reformatted.append("# meta-info")

        # Add the sentence ID line with the correct sentence number
        reformatted.append(f"# :: snt{sentence_counter}")
        # Increment the sentence counter for the next block
        sentence_counter += 1

        if snt_line:
            reformatted.append(snt_line)

        # Build all the morphological rows
        if tx_line:
            # Process each tab-separated part and handle punctuation
            all_tokens = []
            for part in tx_line.split("\t"):
                if part.strip():
                    tokens = split_into_tokens(part.strip())
                    all_tokens.extend(tokens)
            
            # Generate index numbers
            index_parts = [str(i+1) for i in range(len(all_tokens))]
            
            # Add rows with new labels but preserve original content
            reformatted.append(INDEX_TITLE + "\t".join(index_parts))
            reformatted.append(TITLES["tx"] + tx_line)
            if mb_line: reformatted.append(TITLES["mb"] + mb_line)
            if ge_line: reformatted.append(TITLES["ge"] + ge_line)
            if ps_line: reformatted.append(TITLES["ps"] + ps_line)
            
            # Add translation on its own line if it exists
            if tr_text:
                reformatted.append(TRANSLATION_TITLE + tr_text)

        # Add the sections with their content
        reformatted.append("")
        reformatted.append("# sentence level graph:")
        if sentence_level_graph:
            for line in sentence_level_graph[1:]:  # Skip the header since we already added it
                reformatted.append(line)

        reformatted.append("")
        reformatted.append("# alignment:")
        if alignment_lines:
            for line in alignment_lines[1:]:  # Skip the header since we already added it
                reformatted.append(line)

        reformatted.append("")
        reformatted.append("# document level annotation:")
        if doc_level_annotation:
            for line in doc_level_annotation[1:]:  # Skip the header since we already added it
                reformatted.append(line)

        # Add a newline before the next block
        reformatted.append("")

    # Write out the reformatted file
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
    input_dir = Path(root) / "umr_1_0/arapaho/original_data"
    output_dir = Path(root) / "umr_1_0/arapaho/formatted_data"
    reformat_folder(input_dir, output_dir)
