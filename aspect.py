import json
from glob import glob
from pprint import pprint
import penman
import re


outputs = []
doc_level_files = glob('./english/original_data/document_level_conversion/*.txt')
full_conversion_files = glob('./english/original_data/full_conversion/**/*.txt', recursive=True)
partial_conversion_files = glob('./english/original_data/partial_conversion/**/*.txt', recursive=True)

curr_files = doc_level_files
curr_output_file = './umr_aspect/doc_level_removed_aligned.json'

"""
specs:
- each folder has its own json
- each json has: file, id, sentence, graph, predicate, variable name, and aspect (if applicable)
- as many copies of graphs as there are predicates
"""

def decode_graph(graph_lines):
    try:
        penmanString = "".join(graph_lines)
        graph = penman.decode(penmanString)
        return graph
    except Exception as e:
        return e


def get_predicates(graph):
    pred_pattern = re.compile(r'[a-z]+.*-[0-9]+')
    predicates = []
    for instance in graph.instances():
        if pred_pattern.match(instance.target):
            predicates.append((instance.source, instance.target))
    
    return predicates


def get_aspect(graph):
    aspects = []
    vars_to_aspect = {}
    for attribute in graph.attributes():
        if attribute.role == ':aspect':
            vars_to_aspect[attribute.source] = attribute.target
    for instance in graph.instances():
        if instance.source in vars_to_aspect:
            aspects.append((instance.source, instance.target, vars_to_aspect[instance.source]))
    
    return aspects


def get_aspect_blanks(graph):
    aspects = []
    new_attributes = []
    vars_to_aspect = {}
    for attribute in graph.attributes():
        if attribute.role == ':aspect':
            vars_to_aspect[attribute.source] = attribute.target
            # new_attributes.append(penman.graph.Attribute(attribute.source, attribute.role, "blank"))
        else:
            new_attributes.append(attribute)
    for instance in graph.instances():
        if instance.source in vars_to_aspect:
            aspects.append((instance.source, instance.target, vars_to_aspect[instance.source]))
    new_graph = penman.Graph(graph.instances() + graph.edges() + new_attributes, top=graph.top)

    return aspects, new_graph


def get_pred_from_file(file):
    outputs = []
    file_head = file.replace('./english/original_data/', '').replace('.txt', '')
    graph_marker = False
    id_pattern = re.compile(r'# ::id ([^:]+) ::')
    curr_id = ""
    curr_sent = ""
    prev_sent = ""
    curr_graph_lines = []
    aspect_marker = False
    for line in open(file, 'r').readlines():
        if ":aspect" in line:
            aspect_marker = True
        if line.startswith("# ::id "):
            try:
                curr_id = id_pattern.match(line).group(1)
            except Exception as e:
                # print("id error")
                # print(file)
                # print(line)
                continue
        if line.startswith("Words:  "):
            prev_sent = curr_sent
            curr_sent = line.replace("Words:  ", "").replace("  ", " ").replace("\n", "")
        if line.startswith("# sentence level graph:"):
            curr_graph_lines = []
            graph_marker = True
            continue
        if graph_marker:
            if line.startswith("# :: note: sentence not included"):
                graph_marker = False
                continue
            if line == "\n":
                graph_marker = False
                if aspect_marker:
                    aspect_marker = False
                    continue
                curr_graph = decode_graph(curr_graph_lines)
                if isinstance(curr_graph, Exception):
                    print("graph error")
                    print(file)
                    print(curr_id)
                    return curr_graph
                predicates = get_predicates(curr_graph)
                if not predicates:
                    # print(file)
                    # print(curr_id)
                    continue
                for pred in predicates:
                    outputs.append({
                        "file": file_head,
                        "id": curr_id,
                        "context": prev_sent,
                        "sentence": curr_sent,
                        "graph": penman.encode(curr_graph),
                        "predicate": pred[1],
                        "variable": pred[0],
                    })
            else:
                curr_graph_lines.append(line)
    return outputs


