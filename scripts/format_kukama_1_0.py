import os, re, json
from pathlib import Path
from tabulate import tabulate
import penman
from penman.exceptions import DecodeError
current_script_dir = Path(__file__).parent
root = current_script_dir.parent

def align_rows(rows):
    """
    Aligns rows of tokens into columns.
    rows: list of lists, e.g. [
      ["Index:", "1", "2", "3"],
      ["Words:", "tsɨmɨntsarara", "amutsu", "TA"],
      ["Morphemes:", "ts-", "ɨmɨntsara", "-ra", "amu", "-utsu", "None"],
      ...
    ]
    Returns a list of aligned strings, one per row.
    """
    if not rows:
        return []

    # Find the widest row
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
    Given the lines for a single block (starting with '# :: sntN'),
    parse out morphological lines, the sentence-level graph, alignment, doc-level annotation.
    Return a dict with the needed info.
    """
    data = {
        "snt_line": None,
        "words": [],
        "morphemes": [],
        "morph_gloss_eng": [],
        "morph_gloss_spa": [],
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

        # Detect snt line
        if ln.startswith("# :: snt"):
            data["snt_line"] = ln
            in_sentence_graph = False
            in_alignment = False
            in_doc_annot = False
            continue

        # If we see "# sentence level graph:"
        if ln.startswith("# sentence level graph"):
            in_sentence_graph = True
            in_alignment = False
            in_doc_annot = False
            continue

        # If we see "# alignment:"
        if ln.startswith("# alignment") or ln.startswith("# alignments"):
            in_sentence_graph = False
            in_alignment = True
            in_doc_annot = False
            continue

        # If we see "# document level annotation:" or "# document level graph:"
        if ln.startswith("# document level annotation") or ln.startswith("# document level graph"):
            in_sentence_graph = False
            in_alignment = False
            in_doc_annot = True
            continue

        # If we're in the sentence-level graph block
        if in_sentence_graph:
            data["sentence_graph"].append(ln)
            continue
        # If in alignment block
        if in_alignment:
            data["alignment"].append(ln)
            continue
        # If in doc-level annotation
        if in_doc_annot:
            data["doc_annotation"].append(ln)
            continue

        # Otherwise, let's see if it's a morphological line
        # We'll check line starts:
        # "Words"
        # "Morphemes"
        # "Morpheme Gloss(English)"
        # "Morpheme Gloss(Spanish)"
        # "English Sent Gloss:"
        # "Spanish Sent Gloss:"
        # etc.
        # Then parse the tokens.
        # e.g.: "Words                          tsɨmɨntsarara           amutsu    TA"
        # We'll split on whitespace. The first token is "Words", the rest are tokens.

        # We can do something like:
        # If the line starts with "Words", we parse the rest into data["words"].
        # But watch out for lines like "English Sent Gloss: I will tell something"

        # Let's define a pattern for morphological lines:
        # <Label> : <tokens...> OR <Label><some spacing> <tokens...>

        # We'll do a simplified approach: check known keywords
        stripped_lower = ln.strip().lower()
        if stripped_lower.startswith("words"):
            # parse tokens after the word "Words"
            parts = ln.split(None, 1)  # e.g. ["Words", "tsɨmɨntsarara ..."]
            if len(parts) > 1:
                tokens_line = parts[1].split()
                data["words"] = tokens_line
            continue

        if stripped_lower.startswith("morphemes"):
            # parse tokens after "Morphemes"
            parts = ln.split(None, 1)
            if len(parts) > 1:
                tokens_line = parts[1].split()
                data["morphemes"] = tokens_line
            continue

        # e.g. "Morpheme Gloss(English)"
        # We'll do a simpler check:
        if stripped_lower.startswith("morpheme gloss(english)"):
            parts = ln.split(None, 1)
            if len(parts) > 1:
                tokens_line = parts[1].split()
                data["morph_gloss_eng"] = tokens_line
            continue

        if stripped_lower.startswith("morpheme gloss(spanish)"):
            parts = ln.split(None, 1)
            if len(parts) > 1:
                tokens_line = parts[1].split()
                data["morph_gloss_spa"] = tokens_line
            continue

        # English Sent Gloss:
        if stripped_lower.startswith("english sent gloss:"):
            # everything after that is the line
            idx = ln.lower().index("english sent gloss:") + len("english sent gloss:")
            text = ln[idx:].strip()
            data["eng_sent_gloss"] = text
            continue

        # Spanish Sent Gloss:
        if stripped_lower.startswith("spanish sent gloss:"):
            idx = ln.lower().index("spanish sent gloss:") + len("spanish sent gloss:")
            text = ln[idx:].strip()
            data["spa_sent_gloss"] = text
            continue

    return data

def reformat_block(data_dict):
    """
    Build the new format block lines from the parsed data.
    """
    lines = []
    lines.append("################################################################################")
    lines.append("# meta-info ")  # could also do "# meta-info :: sent_id = something" if you want

    # Add the snt_line if present
    if data_dict["snt_line"]:
        lines.append(data_dict["snt_line"])

    # Build "Index:" row using length of data_dict["words"]
    # For example, if words has 3 tokens, Index row is ["Index:", "1", "2", "3"]
    morphological_rows = []
    if data_dict["words"]:
        index_row = ["Index:"]
        for i in range(len(data_dict["words"])):
            index_row.append(str(i+1))
        morphological_rows.append(index_row)
        morphological_rows.append(["Words:"] + data_dict["words"])
    if data_dict["morphemes"]:
        morphological_rows.append(["Morphemes:"] + data_dict["morphemes"])
    if data_dict["morph_gloss_eng"]:
        morphological_rows.append(["Morpheme Gloss(English):"] + data_dict["morph_gloss_eng"])
    if data_dict["morph_gloss_spa"]:
        morphological_rows.append(["Morpheme Gloss(Spanish):"] + data_dict["morph_gloss_spa"])

    # If we have an English Sent Gloss
    if data_dict["eng_sent_gloss"]:
        morphological_rows.append(["English Sent Gloss:", data_dict["eng_sent_gloss"]])

    # If we have a Spanish Sent Gloss
    if data_dict["spa_sent_gloss"]:
        morphological_rows.append(["Spanish Sent Gloss:", data_dict["spa_sent_gloss"]])

    aligned = align_rows(morphological_rows)
    lines.extend(aligned)

    # blank line, then "# sentence level graph:"
    if data_dict["sentence_graph"]:
        lines.append("")
        lines.append("# sentence level graph:")
        lines.extend(data_dict["sentence_graph"])

    # blank line, then "# alignment:"
    if data_dict["alignment"]:
        lines.append("")
        lines.append("# alignment:")
        lines.extend(data_dict["alignment"])

    # blank line, then "# document level annotation:"
    if data_dict["doc_annotation"]:
        lines.append("")
        lines.append("# document level annotation:")
        lines.extend(data_dict["doc_annotation"])

    lines.append("")
    return lines

def reformat_file(input_path, output_path):
    """
    Read one file, split it into blocks (# :: sntN), parse each, reformat each,
    and write the new lines.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Split into blocks
    blocks = []
    current_block = []
    for line in lines:
        if line.strip().startswith("# :: snt"):
            # Start a new block
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)
    # Add last block
    if current_block:
        blocks.append(current_block)

    all_new_lines = []
    for blk in blocks:
        parsed = parse_block(blk)
        reformatted = reformat_block(parsed)
        all_new_lines.extend(reformatted)

    with open(output_path, "w", encoding="utf-8") as outf:
        for ln in all_new_lines:
            outf.write(ln + "\n")

def reformat_folder(input_folder, output_folder):
    """Process all .txt files in input_folder -> new folder with reformatted files."""
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
    input_dir = Path(root) / "umr_1_0/kukama/"
    output_dir = Path(root) / "umr_1_0_formatted/kukama/"
    reformat_folder(input_dir, output_dir)

