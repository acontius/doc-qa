# 📚 Document Q&A — Persian RAG System

> A simple, Dockerized Django-based Document Q&A system built around **DOCX ingestion, multilingual embeddings, PostgreSQL + pgvector, hybrid retrieval, and grounded LLM generation**.

This project was built as an interview project for **Roshan AI**.

The main idea is simple:

> Give the system some documents → index them → ask questions → get answers based only on those documents.

Repository:

👉 https://github.com/acontius/doc-qa

---

# 🧠 What is this project?

Document Q&A is a Retrieval-Augmented Generation (RAG) system.

Instead of sending an entire document to an LLM and hoping that it knows what to do, the system first turns the documents into searchable pieces.

The high-level workflow is:

```text
                 ┌─────────────────────┐
                 │      DOCX File      │
                 └──────────┬──────────┘
                            │
                            ▼
                     Text Extraction
                            │
                            ▼
                         Chunking
                            │
                            ▼
                        Embedding
                            │
                            ▼
                    PostgreSQL + pgvector
                            │
                            │
                       User Question
                            │
                            ▼
                       Embedding
                            │
                            ▼
                     Vector Retrieval
                            │
                            ▼
                    Hybrid Re-ranking
                            │
                            ▼
                      Relevant Context
                            │
                            ▼
                           LLM
                            │
                            ▼
                    Grounded Answer
````

The important part is that the LLM is **not supposed to answer from its own knowledge**.

It receives the question together with retrieved document context and is instructed to answer only from that context.

If useful information cannot be found:

```text
در اسناد ارائه‌شده پاسخی یافت نشد.
```

---

# 🎯 Project Goals

The project was designed with a few very explicit goals:

* Support `.docx` documents.
* Extract and store the complete document text.
* Split documents into meaningful chunks.
* Generate multilingual embeddings.
* Store embeddings inside PostgreSQL using `pgvector`.
* Retrieve relevant chunks for a question.
* Combine semantic similarity with simple keyword overlap.
* Send only retrieved context to the LLM.
* Generate Persian answers.
* Store complete Q&A history.
* Expose the functionality through a REST API.
* Provide Swagger/OpenAPI documentation.
* Provide Django Admin as the only UI.
* Run the whole project through Docker.
* Keep the architecture simple and understandable.

The most important engineering decision was:

> **Prefer simplicity and maintainability over unnecessary infrastructure.**

This was an intentionally small project with a limited development window, so technologies such as Celery, Redis, RabbitMQ, Kubernetes, GraphQL, separate frontend applications, or external vector databases were intentionally avoided.

---

# 🧩 Why are there so many Milestones?

The project was divided into smaller milestones because solving a smaller problem is easier than solving one huge problem.

The development was split into:

1. Infrastructure
2. Document Ingestion
3. Retrieval
4. LLM / RAG
5. Question History
6. Complete API & Documentation
7. Tests & Sample Data
8. Finalization

The milestones are not independent applications.

They progressively build one pipeline:

```text
Infrastructure
      │
      ▼
Document Ingestion
      │
      ▼
Retrieval
      │
      ▼
LLM / RAG
      │
      ▼
Question History
      │
      ▼
Complete API
      │
      ▼
Tests / Sample Data
      │
      ▼
Finalization
```

---

# 🏗️ Architecture

The project follows a relatively simple layered architecture.

```text
                     REST API
                        │
                        ▼
              ┌───────────────────┐
              │      Views        │
              │   / ViewSets      │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │   Serializers     │
              │    Validation     │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │     Services      │
              │  Business Logic   │
              └───────┬─────┬─────┘
                      │     │
              ┌───────┘     └────────┐
              ▼                       ▼
        Document Pipeline        RAG Pipeline
              │                       │
              ▼                       ▼
         PostgreSQL              pgvector + LLM
```

A key architectural rule is:

> Views should not contain business logic.

A view should mostly do:

```text
validate request
      ↓
call service
      ↓
