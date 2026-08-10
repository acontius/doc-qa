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

### Welcome to second Milestone-Document Management
