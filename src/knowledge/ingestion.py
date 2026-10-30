
# src/knowledge/ingestion.py

import hashlib
from pathlib import Path

from sqlalchemy import select
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from src.database import AsyncSessionLocal
from src.knowledge.models import KnowledgeChunk
from src.knowledge.embeddings import get_embeddings


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def get_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


async def ingest_knowledge():
    embedder = get_embeddings()

    sources = [
        ("faq", DATA_DIR / "faq"),
        ("policy", DATA_DIR / "policies"),
    ]

    total_updated = 0

    async with AsyncSessionLocal() as db:
        found_files = 0

        for doc_type, folder in sources:
            if not folder.exists():
                continue

            for file_path in sorted(folder.glob("*.md")):
                found_files += 1

                content = file_path.read_text(
                    encoding="utf-8"
                )

                document_id = (
                    file_path.relative_to(DATA_DIR)
                    .with_suffix("")
                    .as_posix()
                )

                title = get_title(
                    content,
                    file_path.stem,
                )

                chunks = splitter.split_text(content)

                result = await db.scalars(
                    select(KnowledgeChunk).where(
                        KnowledgeChunk.document_id
                        == document_id
                    )
                )

                existing = {
                    row.chunk_index: row
                    for row in result.all()
                }

                changed = []

                for index, chunk in enumerate(chunks):
                    text_to_embed = f"{title}\n\n{chunk}"

                    content_hash = hashlib.sha256(
                        text_to_embed.encode("utf-8")
                    ).hexdigest()

                    old = existing.get(index)

                    if old and old.content_hash == content_hash:
                        continue

                    changed.append(
                        (index, chunk, content_hash)
                    )

                if changed:
                    vectors = await embedder.aembed_documents(
                        [
                            f"{title}\n\n{chunk}"
                            for _, chunk, _ in changed
                        ]
                    )

                    for (index, chunk, content_hash), vector in zip(
                        changed, vectors, strict=True
                    ):
                        row = existing.get(index)

                        if row is None:
                            row = KnowledgeChunk(
                                document_id=document_id,
                                chunk_index=index,
                                doc_type=doc_type,
                                title=title,
                                content=chunk,
                                content_hash=content_hash,
                                embedding=vector,
                            )
                            db.add(row)
                        else:
                            row.doc_type = doc_type
                            row.title = title
                            row.content = chunk
                            row.content_hash = content_hash
                            row.embedding = vector

                    total_updated += len(changed)

                # Delete outdated chunks if document shrank
                for index, row in existing.items():
                    if index >= len(chunks):
                        await db.delete(row)

                await db.commit()

                print(
                    f"{document_id}: "
                    f"{len(chunks)} chunks, "
                    f"{len(changed)} embedded"
                )

        if found_files == 0:
            raise RuntimeError(
                f"No Markdown files found in {DATA_DIR}"
            )

    print(f"Finished. Embedded {total_updated} chunks.")
