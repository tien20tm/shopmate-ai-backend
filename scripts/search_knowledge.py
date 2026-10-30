import argparse
import asyncio

from src.knowledge.retriever import search_knowledge


async def main(query: str):
    results = await search_knowledge(query)

    for index, doc in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print("Title:", doc["title"])
        print("Similarity:", round(doc["similarity"], 4))
        print("Content:", doc["content"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")

    args = parser.parse_args()

    asyncio.run(main(args.query))