import re
import penman
from penman.exceptions import DecodeError

# Choose the width you like (2 or 4 are common)
GRAPH_INDENT = 2

def reindent_graph(lines):
    """Return the same graph, pretty-printed with a fixed indent."""
    text = "\n".join(lines)
    try:
        g = penman.decode(text)               # parse
        return penman.encode(g, indent=GRAPH_INDENT).splitlines()
    except DecodeError as e:
        # fall back to original if the graph is malformed
        print(f"Warning: Could not parse graph, using original formatting. Error: {e}")
        return lines

def spaces_to_tabs(text):
    """
    Convert a space-indented string to use tabs instead.
    This is applied after penman has formatted the graph with consistent spacing.
    """
    lines = text.splitlines()
    result = []
    
    for line in lines:
        # Check if this is a header line
        if line.strip().startswith("#"):
            result.append(line)
            continue
            
        # Handle indentation
        stripped = line.lstrip()
        
        # Root node - no indentation
        if line.strip().startswith("(") and "/" in line and not ":" in line:
            result.append(line.strip())
            continue
            
        # Get indentation level based on leading spaces
        leading_spaces = len(line) - len(stripped)
        indent_level = leading_spaces // GRAPH_INDENT
        
        # Create the tab-indented line
        tabbed_line = "\t" * indent_level + stripped
        
        result.append(tabbed_line)
    
    return "\n".join(result)

def format_graph(graph_text):
    """
    Two-step formatting:
    1. Use penman to get consistent space-based indentation
    2. Convert spaces to tabs
    """
    # First split into sections
    lines = graph_text.splitlines()
    section_start = -1
    
    # Find where the graph section starts (after the header)
    for i, line in enumerate(lines):
        if line.strip() == "# sentence level graph:":
            section_start = i + 1
            break
    
    if section_start == -1 or section_start >= len(lines):
        # No graph section found or it's empty
        return graph_text
    
    # First, find where the graph ends (next section or end of text)
    section_end = len(lines)
    for i in range(section_start, len(lines)):
        if lines[i].strip().startswith("# "):
            section_end = i
            break
    
    # Extract the graph part (without the header)
    graph_part = lines[section_start:section_end]
    
    # Step 1: Reindent with penman for consistency
    formatted_graph = reindent_graph(graph_part)
    
    # Step 2: Convert spaces to tabs
    tabbed_graph = spaces_to_tabs("\n".join(formatted_graph))
    
    # Reconstruct the full text
    result = lines[:section_start]  # Everything before graph
    result.extend(tabbed_graph.splitlines())  # The formatted graph
    result.extend(lines[section_end:])  # Everything after graph
    
    return "\n".join(result)

def format_doc_annotation(annotation_text):
    """
    Format document level annotations with consistent tab indentation.
    
    Args:
        annotation_text (str): Document level annotation text with space indentation
        
    Returns:
        str: Document level annotation with tab indentation
    """
    lines = annotation_text.splitlines()
    result = []
    
    # Find the document level annotation section
    section_start = -1
    for i, line in enumerate(lines):
        if line.strip() == "# document level annotation:":
            section_start = i
            break
    
    if section_start == -1:
        # No document level annotation found
        return annotation_text
        
    # Add the header
    result.append(lines[section_start])
    
    # Process the annotation content
    content_lines = lines[section_start+1:]
    
    # Format each line
    for line in content_lines:
        stripped = line.strip()
        
        # Root node definition - no indentation
        if stripped.startswith("(") and "/" in stripped and not stripped.startswith(":"):
            result.append(stripped)
            continue
            
        # First level attribute
        if stripped.startswith(":temporal") or stripped.startswith(":modal") or stripped.startswith(":coref"):
            # Find how many open parentheses at the beginning of the content (for nested expressions)
            open_paren_count = stripped.count("(") - stripped.count(")")
            
            # First level indentation
            result.append("\t" + stripped)
            continue
            
        # Nested items in a list (like temporal relations)
        if stripped.startswith("(") and ":" in stripped:
            # This is a nested relation inside a list
            result.append("\t\t" + stripped)
            continue
            
        # Default case - maintain the nesting level based on parentheses balance
        leading_spaces = len(line) - len(stripped)
        indent_level = leading_spaces // 2  # Assuming 2 spaces per level
        result.append("\t" * indent_level + stripped)
    
    return "\n".join(result)

def format_alignment(alignment_text):
    """
    Format alignment section to have space after the colon, not before.
    Changes "s3s :0-0" to "s3s: 0-0"
    
    Args:
        alignment_text (str): The alignment section text
        
    Returns:
        str: Properly formatted alignment section
    """
    lines = alignment_text.splitlines()
    result = []
    
    # Keep the header line as is
    if lines and lines[0].strip() == "# alignment:":
        result.append(lines[0])
        lines = lines[1:]
        
    # Process each alignment line
    for line in lines:
        # Skip empty lines
        if not line.strip():
            result.append(line)
            continue
            
        # Match the pattern "variable :coordinates"
        if " :" in line:
            # Replace space before colon with no space, and ensure space after colon
            parts = line.split(" :")
            if len(parts) == 2:
                var = parts[0].strip()
                coords = parts[1].strip()
                result.append(f"{var}: {coords}")
                continue
                
        # If it doesn't match the pattern, keep as is
        result.append(line)
        
    return "\n".join(result)

