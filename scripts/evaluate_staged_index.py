#!/usr/bin/env python3
"""Run retrieval-only checks against the isolated PDF2 candidate corpus."""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / "backend" / ".env")
load_dotenv(PROJECT_ROOT / ".env")

from backend.core.config import config
from backend.main import RAGService, SessionLocal, llm_client

DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
QUESTION_PREFIX = re.compile(r"^(give me|tell me|share|list|describe|explain)\b", re.I)


def read_questions(path: Path) -> list[tuple[str, str]]:
    """Extract headings and questions from a DOCX without adding dependencies."""
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    output: list[tuple[str, str]] = []
    category = "Uncategorized"
    for paragraph in root.findall(".//w:p", DOCX_NS):
        text = "".join(
            node.text or "" for node in paragraph.findall(".//w:t", DOCX_NS)
        ).strip()
        if not text:
            continue
        style_node = paragraph.find("w:pPr/w:pStyle", DOCX_NS)
        style = (
            style_node.get(f"{{{DOCX_NS['w']}}}val", "")
            if style_node is not None
            else ""
        )
        if style.lower().startswith("heading") and "?" not in text:
            category = text
        elif "?" in text or QUESTION_PREFIX.match(text):
            output.append((category, text))
    return output


def expected_source_families(category: str) -> tuple[str, ...]:
    value = category.casefold()
    if any(
        word in value
        for word in ("leave", "probation", "separation", "learning", "certification")
    ):
        return ("employee_handbook",)
    if "referral" in value:
        return ("referral", "rewards")
    if "medical" in value or "insurance" in value or "benefit" in value:
        return ("gmc", "policy_handbook", "employee_handbook")
    if (
        "per diem" in value
        or "forex" in value
        or "travel" in value
        or "trip" in value
        or "passport" in value
    ):
        return ("travel", "per diem", "employee_handbook")
    if "code of conduct" in value or "compliance" in value:
        return ("code_of_conduct", "disciplinary")
    return ()


async def evaluate(paths: list[Path], limit: int | None) -> None:
    questions = [item for path in paths for item in read_questions(path)]
    if limit:
        questions = questions[:limit]
    if not questions:
        raise SystemExit("No question prompts were extracted from the DOCX files.")

    prompts = [question for _, question in questions]
    vectors: list[list[float]] = []
    for start in range(0, len(prompts), 64):
        vectors.extend(await llm_client.get_embeddings(prompts[start : start + 64]))

    db = SessionLocal()
    try:
        rag = RAGService(db, corpus="pdf2_stage")
        category_totals: dict[str, list[int]] = {}
        missed: list[tuple[str, str, str, float]] = []
        for (category, question), vector in zip(questions, vectors):
            results = await rag.retrieve_relevant_chunks(
                question,
                top_k=config.TOP_K_RETRIEVAL,
                query_embedding=vector,
            )
            sources = [item["document_name"].casefold() for item in results]
            families = expected_source_families(category)
            expected_hit = not families or any(
                family in source for family in families for source in sources
            )
            totals = category_totals.setdefault(category, [0, 0])
            totals[0] += 1
            totals[1] += int(expected_hit)
            if not expected_hit:
                best_source = results[0]["document_name"] if results else "NO_MATCH"
                best_score = results[0]["similarity_score"] if results else 0.0
                missed.append((category, question, best_source, best_score))

        print(f"Question prompts evaluated: {len(questions)}")
        print(
            "\nExpected-source retrieval by question section (heuristic; review misses):"
        )
        for category, (count, hits) in category_totals.items():
            print(f"  {category}: {hits}/{count}")
        print("\nQuestions whose top-K did not include the expected source family:")
        for category, question, source, score in missed:
            print(f"  [{category}] top={source} score={score:.3f} :: {question}")
        print("\nThis is a retrieval diagnostic, not a gold-answer accuracy score.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        nargs="+",
        type=Path,
        default=[
            PROJECT_ROOT / "Sample Questions for Testing HR Agent.docx",
            PROJECT_ROOT / "Sample Questions for Testing HR Agent - 2nd set-new.docx",
        ],
    )
    parser.add_argument("--limit", type=int, help="Evaluate only the first N prompts")
    args = parser.parse_args()
    asyncio.run(evaluate(args.questions, args.limit))


if __name__ == "__main__":
    main()
