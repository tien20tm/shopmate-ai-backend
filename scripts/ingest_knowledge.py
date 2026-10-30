import asyncio

from src.knowledge.ingestion import ingest_knowledge


if __name__ == "__main__":
    asyncio.run(ingest_knowledge())