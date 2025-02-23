import os, re, json
from pathlib import Path
from tabulate import tabulate
import penman
from penman.exceptions import DecodeError
current_script_dir = Path(__file__).parent
root = current_script_dir.parent

import os
import re

def align_rows(rows):
    """
    Aligns rows of tokens into columns.
    rows: list of lists, e.g. [
      ["Index:", "1", "2"],
      ["Words:", "anyentehlehlta", "ampay'avehla'"],
      ["Morphemes:", "an-", "yentehl", "-e", "=hlta", ...],
      ...
    ]
    Returns a list of aligned strings, one per row.
    """
    if not rows:
        return []

    # Find how many columns in the widest row
    max_cols = max(len(r) for r in rows)

    # Compute max width per column
    col_widths = [0] * max_cols
    for row in rows:
        for c, cell in enumerate(row):
            col_widths[c] = max(col_widths[c], len(cell))

    # Build aligned lines
    aligned_lines = []
    for row in rows:
        padded_cells = []
        for c, cell in enumerate(row):
            padded_cells.append(cell.ljust(col_widths[c]))
        # Join columns with a single space
        aligned_lines.append(" ".join(padded_cells))

    return aligned_lines

def parse_block(block_lines):
    """
    Given lines for one block (starting with '# :: sntX'), gather:
      - snt_line
      - words, morphemes, morph_gloss_en, morph_gloss_es, morph_cat, word_gloss
      - english_sent_gloss, spanish_sent_gloss
      - sentence_level_graph, alignment, doc_annotation
    """
    data = {
        "snt_line": None,
        "words": [],
        "morphemes": [],
        "morph_gloss_en": [],
        "morph_gloss_es": [],
        "morph_cat": [],
        "word_gloss": [],
        "eng_sent_gloss": "",
        "spa_sent_gloss": "",
        "sentence_graph": [],
        "alignment": [],
        "doc_annotation": []
    }

    in_sentence_graph = False
    in_alignment = False
    in_doc_annot = False

    for line in block_lines:
        ln = line.rstrip("\n")

        # Check for # :: snt
        if ln.startswith("# :: snt"):
            data["snt_line"] = ln
            in_sentence_graph = False
            in_alignment = False
            in_doc_annot = False
            continue

        # # sentence level graph:
        if ln.startswith("# sentence level graph"):
            in_sentence_graph = True
            in_alignment = False
            in_doc_annot = False
            continue

        # # alignment:
        if ln.startswith("# alignment") or ln.startswith("# alignments"):
            in_sentence_graph = False
            in_alignment = True
            in_doc_annot = False
            continue

        # # document level annotation:
        if ln.startswith("# document level annotation") or ln.startswith("# document level graph"):
            in_sentence_graph = False
            in_alignment = False
            in_doc_annot = True
            continue

        # If we're in the sentence-level graph
        if in_sentence_graph:
            data["sentence_graph"].append(ln)
            continue
        # If we're in alignment
        if in_alignment:
            data["alignment"].append(ln)
            continue
        # If we're in doc-level annotation
        if in_doc_annot:
            data["doc_annotation"].append(ln)
            continue

        # Otherwise, check morphological lines:
        # We'll do a simpler approach: check if line starts with "Words", "Morphemes", etc.
        # Then parse the rest as tokens.
        # Or if line starts with e.g. "English Sent Gloss:", we store that in data["eng_sent_gloss"].

        # Lowercase check:
        line_low = ln.lower()

        if line_low.startswith("words"):
            # e.g. "Words         anyentehlehlta  ampay'avehla'"
            parts = ln.split(None, 1)
            if len(parts) > 1:
                data["words"] = parts[1].split()
            continue

        if line_low.startswith("morphemes"):
            parts = ln.split(None, 1)
            if len(parts) > 1:
                data["morphemes"] = parts[1].split()
            continue

        if line_low.startswith("morpheme gloss(en)"):
            parts = ln.split(None, 1)
            if len(parts) > 1:
                data["morph_gloss_en"] = parts[1].split()
            continue

        if line_low.startswith("morpheme gloss(es)"):
            parts = ln.split(None, 1)
            if len(parts) > 1:
                data["morph_gloss_es"] = parts[1].split()
            continue

        if line_low.startswith("morpheme cat"):
            parts = ln.split(None, 1)
            if len(parts) > 1:
                data["morph_cat"] = parts[1].split()
            continue

        if line_low.startswith("word gloss"):
            parts = ln.split(None, 1)
            if len(parts) > 1:
                data["word_gloss"] = parts[1].split()
            continue

        # English Sent Gloss:
        if line_low.startswith("english sent gloss:"):
            idx = ln.lower().index("english sent gloss:") + len("english sent gloss:")
            text = ln[idx:].strip()
            data["eng_sent_gloss"] = text
            continue

        # Spanish Sent Gloss:
        if line_low.startswith("spanish sent gloss:"):
            idx = ln.lower().index("spanish sent gloss:") + len("spanish sent gloss:")
            text = ln[idx:].strip()
            data["spa_sent_gloss"] = text
            continue

    return data

