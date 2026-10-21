"""Run the Task 3 comparison with real embeddings and reproducible evidence."""

import contextlib
import csv
import io
import sys
from pathlib import Path

import numpy as np
import sentence_transformers
import torch
import transformers

from embedding_retrieve import EmbeddingIndex, MODEL_NAME
from retrieve import load_chunks, print_results, rank_chunks, score_chunks

ROOT = Path(__file__).resolve().parent
QUESTIONS = [
    ("Q1", "May a trained graduate student operate the laser alone at 19:00?", ["A1", "A2"]),
    ("Q2", "Can I use the laser without another person present?", ["A2"]),
    ("Q3", "How frequently must I refresh my laser qualification?", ["T1"]),
    ("Q4", "What is the laser wavelength?", []),
]
FIELDS = ["question_id", "keyword_top_ids", "keyword_scores", "embedding_top_ids",
          "embedding_scores", "required_ids", "keyword_evidence_complete",
          "embedding_evidence_complete", "observation"]


def embedding_report(chunks, scores, ranked, k):
    lines = [f"Embedding retrieval; k={k}", "All six scores (descending):"]
    for i in ranked:
        lines.append(f"{chunks[i].chunk_id} | {chunks[i].filename} | score={scores[i]:.8f}")
    lines.append("Selected passages:")
    for i in ranked[:k]:
        c = chunks[i]
        lines.extend([f"[{c.chunk_id}] {c.filename} | score={scores[i]:.8f}", c.text])
    return "\n".join(lines)


def main():
    chunks = load_chunks()
    assert len(chunks) == 6
    index = EmbeddingIndex(chunks)  # Encode documents once for all questions.
    header = ["Task 3 actual local run; no borrowed output",
              f"python={sys.version.split()[0]}", f"model={MODEL_NAME}",
              f"device={index.model.device}",
              f"sentence-transformers={sentence_transformers.__version__}",
              f"numpy={np.__version__}", f"torch={torch.__version__}",
              f"transformers={transformers.__version__}",
              f"document_matrix.shape={index.document_matrix.shape}",
              "Document embeddings computed once and reused across all questions.",
              "Scores use full precision for ranking and eight decimals for display."]
    logs = header.copy()
    rows = []
    q1 = None
    for qid, question, required in QUESTIONS:
        keyword = rank_chunks(score_chunks(question, chunks))
        selected_kw = [r for r in keyword if r.score > 0][:2]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            print_results(question, keyword, 2)
        vector, scores, ranked = index.search(question)
        logs.extend(["", f"=== {qid} ===", out.getvalue().strip(),
                     f"question_vector.shape={vector.shape}; length={np.linalg.norm(vector):.6f}",
                     embedding_report(chunks, scores, ranked, 2)])
        rows.append(dict(zip(FIELDS, [qid,
            ";".join(r.chunk.chunk_id for r in selected_kw),
            ";".join(str(r.score) for r in selected_kw),
            ";".join(chunks[i].chunk_id for i in ranked[:2]),
            ";".join(f"{scores[i]:.8f}" for i in ranked[:2]),
            ";".join(required) if required else "absent", "", "", ""])))
        if qid == "Q1":
            q1 = question
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "retrieval-runs.txt").write_text("\n".join(logs) + "\n")
    with (ROOT / "results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    experiment = header + ["", "Q1 k experiment", f"Question: {q1}",
                           "Required IDs: A1;A2"]
    for k in (1, 3):
        _, scores, ranked = index.search(q1)
        selected = {chunks[i].chunk_id for i in ranked[:k]}
        covered = len(selected & {"A1", "A2"})
        experiment.extend(["", embedding_report(chunks, scores, ranked, k),
                           f"Required evidence coverage={covered}/2",
                           f"Evidence complete={covered == 2}"])
    (evidence / "k-experiment.txt").write_text("\n".join(experiment) + "\n")
    for row in rows:
        print(row)
    print("Saved evidence/retrieval-runs.txt, results.csv, evidence/k-experiment.txt")


if __name__ == "__main__":
    main()
