# ShopMate AI — Project Plan (MVP v1.0)

> **Tên dự án:** ShopMate AI  
> **Tagline:** AI-powered E-commerce Customer Support Agent  
> **Mục tiêu:** Pet project end-to-end tập trung vào Embedding, Vector Search, RAG, Tool Calling, AI Agent, LangChain và LangGraph.  
> **Thời gian dự kiến:** 8 ngày, khoảng 25–35 giờ (ước tính; tuỳ mức độ quen Python/React).  
> **Ngôn ngữ ứng dụng / dữ liệu:** Tiếng Việt.  
> **Kiến trúc:** 2 Git repositories độc lập (Frontend + Backend), **1 FastAPI backend**, 1 PostgreSQL database.

---

## 1. Tóm tắt sản phẩm

ShopMate AI là website demo hỗ trợ khách hàng của một cửa hàng công nghệ giả lập. Người dùng có thể:

1. Xem danh sách và chi tiết đơn hàng trên dashboard.
2. Chat bằng tiếng Việt để hỏi FAQ và chính sách bán hàng.
3. Hỏi AI về trạng thái đơn hàng.
4. Đặt câu hỏi cần **kết hợp** dữ liệu đơn hàng trong PostgreSQL và chính sách trong RAG.
5. Xem nguồn tài liệu tham chiếu và (nếu kịp) các tool Agent đã gọi.

**Ví dụ demo:** "Đơn ORD-002 đang giao, tôi có hủy được không?" → Agent gọi tool tra cứu đơn hàng và tool tìm chính sách, sau đó trả lời có nguồn.

### Mục tiêu học tập

- **Embedding:** Biến đoạn tài liệu thành vector.
- **Vector DB:** Lưu và tìm kiếm vector bằng pgvector.
- **RAG:** Retrieve các đoạn liên quan và dùng làm ngữ cảnh cho câu trả lời.
- **LangChain:** Tích hợp chat model, embedding model, tools và các thành phần RAG.
- **Agent / Tool Calling:** Quyết định khi nào tra cứu tài liệu, khi nào truy vấn đơn hàng, hoặc cả hai.
- **LangGraph:** Quản lý vòng lặp Agent → Tool(s) → Agent → Answer.
- **Evaluation:** Đánh giá retrieval, tool selection và tính đúng đắn của phản hồi.

---

## 2. Phạm vi MVP

### Bắt buộc

- [ ] Chat AI tiếng Việt, trả lời có tham chiếu nguồn khi dùng RAG.
- [ ] Tra cứu trạng thái đơn hàng từ PostgreSQL qua Agent tool.
- [ ] Câu hỏi kết hợp **Order + Policy** hoạt động đúng.
- [ ] Dashboard đơn hàng và màn hình chi tiết đơn hàng.
- [ ] Trang Knowledge Base hiển thị FAQ/policy dùng trong RAG.
- [ ] Chat memory trong cùng session (in-memory cho local demo).
- [ ] Dataset giả lập tiếng Việt, nhất quán giữa FAQ, policy, product và order.
- [ ] Hai repo chạy độc lập ở local và FE gọi BE qua REST.
- [ ] Có bộ evaluation cơ bản và README cho từng repo.

### Tùy chọn nếu còn thời gian

- Agent debug panel hiển thị `tools_used` và nguồn tài liệu.
- Product catalog đơn giản; nếu chưa kịp, sản phẩm chỉ xuất hiện trong Order Detail.
- Deploy bản demo public.

### Không nằm trong MVP

Authentication thật, thanh toán, hủy/hoàn tiền thật, multi-agent, upload tài liệu qua UI, crawler Shopee/TikTok Shop, streaming, Redis, Kafka, Celery, Kubernetes, fine-tuning, CI/CD phức tạp.

> **Giới hạn demo:** Dùng `DEMO_CUSTOMER_ID` ở **backend**. Không nhận `customer_id` từ input của LLM; mọi truy vấn đơn hàng phải lọc theo customer ID hiện tại. Chưa phải giải pháp xác thực production.

---

## 3. Tech stack