return response
```

It should not manually:

* extract DOCX files
* chunk text
* generate embeddings
* perform vector queries
* call the LLM
* manage transactional ingestion

Those responsibilities belong in the service layer.

---

# 📁 Project Structure

```text
doc-qa/
│
├── apps/
│   └── documents/
│       ├── admin.py
│       ├── apps.py
│       ├── forms.py
│       ├── models.py
│       ├── serializers.py
│       ├── services.py
│       ├── urls.py
│       ├── views.py
│       ├── tests.py
│       └── migrations/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── roshan/
│   └── assets/
│       └── Images/
│
├── media/
│
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

The important application code lives under:

```text
apps/documents/
```

The project intentionally keeps the application structure small.

---

# 🛠️ Technology Stack

| Component           | Technology                               |
| ------------------- | ---------------------------------------- |
| Backend             | Django 5.x                               |
| API                 | Django REST Framework                    |
| API Docs            | drf-spectacular / Swagger UI             |
| Database            | PostgreSQL                               |
| Vector Search       | pgvector                                 |
| DOCX parsing        | python-docx                              |
| Chunking            | LangChain RecursiveCharacterTextSplitter |
| Embeddings          | sentence-transformers                    |
| Embedding model     | `paraphrase-multilingual-MiniLM-L12-v2`  |
| Embedding dimension | 384                                      |
| LLM communication   | LangChain + OpenAI-compatible API        |
| LLM provider        | OpenRouter                               |
| Containerization    | Docker / Docker Compose                  |
| Production server   | Gunicorn                                 |
| Configuration       | `.env`                                   |

---

# 🚀 Running the Project

## Option 1 — Docker

The intended deployment path is Docker.

Copy the environment template:

```bash
cp .env.example .env
```

Then configure the required values.

Start the application:

```bash
docker compose up --build
```

After the containers are running:

```bash
docker compose exec web python manage.py migrate
```

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

The application should then be available at:

```text
http://127.0.0.1:8000/
```

---

# 🧪 Local Development

A local Python environment can also be used.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Run Django:

```bash
python manage.py runserver
```

---

# ⚙️ Environment Variables

The project does not hard-code secrets.

The main configuration is supplied through `.env`.

Example:

```env
DJANGO_SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=doc_qa
POSTGRES_USER=doc_qa
POSTGRES_PASSWORD=doc_qa
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=
OPENROUTER_TIMEOUT=60

OPENROUTER_HTTP_REFERER=http://127.0.0.1:8000
OPENROUTER_X_TITLE=Document Q&A

EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384

CHUNK_SIZE=1000
CHUNK_OVERLAP=200

RETRIEVER_TOP_K=6
RETRIEVER_CANDIDATE_MULTIPLIER=3

MAX_UPLOAD_SIZE_MB=10
```

`.env` should never be committed.

Only `.env.example` belongs in Git.

---

# 1️⃣ Milestone 1 — Infrastructure

The first milestone established the foundation.

The project needed:

* Django
* PostgreSQL
* environment-based configuration
* REST API
* API documentation
* Django Admin
* health checking
* Docker support

The main infrastructure endpoints are:

```text
GET /api/health/
GET /api/schema/
GET /api/docs/
```

and:

```text
/admin/
```

---

## Health Check

The health endpoint exists so the application can quickly report whether its important dependencies are configured and reachable.

```text
GET /api/health/
```

This is useful both during development and deployment.

---

## Swagger

Swagger/OpenAPI is available through:

```text
/api/docs/
```

It provides an interactive way to inspect and test the REST API.

![Swagger](roshan/assets/Images/swagger-milestone2.png)

---

# 2️⃣ Milestone 2 — Document Ingestion

This is where the actual document pipeline was built.

The goal was:

```text
DOCX
 ↓
Validation
 ↓
Extraction
 ↓
Chunking
 ↓
Embedding
 ↓
pgvector
```

---

# 📄 Document Model

A document stores:

```text
Document
├── id
├── title
├── file
├── full_text
├── chunk_count
├── embedding_model
├── created_at
└── updated_at
```

The chunks are stored separately:

```text
DocumentChunk
├── id
├── document
├── chunk_index
├── text
├── embedding[384]
└── created_at
```

The current implementation uses a PostgreSQL vector field with 384 dimensions. The chunk table also has a uniqueness constraint over `(document, chunk_index)`. 

