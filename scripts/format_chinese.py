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
    using tabulate for alignment, with proper handling of Chinese character widths.
    """
    try:
        import wcwidth
    except ImportError:
        import os
        os.system('pip install wcwidth')
        import wcwidth

    # Calculate display widths for each word
    word_widths = [sum(wcwidth.wcwidth(c) for c in word) for word in words]
    
    # Create the index numbers with proper spacing
    indices = [str(i + 1) for i in range(len(words))]
    index_widths = [len(idx) for idx in indices]
    
    # Calculate the width needed for each column
    column_widths = [max(iw, ww) for iw, ww in zip(index_widths, word_widths)]
    
    # Create the lines with proper spacing
    index_line = "Index:" + "".join(f" {idx:>{width}}" for idx, width in zip(indices, column_widths))
    words_line = "Words:" + "".join(f" {word:<{width}}" for word, width in zip(words, column_widths))

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

def parse_alignment_span(span_str):
    """
    Parse an alignment span string (e.g., "1-1", "0-0", "-1--1", "1-2, 5-6") into a list of tuples.
    Returns list of (start, end) tuples or None if invalid format.
    """
    try:
        # Handle special cases first
        if span_str == "-1--1":
            return [(-1, -1)]
        if span_str == "0-0":
            return [(0, 0)]
        
        # Handle invalid formats
        if "undefined" in span_str.lower():
            print(f"Warning: Found 'undefined' in alignment span: {span_str}")
            return None
        
        # Split multiple spans if they exist
        spans = [s.strip() for s in span_str.split(",")]
        result = []
        
        for span in spans:
            if "-" not in span:
                print(f"Warning: Invalid span format (missing hyphen): {span}")
                continue
            try:
                start, end = map(int, span.split("-"))
                result.append((start, end))
            except ValueError:
                print(f"Warning: Invalid numbers in span: {span}")
                continue
            
        return result if result else None
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid alignment span format: {span_str} ({str(e)})")
        return None

def validate_alignment_span(span_str, max_token_idx):
    """
    Validate that an alignment span is well-formed and within bounds.
    Args:
        span_str: The span string to validate (e.g., "1-1" or "1-2, 5-6")
        max_token_idx: The maximum valid token index (length of sentence)
    Returns:
        bool: True if valid, False otherwise
    """
    spans = parse_alignment_span(span_str)
    if spans is None:
        return False
        
    # Special cases with single span
    if len(spans) == 1:
        start, end = spans[0]
        if (start, end) == (-1, -1) or (start, end) == (0, 0):
            return True
    
    # For all spans (including multiple spans):
    for start, end in spans:
        # Each span must satisfy:
        # 1. start <= end
        # 2. start >= 1 (1-based indexing)
        # 3. end <= max_token_idx
        if not (start <= end and start >= 1 and end <= max_token_idx):
            return False
            
        # For multiple spans, also check they don't overlap
        for other_start, other_end in spans:
            if (start, end) != (other_start, other_end):  # Don't compare span with itself
                # Check for overlap
                if not (end < other_start or start > other_end):
                    print(f"Warning: Overlapping spans in alignment: {span_str}")
                    return False
    
    return True

def process_alignment(var, span_str, max_token_idx):
    """
    Process and validate an alignment entry.
    Returns (var, span_str) tuple if valid, None otherwise.
    """
    var = var.strip()
    span_str = span_str.strip()
    
    if not var:
        print(f"Warning: Empty variable name in alignment")
        return None
        
    if not validate_alignment_span(span_str, max_token_idx):
        print(f"Warning: Invalid alignment span {span_str} for variable {var}")
        return None
        
    return (var, span_str)

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
            elif line.startswith("# :: snt") or line.startswith("# ::snt"):
                sent_level_annot = False
                alignment_annot = False
                doc_level_annot = False
                if current_annotation:
                    parsed_data["annotations"].append(current_annotation)
                # Try both formats
                match = re.search(r"# ::(?: )?snt(\d+)(?:Sentence:)?", line)
                sentence_id = None
                if match:
                    sentence_id = int(match.group(1))
                else:
                    print("ERROR: there is no sentence_id extracted. ")
                if "\t" not in line: #lin bin's file
                    line = re.sub(r"(# ::(?: )?snt\d+(?:Sentence:)?)\s+", r"\1\t", line)
                current_annotation = {
                    "meta_info": "",
                    "sentence_id": sentence_id,
                    "sentence": line.split("\t", 1)[1] if "\t" in line else line.split("Sentence:", 1)[1] if "Sentence:" in line else "",
                    "index":"",
                    "words": line.split("\t", 1)[1].split() if "\t" in line else line.split("Sentence:", 1)[1].split() if "Sentence:" in line else [],
                    "sentence_level_graph": "",
                    "alignments": {},  # Initialize as empty dictionary instead of empty string
                    "document_level_annotation": "",
                }
            elif current_annotation and line.startswith("# sentence level graph:"):
                sent_level_annot = True
                alignment_annot = False
                doc_level_annot = False
                current_annotation["sentence_level_graph"] = ""
            elif current_annotation and line.startswith("# alignment:"):
                sent_level_annot = False
                alignment_annot = True
                doc_level_annot = False
                # Parse the first alignment on this line after "# alignment:"
                parts = line.split(":", 2)
                if len(parts) > 2 and ":" in parts[2]:  # Make sure we have enough parts and there's an alignment
                    first_alignment = parts[2].strip()
                    var, span = first_alignment.split(":", 1)
                    max_tokens = len(current_annotation["words"])
                    alignment_entry = process_alignment(var, span, max_tokens)
                    if alignment_entry:
                        current_annotation["alignments"][alignment_entry[0]] = alignment_entry[1]
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
                        # Parse subsequent alignment lines
                        if ":" in line:  # Make sure it's a valid alignment line
                            var, span = line.strip().split(":", 1)
                            max_tokens = len(current_annotation["words"])
                            alignment_entry = process_alignment(var, span, max_tokens)
                            if alignment_entry:
                                current_annotation["alignments"][alignment_entry[0]] = alignment_entry[1]
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

    # After reading the file, before saving to JSON, generate and merge alignments
    for annot in parsed_data["annotations"]:
        sent_level_graph = annot["sentence_level_graph"]
        doc_level_graph = annot["document_level_annotation"]
        
        # Generate new alignments from the graph
        num_tokens = len(annot["words"])
        words = annot["words"]
        generated_alignments = generate_alignments_from_graph(sent_level_graph, words, num_tokens)
        
        # Replace all alignments with generated ones
        annot["alignments"] = generated_alignments
        
        # Process modal triples as before
        if doc_level_graph.strip() and not "ROOT" in doc_level_graph:
            doc_level_graph = add_modal_triple(doc_level_graph, "(ROOT :modal AUTH)")
        try:
            g = penman.decode(sent_level_graph)
            triples = g.triples
            for triple in triples:
                if triple[1] == ":MODSTR" or triple[1] == ":modal-strength":
                    if doc_level_graph.strip():
                        doc_level_graph = add_modal_triple(doc_level_graph, f"(AUTH :{triple[2]} {triple[0]})")
            # Filter out any triple whose relation is ':MODSTR'
            filtered_triples = [t for t in triples if t[1] != ':MODSTR' and t[1] != ":modal-strength"]

            # Build a new Graph with the filtered triples
            new_graph = penman.Graph(filtered_triples, epidata=g.epidata)

            # Encode back to AMR-like text
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
            alignments = entry.get("alignments", {})
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
                if alignments:
                    # Sort alignments by variable name for consistent output
                    for var in sorted(alignments.keys()):
                        out_file.write(f"{var}: {alignments[var]}\n")
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Chinese UMR files')
    parser.add_argument('--step', type=str, choices=['txt2json', 'json2txt', 'both'], 
                      default='both', help='Which step to run: txt2json (convert txt to json), json2txt (convert json to formatted txt), or both')
    
    args = parser.parse_args()
    
    if args.step in ['txt2json', 'both']:
        print("Step 1: Converting txt files to json...")
        folder_umr_writer_txt2json()
    
    if args.step in ['json2txt', 'both']:
        print("Step 2: Converting json files to formatted txt...")
        batch_json2txt(Path(root) / 'chinese/jsons', Path(root) / 'chinese/formatted_data')
    
    print("Done!")
