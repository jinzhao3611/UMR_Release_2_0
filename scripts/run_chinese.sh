#!/bin/bash

# Set the input directory containing the files to process
INPUT_DIR="../chinese/formatted_data"
# Set the output directory where errors will be stored
OUTPUT_DIR="../chinese/errors"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

# Iterate through all files in the input directory
for input_file in "$INPUT_DIR"/*; do
    # Extract the base name of the file (e.g., Document_Level_Graphs_2.txt)
    base_name=$(basename "$input_file")

    # Construct the output file path
    output_file="$OUTPUT_DIR/$base_name"

    # Run the Python script and redirect both stdout and stderr to the file
    echo "Processing $input_file -> $output_file"
    python validate.py "$input_file" > "$output_file" 2>&1
done

echo "All files processed."