---

# 📤 DOCX Validation

Simply checking:

```text
filename.endswith(".docx")
```

is not enough.

The ingestion pipeline therefore validates multiple properties:

```text
Extension
   +
File size
   +
DOCX / OOXML structure
   +
python-docx parsing
```

This helps reject:

* empty files
* corrupted DOCX files
* invalid ZIP/OOXML structures
* incorrect extensions
* oversized uploads

The upload path is also generated by the application rather than trusting the user's filename. The current implementation uses a date-based path and UUID filename:

```text
documents/YYYY/MM/<uuid>.docx
```

This avoids filename collisions and reduces reliance on user-controlled filenames. 

---

# 📝 DOCX Extraction

`python-docx` is used because the project only needs DOCX support.

The extractor collects:

* paragraphs
* table content

The resulting text is normalized before it is stored.

The full extracted text is stored in:

```text
Document.full_text
```

This is important because the original document content remains available even after chunking.

---

# ✂️ Chunking

The project uses:

```text
RecursiveCharacterTextSplitter
```

with:

```text
chunk_size = 1000
chunk_overlap = 200
```

The reason is straightforward.

If chunks are too large:

```text
less precise retrieval
more irrelevant context
```

If chunks are too small:

```text
context gets fragmented
semantic meaning can be lost
```

The 200-character overlap helps preserve context between adjacent chunks.

Empty chunks are removed.

---

# 🧠 Embeddings

The embedding model is:

```text
sentence-transformers/
paraphrase-multilingual-MiniLM-L12-v2
```

The important reason for choosing this model was Persian/multilingual support while keeping the model relatively lightweight.

Its embedding size is:

```text
384
```

Therefore:

```python
VectorField(dimensions=384)
```

is used in PostgreSQL.

The embedding service is implemented as a singleton.

The idea is simple:

> Loading a transformer model repeatedly for every request would be unnecessarily expensive.

Instead, the model is loaded once and reused.

---

# 🗄️ PostgreSQL + pgvector

Instead of introducing a separate vector database, embeddings are stored directly in PostgreSQL.

This was an intentional trade-off.

### Advantages

* one database
* simpler deployment
* fewer dependencies
* transactions cover normal database writes
* vector data lives next to document metadata
* PostgreSQL already exists in the stack

The project uses `pgvector` and an HNSW index with cosine distance. The current model definition uses `vector_cosine_ops` for the HNSW index. 

---

# 🔄 Ingestion Lifecycle

Creating a document roughly follows:

```text
Upload
  ↓
Validate
  ↓
Save document
  ↓
Extract
  ↓
Chunk
  ↓
Embed
  ↓
Store chunks + vectors
```

Updating a title only does not require re-indexing.

Updating the actual file does:

```text
New file
 ↓
Validate
 ↓
Extract
 ↓
Chunk
 ↓
Embed
 ↓
Replace old chunks
 ↓
Delete old file
```

Reindexing:

```text
Existing file
 ↓
Extract
 ↓
Chunk
 ↓
Embed
 ↓
Replace chunks
```

Deleting a document removes:

```text
Document
 +
DocumentChunks
 +
uploaded file
```

---

# 🛡️ Failure Handling

Ingestion is a multi-step operation.

A failure could happen after:

```text
DB write
```

but before:

```text
embedding
```

or after:

```text
file storage
```

but before:

```text
chunk creation
```

Therefore the service layer uses transactions and cleanup logic so that partial ingestion does not leave the database in an inconsistent state.

This is one of the reasons ingestion logic belongs in the service layer rather than inside the view.

---

# 3️⃣ Milestone 3 — Retrieval

Once documents are indexed, the system needs to answer:

> Which chunks are relevant to this question?

The retrieval pipeline is:

```text
Question
   ↓
Question embedding
   ↓
pgvector candidate search
   ↓
Vector similarity
   +
Keyword overlap
   ↓
Hybrid score
   ↓
Top-K chunks
```

---

# 🔎 Candidate Retrieval

The configured value is:

```text
RETRIEVER_TOP_K=6
```

