#!/usr/bin/env python3
import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

def parse_umr_file(file_path: str) -> Dict[str, Any]:
    """Parse a UMR file into a dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    language = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
    filename = os.path.basename(file_path)
    
    # Split the file into blocks separated by 80 hash signs
    blocks = re.split(r'#{80,}', content)
    blocks = [block.strip() for block in blocks if block.strip()]
    
    parsed_blocks = []
    for block in blocks:
        # Split each block into parts
        parts = block.split('#')
        parts = [part.strip() for part in parts if part.strip()]
        
        if len(parts) < 3:  # Need at least meta, sentence, and one annotation
            continue
        
        block_data = {}
        
        # Parse meta info
        meta_part = parts[0]
        block_data["meta_info"] = parse_meta_info(meta_part)
        
        # Parse sentence information
        sentence_part = parts[1]
        block_data["sentence_info"] = parse_sentence_info(sentence_part)
        
        # Find and parse sentence level graph
        sentence_graph = None
        for part in parts:
            if part.startswith('sentence level graph:'):
                sentence_graph = part.replace('sentence level graph:', '').strip()
                break
        block_data["sentence_annotation"] = sentence_graph
        
        # Find and parse alignment
        alignment = None
        for part in parts:
            if part.startswith('alignment:'):
                alignment = part.replace('alignment:', '').strip()
                break
        block_data["alignment"] = alignment
        
        # Find and parse document level annotation
        doc_annotation = None
        for part in parts:
            if part.startswith('document level annotation:'):
                doc_annotation = part.replace('document level annotation:', '').strip()
                # Check if it's empty or just contains (sXsX / sentence)
                if doc_annotation and not re.match(r'^\s*\(\w+\s*/\s*sentence\)\s*$', doc_annotation):
                    block_data["has_document_annotation"] = True
                else:
                    block_data["has_document_annotation"] = False
                break
        block_data["document_annotation"] = doc_annotation
        
        parsed_blocks.append(block_data)
    
    result = {
        "filename": filename,
        "language": language,
        "blocks": parsed_blocks
    }
    
    return result

def parse_meta_info(meta_part: str) -> str:
    """Parse meta information from UMR file content."""
    # Return the meta part as a string instead of a dictionary
    return meta_part.strip()

def parse_sentence_info(sentence_part: str) -> Dict[str, str]:
    """Parse sentence information."""
    info = {}
    
    lines = sentence_part.split('\n')
    current_key = None
    
    for line in lines:
        if ':' in line and not line.strip().startswith('#'):
            parts = line.split(':', 1)
            current_key = parts[0].strip()
            value = parts[1].strip()
            # Skip empty key and Index key
            if current_key == "" or current_key == "Index":
                continue
            info[current_key] = value
        elif current_key and line.strip() and not line.strip().startswith('#') and current_key != "" and current_key != "Index":
            info[current_key] += ' ' + line.strip()
    
    return info

def has_document_level_annotation(document_annotation: str) -> bool:
    """Check if the document has meaningful document level annotation."""
    if not document_annotation:
        return False
    
    # If it's just (sXsX / sentence), consider it empty
    if re.match(r'^\s*\(\w+\s*/\s*sentence\)\s*$', document_annotation):
        return False
    
    return True

def find_umr_files(root_dir: str) -> List[str]:
    """Find all UMR files in the directory structure."""
    umr_files = []
    
    for lang_dir in os.listdir(root_dir):
        lang_path = os.path.join(root_dir, lang_dir)
        if not os.path.isdir(lang_path):
            continue
        
        # Check both umr_data and formatted_data directories
        for data_dir in ['umr_data', 'formatted_data']:
            dir_path = os.path.join(lang_path, data_dir)
            if not os.path.exists(dir_path):
                continue
                
            for filename in os.listdir(dir_path):
                if filename.endswith(".umr"):
                    umr_files.append(os.path.join(dir_path, filename))
                
    return umr_files

def filter_files(parsed_files: List[Dict[str, Any]], 
                 language: Optional[str] = None,
                 has_partial_conversion: Optional[bool] = None,
                 has_document_annotation: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Filter parsed files based on criteria."""
    filtered_files = parsed_files.copy()
    
    if language:
        filtered_files = [f for f in filtered_files if f["language"] == language]
    
    if has_partial_conversion is not None:
        temp_files = []
        for file in filtered_files:
            has_partial = False
            for block in file.get("blocks", []):
                # Check if any block in the file has partial_conversion
                meta_info = block.get("meta_info", "")
                if "type = partial_conversion" in meta_info:
                    has_partial = True
                    break
            
            # Include file based on whether it should have partial conversion or not
            if has_partial == has_partial_conversion:
                temp_files.append(file)
            
        filtered_files = temp_files
    
    if has_document_annotation is not None:
        temp_files = []
        for file in filtered_files:
            include_file = False
            for block in file.get("blocks", []):
                if block.get("has_document_annotation", False) == has_document_annotation:
                    include_file = True
                    break
            if include_file:
                temp_files.append(file)
        filtered_files = temp_files
    
    return filtered_files

def main():
    parser = argparse.ArgumentParser(description='Parse UMR files to JSON with filtering options')
    parser.add_argument('--root-dir', type=str, default='.',
                        help='Root directory containing language subdirectories (default: current directory)')
    parser.add_argument('--output', type=str, default='umr_data.json',
                        help='Output JSON file path (default: umr_data.json in current directory)')
    parser.add_argument('--language', type=str,
                        help='Filter by language (e.g., english, chinese)')
    parser.add_argument('--partial-conversion', action='store_true',
                        help='Only include files with type=partial_conversion')
    parser.add_argument('--no-partial-conversion', action='store_true',
                        help='Exclude files with type=partial_conversion')
    parser.add_argument('--has-document-annotation', action='store_true',
                        help='Only include files with document level annotation')
    parser.add_argument('--no-document-annotation', action='store_true',
                        help='Only include files without document level annotation')
    parser.add_argument('--pretty', action='store_true',
                        help='Output pretty-printed JSON')
    
    args = parser.parse_args()
    
    # Validate conflicting arguments
    if args.partial_conversion and args.no_partial_conversion:
        parser.error("--partial-conversion and --no-partial-conversion cannot be used together")
    
    if args.has_document_annotation and args.no_document_annotation:
        parser.error("--has-document-annotation and --no-document-annotation cannot be used together")
    
    # Find and parse all UMR files
    root_dir = os.path.abspath(args.root_dir)
    print(f"Looking for UMR files in {root_dir}...")
    
    umr_files = find_umr_files(root_dir)
    print(f"Found {len(umr_files)} UMR files")
    
    parsed_files = []
    for file_path in umr_files:
        try:
            parsed = parse_umr_file(file_path)
            parsed_files.append(parsed)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    # Apply filters
    has_partial_conversion = None
    if args.partial_conversion:
        has_partial_conversion = True
    elif args.no_partial_conversion:
        has_partial_conversion = False
    
    has_document_annotation = None
    if args.has_document_annotation:
        has_document_annotation = True
    elif args.no_document_annotation:
        has_document_annotation = False
    
    filtered_files = filter_files(
        parsed_files,
        language=args.language,
        has_partial_conversion=has_partial_conversion,
        has_document_annotation=has_document_annotation
    )
    
    print(f"After filtering: {len(filtered_files)} files")
    
    # Create directories if they don't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        if args.pretty:
            json.dump(filtered_files, f, indent=2)
        else:
            json.dump(filtered_files, f)
    
    print(f"Output written to {args.output}")

if __name__ == "__main__":
    main() 