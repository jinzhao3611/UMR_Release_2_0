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

def process_alignments(alignment_text):
    """
    Process alignment text from the format 's1a: 0-0\ns1b: 0-0' to a dictionary
    """
    alignments = {}
    if not alignment_text:
        return alignments
    
    # Split by newlines or by "s" for formats that don't have newlines
    lines = re.split(r'\n|(?=s\d+[a-zA-Z])', alignment_text.strip())
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse 's1a: 0-0' format
        match = re.match(r'(s\d+[a-zA-Z]\d*):?\s+(\S+)', line)
        if match:
            var = match.group(1)
            alignment = match.group(2)
            alignments[var] = alignment
    
    return alignments

def create_document_level_annotation(sentence_id, doc_annotation_part):
    """Create a properly formatted document level annotation"""
    # Start with the header
    doc_annotation = ["# document level annotation:"]
    
    # If there's existing doc annotation content, process it
    if doc_annotation_part and doc_annotation_part.strip():
        lines = doc_annotation_part.strip().split('\n')
        
        # Process the lines to make sure closing brackets don't end up on their own line
        processed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if the next line is just closing parentheses
            if i < len(lines) - 1 and all(c == ')' for c in lines[i+1].strip()):
                processed_lines.append(line + lines[i+1].strip())
                i += 2  # Skip the next line
            else:
                processed_lines.append(line)
                i += 1
        
        # Add the processed lines to the annotation
        doc_annotation.extend(processed_lines)
    else:
        # Otherwise create a simple placeholder with the closing bracket on the same line
        sentence_var = f"s{sentence_id}s0"
        doc_annotation.append(f"({sentence_var} / sentence)")
    
    return doc_annotation

def format_checkedout_file(input_file, output_file):
    """
    Format a file from the utils/checkedout directory to match the format of
    files in the chinese/formatted_data directory.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the file into sections based on '# :: snt'
    header_match = re.search(r'(.*?)# :: snt', content, re.DOTALL)
    header = header_match.group(1) if header_match else ""
    
    # Find the index of "Source File" section
    source_file_index = content.find("# Source File:")
    if source_file_index != -1:
        content = content[:source_file_index]
    
    # Split content by sections
    sections = re.split(r'# :: snt', content)
    sections = [s for s in sections if s.strip() and "# sentence level graph:" in s]
    
    with open(output_file, 'w', encoding='utf-8') as out:
        for i, section in enumerate(sections, 1):
            # Extract sentence ID and text
            sentence_id_match = re.match(r'(\d+)\s+(.+?)\n', section)
            sentence_id = sentence_id_match.group(1) if sentence_id_match else str(i)
            sentence_text = sentence_id_match.group(2) if sentence_id_match else ""
            
            # Split into sections
            parts = re.split(r'# (sentence level graph:|alignment:|document level annotation:)', section)
            if len(parts) < 4:
                continue
            
            graph_part = parts[2].strip() if len(parts) > 2 else ""
            alignment_part = parts[4].strip() if len(parts) > 4 else ""
            doc_annotation_part = parts[6].strip() if len(parts) > 6 else ""
            
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
                    
                    # Add the words line
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
            
            # Process and write alignment section
            out.write("# alignment:\n")
            alignments = process_alignments(alignment_part)
            for var in sorted(alignments.keys()):
                out.write(f"{var}: {alignments[var]}\n")
            out.write("\n")
            
            # Generate and write document level annotation with improved indentation
            doc_annotation = create_document_level_annotation(sentence_id, doc_annotation_part)
            standardized_doc = standardize_document_tree_indentation(doc_annotation)
            
            for line in standardized_doc:
                out.write(line + "\n")
            out.write("\n\n")

def process_directory():
    """Process all files in the utils/checkedout directory."""
    input_dir = "utils/checkedout"
    output_dir = "utils/formatted_checkedout"
    
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
        format_checkedout_file(input_file, output_file)
        print(f"Completed formatting {file_name_without_ext}")

if __name__ == "__main__":
    process_directory()
    print("All files have been formatted successfully.") 