def get_aspect_from_file(file):
    outputs = []
    file_head = file.replace('./english/original_data/', '').replace('.txt', '')
    graph_marker = False
    align_marker = False
    id_pattern = re.compile(r'# ::id ([^: ]+)')
    curr_id = ""
    curr_sent = ""
    curr_graph_lines = []
    curr_align_lines = []
    for line in open(file, 'r').readlines():
        if line.startswith("# ::id "):
            try:
                curr_id = id_pattern.match(line).group(1)
            except Exception as e:
                print("id error", file, line)
                continue
        if line.startswith("Index: "):
            try:
                max_ind = int(line.split()[-1])
            except:
                continue
        if line.startswith("Words:  "):
            # curr_sent = line.replace("Words:  ", "").replace("  ", " ").replace("\n", "")
            ind_sent = line.split()[1:]
            try:
                if len(ind_sent) != max_ind:
                    print("index error", file, curr_id)
            except:
                continue
            curr_sent = {i+1: word for i, word in enumerate(ind_sent)}
        if line.startswith("# sentence level graph:"):
            curr_graph_lines = []
            graph_marker = True
            continue
        if line.startswith("# alignment:"):
            curr_align_lines = []
            align_marker = True
            continue
        if align_marker:
            if line == "\n":
                align_marker = False
                for asp in aspects:
                    outputs.append({
                        "file": file_head,
                        "id": curr_id,
                        "sentence": curr_sent,
                        "graph": penman.encode(curr_graph),
                        "predicate": asp[1],
                        "variable": asp[0],
                        "aspect": asp[2],
                        "alignment": curr_align_lines,
                    })
            else:
                curr_align_lines.append(line[:-1])
        if graph_marker:
            if line.startswith("# :: note: sentence not included") or line.startswith("# :: note: graph is only"):
                graph_marker = False
                continue
            if line == "\n":
                graph_marker = False
                curr_graph = decode_graph(curr_graph_lines)
                if isinstance(curr_graph, Exception):
                    print("graph error", file, curr_id)
                    return curr_graph
                aspects = get_aspect(curr_graph)
                if not aspects:
                    # print("no aspects", file, curr_id)
                    continue
            else:
                curr_graph_lines.append(line)
    return outputs


def get_blank_aspect_from_file(file):
    outputs = []
    file_head = file.replace('./english/original_data/', '').replace('.txt', '')
    graph_marker = False
    align_marker = False
    id_pattern = re.compile(r'# ::id ([^: ]+)')
    curr_id = ""
    curr_sent = ""
    curr_graph_lines = []
    curr_align_lines = []
    for line in open(file, 'r').readlines():
        if line.startswith("# ::id "):
            try:
                curr_id = id_pattern.match(line).group(1)
            except Exception as e:
                print("id error", file, line)
                continue
        if line.startswith("Index: "):
            try:
                max_ind = int(line.split()[-1])
            except:
                continue
        if line.startswith("Words:  "):
            # curr_sent = line.replace("Words:  ", "").replace("  ", " ").replace("\n", "")
            ind_sent = line.split()[1:]
            try:
                if len(ind_sent) != max_ind:
                    print("index error", file, curr_id)
            except:
                continue
            curr_sent = {i+1: word for i, word in enumerate(ind_sent)}
        if line.startswith("# sentence level graph:"):
            curr_graph_lines = []
            graph_marker = True
            continue
        if line.startswith("# alignment:"):
            curr_align_lines = []
            align_marker = True
            continue
        if align_marker:
            if line == "\n":
                align_marker = False
                for asp in aspects:
                    outputs.append({
                        "file": file_head,
                        "id": curr_id,
                        "sentence": curr_sent,
                        "graph": penman.encode(new_graph),
                        "predicate": asp[1],
                        "variable": asp[0],
                        "aspect": asp[2],
                        "alignment": curr_align_lines,
                    })
            else:
                curr_align_lines.append(line[:-1])
        if graph_marker:
            if line.startswith("# :: note: sentence not included") or line.startswith("# :: note: graph is only"):
                graph_marker = False
                continue
            if line == "\n":
                graph_marker = False
                curr_graph = decode_graph(curr_graph_lines)
                if isinstance(curr_graph, Exception):
                    print("graph error", file, curr_id)
                    return curr_graph
                aspects, new_graph = get_aspect_blanks(curr_graph)
                if not aspects:
                    # print("no aspects", file, curr_id)
                    continue
            else:
                curr_graph_lines.append(line)
    return outputs


outputs = []
for file in curr_files:
    # if "pear_story" in file:
    #     continue
    file_preds = get_blank_aspect_from_file(file)
    # file_preds = get_aspect_from_file(file)
    # file_preds = get_pred_from_file(file)
    if isinstance(file_preds, Exception):
        print("file error")
        print(file)
        print(file_preds)
        continue
    outputs.extend(file_preds)
print(f"Pulled {len(outputs)} samples")
with open(curr_output_file, 'w') as f:
    json.dump(outputs, f, indent=4)