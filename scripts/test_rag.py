
import asyncio

from src.knowledge.rag import answer_from_knowledge


QUESTIONS = [
    "Đơn hàng đang xử lý có thể hủy không?",
    "Đơn đã vận chuyển có hủy được không?",
    "Tôi nhận hàng 3 ngày rồi, có đổi trả được không?",
    "Quá 7 ngày có được đổi trả không?",
    "ShopMate có bán bảo hiểm xe máy không?",
]


async def main():
    for question in QUESTIONS:
        print(f"\nQuestion: {question}")

        result = await answer_from_knowledge(question)

        print(f"Answer: {result['answer']}")
        print(f"Sources: {result['sources']}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