But the system retrieves more candidates first.

By default:

```text
candidate_multiplier = 3
```

Therefore:

```text
6 × 3 = 18 candidates
```

are considered before final ranking.

The reason is that the first vector search is treated as candidate generation rather than the final ranking stage.

---

# 📐 Hybrid Ranking

Two signals are used.

## Vector Score

The pgvector distance is converted into:

```text
vector_score = 1 / (1 + distance)
```

---

## Keyword Score

A simple Unicode-aware tokenizer extracts words from the question and chunk.

Then:

```text
keyword_score =
    overlap(question_terms, chunk_terms)
    /
    max(1, len(question_terms))
```

---

## Final Score

The final score is:

```text
final_score =
    0.7 × vector_score
    +
    0.3 × keyword_score
```

This gives semantic similarity more importance while still rewarding direct lexical matches.

---

# 🇮🇷 Persian Support

The tokenizer normalizes Persian characters and supports mixed Persian/English text.

For example:

```text
ی
ي
```

and:

```text
ک
ك
```

can be normalized.

Punctuation is ignored.

This matters because the project is intended to work with Persian documents and Persian questions.

---

# 📑 Document Filtering

A question can optionally specify:

```json
{
  "document_ids": [1, 4, 7]
}
```

Then retrieval only considers chunks belonging to those documents.

If:

```json
"document_ids": null
```

is used, all indexed documents can participate.

---

# 4️⃣ Milestone 4 — LLM / RAG

This is where retrieval becomes an actual Q&A system.

The full workflow becomes:

```text
Question
   │
   ▼
Retrieve relevant chunks
   │
   ▼
Build context
   │
   ▼
Send question + context to LLM
   │
   ▼
Parse structured response
   │
   ▼
Return answer + sources
```

---

# 🤖 LLM

The project communicates with OpenRouter using an OpenAI-compatible API.

LangChain is used as the LLM communication layer.

This means the application does not hard-code itself to one particular model.

The model is configured using:

```env
OPENROUTER_MODEL=
```

and the API key:

```env
OPENROUTER_API_KEY=
```

This makes switching models much easier.

---

# 🧾 Grounded Prompt

The LLM is instructed to:

1. Answer only from retrieved context.
2. Answer in Persian.
3. Avoid hallucinating.
4. Return structured JSON.
5. Include source information.
6. Report confidence.

The expected structure is conceptually:

```json
{
  "answer": "...",
  "sources": [],
  "confidence": "low"
}
```

If the answer cannot be found in the provided context:

```text
در اسناد ارائه‌شده پاسخی یافت نشد.
```

---

# 🧠 Why RAG instead of sending the whole document?

Sending entire documents directly to an LLM has several problems:

* context can become too large
* irrelevant information is included
* retrieval is less precise
* cost can increase
* grounding becomes harder
* answers can become less reliable

RAG solves this by retrieving only the relevant parts.

```text
10,000 words document
        ↓
     chunking
        ↓
    20+ chunks
        ↓
   retrieve 6
        ↓
LLM sees relevant context
```

This is the main idea behind the project.

---

# 5️⃣ Milestone 5 — Question History

A Q&A system becomes much more useful when questions and answers are persistent.

The project therefore stores:

```text
Question
├── text
├── top_k
├── document_ids
└── created_at
```

and:

```text
Answer
├── question
├── text
├── raw_llm_output
├── confidence
├── sources_json
├── model_name
├── latency_ms
├── error
└── created_at
```

The relationship is:

```text
Question 1 ───── 1 Answer
```

The answer is therefore a snapshot of what happened at question time.

---

# 💾 Why store raw LLM output?

The parsed answer is not always enough.

If the LLM returns malformed JSON or unexpected output, storing:

```text
raw_llm_output
```

makes debugging possible.

It also provides visibility into model behavior.

---

# ⏱️ Why store latency?

The system records:

```text
latency_ms
```

because LLM requests can be slow.

This allows later analysis such as:

```text
Which model is faster?
How long does retrieval + generation take?
Did latency increase after changing the model?
```

---

# 6️⃣ Milestone 6 — Complete API & Documentation

