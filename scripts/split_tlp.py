# chinese/formatted_data/tlp_umr_wa_1120.umr has 1500 sentences in it, I need to split the sentences into 27 chapters.
# however, utils/tlp_umr_wa_seg_0224.txt has the information on how to split the sentences into 27 chapters.
# so, I need to use the information in utils/tlp_umr_wa_seg_0224.txt to split the sentences in chinese/formatted_data/tlp_umr_wa_1120.umr into 27 chapters.
# and save the result in utils/tlp/tlp_chapter\d.txt

import re
from pathlib import Path
import os

def get_chapter_sentence_mapping(input_file_path):
    """
    Parse the input file and return a dictionary mapping chapter numbers to their starting sentence numbers.
    
    Args:
        input_file_path: Path to the input file
        
    Returns:
        dict: A dictionary where keys are chapter numbers and values are starting sentence numbers
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If no chapters are found or if the file format is invalid
    """
    if not input_file_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
        
    chapter_mapping = {}
    current_chapter = None
    
    with open(input_file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Look for chapter number
            chapter_match = re.match(r"# Chapter (\d+)", line)
            if chapter_match:
                current_chapter = int(chapter_match.group(1))
                continue
            
            # Look for sentence number if we just found a chapter
            if current_chapter is not None:
                sent_match = re.match(r"# ::snt(\d+)", line)
                if sent_match:
                    sentence_num = int(sent_match.group(1))
                    chapter_mapping[current_chapter] = sentence_num
                    current_chapter = None  # Reset for next chapter
    
    if not chapter_mapping:
        raise ValueError("No chapters found in the input file")
        
    return chapter_mapping

def split_into_chapters(source_file_path, chapter_starts, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the entire file
    with open(source_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content into blocks at chapter boundaries
    blocks = content.split('################################################################################')
    
    # Sort chapter starts to ensure correct order
    sorted_chapter_starts = sorted(chapter_starts.items(), key=lambda x: int(x[0]))
    
    # Process each chapter
    for i, (chapter, start_sent) in enumerate(sorted_chapter_starts):
        # Get the ending sentence number (next chapter's start - 1, or None for last chapter)
        end_sent = int(sorted_chapter_starts[i + 1][1]) - 1 if i < len(sorted_chapter_starts) - 1 else None
        
        # Initialize chapter content with separator
        chapter_content = ['################################################################################']
        
        # Counter for sequential sentence numbering within the chapter
        sent_counter = 1
        
        # Collect blocks that belong to this chapter
        for block in blocks:
            if not block.strip():
                continue
            
            # Check if this block belongs to the current chapter
            match = re.search(r"# :: snt(\d+)", block)
            if match:
                sent_num = int(match.group(1))
                if sent_num >= int(start_sent) and (end_sent is None or sent_num <= end_sent):
                    # Split block into lines
                    lines = block.strip().split('\n')
                    
                    # Process the meta information line
                    meta_info_added = False
                    processed_lines = []
                    in_graph = False
                    in_alignment = False
                    in_doc_annotation = False
                    
                    for j, line in enumerate(lines):
                        # Track which section we're in
                        if "# sentence level graph:" in line:
                            in_graph = True
                            in_alignment = False
                            in_doc_annotation = False
                        elif "# alignment:" in line:
                            in_graph = False
                            in_alignment = True
                            in_doc_annotation = False
                        elif "# document level annotation:" in line:
                            in_graph = False
                            in_alignment = False
                            in_doc_annotation = True
                            
                        # Process meta-info line
                        if "# meta-info" in line:
                            if not meta_info_added:
                                processed_lines.append(f"{line.strip()} :: sent_id = {sent_num}")
                                meta_info_added = True
                            continue
                            
                        # Process sentence number line
                        if "# :: snt" in line:
                            processed_lines.append(f"# :: snt{sent_counter}")
                            continue
                            
                        # Process sentence level graph
                        if in_graph and line.strip():
                            # Replace sXXX with current sentence counter
                            line = re.sub(r's' + str(sent_num) + r'([a-zA-Z]\d*)', f's{sent_counter}\\1', line)
                            
                        # Process alignments
                        elif in_alignment and line.strip() and ':' in line:
                            # Update variable names in alignments
                            var, span = line.strip().split(':', 1)
                            if var.startswith('s' + str(sent_num)):
                                var = f's{sent_counter}' + var[len(str(sent_num))+1:]
                            line = f"{var}:{span}"
                            
                        # Process document level annotation
                        elif in_doc_annotation and line.strip():
                            # Replace sXXX with current sentence counter
                            line = re.sub(r's' + str(sent_num) + r'([a-zA-Z]\d*)', f's{sent_counter}\\1', line)
                            
                        processed_lines.append(line)
                    
                    # Add the processed lines
                    chapter_content.extend(processed_lines)
                    chapter_content.append('################################################################################')
                    sent_counter += 1
        
        # Write chapter to file
        output_file = os.path.join(output_dir, f'tlp_chapter{chapter}.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(chapter_content))

def main():
    try:
        # Set up paths
        root = Path(__file__).parent.parent
        seg_file = root / "utils" / "tlp_umr_wa_seg_0224.txt"
        formatted_file = root / "chinese" / "formatted_data" / "tlp_umr_wa_1120.umr"
        output_dir = root / "utils" / "tlp"

        # Get chapter-sentence mapping from the segmentation file
        chapter_mapping = get_chapter_sentence_mapping(seg_file)

        # Print the mapping for verification
        print("Chapter to Starting Sentence Mapping:")
        for chapter, sentence in sorted(chapter_mapping.items()):
            print(f"Chapter {chapter}: starts at sentence {sentence}")

        # Split the file into chapters
        split_into_chapters(formatted_file, chapter_mapping, output_dir)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
