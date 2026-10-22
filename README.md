# Cedar RAG

Partners: Mingjiao Diao and Liuyixin Shao.

This teaching project contains the Task 1 keyword-overlap baseline, the Task 2 embedding retriever, and the Task 3 retrieval comparison. Both methods load the six supplied Cedar Lab passages, rank them for a question, and print the evidence selected by the retriever. The retriever scripts do not generate answers; Task 4 uses separate evidence-only answer conversations.

## Environment

Create and activate a Python virtual environment, then install the embedding dependencies recorded for the later task:

```bash
python3 -m venv .venv
source .venv/bin/activate
export HF_HOME="$PWD/.hf-cache"
python -m pip install -r requirements-embedding.txt
```

Task 1 itself uses only the Python standard library.

## Run the keyword retriever

The question is the first argument. The optional second argument is `k`, the maximum number of positive-scoring passages to select; it defaults to 2.

```bash
python retrieve.py "May a trained graduate student operate the laser alone at 19:00?"
python retrieve.py "May a trained graduate student operate the laser alone at 19:00?" 2
```

## How the code works

- `retrieve.py` lines 52–65 load the three text files and preserve each chunk ID, filename, and paragraph text separately.
- Lines 68–70 lowercase text, extract alphanumeric words, remove exactly the required stopwords, and keep only distinct words.
- Lines 73–86 score each chunk by counting distinct words shared with the question.
- Lines 89–94 rank by descending score and then ascending chunk ID.
- Lines 97–117 print all six results and select up to `k` positive-scoring passages.

IDs and filenames are metadata. Only paragraph text is searched.

## Task 1 Q1 check

For Q1, the retriever selected `A1` and `A2`.

A manual check of `A1` gives the three shared searchable words `00`, `graduate`, and `trained`, so its score is 3. The simple baseline does not match `student` with `students`, `operate` with `operating`, or `19` with any passage value because it performs no stemming, synonym expansion, or semantic search.

## Task 2 embedding inspection

Run the real embedding retriever with the same Q1 and `k=2`:

```bash
python embedding_retrieve.py "May a trained graduate student operate the laser alone at 19:00?" 2
```

The command loads `sentence-transformers/all-MiniLM-L6-v2` on the CPU and saves the complete actual report to `evidence/embedding-inspection.txt`. The model download requires internet access the first time. Later runs reuse the local model cache.

The embedding code separates the process into clear stages:

- `embedding_retrieve.py` lines 27–36 call `encode_document` on the six passage texts. IDs and filenames remain metadata and are not encoded.
- Lines 39–46 call `encode_query` on the question with the same model.
- Both calls use `normalize_embeddings=True`, so every vector has length approximately 1.
- Lines 57–69 create one reusable embedding index: the six document vectors are computed once, then reused for each question.
- Line 67 takes the dot product between the six normalized document vectors and the normalized question vector. For normalized vectors, this equals cosine similarity.
- Lines 68–69 rank all six scores; line 82 selects the top `k` without a relevance threshold.
- Lines 136–165 expose the first 12 coordinate products, the remaining-coordinate subtotal, the full dot product, and an independent cosine calculation.

The document matrix has shape `(6, 384)` because there are six passages with 384 coordinates each. The question vector has shape `(384,)`. All 384 coordinates participate in retrieval even though only the first 12 are printed for inspection.

The largest displayed coordinate is `0.1357` at coordinate 12 of T1. The smallest is `-0.1167` at coordinate 5 of T1. Neither value alone explains what T1 means because similarity depends on all 384 coordinates together.

## Model and package versions

The original Task 2 output in `evidence/embedding-inspection.txt` records `sentence-transformers/all-MiniLM-L6-v2` on CPU with Python 3.12.12, sentence-transformers 6.1.0, numpy 2.5.4, transformers 5.20.1, and torch 2.14.1. Task 3's runtime versions are recorded separately in `evidence/retrieval-runs.txt`.

## Task 3 comparison and k experiment

From the project directory, run:

```bash
source .venv/bin/activate
export HF_HOME="$PWD/.hf-cache"
HF_HUB_OFFLINE=1 python compare_retrieval.py
```

This runs Q1–Q4 through both retrievers at k=2, then reruns Q1 embedding retrieval at k=1 and k=3. Documents are encoded once and reused. Outputs are `evidence/retrieval-runs.txt`, `evidence/k-experiment.txt`, and `results.csv`. The script initially leaves judgment columns blank; rerunning it resets those columns. The original blank table is preserved at `evidence/results-before-audit.csv`.

At k=2, keyword retrieval has complete evidence for Q1–Q3; embedding retrieval has partial evidence for Q1 and complete evidence for Q2–Q3. Q4 has no answer in the corpus. Increasing Q1 embedding k from 1 to 3 still omits A1 and leaves required coverage at 1/2. Task 4 answers and audits are saved in the evidence folder.

## Task 4 answers and claim audits

Q1 and Q4 were answered in two fresh projectless Codex conversations using only the question, embedding k=2 selected passages, and the assignment answer prompt. No full corpus or project folder was attached. The reviewed answer turns contain no tool calls for browsing or reading files.

- `evidence/answer-audit-Q1.md` preserves the exact prompt, original answer, claim audit, one instruction revision, revised answer, and reassessment. The original omitted the missing access-hours warning; the revised answer explicitly states it.
- `evidence/answer-audit-Q4.md` preserves the exact prompt, original answer, and claim audit. It correctly says wavelength cannot be determined from the supplied passages, so no rerun was necessary.

## Reflection

### Mingjiao Diao

In this project, I learned how a question becomes an answer with citations. First, the retriever selects passages using keyword overlap or embedding similarity. Then, those passages are given to Codex to write an answer, which needs to be checked against the sources.

One result that stood out was Q1. The embedding method found A2 but missed A1, so it could support the rule against operating alone but could not establish the access hours. Increasing k to 3 still did not recover A1. This showed me that a relevant passage is not always enough for a complete answer.

Next, I would test combining keyword and embedding results to see whether that improves evidence coverage.

### Liuyixin Shao

We built two ways to retrieve evidence for a question. The first approach counts distinct words shared between the question and each passage after removing stopwords, then ranks the passages by the number of matching words. The second approach uses embeddings to encode the passages and question and keeps the top k by cosine similarity. After retrieval, only the question and selected passages (with their chunk IDs) go to a new Codex conversation, with a prompt asking it to cite the supporting chunk ID after each statement in its answer.

One failure we observed was Q1. Embedding retrieval missed A1, even when we tried k = 1, 2, 3, while keyword retrieval did select A1. Next, I think a hybrid retriever would be what we want to test, because keyword matching and embedding similarity each have their own strengths, and combining them might improve the retrieval accuracy.