The project exposes REST endpoints for the major operations.

---

## Health

```http
GET /api/health/
```

---

## Documents

```http
GET    /api/documents/
POST   /api/documents/
GET    /api/documents/{id}/
PATCH  /api/documents/{id}/
DELETE /api/documents/{id}/
POST   /api/documents/{id}/reindex/
```

---

## Retrieval

The retrieval endpoint allows testing the retrieval subsystem independently from generation.

Conceptually:

```text
Question
 ↓
Retriever
 ↓
Relevant chunks
```

This is useful for debugging the RAG pipeline.

---

## Questions

```http
GET  /api/questions/
POST /api/questions/
GET  /api/questions/{id}/
```

A question request can contain:

```json
{
  "question": "این سند درباره چیست؟",
  "top_k": 3,
  "document_ids": [1]
}
```

The result contains:

```json
{
  "question": "این سند درباره چیست؟",
  "answer": "...",
  "sources": [],
  "confidence": "low",
  "latency_ms": 1234
}
```

---

# 📚 Swagger / OpenAPI

Interactive API documentation:

```text
http://127.0.0.1:8000/api/docs/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

This was intentionally included so the API can be tested without needing a separate frontend.

---

# 7️⃣ Milestone 7 — Tests & Sample Data

Testing was not treated as an afterthought.

The test suite covers multiple layers.

---

# 🧪 Test Categories

### Document validation

Tests cover:

* invalid extension
* empty file
* oversized file
* corrupted DOCX
* invalid DOCX structure
* file position preservation

### Extraction

Tests cover:

* paragraphs
* tables
* whitespace normalization
* empty documents

### Chunking

Tests cover:

* configured chunk size
* overlap
* empty chunk removal
* invalid configuration

### Embedding

Tests cover:

* singleton behavior
* multiple inputs
* empty inputs
* model loading failure
* dimension mismatch
* invalid embedding shape

### Retrieval

Tests cover:

* top-k behavior
* document filtering
* empty document set
* invalid questions
* hybrid ranking
* vector scoring
* keyword scoring
* tokenizer behavior

### API

Tests cover:

* document CRUD
* reindex
* validation
* retrieval endpoint
* question endpoint
* question history

---

# 🔬 Integration Testing

One of the important tests goes beyond mocking the entire pipeline.

The real path is exercised:

```text
DOCX
 ↓
Extraction
 ↓
Chunking
 ↓
Real embedding model
 ↓
PostgreSQL
 ↓
pgvector
```

This is important because unit tests alone cannot prove that all pieces work together.

---

# 🌱 Sample Data

Sample data is useful for quickly testing the application after installation.

The project includes tooling for creating sample document data so the ingestion and retrieval pipeline can be tested without manually preparing documents every time.

---

# 8️⃣ Milestone 8 — Finalization

The final milestone focused on turning the implementation into something usable.

This included:

* API cleanup
* Swagger documentation
* Admin usability
* question history inspection
* document identification
* testing
* README/documentation
* Docker support
* cleanup of development workflow

The goal was not to add another large subsystem.

The goal was:

> Make the system understandable, testable and usable.

---

# 🖥️ Django Admin

The project intentionally does not introduce a separate frontend.

Django Admin acts as the operator UI.

```text
/admin/
```

From there documents and Q&A history can be inspected.

---

# 📄 Document Management

Documents can be inspected through:

```text
/admin/documents/document/
```

The admin view provides useful metadata including document IDs, which makes it easier to reference specific documents from the API.

---

# ❓ Question Management

Questions and answers can be inspected through:

```text
/admin/documents/question/
```

The question history provides visibility into:

* question text
* answer
* confidence
* sources
* model
* latency
* errors

This makes the Admin useful for debugging the RAG pipeline rather than being only a database CRUD interface.

---

# 📸 Screenshots

The repository contains screenshots showing the actual development and testing process.

---

## Document Upload — Persian DOCX

![Persian DOCX](roshan/assets/Images/entered-persian-dox.png)

---

## Document Upload — English DOCX

![English DOCX](roshan/assets/Images/entered-docx-eng.png)

---

## Swagger Document API

![Document API](roshan/assets/Images/entering-docx-api-page.png)

---

## Imported Data

![Imported data](roshan/assets/Images/db-checking-imported-datas.png)

---

## Stored Documents

![Stored documents](roshan/assets/Images/listed-inputed-datas.png)

---

## Stored Chunks and Embeddings

![Vector and chunk data](roshan/assets/Images/vector-dim-chunk-testing-saved-inputs.png)

---

## Checking Selected Data

![Selected data](roshan/assets/Images/checking-selected-data.png)

---

## Swagger / API Documentation

![Swagger](roshan/assets/Images/swagger-milestone2.png)

---

## Health Endpoint

![Health](roshan/assets/Images/Mile4-Health-working.png)

---

## RAG Response

![RAG response](roshan/assets/Images/response-of-RAG.png)

---

## Asking Questions

![Ask question](roshan/assets/Images/ask-questions-test.png)

---

## Answered Question

![Answered question](roshan/assets/Images/question-test-answered.png)

---

## Question History

![Answers list](roshan/assets/Images/answers-list.png)

---

## Admin Panel

![Admin panel](roshan/assets/Images/test-admin-panel.png)

---

# 🔐 Security Considerations

This project is not intended to be a complete production security platform, but several basic protections were deliberately implemented.

---

## File Validation

The system does not trust:

```text
filename
extension
content type
```

individually.

DOCX validation uses multiple checks.

---

## Server-generated filenames

Uploaded files are stored using application-generated paths rather than directly using user-provided filenames.

Conceptually:

```text
documents/
    2026/
        08/
            <uuid>.docx
