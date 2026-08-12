### Models
when selecting you must be awware of these parameters :
```
feature             |     shall be .
Pricing             |     must be free or suitable for your budget.
Context Length      |     atleast 8k(rather use +33k).
Language Support    |     must be multilingual or available for Persian.
Speed               |     at least it must be `Medium`.
Quality             |     atleast `Good`.
```

### Testing Models 
```
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "google/gemini-2.0-flash-exp:free",
    "messages": [
      {"role": "user", "content": "سلام، حالت چطوره؟"}
    ]
  }'
```


test site (plural test sites) **A place where products or weapons are tested**. The Nevada test site is contaminated with radiation after years of nuclear testing. (medicine) A clinic or office where medical testing takes place.