def reformat_block(data_dict):
    """
    Build the new format lines from the parsed block data.
    """
    lines = []
    lines.append("################################################################################")
    lines.append("# meta-info ")
    if data_dict["snt_line"]:
        lines.append(data_dict["snt_line"])

    # We'll build morphological rows for alignment:
    # 1) Index: (based on length of data["words"])
    morphological_rows = []

    if data_dict["words"]:
        index_row = ["Index:"]
        for i in range(len(data_dict["words"])):
            index_row.append(str(i+1))
        morphological_rows.append(index_row)

        # Words:
        morphological_rows.append(["Words:"] + data_dict["words"])

    if data_dict["morphemes"]:
        morphological_rows.append(["Morphemes:"] + data_dict["morphemes"])

    if data_dict["morph_gloss_en"]:
        morphological_rows.append(["Morpheme Gloss(en):"] + data_dict["morph_gloss_en"])

    if data_dict["morph_gloss_es"]:
        morphological_rows.append(["Morpheme Gloss(es):"] + data_dict["morph_gloss_es"])

    if data_dict["morph_cat"]:
        morphological_rows.append(["Morpheme Cat:"] + data_dict["morph_cat"])

    if data_dict["word_gloss"]:
        morphological_rows.append(["Word Gloss:"] + data_dict["word_gloss"])

    # English Sent Gloss:
    if data_dict["eng_sent_gloss"] or data_dict["eng_sent_gloss"] == "":
        # Even if empty, we want the line
        morphological_rows.append(["English Sent Gloss:", data_dict["eng_sent_gloss"]])

    # Spanish Sent Gloss:
    if data_dict["spa_sent_gloss"] or data_dict["spa_sent_gloss"] == "":
        morphological_rows.append(["Spanish Sent Gloss:", data_dict["spa_sent_gloss"]])

    aligned = align_rows(morphological_rows)
    lines.extend(aligned)

    # If we have a sentence-level graph
    if data_dict["sentence_graph"]:
        lines.append("")
        lines.append("# sentence level graph:")
        lines.extend(data_dict["sentence_graph"])

    # If we have alignment
    if data_dict["alignment"]:
        lines.append("")
        lines.append("# alignment:")
        lines.extend(data_dict["alignment"])

    # If we have doc-level annotation
    if data_dict["doc_annotation"]:
        lines.append("")
        lines.append("# document level annotation:")
        lines.extend(data_dict["doc_annotation"])

    lines.append("")
    return lines

def reformat_file(input_path, output_path):
    """
    Read one file, split into blocks (# :: sntX), parse & reformat each, write output.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Split into blocks
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
    # Add the last block
    if current_block:
        blocks.append(current_block)

    all_new_lines = []
    for blk in blocks:
        parsed_data = parse_block(blk)
        reformatted = reformat_block(parsed_data)
        all_new_lines.extend(reformatted)

    with open(output_path, "w", encoding="utf-8") as outf:
        for ln in all_new_lines:
            outf.write(ln + "\n")

def reformat_folder(input_folder, output_folder):
    """
    Process all .txt files in input_folder, output to output_folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for fname in os.listdir(input_folder):
        if not fname.endswith(".txt"):
            continue
        old_path = os.path.join(input_folder, fname)
        new_path = os.path.join(output_folder, fname).replace(".txt", ".umr")
        reformat_file(old_path, new_path)
        print(f"Reformatted {old_path} -> {new_path}")

if __name__ == "__main__":
    input_dir = Path(root) / "umr_1_0/sanapana/"
    output_dir = Path(root) / "umr_1_0_formatted/sanapana/"
    reformat_folder(input_dir, output_dir)

