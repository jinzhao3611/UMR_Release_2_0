In respond to https://github.com/ufal/UMR/issues/9
Data format:
################################################################################
# meta-info :: sent_id = NW_PRI_ENG_0153_2000_1214.1
# :: snt1
Index: 1       2       3       4       5       6       7       8       9       10      11      12      13      14      15
Words: Edmund  Pope    tasted  freedom today   for     the     first   time    in      more    than    eight   months  .
# sentence level graph:
(s1t / taste-01
    :ARG0 (s1p / person
        :name (s1n / name :op1 "Edmund" :op2 "Pope"))
    :ARG1 (s1f / free-04
        :ARG1 s1p
        :aspect state)
    :temporal (s1t2 / today)
    :aspect state)

# alignment:
s1t: 3-3
s1n: 1-2
s1p: 0-0
s1f: 4-4
s1t2: 5-5

# document level annotation:
(s1s0 / sentence
    :temporal ((document-creation-time :depends-on s1t2)
            (s1t2 :contains s1t))
    :modal ((root :modal author)
            (author :full-affirmative s1t)
            (author :full-affirmative s1f)))