| Layer | Công nghệ | Vai trò / lý do |
|---|---|---|
| FE | **React + Vite + TypeScript** | SPA gọn, phù hợp dashboard và deploy static |
| UI | **Tailwind CSS + shadcn/ui** | Xây giao diện nhanh, dễ demo |
| BE | **Python + FastAPI** | Một backend duy nhất cho REST, business logic và AI |
| LLM | **OpenAI API** (model cấu hình qua env) | Chat / tool calling |
| Embedding | **OpenAI Embeddings** (model cấu hình qua env) | Embed FAQ/policy và câu hỏi |
| AI framework | **LangChain** | Model, embeddings, retriever/tool integration |
| Agent orchestration | **LangGraph** | Vòng lặp agent và tool execution |
| Database | **PostgreSQL + pgvector** | Relational data và vector search cùng DB |
| DB access | **psycopg 3** + SQL trực tiếp | Ít abstraction, dễ hiểu pgvector; chưa cần ORM |
| Tests | **pytest** (BE), **Vitest** nếu cần (FE) | Kiểm tra chức năng quan trọng |
| Local | **Docker Compose** (trong BE repo) | Chạy Postgres + BE; FE chạy Vite riêng |

**Nguyên tắc:** ưu tiên stack thuận tiện để học AI Engineering, không đổi sang nền tảng khác chỉ vì một dịch vụ deploy miễn phí.

---

## 4. Hai repository độc lập

### Repo 1 — `shopmate-ai-backend`

- Chứa toàn bộ FastAPI, API endpoints, business logic, LangChain, LangGraph, RAG pipeline, SQL schema, data seeds, tests.
- Sở hữu **API contract**; FastAPI tự sinh OpenAPI tại `/openapi.json` và Swagger UI tại `/docs`.
- Deploy lên một nơi chạy Python web service (đề xuất ban đầu: Render).

```text
shopmate-ai-backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── chat.py
│   │   ├── orders.py
│   │   └── knowledge.py
│   ├── agent/
│   │   ├── graph.py
│   │   ├── tools.py
│   │   └── prompts.py
│   ├── rag/
│   │   ├── ingest.py
│   │   └── retriever.py
│   ├── services/
│   │   └── orders.py
│   ├── db/
│   │   └── connection.py
│   └── schemas/
│       └── api.py
├── data/
│   ├── faq/
│   ├── policies/
│   └── seeds/
├── db/
│   └── migrations/
│       └── 001_init.sql
├── evals/
│   └── cases.json
├── tests/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

### Repo 2 — `shopmate-ai-frontend`

- Chứa giao diện React, routes/pages, API client, components, UI state và assets.
- **Không chứa API keys, credentials DB hay logic Agent.**
- Deploy static lên Cloudflare (Workers Static Assets hoặc Pages).

```text
shopmate-ai-frontend/
├── src/
│   ├── app/
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── OrdersPage.tsx
│   │   ├── OrderDetailPage.tsx
│   │   └── KnowledgePage.tsx
│   ├── components/
│   │   ├── layout/
│   │   ├── chat/
│   │   └── orders/
│   ├── lib/
│   │   └── api.ts
│   └── types/
│       └── api.ts
├── public/
├── .env.example
├── package.json
├── vite.config.ts
└── README.md
```

### Quy ước phối hợp giữa 2 repo

1. **Backend là nguồn sự thật** cho API contract (`/openapi.json`). FE định nghĩa TypeScript types dựa trên schema này; chưa cần tự động generate trong MVP.
2. FE chỉ gọi BE qua `VITE_API_BASE_URL`; không truy cập PostgreSQL hay OpenAI trực tiếp.
3. BE cho phép CORS **chỉ với origin FE cụ thể** trong `CORS_ORIGINS`, gồm `http://localhost:5173` khi phát triển local.
4. Không dùng submodule/monorepo hoặc cơ chế sync code giữa hai repo.
5. Hai repo có README và pipeline deploy riêng nếu triển khai sau này.

---

## 5. Kiến trúc hệ thống

