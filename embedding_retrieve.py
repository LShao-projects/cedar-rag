"""Visible embedding retriever for the six Cedar Lab passages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import sentence_transformers
import torch
import transformers
from sentence_transformers import SentenceTransformer

from retrieve import Chunk, load_chunks


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "evidence" / "embedding-inspection.txt"


def format_coordinates(vector: np.ndarray, count: int = 12) -> str:
    """Format the displayed coordinate preview without changing calculations."""
    return "[" + ", ".join(f"{value:.4f}" for value in vector[:count]) + "]"


def encode_documents(
    model: SentenceTransformer, chunks: list[Chunk]
) -> np.ndarray:
    """Encode passage text only; IDs and filenames remain unencoded metadata."""
    return model.encode_document(
        [chunk.text for chunk in chunks],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def encode_question(model: SentenceTransformer, question: str) -> np.ndarray:
    """Encode one question in the same compatible vector space as the passages."""
    return model.encode_query(
        question,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def rank_scores(chunks: list[Chunk], scores: np.ndarray) -> list[int]:
    """Rank by descending similarity, breaking exact ties by ascending chunk ID."""
    return sorted(
        range(len(chunks)),
        key=lambda index: (-float(scores[index]), chunks[index].chunk_id),
    )


class EmbeddingIndex:
    """Encode the six documents once and reuse their matrix for any questions."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.model = SentenceTransformer(MODEL_NAME, device="cpu")
        self.document_matrix = encode_documents(self.model, chunks)

    def search(self, question: str) -> tuple[np.ndarray, np.ndarray, list[int]]:
        question_vector = encode_question(self.model, question)
        scores = self.document_matrix @ question_vector
        ranked_indices = rank_scores(self.chunks, scores)
        return question_vector, scores, ranked_indices


def build_report(question: str, k: int) -> str:
    """Run the real model once and return a complete, inspectable text report."""
    chunks = load_chunks()
    if len(chunks) != 6:
        raise RuntimeError(f"Expected exactly 6 chunks, found {len(chunks)}")

    index = EmbeddingIndex(chunks)
    model = index.model
    document_matrix = index.document_matrix
    question_vector, scores, ranked_indices = index.search(question)
    selected_indices = ranked_indices[: min(k, len(ranked_indices))]

    lines: list[str] = [
        "Cedar RAG embedding inspection",
        f"Question: {question}",
        f"k: {k}",
        "",
        "Model and environment:",
        f"model={MODEL_NAME}",
        f"device={model.device}",
        f"python={sys.version.split()[0]}",
        f"sentence-transformers={sentence_transformers.__version__}",
        f"transformers={transformers.__version__}",
        f"torch={torch.__version__}",
        f"numpy={np.__version__}",
        "",
        "Actual shapes:",
        f"document_matrix.shape={document_matrix.shape}",
        f"question_vector.shape={question_vector.shape}",
        "",
        "Vector previews and lengths:",
        "The first 12 coordinates are displayed to four decimal places.",
        "All 384 coordinates, not just the displayed 12, are used for retrieval.",
    ]

    for chunk, vector in zip(chunks, document_matrix, strict=True):
        lines.append(
            f"{chunk.chunk_id} | {chunk.filename} | "
            f"first_12={format_coordinates(vector)} | "
            f"length={np.linalg.norm(vector):.6f}"
        )
    lines.append(
        f"QUERY | first_12={format_coordinates(question_vector)} | "
        f"length={np.linalg.norm(question_vector):.6f}"
    )

    lines.extend(["", "All similarity scores (descending):"])
    for index in ranked_indices:
        lines.append(
            f"{chunks[index].chunk_id} | {chunks[index].filename} | "
            f"score={scores[index]:.8f}"
        )

    lines.extend(["", "Selected passages:"])
    for index in selected_indices:
        chunk = chunks[index]
        lines.extend(
            [
                f"[{chunk.chunk_id}] {chunk.filename} | score={scores[index]:.8f}",
                chunk.text,
                "",
            ]
        )

    top_index = ranked_indices[0]
    top_chunk = chunks[top_index]
    top_vector = document_matrix[top_index]
    coordinate_products = question_vector * top_vector
    first_twelve_subtotal = float(np.sum(coordinate_products[:12], dtype=np.float64))
    remaining_subtotal = float(np.sum(coordinate_products[12:], dtype=np.float64))
    full_dot_product = float(np.dot(question_vector, top_vector))
    direct_cosine = full_dot_product / float(
        np.linalg.norm(question_vector) * np.linalg.norm(top_vector)
    )
    tolerance = 1e-6

    lines.extend(
        [
            f"Top-passage calculation check: {top_chunk.chunk_id}",
            "First 12 coordinate products:",
        ]
    )
    for coordinate, product in enumerate(coordinate_products[:12], start=1):
        lines.append(f"coordinate_{coordinate:02d}_product={product:.10f}")
    lines.extend(
        [
            f"first_12_subtotal={first_twelve_subtotal:.10f}",
            f"remaining_372_subtotal={remaining_subtotal:.10f}",
            f"subtotal_sum={first_twelve_subtotal + remaining_subtotal:.10f}",
            f"full_dot_product={full_dot_product:.10f}",
            f"direct_cosine={direct_cosine:.10f}",
            f"absolute_difference={abs(full_dot_product - direct_cosine):.12f}",
            f"agree_within_tolerance_{tolerance:g}="
            f"{bool(np.isclose(full_dot_product, direct_cosine, atol=tolerance, rtol=0.0))}",
        ]
    )
    return "\n".join(lines).rstrip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect real embedding retrieval for the Cedar Lab passages."
    )
    parser.add_argument("question", help="Question to retrieve evidence for")
    parser.add_argument(
        "k",
        nargs="?",
        type=int,
        default=2,
        help="number of top embedding results to select (default: 2)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="path for the saved inspection report",
    )
    args = parser.parse_args()
    if args.k < 1:
        parser.error("k must be at least 1")
    return args


def main() -> None:
    args = parse_args()
    report = build_report(args.question, args.k)
    print(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
