#!/usr/bin/env python3
import os
import re
import glob

def standardize_tree_indentation(lines):
    """
    Standardize indentation in tree structures (sentence level graph and document level annotation)
    to exactly match the format in the examples.
    """
    if not lines:
        return []
    
    result = []
    # Keep the header line as is
    if lines and lines[0].strip().startswith("#"):
        result.append(lines[0])
        lines = lines[1:]
    
    # Track node depth and indentation
    depth_stack = []  # Stack to track nested depth
    base_indent = 4   # Base indentation spaces for each level
    
    for line in lines:
        stripped = line.lstrip()
        if not stripped:  # Empty line
            result.append("")
            continue
            
        # Count opening and closing parentheses
        open_count = stripped.count("(")
        close_count = stripped.count(")")
        
        # Determine the indentation level
        if stripped.startswith("("):  # Node definition
            if "/" in stripped:  # This is a concept node
                if not depth_stack:  # Root node
                    indent = 0
                else:  # Non-root nodes
                    indent = len(depth_stack) * base_indent
                depth_stack.append(len(depth_stack))
            else:  # This is a continuation of a previous node
                indent = len(depth_stack) * base_indent if depth_stack else 0
        elif stripped.startswith(":"):  # Property
            # Properties are at the same level as their parent node
            indent = len(depth_stack) * base_indent if depth_stack else base_indent
            if "(" in stripped and "/" in stripped:  # Property introducing a new node
                depth_stack.append(len(depth_stack))
        else:  # Closing parentheses or other content
            indent = len(depth_stack) * base_indent if depth_stack else 0
        
        # Update depth stack based on closing parentheses
        for _ in range(close_count):
            if depth_stack:
                depth_stack.pop()
        
        # Apply indentation
        result.append(" " * indent + stripped)
    
    return result

def standardize_document_tree_indentation(lines):
    """
    Standardize indentation specifically for document-level trees to ensure
    consistent formatting with proper parent-child relationships.
    """
    if not lines:
        return []
    
    result = []
    # Keep the header line as is
    if lines and lines[0].strip().startswith("#"):
        result.append(lines[0])
        lines = lines[1:]
    
    # Track node depth and indentation
    depth_stack = []  # Stack to track nested depth
    base_indent = 4   # Base indentation spaces for each level
    
    # Process lines
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        
        if not stripped:  # Empty line
            result.append("")
            i += 1
            continue
        
        # Count opening and closing parentheses
        open_count = stripped.count("(")
        close_count = stripped.count(")")
        
        # Check if the next line is just closing parentheses
        next_line_is_just_closing = False
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line and all(c == ')' for c in next_line):
                next_line_is_just_closing = True
        
        # Determine the indentation level
        if stripped.startswith("("):  # Node definition
            if "/" in stripped:  # This is a concept node
                if not depth_stack:  # Root node
                    indent = 0
                else:  # Child nodes
                    indent = len(depth_stack) * base_indent
                depth_stack.append(len(depth_stack))
            else:  # This is a continuation of a previous node
                indent = len(depth_stack) * base_indent if depth_stack else 0
        elif stripped.startswith(":"):  # Property
            # Properties are indented 4 spaces from their parent node
            indent = len(depth_stack) * base_indent if depth_stack else base_indent
            # If this property introduces a new node with a concept
            if "(" in stripped and "/" in stripped:
                depth_stack.append(len(depth_stack))
        else:  # Other content including closing parentheses
            # If this line consists only of closing parentheses, it should be merged with the previous line
            if all(c == ')' for c in stripped) and result:
                result[-1] += stripped
                for _ in range(close_count):
                    if depth_stack:
                        depth_stack.pop()
                i += 1
                continue
            indent = len(depth_stack) * base_indent if depth_stack else 0
        
        # If the next line is just closing brackets, merge it with this line
        if next_line_is_just_closing:
            next_line = lines[i + 1].strip()
            stripped += next_line
            close_count += next_line.count(")")
            i += 1  # Skip the next line as we've merged it
        
        # Update depth stack based on closing parentheses
        for _ in range(close_count):
            if depth_stack:
                depth_stack.pop()
        
        # Apply indentation
        result.append(" " * indent + stripped)
        i += 1
    
    return result

def extract_variables_and_concepts(graph_text):
    """Extract variable names and their associated concepts from the graph text"""
    var_to_concept = {}
    var_pattern = r's\d+([a-zA-Z]\d*)'
    var_matches = re.finditer(r'\((s\d+[a-zA-Z]\d*)\s*/\s*([^\s\)]+)', graph_text)
    
    for match in var_matches:
        var = match.group(1)
        concept = match.group(2)
        var_to_concept[var] = concept
    
    return var_to_concept

def find_token_for_concept(concept, words):
    """Find the index of the token that best matches a concept"""
    # Simple exact match
    for i, word in enumerate(words, 1):  # 1-indexed
        if concept == word or concept in word:
            return i
    return 0  # Default to 0 if no match found

