i set chunking size to `1000` which means chunk every doc to `n` chunks with 1000 characters. but there was a problem with that, that important information are not all in the same sentence or it can be spited right in the middle of a word so :   
we have chosen `RecursiveCharacterTextSplitter` cause it will try to end the chunk where it has a meaning(newlines, new paragraphs , ...).

if chunk size be too small it will separate context infos too much and if it gets too big, it may contains many subjects.

chunk overlap was set to 200! y?
it means neighbors have 200 chars in common. 
```
Chunk 1:
[------------------------------------------------]
0                                             1000


Chunk 2:
                    [-----------------------------------------------]
                    800                                      1800
                    ↑
                 overlap
```
to handle interrupted information.

## Retrieval 
```
                 5000 chunks
                      │
                      ▼
              Vector Search
                      │
                      ▼
                18 candidates
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
       Vector Score       Keyword Score
             │                 │
             └────────┬────────┘
                      ▼
                 Final Score
                      │
                      ▼
                  Top 6
                      │
                      ▼
                    LLM
```
we don't want our model to just output what looks alike our question, so we add a key word score to it so that affects the answers and return the one which is having our keyword.
```
vector_score = 1 / (1 + distance)
```
and 
```
keyword_score =
	    overlap(question_terms, chunk_terms)
    / max(1, len(question_terms))
```
then 
```
final_score =
    0.7 * vector_score
    +
	0.3 * keyword_score
```