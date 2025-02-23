/Users/jinzhao/opt/anaconda3/envs/umr_2024_spring/bin/python /Users/jinzhao/schoolwork/UMR_Release_2_0/scripts/statistics.py
Note: 
1. following is the description of what each item means in the three table
2. partial-conversion data means data that are partially converted from amr (english and chinese has this type).
3. non-partial-conversion data includes data that are annotated from scratch or data that are fully converted from amr.
4. english data is still not complete, therefore there are cases english sentences count is larger than sentence-level graphs, that means those sentences indeed still missing sentence level annotations.

=== Stats for ALL ===
+-----------+----------------------------------+
| Metric    | Count                            |
+===========+==================================+
| Documents | Total documents of this language |
+-----------+----------------------------------+

=== Stats for PARTIAL-CONVERSION ===
+----------------------------+-------------------------------------------------------------------+
| Metric                     | Count                                                             |
+============================+===================================================================+
| Documents                  | Documents that contain at least one partial annotation            |
+----------------------------+-------------------------------------------------------------------+
| Sentences (Blocks)         | Sentences that have partially converted annotation                |
+----------------------------+-------------------------------------------------------------------+
| Words                      | Total words of sentences that have partially converted annotation |
+----------------------------+-------------------------------------------------------------------+
| Sentence-level Graphs      | partially converted sentence level annotations                    |
+----------------------------+-------------------------------------------------------------------+
| Doc-level Graphs           | partially converted document level annotations                    |
+----------------------------+-------------------------------------------------------------------+
| Relations (Sentence-level) | Total relations in partially converted sentence level annotation  |
+----------------------------+-------------------------------------------------------------------+
| Concepts (Sentence-level)  | Total concepts in partially converted annotation                  |
+----------------------------+-------------------------------------------------------------------+
| Relations (Document-level) | Total relations in partially converted document level annotation  |
+----------------------------+-------------------------------------------------------------------+

=== Stats for NON-PARTIAL-CONVERSION Blocks ===
+----------------------------+-----------------------------------------------------------------------+
| Metric                     | Count                                                                 |
+============================+=======================================================================+
| Documents                  | Documents that contain at least one non-partial annotation            |
+----------------------------+-----------------------------------------------------------------------+
| Sentences (Blocks)         | Sentences that have non-partially converted annotation                |
+----------------------------+-----------------------------------------------------------------------+
| Words                      | Total words of sentences that have non-partially converted annotation |
+----------------------------+-----------------------------------------------------------------------+
| Sentence-level Graphs      | non-partially converted sentence level annotations                    |
+----------------------------+-----------------------------------------------------------------------+
| Doc-level Graphs           | non-partially converted document level annotations                    |
+----------------------------+-----------------------------------------------------------------------+
| Relations (Sentence-level) | Total relations in non-partially converted sentence level annotation  |
+----------------------------+-----------------------------------------------------------------------+
| Concepts (Sentence-level)  | Total concepts in non-partially converted annotation                  |
+----------------------------+-----------------------------------------------------------------------+
| Relations (Document-level) | Total relations in non-partially converted document level annotation  |
+----------------------------+-----------------------------------------------------------------------+

Process finished with exit code 0
