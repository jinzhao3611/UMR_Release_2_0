python validate.py ../english/formatted_data/Document_Level_Graphs_2.txt > /Users/jinzhao/Downloads/UMR_Release_2_0/english/errors/Document_Level_Graphs_2.txt



English Data: I got two folders from Alvin:
    for full_conversion folder:
    1. this folder contains documents from 4 sources, I break up each source into documents by workset name
    2. the files in this folder have irregular number of line breaks. I fixed it to be there should be two empty lines after each sentence, and one empty line after each annotation block.

    for partial_conversion folder:
    there is no sentence number in each variable




sentence heading standardization: https://github.com/ufal/UMR/issues/9

manual change:
Little_Prince.txt: the linebreak between s71 and s91 is manually changed to "\n"


UMR tool list:
Abstract Concepts/subroles
Abstract Rolesets are added in non_event_rolesets and discourse_concepts in validate.py
Roles are added in known_relations in validate.py
Attributes/values are added in known_relations in validate.py
haven't done anything to NE types yet
We don't have to do anything about three mappings files.


