"""Keyword-overlap baseline retriever for the Cedar Lab passages."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parent / "docs"
STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "to",
    "of",
    "in",
    "at",
    "for",
    "and",
    "or",
    "may",
    "can",
    "i",
    "it",
    "be",
}
CHUNK_PATTERN = re.compile(
    r"^\[([A-Z]\d+)\]\s+(.*?)(?=\n\s*\n\[|\Z)",
    flags=re.MULTILINE | re.DOTALL,
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    filename: str
    text: str


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: int
    matched_words: tuple[str, ...]


def load_chunks(docs_dir: Path = DOCS_DIR) -> list[Chunk]:
    """Load labeled paragraphs while keeping IDs and filenames as metadata."""
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*.txt")):
        source = path.read_text(encoding="utf-8")
        for chunk_id, paragraph_text in CHUNK_PATTERN.findall(source):
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    filename=path.name,
                    text=paragraph_text.strip(),
                )
            )
    return chunks


def searchable_words(text: str) -> set[str]:
    """Return distinct lowercase alphanumeric words minus the required stopwords."""
    return set(TOKEN_PATTERN.findall(text.lower())) - STOPWORDS


def score_chunks(question: str, chunks: list[Chunk]) -> list[ScoredChunk]:
    """Score chunks by their distinct shared words with the question."""
    query_words = searchable_words(question)
    scored: list[ScoredChunk] = []
    for chunk in chunks:
        matched_words = tuple(sorted(query_words & searchable_words(chunk.text)))
        scored.append(
            ScoredChunk(
                chunk=chunk,
                score=len(matched_words),
                matched_words=matched_words,
            )
        )
    return scored


def rank_chunks(scored_chunks: list[ScoredChunk]) -> list[ScoredChunk]:
    """Rank by descending score, breaking ties by ascending chunk ID."""
    return sorted(
        scored_chunks,
        key=lambda result: (-result.score, result.chunk.chunk_id),
    )


def print_results(question: str, ranked_chunks: list[ScoredChunk], k: int) -> None:
    """Print every score followed by up to k positive-scoring passages."""
    print(f"Question: {question}")
    print(f"k: {k}")
    print("\nAll chunk scores:")
    for result in ranked_chunks:
        words = ", ".join(result.matched_words) if result.matched_words else "(none)"
        print(
            f"{result.chunk.chunk_id} | {result.chunk.filename} | "
            f"score={result.score} | matched_words={words}"
        )

    selected = [result for result in ranked_chunks if result.score > 0][:k]
    if not selected:
        print("\nNo matching passages.")
        return

    print("\nSelected passages:")
    for result in selected:
        print(f"\n[{result.chunk.chunk_id}] {result.chunk.filename}")
        print(result.chunk.text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank the Cedar Lab passages by distinct keyword overlap."
    )
    parser.add_argument("question", help="Question to retrieve evidence for")
    parser.add_argument(
        "k",
        nargs="?",
        type=int,
        default=2,
        help="maximum positive-scoring passages to select (default: 2)",
    )
    args = parser.parse_args()
    if args.k < 1:
        parser.error("k must be at least 1")
    return args


def main() -> None:
    args = parse_args()
    chunks = load_chunks()
    if len(chunks) != 6:
        raise RuntimeError(f"Expected exactly 6 chunks, found {len(chunks)}")
    ranked_chunks = rank_chunks(score_chunks(args.question, chunks))
    print_results(args.question, ranked_chunks, args.k)


if __name__ == "__main__":
    main()
