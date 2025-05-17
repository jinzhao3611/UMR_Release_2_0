# Usage
The English UMR 2.0 dataset is a subset of the English AMR dataset selected for conversion into UMR graphs. A list of included sentences along with their corresponding filenames can be found in `directory_by_sentence.tsv`. Not all sentences have been fully converted, the three levels of completeness are:

- <strong>Document Level Conversion:</strong> Sentence level graph fully converted based on current UMR guidelines with document level annotation also provided.
- <strong>Full Conversion:</strong> Sentence level graph fully converted based on current UMR guidelines but no document level annotation.
- <strong>Partial Conversion:</strong> Sentence level graphs with roleset conversions detailed below: 

| Original AMR Structure             | UMR 2.0 Structure     | Change Type   | Number of Occurrences |
|------------------------------------|-----------------------|---------------|:---------------------:|
| :location                          | :place                | deterministic | 17,108                |
| :location-of                       | :place-of             | deterministic | 0                     |
| :companion                         | :accompanier          | deterministic | 29                    |
| :companion-of                      | :accompanier-of       | deterministic | 0                     |
| :beneficiary                       | :affectee             | deterministic | 69                    |
| :beneficiary-of                    | :affectee-of          | deterministic | 0                     |
| :time                              | :temporal             | deterministic | 2,543                 |
| :time-of                           | :temporal-of          | deterministic | 0                     |
| :li                                | :list-item            | deterministic | 0                     |
| :poss                              | :possessor            | deterministic | 566                   |
| :poss-of                           | :possessor-of         | deterministic | 0                     |
| be-located-at-91                   | have-place-91         | deterministic | 272                   |
| be-temporally-at-91                | have-temporal-91      | deterministic | 19                    |
| have-li-91                         | have-list-item-91     | deterministic | 2                     |
| instead-of-91                      | have-substitute-91    | deterministic | 324                   |
| have-rel-role-91                   | have-rel-role-92      | deterministic | 160                   |
| have-org-role-91                   | have-org-role-92      | deterministic | 140                   |
| surface form:  'or else' \| 'lest' | :apprehensive         | new role      | 0                     |
| surface form:  'or else' \| 'lest' | :apprehensive-of      | new role      | 0                     |
| contrast-01                        | contrast-91           | mixed         | 433                   |
| contrast-01                        | have-apprehensive-91  | mixed         | 0                     |
| contrast-01                        | have-pure-addition-91 | mixed         | 0                     |
| have-mod-91                        | have-mod-91           | manual split  | 50                    |
| have-mod-91                        | have-other-role-91    | manual split  | 0                     |
| have-mod-91                        | identity-91           | manual split  | 24                    |
| have-mod-91                        | have-role-91          | manual split  | 45                    |
| infer-01                           | infer-91              | mixed         | 128                   |
| infer-01                           | have-reason-91        | mixed         | 41                    |
| be-from-91                         | have-start-91         | mixed         | 4                     |
| be-from-91                         | have-source-91        | mixed         | 2                     |
| be-from-91                         | have-material-91      | mixed         | 0                     |
| be-from-91                         | from-boundary-01      | mixed         | 28                    |
| mean-01                            | mean-91               | mixed         | 127                   |
| resemble-01                        | resemble-91           | mixed         | 639                   |
| last-01                            | have-duration-91      | mixed         | 2                     |
| realize-01                         | aware-01              | mixed         | 2                     |
| except-01                          | have-subtraction-91   | mixed         | 65                    |

# Acknowledgments

The creators of the English UMRs wish to express their gratitude to Matt Buchholz, Skatje Myers, Alexis Palmer, Martha Palmer, Jin Zhao, Claire Bonial, Tim O’Gorman, Kristin Wright-Bettner, Benét Post, Alvin Chen, Marie MacGregor, Ahmed Elsayed, Carlos Gomez, Loden Havenmeier, and Ath Kilgore for their assistance.


<pre>
=== Machine-readable metadata (DO NOT REMOVE!) ================================
License: CC BY-SA 4.0
Contributors: Julia Bonn, Jens E. Van Gysel, Meagan Vigus
Contact: julia.bonn@colorado.edu
===============================================================================
</pre>