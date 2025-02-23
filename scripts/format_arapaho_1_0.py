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
    Given a list of rows (each a list of strings), compute the max width
    of each column and pad so columns are aligned.
    Returns a list of joined strings (one per row).
    """
    if not rows:
        return []

    # 1) Find how many columns we have in the widest row
    max_cols = max(len(r) for r in rows)

    # 2) Compute the max width of each column c
    col_widths = [0] * max_cols
    for r in rows:
        for c, cell in enumerate(r):
            col_widths[c] = max(col_widths[c], len(cell))

    # 3) Build each row as a padded string
    aligned_lines = []
    for r in rows:
        # For columns that don't exist in this row, treat as empty
        padded_cells = []
        for c in range(max_cols):
            if c < len(r):
                cell = r[c]
            else:
                cell = ""
            padded_cells.append(cell.ljust(col_widths[c]))
        # Join them with a space in between (or tab if you prefer)
        aligned_lines.append(" ".join(padded_cells))
    return aligned_lines

def reformat_file(old_path, new_path):
    with open(old_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = []
    current_block = []

    # Split the file into blocks whenever we see "# :: snt..."
    for line in lines:
        if line.strip().startswith("# :: snt"):
            # start a new block
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)
    # Add the last block if not empty
    if current_block:
        blocks.append(current_block)

    reformatted_lines = []
    for block in blocks:
        block_stripped = [ln.rstrip("\n") for ln in block]

        # We'll store morphological lines:
        tx_tokens = []
        mb_tokens = []
        ge_tokens = []
        ps_tokens = []
        tr_tokens = []

        snt_line = None
        sentence_level_graph = []
        doc_level_graph = []
        alignment_lines = []

        in_slevel_graph = False
        in_dlevel_graph = False
        in_alignment = False

        for ln in block_stripped:
            # detect the # :: snt line
            if ln.startswith("# :: snt"):
                snt_line = ln
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = False
                continue

            # parse morphological lines
            parts = ln.split()
            if not parts:
                # blank or empty line
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = False
                continue

            tag = parts[0]
            tokens = parts[1:]

            if tag == "tx":
                tx_tokens = tokens
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = False
            elif tag == "mb":
                mb_tokens = tokens
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = False
            elif tag == "ge":
                ge_tokens = tokens
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = False
            elif tag == "ps":
                ps_tokens = tokens
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = False
            elif tag == "tr":
                tr_tokens = tokens
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = False

            elif ln.startswith("# sentence level graph"):
                # from now on, lines go into sentence_level_graph
                sentence_level_graph = []
                in_slevel_graph = True
                in_dlevel_graph = False
                in_alignment = False
            elif ln.startswith("# alignments") or ln.startswith("# alignment"):
                alignment_lines = []
                in_slevel_graph = False
                in_dlevel_graph = False
                in_alignment = True
            elif ln.startswith("# document level graph"):
                doc_level_graph = []
                in_slevel_graph = False
                in_dlevel_graph = True
                in_alignment = False
            else:
                # If we're inside the sentence-level graph block, store it
                if in_slevel_graph:
                    sentence_level_graph.append(ln)
                elif in_dlevel_graph:
                    doc_level_graph.append(ln)
                elif in_alignment:
                    alignment_lines.append(ln)
                else:
                    # Possibly ignore or handle otherwise
                    pass

        # Build up the morphological table lines
        # We'll store them as rows of tokens, then align them
        rows = []
        # 1) index row
        if tx_tokens:
            index_row = ["Index:"]
            for i in range(len(tx_tokens)):
                index_row.append(str(i+1))
            rows.append(index_row)

        # 2) words row
        if tx_tokens:
            rows.append(["Words:"] + tx_tokens)

        # 3) mb row
        if mb_tokens:
            rows.append(["mb:"] + mb_tokens)

        # 4) ge row
        if ge_tokens:
            rows.append(["ge:"] + ge_tokens)

        # 5) ps row
        if ps_tokens:
            rows.append(["ps:"] + ps_tokens)

        # 6) tr row
        if tr_tokens:
            rows.append(["tr:"] + tr_tokens)

        aligned_rows = align_rows(rows)

        # Now output the re-formatted block
        reformatted_lines.append("################################################################################")
        reformatted_lines.append("# meta-info")
        if snt_line:
            reformatted_lines.append(snt_line)

        # Add the aligned morphological lines
        reformatted_lines.extend(aligned_rows)

        # # sentence level graph
        if sentence_level_graph:
            reformatted_lines.append("")
            reformatted_lines.append("# sentence level graph: ")
            reformatted_lines.extend(sentence_level_graph)

        # # alignment
        if alignment_lines:
            reformatted_lines.append("")
            reformatted_lines.append("# alignment:")
            reformatted_lines.extend(alignment_lines)

        # # document level annotation
        if doc_level_graph:
            reformatted_lines.append("")
            reformatted_lines.append("# document level annotation: ")
            reformatted_lines.extend(doc_level_graph)

        reformatted_lines.append("")

    # Write out the final lines
    with open(new_path, "w", encoding="utf-8") as fout:
        for ln in reformatted_lines:
            fout.write(ln + "\n")

    print(f"Done. Reformatted output in {new_path}")


def reformat_folder(input_folder, output_folder):
    """
    Process all files in input_folder (that match some pattern, e.g. .txt)
    and write reformatted files to output_folder with the same filename.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for fname in os.listdir(input_folder):
        # skip non-.txt if that's desired
        if not fname.endswith(".txt"):
            continue

        old_path = os.path.join(input_folder, fname)
        new_path = os.path.join(output_folder, fname).replace(".txt", ".umr")
        reformat_file(old_path, new_path)

if __name__ == "__main__":
    input_dir = Path(root) / "umr_1_0/arapaho/"
    output_dir = Path(root) / "umr_1_0_formatted/arapaho/"
    reformat_folder(input_dir, output_dir)
