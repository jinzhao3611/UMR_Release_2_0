# UMR 2.0 Data Release

## Table of Contents
- [UMR 2.0 Data Release](#umr-20-data-release)
  - [UMR 2.0 Data Parser Tool](#umr-20-data-parser-tool)
    - [Usage](#usage)
    - [Options](#options)
    - [Examples](#examples)
    - [Output Format](#output-format)
  - [UMR 2.0 Data format Description](#umr-20-data-format-description)
    - [Block Structure](#block-structure)
    - [Meta Information](#1-meta-information)
    - [Sentence Information](#2-sentence-information)
    - [Sentence-Level UMR Annotation](#3-sentence-level-umr-annotation)
    - [Alignment Information](#4-alignment-information)
    - [Document-Level Annotation](#5-document-level-annotation)
    - [Language Coverage](#language-coverage)
  - [Statistics Tables Description](#statistics)

## UMR 2.0 Data Parser Tool

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

## UMR 2.0 Data format Description

This dataset is organized in **blocks**, each corresponding to a single sentence.  
Blocks are separated by a line of 80 hash signs:

### Block Structure

Within each block, there are **five parts**, separated by a single hash sign (`#`):

---

### 1. Meta Information

- Entries are separated by two colons (`::`).
- Example entries:
  - `type = partial_conversion`: Indicates that the UMR annotation for this sentence was converted from AMR.
  - `sent_id = u_tree-cs-s1-root`: Maps to the original sentence ID from the source workset.

---

### 2. Sentence Information

This section may include the following fields:

- **Index**: Token indices  
- **Words**: Tokens of the sentence  
- **Morphemes**: Morphological breakdown of words  
- **Morpheme Gloss (English)**: English glosses of morphemes  
- **Morpheme Gloss (Spanish)**: Spanish glosses of morphemes  
- **Morpheme Category**: Categories or grammatical roles of morphemes  
- **Words (English)**: English translation of the individual words  
- **Part of Speech**: POS tags  
- **Sentence**: Original sentence  
- **Translation (English)**: English translation of the sentence  
- **Translation (Spanish)**: Spanish translation of the sentence  

---

### 3. Sentence-Level UMR Annotation

- UMR structure is represented in **Penman notation**.

---

### 4. Alignment Information

- Alignments between UMR concepts and token indices.

---

### 5. Document-Level Annotation

- UMR structure is represented by temporal/model/coreference relation triples. 


---

### Language Coverage

This dataset includes annotated data from the following languages:

#### Unchanged from UMR 1.0 Release

- Arapaho  
- Kukama  
- Navajo  
- Sanapaná  

#### Extended from UMR 1.0 Release

- English  
- Chinese  

#### Newly Added in UMR 2.0 Release

- Czech  
- Latin  

---

### Notes

For detailed mapping between the current file names and their original workset names, refer to the provided **umr_file_name_mapping.txt**.

## Statistics Tables Description

Run `statistics.py` to generate the `umr_statistics.txt` file, which contains summary tables.

### Notes:
- The following descriptions explain the metrics used in the three types of tables.
- **Partial-conversion data** refers to data that have been partially converted from AMR.
- **Non-partial-conversion data** includes data that were manually annotated.


### Stats for ALL

| Metric    | Count                            |
|-----------|----------------------------------|
| Documents | Total documents of this language |

---

### Stats for PARTIAL-CONVERSION

| Metric                     | Count                                                             |
|----------------------------|-------------------------------------------------------------------|
| Documents                  | Documents that contain at least one partial annotation            |
| Sentences (Blocks)         | Sentences that have partially converted annotations                |
| Words                      | Total words of sentences that have partially converted annotations |
| Sentence-level Graphs      | Partially converted sentence level annotations                    |
| Doc-level Graphs           | Partially converted document level annotations                    |
| Relations (Sentence-level) | Total relations in partially converted sentence level annotations  |
| Concepts (Sentence-level)  | Total concepts in partially converted annotations                  |
| Relations (Document-level) | Total relations in partially converted document level annotations  |

---

### Stats for NON-PARTIAL-CONVERSION Blocks

| Metric                     | Count                                                                 |
|----------------------------|------------------------------------------------------------------------|
| Documents                  | Documents that contain at least one non-partial annotation            |
| Sentences (Blocks)         | Sentences that have non-partially converted annotations                |
| Words                      | Total words of sentences that have non-partially converted annotations |
| Sentence-level Graphs      | Manually annotated sentence level graphs                    |
| Doc-level Graphs           | Manually annotated document level graphs                    |
| Relations (Sentence-level) | Total relations in manually annotated sentence level annotations  |
| Concepts (Sentence-level)  | Total concepts in manually annotated annotations                  |
| Relations (Document-level) | Total relations in manually annotated document level annotations  |