# Unit test for format_doc_annotation
def test_format_doc_annotation():
    # Input with space indentation
    input_text = """# document level annotation:
(s3s0 / sentence
  :temporal ((s3t :overlap s3w)
                    (s3w :overlap s3y)
                    (s2m :contained s3t))
  :modal ((root :modal author)
                    (author :full-affirmative s3y)
                    (author :full-affirmative s3w)
                    (author :full-affirmative s3t))
  :coref ((s2m :subset-of s3t)
                    (s2k :same-entity s3p)
                    (s2p :same-entity s3p2)))"""
    
    # Expected output with tab indentation
    expected_tab_indented = """# document level annotation:
(s3s0 / sentence
	:temporal ((s3t :overlap s3w)
		(s3w :overlap s3y)
		(s2m :contained s3t))
	:modal ((root :modal author)
		(author :full-affirmative s3y)
		(author :full-affirmative s3w)
		(author :full-affirmative s3t))
	:coref ((s2m :subset-of s3t)
		(s2k :same-entity s3p)
		(s2p :same-entity s3p2)))"""
    
    # Format the document annotation
    formatted = format_doc_annotation(input_text)
    
    # Print results for inspection
    print("ORIGINAL DOC ANNOTATION:\n" + input_text)
    print("\nFORMATTED DOC ANNOTATION:\n" + formatted)
    print("\nEXPECTED DOC ANNOTATION:\n" + expected_tab_indented)
    
    # Check if formatted matches expected exactly
    assert formatted == expected_tab_indented, "Formatted output doesn't match expected tab-indented format"
    
    print("Test passed! Document annotation formatted correctly with tabs.")

# Unit test for format_graph
def test_format_graph():
    # Input with space indentation
    input_text = """# sentence level graph:
(s3t / tsapuki
  :actor (s3p / person
           :refer-person 3rd
           :refer-number plural
           :mod (s3t2 / tua))
  :recipient (s3p2 / person
               :refer-person 3rd
               :actor-of (s3y / yuti
                           :place (s3u / ukaka)
                           :aspect state))
  :place (s3p3 / peka)
  :source s3p3
  :aspect perfective
  :temporal (s3w / wɨwɨta
              :aspect activity))"""
    
    # Expected output with tab indentation
    expected_tab_indented = """# sentence level graph:
(s3t / tsapuki
	:actor (s3p / person
		:refer-person 3rd
		:refer-number plural
		:mod (s3t2 / tua))
	:recipient (s3p2 / person
		:refer-person 3rd
		:actor-of (s3y / yuti
			:place (s3u / ukaka)
			:aspect state))
	:place (s3p3 / peka)
	:source s3p3
	:aspect perfective
	:temporal (s3w / wɨwɨta
		:aspect activity))"""
    
    # Format the graph
    formatted = format_graph(input_text)
    
    # Print results for inspection
    print("ORIGINAL:\n" + input_text)
    print("\nFORMATTED:\n" + formatted)
    print("\nEXPECTED:\n" + expected_tab_indented)
    
    # Check if formatted matches expected exactly
    assert formatted == expected_tab_indented, "Formatted output doesn't match expected tab-indented format"
    
    print("Test passed! Formatted output exactly matches expected tab-indented format.")

# Unit test for format_alignment
def test_format_alignment():
    # Input with space before colon
    input_text = """# alignment:
s3s :0-0
s3u :3-3
s3y :1-1
s3p :empty

s3x :5-5"""
    
    # Expected output with space after colon
    expected_output = """# alignment:
s3s: 0-0
s3u: 3-3
s3y: 1-1
s3p: empty

s3x: 5-5"""
    
    # Format the alignment section
    formatted = format_alignment(input_text)
    
    # Print results for inspection
    print("ORIGINAL ALIGNMENT:\n" + input_text)
    print("\nFORMATTED ALIGNMENT:\n" + formatted)
    print("\nEXPECTED ALIGNMENT:\n" + expected_output)
    
    # Check if formatted matches expected exactly
    assert formatted == expected_output, "Formatted alignment doesn't match expected format"
    
    print("Test passed! Alignment formatted correctly with space after colon.")

if __name__ == "__main__":
    test_format_graph()
    print("\n----- Testing Document Annotation Formatting -----\n")
    test_format_doc_annotation()
    print("\n----- Testing Alignment Formatting -----\n")
    test_format_alignment() 