def generate_alignments_from_graph(graph_text, words, num_tokens):
    """Generate alignment entries based on variable names and concepts"""
    alignments = {}
    var_to_concept = extract_variables_and_concepts(graph_text)
    
    for var, concept in var_to_concept.items():
        token_idx = find_token_for_concept(concept, words)
        if token_idx > 0:
            alignments[var] = f"{token_idx}-{token_idx}"
        else:
            alignments[var] = "0-0"
    
    # For any variables in the graph not matched to concepts
    var_pattern = r's\d+[a-zA-Z]\d*'
    all_vars = set(re.findall(var_pattern, graph_text))
    
    for var in all_vars:
        if var not in alignments:
            alignments[var] = "0-0"
    
    return alignments

def create_document_level_annotation(sentence_id, graph_part):
    """Create a properly formatted document level annotation"""
    sentence_var = f"s{sentence_id}s0"
    
    # Determine if we need temporal or modal properties
    has_temporal = ":temporal" in graph_part
    has_modal = ":modal" in graph_part or ":ARG" in graph_part
    
    # Create the annotation
    doc_annotation = ["# document level annotation:"]
    
    if not has_temporal and not has_modal:
        # Simple case - no properties
        doc_annotation.append(f"({sentence_var} / sentence)")
    else:
        # Case with properties - add them on separate lines but put closing bracket at the end
        doc_annotation.append(f"({sentence_var} / sentence")
        
        # Add temporal property if needed
        if has_temporal:
            if has_modal:
                # If we have both, temporal doesn't get the closing bracket
                doc_annotation.append(f"    :temporal ((document-creation-time :before s{sentence_id}x))")
            else:
                # If we only have temporal, it gets the closing bracket
                doc_annotation.append(f"    :temporal ((document-creation-time :before s{sentence_id}x)))")
        
        # Add modal property if needed
        if has_modal:
            # Modal gets the closing bracket if it's the last property
            doc_annotation.append(f"    :modal ((root :modal author)))")
    
    return doc_annotation

def format_llm_parsed_file(input_file, output_file):
    """
    Format a file from the utils/llm_parsed directory to match the format of
    files in the chinese/formatted_data directory.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Split content by sections
    sections = content.split('# :: snt')
    
    with open(output_file, 'w', encoding='utf-8') as out:
        # Write header for the first section
        if len(sections) > 1:
            for i, section in enumerate(sections[1:], 1):  # Skip empty first split
                # Split the section into sentence and graph parts
                section_parts = section.split('# sentence level graph:')
                
                # Only process if we have valid content
                if len(section_parts) < 2:
                    continue
                
                sentence_part = section_parts[0].strip()
                graph_part = section_parts[1].strip() if len(section_parts) > 1 else ""
                
                # Extract sentence ID and text
                sentence_id = str(i)
                sentence_text = sentence_part
                
                # Write the separator
                out.write("################################################################################\n")
                
                # Write meta-info section
                out.write("# meta-info\n")
                out.write(f"# :: snt{sentence_id}\n")
                
                # Create an indexed version of the words in the sentence
                words = []
                if sentence_text:
                    # Remove any leading numbers that might be sentence IDs
                    cleaned_text = re.sub(r'^\d+\s+', '', sentence_text)
                    words = cleaned_text.split()
                    if words:
                        # Generate index line with proper spacing for the UMR format
                        index_parts = ["Index:"]
                        for i in range(len(words)):
                            # Make each index at least 5 characters wide with right alignment
                            index_parts.append(f"{i+1:5d}")
                        index_line = "".join(index_parts)
                        
                        # Add sentence text without sentence number
                        words_line = f"Words: {' '.join(words)}"
                        
                        out.write(f"{index_line}\n")
                        out.write(f"{words_line}\n\n")
                
                # Standardize indentation in the graph part
                graph_lines = ["# sentence level graph:"] + graph_part.split("\n")
                standardized_graph = standardize_tree_indentation(graph_lines)
                
                # Write sentence level graph with standardized indentation
                for line in standardized_graph:
                    out.write(line + "\n")
                out.write("\n")
                
                # Write alignment section with attempted word-concept mapping
                out.write("# alignment:\n")
                alignments = generate_alignments_from_graph(graph_part, words, len(words))
                for var in sorted(alignments.keys()):
                    out.write(f"{var}: {alignments[var]}\n")
                out.write("\n")
                
                # Generate and write document level annotation with improved standardized indentation
                doc_annotation = create_document_level_annotation(sentence_id, graph_part)
                standardized_doc = standardize_document_tree_indentation(doc_annotation)
                
                for line in standardized_doc:
                    out.write(line + "\n")
                out.write("\n\n")

def process_directory():
    """Process all files in the utils/llm_parsed directory."""
    input_dir = "utils/llm_parsed"
    output_dir = "utils/formatted_output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all .txt files in the input directory
    input_files = glob.glob(os.path.join(input_dir, "*.txt"))
    
    for input_file in input_files:
        # Get the base filename without extension
        base_name = os.path.basename(input_file)
        file_name_without_ext = os.path.splitext(base_name)[0]
        
        # Create output file path with .umr extension
        output_file = os.path.join(output_dir, f"{file_name_without_ext}.umr")
        
        print(f"Processing {input_file} -> {output_file}")
        format_llm_parsed_file(input_file, output_file)
        print(f"Completed formatting {file_name_without_ext}")

if __name__ == "__main__":
    process_directory()
    print("All files have been formatted successfully.")