```mermaid
flowchart TB
    FE["React + Vite + TS\nCloudflare static hosting"]
    API["FastAPI\nREST + Business Logic"]
    AGENT["LangGraph Agent\nLangChain + LLM"]
    KNOW["search_knowledge_base\nRAG Tool"]
    ORDER["get_order_status\nOrder Tool"]
    DB[("PostgreSQL + pgvector")]
    OPENAI["OpenAI API\nLLM + Embeddings"]

    FE -->|HTTPS REST| API
    API -->|Chat requests| AGENT
    API -->|Orders / Knowledge API| DB
    AGENT -->|Tool call| KNOW
    AGENT -->|Tool call| ORDER
    KNOW --> DB
    ORDER -->|Business service + scoped SQL| DB
    AGENT --> OPENAI
    KNOW -->|Query embedding| OPENAI
```

**Quan trọng:** Chỉ có **1 backend process FastAPI**. LangGraph/RAG là các module trong repo backend, **không phải một microservice riêng**.

### RAG ingest (offline / command chạy khi seed hoặc thay tài liệu)

```text
FAQ/Policy Markdown
   → Load → Chunk → Embed → PostgreSQL pgvector
```

### Chat runtime

```text
User message → FastAPI → LangGraph Agent
   ├── search_knowledge_base → Embed query → pgvector search
   └── get_order_status → SQL truy vấn order theo DEMO_CUSTOMER_ID
→ Agent tổng hợp → Answer + Sources + Tools Used → Frontend
```

### LangGraph workflow tối giản

```mermaid
flowchart LR
    S([START]) --> A[Agent node]
    A --> Q{Tool call?}
    Q -->|Có| T[ToolNode]
    T --> A
    Q -->|Không| E([END])
```

- Hai tool: `search_knowledge_base(query)` và `get_order_status(order_id)`.
- Không cần planner, supervisor hay multi-agent.
- Dùng in-memory checkpointer cho local demo; history mất khi process restart. Nếu deploy miễn phí có sleep/restart thì **không đảm bảo memory bền vững**.
- Giới hạn số vòng gọi tool và request timeout để tránh loop.

---

## 6. Dataset giả lập (tạo khi đến Day 2)

| Nhóm | Quy mô dự kiến | Lưu ở đâu | AI dùng như thế nào |
|---|---:|---|---|
| FAQ | 30 câu | Markdown → `knowledge_chunks` | RAG |
| Policies | 5–7 tài liệu | Markdown → `knowledge_chunks` | RAG |
| Products | 30 sản phẩm | PostgreSQL | Dashboard / chi tiết order |
| Customers | 20 khách hàng | PostgreSQL | Quan hệ dữ liệu demo |
| Orders | 100 đơn hàng + items | PostgreSQL | Agent tool / dashboard |

- Chủ đề: vận chuyển, giao trễ, hủy đơn, trả hàng/hoàn tiền, bảo hành, thanh toán, điều kiện đổi trả.
- Dữ liệu **tiếng Việt**, được viết riêng, thống nhất về chính sách và trạng thái đơn hàng.
- Đơn hàng/customer/product là dữ liệu quan hệ, **không cần embedding**.
- Dataset chưa được tạo trong bước lập kế hoạch này.

---

## 7. API contract dự kiến

**Base URL:** `/api/v1`

| Method | Endpoint | Mục đích |
|---|---|---|
| `GET` | `/health` | Health check (có thể đặt ngoài prefix v1) |
| `GET` | `/api/v1/orders` | Danh sách đơn hàng của demo customer |
| `GET` | `/api/v1/orders/{order_id}` | Chi tiết một đơn hàng thuộc demo customer |
| `GET` | `/api/v1/knowledge` | Danh sách FAQ/policy hiển thị trên UI |
| `POST` | `/api/v1/chat` | Chat với LangGraph Agent |

**Chat request:**

```json
{
  "session_id": "demo-session-001",
  "message": "Đơn ORD-002 đã gửi đi rồi, tôi có hủy được không?"
}
```

**Chat response (ví dụ):**

