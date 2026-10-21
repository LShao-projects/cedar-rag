# Task 1 audit

## Confirm there are exactly six chunks and their text matches the handout

We confirm that the three source files contain exactly six chunks: A1, A2, T1, T2, B1, and B2. We compared all six chunks with the handout and confirmed that their text matches.

## Check one score yourself by counting distinct shared words

Q1 is: "May a trained graduate student operate the laser alone at 19:00?"

After lowercasing the question, extracting alphanumeric words, and removing the required stopwords, its searchable words are "trained", "graduate", "student", "operate", "laser", "alone", "19", and "00". A1 shares three of these words: "trained", "graduate", and "00". The retriever counts distinct shared words, so the repeated "00" in A1 counts only once. This gives A1 a score of 3.

The words "student" and "students" do not match, and neither do "operate" and "operating." The number "19" does not appear in A1.

## Record the selected IDs for Q1. Do they include both the general access rule and the laser operating rule

Yes. We confirm that keyword retrieval selected A1 and A2 for Q1. A1 contains the general laboratory access rule, and A2 contains the laser operating rule. The selected set includes both required passages.
