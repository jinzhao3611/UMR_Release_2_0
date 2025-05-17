# UMR Parser Tool

This repository contains two Python tools for working with UMR (Uniform Meaning Representation) data:

1. `rename_umr_files.py` - Renames UMR files to follow a consistent naming convention
2. `parse_umr_to_json.py` - Parses UMR files into JSON format with filtering options

## UMR Parser Tool

The `parse_umr_to_json.py` script extracts content from UMR files and converts it to JSON format. It properly handles the block structure of UMR files, where:

- Files are divided into blocks (sentences) separated by 80 hash signs (`####...####`)
- Each block contains 5 parts separated by single hash signs (`#`):
  1. Meta info (with `::` separators)
  2. Sentence information (index, words, morphemes, etc.)
  3. Sentence level UMR annotation (after `# sentence level graph:`)
  4. Alignment information (after `# alignment:`) 
  5. Document level annotation (after `# document level annotation:`)

### Usage

```bash
python parse_umr_to_json.py [options]
```

### Options

- `--root-dir PATH` - Root directory containing language subdirectories (default: "ready_to_release")
- `--output PATH` - Output JSON file path (default: "umr_data.json")
- `--language LANG` - Filter by language (e.g., english, chinese)
- `--partial-conversion` - Only include files with type=partial_conversion in meta information
- `--no-partial-conversion` - Exclude files with type=partial_conversion in meta information
- `--has-document-annotation` - Only include files with document level annotation
- `--no-document-annotation` - Only include files without document level annotation
- `--pretty` - Output pretty-printed JSON

### Examples

1. Convert all UMR files to JSON:
   ```bash
   python parse_umr_to_json.py
   ```

2. Convert only English UMR files:
   ```bash
   python parse_umr_to_json.py --language english
   ```

3. Convert only files with document level annotation:
   ```bash
   python parse_umr_to_json.py --has-document-annotation
   ```

4. Convert only Czech files without partial conversion:
   ```bash
   python parse_umr_to_json.py --language czech --no-partial-conversion
   ```

### Output Format

The script outputs a JSON file containing an array of UMR documents. Each document has the following structure:

```json
{
  "filename": "english_umr-0001.umr",
  "language": "english",
  "blocks": [
    {
      "meta_info": {
        "sent_id": "u_tree-cs-s1-root",
        "snt1": ""
      },
      "sentence_info": {
        "Index": "1 2 3 4 5 6 7 8 9 10",
        "Words": "200 dead , 1,500 feared missing in Philippines landslide ."
      },
      "sentence_annotation": "(s1p / publication-91 :ARG1 (s1l / landslide-01...))",
      "alignment": "s1p: 0-0\ns1l: 9-9...",
      "document_annotation": "(s1s0 / sentence :temporal ((document-creation-time :before s1l)...))",
      "has_document_annotation": true
    },
    {
      // Additional blocks for other sentences in the file
    }
  ]
}
```

## UMR File Renaming Tool

The `rename_umr_files.py` script renames UMR files to follow the naming convention established in UMR 1.0 Release. See script comments for more details.

### Usage

```bash
python rename_umr_files.py
```

## Requirements

- Python 3.6+
- The UMR_Release_2_0 directory structure with language subdirectories 