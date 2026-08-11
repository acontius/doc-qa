### What did we do and want to do...

**This is My interview project for Roshan company...**

For this project we have 9 Milestones. at least till now. i dont know what am i going to do in next few minutes **:)**.
list of milestones :
1) Infrastructure
2) Document Management
3) Chunking & Embeddings
4) Retrieval
5) LLM / RAG
6) Question History
7) Complete API & Documentation
8) Tests & Sample Data
9) Finalization


### so why are they so many ? 
cause i thought the **smaller** the problem is, the **easier it is to solve**.

## Important
in the whole project we have simplicity instead of complexity with over engineering cause we have 7 day deadline. 

# Lets Start
## Infrastructure
project is based on the Django framework. so lets install dependecies.

```bash
pip install requirements.txt
```

you shall do this a lil later. to do this we have to know what we want. 

my DBMS Stack is PostgreSQL, backend was forced to Django5.x.

you may install postgresql on arch by:
```bash 
sudo pacman -S postgresql
```
and django by :
```bash 
pip install django
```

then we had to conect them toghether :
1) added requirement information for this action to my `.env` so the information stay safe. and filled it with required data:
```md
# PostgreSQL
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
```
then went to settings.py to continue the process and tell django to know where to look at:
```python 
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "document_qa"),
        "USER": os.getenv("POSTGRES_USER", "document_qa"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "document_qa"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}
```

after stablishing the connection i set some urls to check if everything is ok and created a superuser as the doc say's.
now we have some endpoints to check everything such as swagger_ui.

available endpoint are :
```link
https://my-domain:my-port/api/health
https://my-domain:my-port/api/doc
https://my-domain:my-port/schema
https://my-domain:my-port/admin
```

[health endpoint](https://my-domain:my-port/api/health) will check if the LLM, Database, Django ... are connected.

then we have [schema](https://my-domain:my-port/schema) which is used to get the openai setting.

take a look at [doc](https://my-domain:my-port/api/doc) and you will found out quickly that it is the famous `Swagger`.

the last one is [admin](https://my-domain:my-port/admin) which you may login whith it and enjoy **POWER**.

#### END OF Milestone1-Infrastructure
---

### Welcome to second Milestone-Document Ingestion Subsystem
**at the end of this milestone we shall**:
```http
POST   /api/documents/
GET    /api/documents/
GET    /api/documents/{id}/
PATCH  /api/documents/{id}/
DELETE /api/documents/{id}/
POST   /api/documents/{id}/reindex/
```
Upload a file(.docx) and save it to Database.
```tree
Document
├── title
├── file
├── full_text
├── chunk_count
└── embedding_model

DocumentChunk
├── document
├── chunk_index
├── text
└── embedding[384]
```

my choises are : 
- Docx Parser 
    - python-docx 
        - because we only have docx and there is no need for extra dependecies.

- Chunking 
    - RecursiveCharacterTextSplitter\
        - cause it tries to split meaningful
    - chunk_size=1000
        - don't want chunks to be so big so each chunk contains multi subjects and neither want it to be so small so the context split too much.
    - chunk_overlap=200
        - 20% overlap is OK i thought

- Embedding
    - sentence-transformers
    - paraphrase-multilingual-MiniLM-L12-v2
        - Supportss Persian
    - 384 dimensions(because of the model)

- Vector DB 
    - PostgreSQL + pgvector
        - Cause it came for postgres to solve the saving embeding problem.
    


the whole pipeline is somthing like :
```
                    DOCX
                     │
                     ▼
              Upload validation
                     │
          ┌──────────┴──────────┐
          │                     │
       size/type             valid DOCX?
          │                     │
          └──────────┬──────────┘
                     ▼
              DOCX extraction
                     │
          paragraphs + tables
                     │
                     ▼
              normalized text
                     │
                     ▼
               full_text
                     │
                     ▼
        RecursiveCharacterTextSplitter
                     │
                     ▼
                  chunks
                     │
                     ▼
          SentenceTransformer
                     │
                     ▼
             384-dim vectors
                     │
                     ▼
              PostgreSQL
                 + pgvector
                     │
             ┌───────┴───────┐
             ▼               ▼
          Document      DocumentChunk
```

```
Document → Extraction → Chunk → Embedding → pgvector
```

view shall not do : 
- extract
- chunk
- embed
- save
- and ...

it must just go for :
validating request -> call servieces -> return response
                      
                            ^
                            | 
                      
                      prepare document
                      
                      save document
                      
                      replace chunks
                      
                      delete old file

we are going to save docs with UUID or our valid names to reduce `conflicts` and `file upload` attack vulnerability.

something like : `documents/2026/08/1234...4321.docs`

<font color=red size=6>BUT</font>
we wont stick only to that and will try to check i multiple time. even  checking extension is not enougth cause `attacker.php.docx` is still a docx and still vulnerable.

so :
```
extension check
        +
size check
        +
ZIP/OOXML structure
        +
python-docx parsing
```

What we have done till this commit is :
```
M2-A  Document model + migrations       ✅
M2-B  DOCX validation                   ✅
M2-C  DOCX extraction                   ✅
M2-D  Chunking                          ✅
M2-E  Embedding service                  ← NEXT
M2-F  pgvector storage                   ←
M2-G  Reindex lifecycle                  ←
M2-H  Retrieval                          ←
M2-I  API hardening                      ←
M2-J  Integration tests                  ←
```