```json
{
  "answer": "Đơn ORD-002 đang được vận chuyển nên không thể hủy trực tiếp theo chính sách hiện tại.",
  "sources": [
    {
      "document_id": "cancellation_policy",
      "title": "Chính sách hủy đơn hàng"
    }
  ],
  "tools_used": ["get_order_status", "search_knowledge_base"]
}
```

- `sources` và `tools_used` lấy từ kết quả thực thi tool, không để LLM tự bịa metadata.
- Đối với order không thuộc demo customer: trả `404` chung, không lộ thông tin khách hàng khác.
- FE và BE phát triển độc lập dựa trên contract này.

---

## 8. Kế hoạch 8 ngày

| Ngày | Chủ đề | Việc chính | Deliverable / Done when |
|---|---|---|---|
| **Day 1** | Setup & database | Tạo **2 repos**, cấu hình FastAPI, React/Vite, Postgres/pgvector, `.env.example`, CORS local | FE và BE chạy độc lập; BE kết nối DB; FE gọi được `/health` |
| **Day 2** | Dataset & basic APIs | Soạn mock data tiếng Việt; migration/seed; Orders + Knowledge APIs | Danh sách/chi tiết order và metadata knowledge có thể truy vấn qua Swagger |
| **Day 3** | Embedding & Vector Search | Markdown loader, chunking, embeddings, insert/upsert pgvector, search top-k | Query tiếng Việt tìm đúng chính sách; chạy ingest lại không tạo trùng |
| **Day 4** | RAG | LangChain retriever + LLM + system prompt + source references | FAQ/policy Q&A có nguồn, thiếu tài liệu thì không tự khẳng định |
| **Day 5** | Agent & LangGraph | Tạo 2 tools, ToolNode, memory/session, kết hợp Order + Policy | Agent chọn đúng tool và xử lý được câu hỏi cần cả 2 tools |
| **Day 6** | Frontend dashboard | Orders list/detail, Knowledge page, Chat UI, gọi API BE | Demo flow đầy đủ trên browser local |
| **Day 7** | Integration & Evaluation | 20 test cases, kiểm tra đúng tool, grounding, isolation và lỗi API/CORS | Có kết quả evaluation; không rò dữ liệu order khác customer |
| **Day 8** | Polish & documentation | README **cho cả 2 repo**, diagram, screenshots, quickstart, demo script | MVP chạy local và có thể trình diễn end-to-end |

**Day 9 (optional):** Deploy FE lên Cloudflare, BE lên Render, DB lên Supabase; chỉnh URL/CORS, thử nghiệm demo public. **Deploy không phải điều kiện bắt buộc để hoàn thành mục tiêu AI.**

### Các milestone

- **M1 — Day 4:** RAG hỏi đáp chính sách hoạt động.
- **M2 — Day 5:** LangGraph Agent gọi đúng tool, kết hợp order + policy.
- **M3 — Day 8:** Dashboard + BE + AI hoàn chỉnh, có tests và tài liệu.

---

## 9. Deployment dự kiến (ưu tiên free tier, không ràng buộc thiết kế)

| Thành phần | Dịch vụ dự kiến | Ghi chú |
|---|---|---|
| FE (`shopmate-ai-frontend`) | **Cloudflare Workers Static Assets / Pages** | Deploy riêng từ FE repo; host SPA tĩnh |
| BE (`shopmate-ai-backend`) | **Render Free** hoặc Python hosting tương đương | Chạy FastAPI; miễn phí có giới hạn và sleep/cold start |
| Database | **Supabase Free** (PostgreSQL + pgvector) | Kiểm tra quota, project pause và connection settings lúc deploy |
| AI API | **OpenAI API** | Có thể phát sinh phí theo token; không thuộc free cloud hosting |

**Không ưu tiên chạy FastAPI + LangGraph trên Cloudflare Workers** ở MVP vì tính tương thích Python runtime/dependencies cần được kiểm chứng; không nên đánh đổi stack AI để ép toàn bộ lên Cloudflare.

### Cấu hình env giữa hai repo

**Backend `.env.example`:**

```dotenv
DATABASE_URL=postgresql://shopmate:local_dev_only@localhost:5432/shopmate
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DEMO_CUSTOMER_ID=1
CORS_ORIGINS=http://localhost:5173
```

