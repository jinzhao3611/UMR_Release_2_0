#!/usr/bin/env python3
import os
import re
import glob
from pathlib import Path
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
    in_property_list = False  # Track if we're inside a property list
    property_first_item = False  # Track if this is the first item in a property list
    
    # First, combine property with its first list item if they're on separate lines
    i = 0
    combined_lines = []
    while i < len(lines):
        line = lines[i].strip()
        
        # If this line starts a property with a list
        if line.startswith(":") and "(" in line and line.endswith("("):
            # Check if next line is a list item
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("("):
                # Combine property with first list item
                combined_lines.append(line + lines[i + 1].strip())
                i += 2
                continue
        
        combined_lines.append(line)
        i += 1
    
    # Now process the combined lines
    i = 0
    while i < len(combined_lines):
        line = combined_lines[i]
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
        if i < len(combined_lines) - 1:
            next_line = combined_lines[i + 1].strip()
            if next_line and all(c == ')' for c in next_line):
                next_line_is_just_closing = True
        
        # Check if this is a property line with a list
        is_property_with_list = False
        if stripped.startswith(":") and "(" in stripped:
            property_open_parens = stripped.count("(")
            # If a property contains an opening bracket for a list
            if property_open_parens >= 2 or (property_open_parens == 1 and ":" in stripped[stripped.find("("):]):
                is_property_with_list = True
                in_property_list = True
                property_first_item = True
        
        # Determine the indentation level
        if stripped.startswith("("):  # Node definition
            if "/" in stripped:  # This is a concept node
                if not depth_stack:  # Root node
                    indent = 0
                else:  # Child nodes
                    indent = len(depth_stack) * base_indent
                depth_stack.append(len(depth_stack))
                in_property_list = False
                property_first_item = False
            elif in_property_list and not property_first_item and ":" in stripped:  # This is a property list item after the first one
                # Additional items in property list are indented 8 spaces (4 more than property)
                indent = (len(depth_stack) - 1) * base_indent + base_indent * 2
            else:  # This is a continuation of a previous node
                indent = len(depth_stack) * base_indent if depth_stack else 0
                property_first_item = False
        elif stripped.startswith(":"):  # Property
            # Properties are indented 4 spaces from their parent node
            indent = len(depth_stack) * base_indent if depth_stack else base_indent
            
            # If this is not a property with a list, reset list tracking
            if not is_property_with_list:
                in_property_list = False
                property_first_item = False
            
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
            in_property_list = False
            property_first_item = False
        
        # If the next line is just closing brackets, merge it with this line
        if next_line_is_just_closing:
            next_line = combined_lines[i + 1].strip()
            stripped += next_line
            close_count += next_line.count(")")
            i += 1  # Skip the next line as we've merged it
        
        # Apply indentation
        result.append(" " * indent + stripped)
        
        # Update tracking for next iteration
        if in_property_list and property_first_item:
            property_first_item = False
        
        # Update depth stack based on closing parentheses
        for _ in range(close_count):
            if depth_stack:
                depth_stack.pop()
        
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
        
        # Track the root node and its direct children (properties)
        root_node = None
        properties = {}
        current_prop = None
        content_by_prop = {}
        
        # First pass: collect all properties and their content
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("(") and "/" in line:
                # This is the root node
                root_node = line
            elif line.startswith(":"):
                # This is a property
                parts = line.split(None, 1)
                current_prop = parts[0]  # Get the property name
                properties[current_prop] = []
                
                # If there's a content part on this line
                if len(parts) > 1 and parts[1].strip():
                    content = parts[1].strip()
                    properties[current_prop].append(content)
            elif current_prop:
                # This line continues the current property
                properties[current_prop].append(line)
        
        # Add the root node
        if root_node:
            doc_annotation.append(root_node)
            
            # Add each property with the desired formatting
            for prop, content_list in properties.items():
                if not content_list:
                    continue
                    
                # For the first content item, keep it on the same line as the property
                first_item = content_list[0]
                doc_annotation.append(f"    {prop} {first_item}")
                
                # For subsequent items, indent by 8 spaces
                for item in content_list[1:]:
                    doc_annotation.append(f"        {item}")
    else:
        # Otherwise create a simple placeholder with the closing bracket on the same line
        sentence_var = f"s{sentence_id}s0"
        doc_annotation.append(f"({sentence_var} / sentence)")
    
    # No need to apply standardize_document_tree_indentation since we're manually constructing
    # the document annotation with the exact desired formatting
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
            
            # Write document level annotation
            out.write("# document level annotation:\n")
            
            # Custom formatting for document level annotation
            if doc_annotation_part and doc_annotation_part.strip():
                lines = doc_annotation_part.strip().split('\n')
                
                current_indentation = 0
                current_property = None
                first_item_in_list = False
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    if not stripped:
                        continue
                    
                    # Handle root node (no indentation)
                    if stripped.startswith("(") and "/" in stripped:
                        out.write(f"{stripped}\n")
                        current_indentation = 4  # Set indentation for properties
                    
                    # Handle properties (indent 4 spaces)
                    elif stripped.startswith(":"):
                        current_property = stripped.split()[0]
                        
                        # Check if this property has list content on the same line
                        if "(" in stripped:
                            # Get the content part
                            content_start = stripped.find("(")
                            property_part = stripped[:content_start].strip()
                            content_part = stripped[content_start:].strip()
                            
                            # Write property with first list item on the same line
                            out.write(f"{' ' * current_indentation}{property_part} {content_part}\n")
                            first_item_in_list = True
                        else:
                            # Property without content on the same line
                            out.write(f"{' ' * current_indentation}{stripped}\n")
                            first_item_in_list = False
                    
                    # Handle list items after a property (indent 8 spaces if not the first item)
                    elif current_property and stripped.startswith("(") and ":" in stripped:
                        if first_item_in_list:
                            # This is a second or later item in a list
                            out.write(f"{' ' * 8}{stripped}\n")
                        else:
                            # This is the first list item
                            out.write(f"{' ' * current_indentation}{current_property} {stripped}\n")
                            first_item_in_list = True
                    
                    # Handle other content or closing brackets
                    else:
                        # If it's a closing bracket for the root node, no indentation
                        if stripped == ")" and i == len(lines) - 1:
                            out.write(f"{stripped}\n")
                        else:
                            # Use 8 spaces for subsequent list items
                            indentation = 8 if first_item_in_list else current_indentation
                            out.write(f"{' ' * indentation}{stripped}\n")
            else:
                # Simple placeholder
                sentence_var = f"s{sentence_id}s0"
                out.write(f"({sentence_var} / sentence)\n")
            
            out.write("\n\n")

def process_directory():
    """Process all files in the utils/checkedout directory."""
    current_script_dir = Path(__file__).parent
    root = current_script_dir.parent
    input_dir = Path(root) / "exported_writer_2_0/original_data"
    output_dir = Path(root) / "exported_writer_2_0/formatted_data"
    
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