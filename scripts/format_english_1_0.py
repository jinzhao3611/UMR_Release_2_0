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
                snt_line = line
                # parse out the tokens to the right
                # Format might be: "# :: snt2 该 周报 综合 ..."
                # We'll split on whitespace, ignoring the first two tokens: "#", "::", and "snt2" as well
                # But actually let's do a simpler approach:
                line_split = line.split(None, 2)  # up to 3 parts
                # e.g. ["#", "::", "snt2    该 周报 综合..."]
                if len(line_split) > 2:
                    # we want the 3rd part which might be "snt2 该 周报..."
                    third_part = line_split[2].strip()
                    # Now let's see if there's a tab or something
                    # Some users do: "# :: snt2\t该 周报", others do "# :: snt2 该 周报"
                    # We'll do a regex to separate the "snt2" from the rest:
                    match = re.match(r"(snt\d+)\s+(.*)", third_part)
                    if match:
                        snt_number = match.group(1)  # "snt2"
                        tokens_str = match.group(2)  # "该 周报 综合 ..."
                        sentence_tokens = tokens_str.split()
                    else:
                        # fallback if no match
                        # possibly there's a tab
                        if "\t" in third_part:
                            parts2 = third_part.split("\t", 1)
                            snt_number = parts2[0]
                            sentence_tokens = []
                            if len(parts2) > 1:
                                sentence_tokens = parts2[1].split()
                        else:
                            # no tokens found
                            snt_number = third_part
                            sentence_tokens = []
                else:
                    # no tokens
                    snt_number = ""
                    sentence_tokens = []

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
        # We'll guess a sent_id from the snt_number. For example, if snt_number="snt2"
        # we might produce "u_tree-cs-s2-root". Adjust as needed.
        # If no snt_number found, just do something generic
        if not snt_number:
            snt_number = "sntX"
        # Example: snt2 -> s2 => "u_tree-cs-s2-root"
        # We'll parse out the digits:
        digits_match = re.search(r"snt(\d+)", snt_number)
        if digits_match:
            short_id = digits_match.group(1)  # e.g. "2"
            full_sent_id = f"u_tree-cs-s{short_id}-root"
        else:
            full_sent_id = "u_tree-cs-sX-root"

        reformatted.append(f"# meta-info :: sent_id = {full_sent_id}")

        if snt_line:
            reformatted.append(snt_line)

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

        # Print alignment lines
        if alignment_lines:
            reformatted.append("")
            reformatted.append("# alignment:")
            reformatted.extend(alignment_lines)

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
    input_dir = Path(root) / "umr_1_0/english/original_data"
    output_dir = Path(root) / "umr_1_0/english/formatted_data"
    reformat_folder(input_dir, output_dir)