**Frontend `.env.example`:**

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

- FE deploy: cập nhật `VITE_API_BASE_URL` thành HTTPS URL của BE; biến `VITE_*` **public** và được đóng gói vào FE build, không chứa secret.
- BE deploy: đặt `CORS_ORIGINS` bằng origin Cloudflare thực tế, không dùng `*` cho production demo.
- Không commit `.env`, API key hoặc database credentials.
- Kiểm tra các điều khoản/quota free tier tại thời điểm triển khai vì có thể thay đổi.

---

## 10. Evaluation & tiêu chí hoàn thành

**Bộ eval:** khoảng 20 tình huống, gồm FAQ, policy, order lookup, câu hỏi kết hợp, order không tồn tại, order thuộc customer khác, câu hỏi ngoài tài liệu và prompt injection đơn giản.

**Đánh giá tối thiểu:**

1. RAG lấy được đoạn chính sách liên quan (manual check hoặc expected document IDs).
2. Agent dùng đúng tool(s): FAQ → knowledge; order → order; combined → cả hai.
3. Answer chỉ khẳng định thông tin có trong dữ liệu/tool output; trả lời không biết nếu thiếu chứng cứ.
4. Order lookup chỉ trả dữ liệu thuộc demo customer (test truy cập trái phép bắt buộc pass 100%).
5. Không tự tuyên bố đã hủy hoặc hoàn tiền vì MVP chỉ có read-only tools.
6. FE/BE hoạt động với hai origin khác nhau, không lỗi CORS khi cấu hình đúng.

**Mục tiêu tham khảo:** tối thiểu 17/20 test cases đạt tiêu chí chức năng; lỗi lộ thông tin đơn hàng phải bằng 0.

### Definition of Done

- [ ] Repo BE chứa API, LangGraph, RAG pipeline, migrations/seeds, tests, README.
- [ ] Repo FE chứa dashboard + AI Chat, API client, README.
- [ ] `docker compose up` chạy được Backend và DB tại local; FE chạy `npm run dev`.
- [ ] Ingest tài liệu thành embeddings, semantic search chạy đúng.
- [ ] Chat trả lời FAQ/policy, trạng thái order và câu hỏi kết hợp.
- [ ] Chat hiển thị nguồn khi dùng RAG.
- [ ] Demo customer không xem được order của customer khác.
- [ ] Bộ evaluation cơ bản có kết quả được ghi trong README.
- [ ] Có hướng dẫn chạy **cả 2 repo cùng nhau**.

---

## 11. Future improvements (ngoài MVP)

1. Persistent LangGraph memory (PostgreSQL checkpointer).
2. Structured observability/tracing và Agent debug UI.
3. RAG evaluation định lượng, hybrid search hoặc reranking nếu thực sự cần.
4. Streaming responses bằng SSE.
5. Xác thực user thật và customer-scoped data access.
6. Human approval trước khi thực hiện hủy đơn, đổi trạng thái hay refund.

---

## 12. Nguyên tắc triển khai

- **AI-first:** Làm Embedding → Vector Search → RAG → Agent → LangGraph → Evaluation theo thứ tự.
- **One backend:** Toàn bộ business logic và AI trong FastAPI, không tạo thêm Go/Python service.
- **Two independent repos:** FE/BE độc lập để dễ deploy, chỉ giao tiếp bằng REST/OpenAPI contract.
- **One database:** PostgreSQL dùng cho cả relational data và pgvector.
- **Data-first:** Dùng bộ dữ liệu giả lập tiếng Việt có logic nghiệp vụ nhất quán; chưa cần crawler.
- **Minimal MVP:** Không thêm framework, service hoặc infrastructure nếu chưa giải quyết nhu cầu hiện tại.

**Kết quả cuối cùng:** Hai GitHub repos riêng biệt, một ứng dụng ShopMaffte AI demo end-to-end trên local, thể hiện rõ hiểu biết về RAG, Agent, LangGraph và kỹ năng tích hợp Full-stack.