import json, os, re
from pathlib import Path
import penman
from tabulate import tabulate

# Get the directory of the current script
current_script_dir = Path(__file__).parent

# Construct the path to the file
root = current_script_dir.parent

def count(json_file_path):
    word_per_file = 0
    concepts_per_file = 0
    sent_relation_per_file = 0
    sent_annotation_per_file = 0
    doc_annotation_per_file = 0
    sentence_per_file = 0

    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for block in data:
        sentence_per_file += 1
        print(json_file_path)
        if block["sentence_level_graph"]:
            sent_annotation_per_file += 1
        if "\n" in block["document_level_annotation"]:
            doc_annotation_per_file += 1
        try:
            triples = penman.decode(block["sentence_level_graph"]).triples

            relations_count = sum(1 for triple in triples if triple[1] != ':instance')
            concepts_count = sum(1 for triple in triples if triple[1] == ':instance')
            # print(len(block["words"]))
            # print(relations_count)
            # print(concepts_count)
            # print("******************")
            word_per_file += len(block["words"])
            concepts_per_file += concepts_count
            sent_relation_per_file += relations_count
        except penman.exceptions.DecodeError:
            print(penman.exceptions.DecodeError)
    return word_per_file, concepts_per_file, sent_relation_per_file, sent_annotation_per_file, doc_annotation_per_file, sentence_per_file



def batch_count(json_folder):
    files_per_folder = 0
    word_per_folder = 0
    concepts_per_folder = 0
    sent_relations_per_folder = 0
    sentence_annotation_per_folder = 0
    doc_annotation_per_folder = 0
    sentence_per_folder = 0
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            json_file_path = os.path.join(json_folder, filename)
            word_per_file, concepts_per_file, sent_relation_per_file, sent_annotation_per_file, doc_annotation_per_file, sentence_per_file = count(json_file_path)
            files_per_folder += 1
            word_per_folder += word_per_file
            concepts_per_folder += concepts_per_file
            sent_relations_per_folder += sent_relation_per_file
            sentence_annotation_per_folder += sent_annotation_per_file
            doc_annotation_per_folder += doc_annotation_per_file
            sentence_per_folder += sentence_per_file
    # Prepare data for the table
    headers = ["Metric", "Count"]
    data = [
        ["Documents", files_per_folder],
        ["Sentences", sentence_per_folder],
        ["Words", word_per_folder],
        ["Sentence Annotations", sentence_annotation_per_folder],
        ["Document Annotations", doc_annotation_per_folder],
        ["Concepts", concepts_per_folder],
        ["Sentence Relations", sent_relations_per_folder],
    ]

    # Print the table
    print(tabulate(data, headers, tablefmt="grid"))


# Example usage
# json_file_path = Path(root) / 'czech/jsons/czech_ln94200_1.json'
# count(json_file_path)

# RUN this to get the count of the language
lang = 'english'
batch_count(json_folder=Path(root) / f'{lang}/jsons/')