```

The implementation generates this path from the current date and a UUID. 

---

## Upload Size

Uploads have a configurable maximum size:

```env
MAX_UPLOAD_SIZE_MB=10
```

---

## Secrets

Secrets belong in:

```text
.env
```

and not:

```text
source code
README
Git
```

---

# ⚖️ Important Engineering Trade-offs

This project intentionally does not try to be a giant enterprise RAG platform.

That was a feature, not a bug.

---

## PostgreSQL + pgvector vs Dedicated Vector DB

### Chosen

```text
PostgreSQL + pgvector
```

### Why?

Because we already need PostgreSQL.

Using another database would introduce:

```text
another service
another deployment
another connection
another failure point
```

For this project's size, pgvector is enough.

### Trade-off

A dedicated vector database may provide more specialized capabilities at very large scale.

But for this project:

```text
simplicity > unnecessary infrastructure
```

---

# 🧵 Synchronous Processing vs Celery

The system processes ingestion synchronously.

That means:

```text
upload
 ↓
extract
 ↓
embed
 ↓
save
 ↓
response
```

happens during the request.

### Why?

Because the project is intentionally simple.

Introducing:

```text
Celery
Redis
RabbitMQ
```

would significantly increase operational complexity.

### Trade-off

Large documents and many simultaneous users would eventually benefit from background processing.

That is a future improvement, not something needed for the current scope.

---

# 🧠 Local Embeddings vs API Embeddings

Embeddings are generated locally using:

```text
sentence-transformers
```

instead of a paid embedding API.

### Advantages

* no API cost
* no embedding network dependency
* consistent model
* privacy-friendly
* works offline after model download

### Trade-off

The model consumes local CPU/RAM and model loading takes time.

---

# 🌐 OpenRouter vs Hard-coded LLM Provider

The project uses an OpenAI-compatible interface through LangChain.

The actual model is configured using:

```env
OPENROUTER_MODEL=
```

This makes model switching easier.

The application does not need to know the internal implementation details of every provider.

---

# 🔎 Vector Search + Keyword Search

Pure vector search is good for semantic similarity.

But exact terms can still matter.

For example:

```text
"API version 3"
```

might benefit from exact lexical matching.

Therefore the project uses:

```text
70% semantic similarity
+
30% keyword overlap
```

This is not intended to compete with sophisticated learning-to-rank systems.

It is intentionally:

```text
simple
transparent
debuggable
```

---

# 🏛️ Why Services?

One of the most important architecture decisions is keeping business logic inside services.

For example:

```text
View
 ↓
