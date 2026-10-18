# Cedar RAG

This teaching project currently contains the Task 1 keyword-overlap baseline and the Task 2 embedding retriever. Both methods load the six supplied Cedar Lab passages, rank them for a question, and print the evidence selected by the retriever. They do not generate an answer.

## Environment

Create and activate a Python virtual environment, then install the embedding dependencies recorded for the later task:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
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
