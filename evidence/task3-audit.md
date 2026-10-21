# Task 3 retrieval audit

These judgments were drafted by Codex from the actual local run. The student should check the evidence and confirm or revise them. No personal reflection is included.

| Question | Keyword IDs | Required coverage | Embedding IDs | Required coverage |
| --- | --- | --- | --- | --- |
| Q1 | A1, A2 | 2/2, complete | A2, T1 | 1/2, partial |
| Q2 | A2, B1 | 1/1, complete | A2, T1 | 1/1, complete |
| Q3 | T1, A2 | 1/1, complete | T1, B1 | 1/1, complete |
| Q4 | A2, B1 | Not applicable, answer absent | T1, A2 | Not applicable, answer absent |

## Q1 and missing evidence

A2 supports the rule requiring two trained people whenever the laser is operating. A1 supplies the 08:00 to 22:00 access window for trained graduate students. The embedding top two omit A1, so they cannot establish that 19:00 falls within permitted access hours. Being able to say no to operating alone from A2 does not make the evidence set complete for the full time-and-operation explanation.

## Paraphrases

For Q2, A2 has embedding similarity 0.58519340, connecting “without another person present” with the two-trained-people rule. The keyword method also succeeds: A2 shares “laser” and “present” (score 2), even though it cannot match “person” to “people”.

For Q3, T1 has embedding similarity 0.74202740 and describes renewal every 12 months. Keyword retrieval also succeeds with the exact shared words “laser” and “must” (score 2). Therefore these results do not show that embeddings always outperform keywords.

## Missing information in Q4

None of the six passages specifies laser wavelength. Embeddings rank the available documents and always return top k without a relevance threshold, so T1 and A2 are returned even when neither answers the question. A positive dot product is not proof of answerability. Keyword retrieval also returns passages because they contain “laser”. Both completeness fields are false; this is not treated as a coverage ratio or successful answer retrieval.

## Changing k for Q1

| k | Selected IDs | Required coverage | Complete? |
| --- | --- | --- | --- |
| 1 | A2 | 1/2 | No |
| 2 | A2, T1 | 1/2 | No |
| 3 | A2, T1, B1 | 1/2 | No |

Moving from k=1 to k=2 adds T1, a relevant training condition, but no access hours. Moving to k=3 adds B1, which gives booking duration and reservation instructions rather than evidence resolving the time or solo-operation question. A1 remains fourth (0.37424889), so k=3 still misses it. Larger k does not necessarily improve required evidence coverage.

## Reproducibility

Run `compare_retrieval.py` using the project virtual environment and model cache. The document matrix is computed once per process and reused across Q1–Q4 and the k experiment. Rankings use all 384 coordinates, descending score, and ascending ID for ties. Keyword scores and embedding similarities have different scales and are not numerically comparable.

`evidence/retrieval-runs.txt` and `evidence/k-experiment.txt` contain actual local outputs and versions. `evidence/results-before-audit.csv` preserves the initial four rows with blank judgment fields. `results.csv` contains the subsequent judgments. Rerunning the comparison script resets `results.csv` judgment fields to blank as required by the initial collection step; review and reapply judgments afterward.