Service
 ↓
Extraction
 ↓
Chunking
 ↓
Embedding
 ↓
Database
```

instead of:

```text
View
 ├── parse DOCX
 ├── chunk
 ├── embed
 ├── save
 ├── delete old file
 ├── rollback
 └── ...
```

This keeps views thin and makes the actual pipeline easier to test.

---

# 🧪 Why Mock LLM Calls in Tests?

Calling a real LLM for every test would be:

* slow
* unreliable
* dependent on network
* dependent on API availability
* potentially expensive

Therefore unit/API tests mock the LLM.

The real embedding integration path is tested separately where appropriate.

This gives us:

```text
fast deterministic tests
+
real integration coverage
```

instead of making the entire test suite depend on an external API.

---

# 🧱 Data Model

The main relationships are:

```text
Document
   │
   └──────< DocumentChunk


Question
   │
   └────── Answer
```

`DocumentChunk` uses:

```text
CASCADE
```

when its parent document is deleted.

This means stale chunks cannot remain after deleting their document.

The `(document, chunk_index)` pair is unique, preventing duplicate chunk indices within the same document. 

---

# 🔄 Complete RAG Workflow

The entire system can now be described in one diagram:

```text
                    ┌──────────────┐
                    │    DOCX      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Validation  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Extraction  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Chunking   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Embedding   │
                    └──────┬───────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │ PostgreSQL + pgvector   │
              └────────────┬────────────┘
                           │
                           │
                    User Question
                           │
                           ▼
                    ┌──────────────┐
                    │  Embedding   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Vector Search│
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │Hybrid Ranking│
                    └──────┬───────┘
                           │
                           ▼
                    Relevant Chunks
                           │
                           ▼
                    ┌──────────────┐
                    │     LLM      │
                    └──────┬───────┘
                           │
                           ▼
                 Grounded Persian Answer
                           │
                           ▼
                    Question + Answer
                         History
```

---

# 🧭 Typical User Journey

A normal user/operator workflow looks like this:

```text
1. Start application
       ↓
2. Open Swagger/Admin
       ↓
3. Upload DOCX
       ↓
4. Document is indexed
       ↓
5. Verify chunks/embedding
       ↓
6. Ask a question
       ↓
7. Retriever finds relevant chunks
       ↓
8. LLM generates grounded answer
       ↓
9. Sources are returned
       ↓
10. Question/Answer is persisted
```

---

# 🧪 Useful Manual Tests

After starting the application, a useful verification sequence is:

### 1. Health

```http
GET /api/health/
```

### 2. Open Swagger

```text
/api/docs/
```

### 3. Upload a DOCX

```http
POST /api/documents/
```

### 4. Check document list

```http
GET /api/documents/
```

### 5. Inspect a document

```http
GET /api/documents/{id}/
```

### 6. Test retrieval

Ask a question where the answer definitely exists inside the document.

### 7. Test RAG

Ask the same question through:

```http
POST /api/questions/
```

### 8. Test unsupported question

Ask something unrelated to the document.

The expected behavior is that the system should not invent an answer.

### 9. Check history

```http
GET /api/questions/
```

### 10. Inspect the answer

```http
GET /api/questions/{id}/
```

---

# 🧰 Useful Commands

Check Django:

```bash
python manage.py check
```

Create migrations:

```bash
python manage.py makemigrations
```

Apply migrations:

```bash
python manage.py migrate
```

Run tests:

```bash
python manage.py test apps.documents.tests -v 2
```

Run server:

```bash
python manage.py runserver
```

Create admin:

```bash
python manage.py createsuperuser
```

---

# 🐳 Docker Architecture

The Docker setup intentionally remains small.

Conceptually:

```text
Docker Compose
      │
      ├───────────────┐
      ▼               ▼
   Django          PostgreSQL
   + Gunicorn       + pgvector
      │
      │
      ├── media
      ├── staticfiles
      └── HF cache
