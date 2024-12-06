import csv
from validate import known_relations
# import pandas as pd
def from_roles():
    roles = []

    # Adjust the filename as needed.
    # Assumes the CSV has headers and that column B is the primary role, C is the inverse role.
    with open('../umr_tool_list/roles.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # If there's a header row; if not, remove this line.

        for row in reader:
            # Assuming column B is at index 1 and column C is at index 2
            role_col_b = row[1].strip() if len(row) > 1 else ""
            # role_col_c = row[2].strip() if len(row) > 2 else "" # I don't want the inverse roles anymore

            # Check if they start with ':'
            if role_col_b.startswith(':'):
                roles.append(role_col_b)
            # if role_col_c.startswith(':'):
            #     roles.append(role_col_c)

    # print("Extracted Participant Roles:")
    # for r in roles:
    #     print(r)
    return roles

# def from_ne_types():
#     # Load the CSV file
#     file_path = '../umr_tool_list/ne_types.csv'
#
#     # Read the CSV file into a DataFrame
#     df = pd.read_csv(file_path, header=None)
#
#     # Extract all the named entity types starting from row 4 (index 3 in pandas)
#     named_entity_types = set()
#     for row in df.iloc[3:].values:  # Start from row 4
#         for cell in row:
#             if pd.notnull(cell):  # Exclude NaN cells
#                 named_entity_types.add(cell.strip())
#     return named_entity_types

if __name__ == '__main__':
    umr_tool_roles = set(from_roles())
    validate_roles = set(known_relations.keys())

    # print(umr_tool_roles - validate_roles)
    print(validate_roles - umr_tool_roles)