```

The database uses:

```text
pgvector/pgvector:pg16
```

and the services are coordinated through Docker Compose.

Persistent volumes are used so database and relevant application data survive container recreation. 

---

# 📦 Why Docker?

Docker makes the environment reproducible.

Instead of requiring every developer to manually configure:

```text
PostgreSQL
pgvector
Python
dependencies
```

the application can be started using:

```bash
docker compose up --build
```

This is especially useful for interview/project delivery.

---

# 🚧 Current Limitations

This project intentionally has a limited scope.

Some things that are **not** implemented include:

* background task processing
* streaming LLM responses
* multi-user authorization
* advanced permission management
* OCR for scanned PDFs/images
* PDF ingestion
* advanced table understanding
* sophisticated reranking models
* conversation-aware multi-turn RAG
* distributed vector infrastructure
* production-scale observability
* sophisticated caching

These are possible future improvements.

---

# 🚀 Future Improvements

If this system needed to evolve beyond the current project, a reasonable roadmap would be:

### 1. Background ingestion

Move expensive ingestion into asynchronous workers.

```text
Upload
 ↓
Queue
 ↓
Worker
 ↓
Extract → Chunk → Embed
```

### 2. Better reranking

Replace the simple keyword component with a cross-encoder or dedicated reranker.

### 3. Better document parsing

Support:

```text
PDF
HTML
TXT
Markdown
```

and richer document structures.

### 4. Streaming answers

Allow users to receive generated tokens progressively.

### 5. Authentication

Introduce proper users, permissions and document ownership.

### 6. Observability

Add metrics for:

```text
retrieval latency
embedding latency
LLM latency
failure rate
token usage
```

### 7. Evaluation

Build a dataset containing:

```text
question
expected answer
expected source
```

and measure retrieval and generation quality automatically.

---

# 🎓 What I Learned From This Project

The most important lesson was that building a RAG system is not just:

```text
LLM + vector database
```

There are several independent engineering problems:

```text
file validation
      ↓
document extraction
      ↓
chunking
      ↓
embedding
      ↓
vector storage
      ↓
retrieval
      ↓
ranking
      ↓
context construction
      ↓
LLM generation
      ↓
structured parsing
      ↓
persistence
      ↓
API
      ↓
testing
```

Breaking the problem into milestones made each part much easier to reason about.

The other important lesson was:

> A simple architecture that you understand completely is usually better than a complicated architecture you cannot explain.

---

# 🏁 Final Architecture Summary

The final system can be summarized as:

```text
                    DOCUMENT SIDE

DOCX
 │
 ▼
Validation
 │
 ▼
Extraction
 │
 ▼
Chunking
 │
 ▼
Embedding
 │
 ▼
PostgreSQL + pgvector
 │
 └─────────────────────────┐
                           │
                           ▼
                    RETRIEVAL SIDE

Question
 │
 ▼
Embedding
 │
 ▼
Vector Candidates
 │
 ▼
Hybrid Ranking
 │
 ▼
Top-K Context
 │
 ▼
LLM
 │
 ▼
Grounded Answer
 │
 ▼
Question + Answer History
```

And the application architecture is:

```text
                 ┌───────────────┐
                 │    Django     │
                 └───────┬───────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
           REST API             Admin UI
              │                     │
              └──────────┬──────────┘
                         ▼
                    Service Layer
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       Document Pipeline         RAG Pipeline
             │                       │
             └───────────┬───────────┘
                         ▼
                  PostgreSQL
                         +
                      pgvector
```

---

# ❤️ Final Note

This project started as a relatively simple interview requirement:

> Build a document Q&A system.

Instead of trying to build everything at once, the problem was broken into smaller milestones.

That made it possible to understand every part of the system:

```text
Infrastructure
→ Ingestion
→ Retrieval
→ RAG
→ History
→ API
→ Testing
→ Finalization
```

The final result is intentionally not an over-engineered enterprise platform.

It is a small, understandable and extensible RAG application that demonstrates the complete path from:

```text
DOCX
```

to:

```text
Grounded Persian Answer
```

while keeping the underlying architecture simple enough to explain, test and maintain.

---

# 📜 License

This project was developed as an interview/project submission.

See the repository for the current project state:

👉 [https://github.com/acontius/doc-qa](https://github.com/acontius/doc-qa)