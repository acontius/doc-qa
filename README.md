📄 Document Q&A — سامانه پرسش و پاسخ از اسناد
یک سامانه RAG (Retrieval-Augmented Generation) برای پرسش و پاسخ هوشمند از اسناد متنی فارسی و انگلیسی با استفاده از Django، LangChain، PostgreSQL/pgvector و مدل‌های زبانی OpenRouter.
🎯 هدف پروژه
این پروژه یک سیستم ساده، قابل‌اعتماد و قابل توسعه برای:

    📤 آپلود و مدیریت اسناد Word با پسوند docx
    📖 استخراج متن کامل اسناد شامل پاراگراف‌ها و جداول
    ✂️ تقسیم هوشمند متن به قطعات یا chunks
    🧠 تبدیل به بردار معنایی با مدل embedding محلی
    🔍 جست‌وجوی ترکیبی معنایی و کلیدواژه با reranking
    💬 تولید پاسخ دقیق فقط بر اساس محتوای اسناد بدون توهم‌بافی LLM
    📚 ذخیره تاریخچه پرسش‌ها و پاسخ‌ها
    📊 ذکر منابع برای هر پاسخ

رابط کاربری پروژه Django Admin است و فرانت‌اند جداگانه ندارد.
✨ قابلیت‌های اصلی
قابلیت
	
وضعیت
	
توضیحات
آپلود اسناد DOCX
	
✅
	
با اعتبارسنجی سایز و محتوا
استخراج متن کامل
	
✅
	
شامل پاراگراف و جداول
Chunking هوشمند
	
🔄
	
با overlap قابل تنظیم
Embedding محلی
	
🔄
	
با sentence-transformers
جست‌وجوی معنایی
	
🔄
	
با pgvector
Reranking ترکیبی
	
🔄
	
۰٪ معنایی + ۳۰٪ کلیدواژه
تولید پاسخ با LLM
	
🔄
	
از طریق OpenRouter
تاریخچه پرسش/پاسخ
	
🔄
	
با ذکر منابع
REST API کامل
	
✅
	
با Swagger UI
Docker Ready
	
✅
	
اجرای تک‌دستوری
✅ انجام شده | 🔄 در حال توسعه | ❌ هنوز شروع نشده
🛠️ Tech Stack
لایه
	
تکنولوژی
Backend
	
Python 3.12, Django 5.2, DRF 3.17
Database
	
PostgreSQL 16 + pgvector 0.5
LLM Provider
	
OpenRouter با مدل‌های رایگان
RAG Pipeline
	
LangChain 1.3 + langchain-text-splitters
Embeddings
	
sentence-transformers مدل multilingual با ۳۸۴ بُعد
ML Runtime
	
PyTorch 2.13 نسخه CPU
API Docs
	
drf-spectacular با OpenAPI 3 و Swagger
Containerization
	
Docker + docker-compose
Production Server
	
Gunicorn
🏗️ معماری سیستم

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29

جریان RAG هنگام پرسش سوال

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26

📋 پیش‌نیازها
برای اجرای Docker (تحویل نهایی و دفاع)

    Docker 24 به بالا
    Docker Compose V2
    حداقل 4GB RAM برای مدل embedding
    حدود 10GB فضای دیسک

برای توسعه روی Host

    Python 3.12 به بالا
    PostgreSQL 16 با افزونه pgvector
    pip

🚀 راه‌اندازی سریع با Docker
این روش برای تحویل نهایی و دفاع پروژه توصیه می‌شود:

1
2
3
4
5
6
7
8
9
10
11
12
13

Docker به صورت خودکار این مراحل را انجام می‌دهد:

    آماده‌سازی PostgreSQL + pgvector
    نصب dependency ها
    اجرای migration ها
    جمع‌آوری static files
    اجرای Gunicorn روی پورت 8000

ساخت کاربر admin

1

توقف و پاک‌سازی

1
2
3
4
5

💻 راه‌اندازی برای توسعه روی Host
اگر می‌خواهید خارج از Docker توسعه دهید:

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18

نکته مهم: فایل .env فقط یک بار هنگام استارت Django خوانده می‌شود. بعد از تغییر .env حتماً سرور را ریستارت کنید.
🔐 متغیرهای محیطی
متغیر
	
پیش‌فرض
	
توضیح
DJANGO_SECRET_KEY
	
-
	
در production الزامی
DEBUG
	
False
	
فقط در توسعه True
ALLOWED_HOSTS
	
localhost,127.0.0.1
	
دامنه‌های مجاز
POSTGRES_DB
	
doc_qa
	
نام دیتابیس
POSTGRES_USER
	
doc_qa
	
یوزر دیتابیس
POSTGRES_PASSWORD
	
doc_qa
	
در production تغییر دهید
POSTGRES_HOST
	
db
	
در Docker برابر db و روی host برابر 127.0.0.1
POSTGRES_PORT
	
5432
	
روی host مثلاً 5433
OPENROUTER_API_KEY
	
-
	
از openrouter.ai دریافت کنید
OPENROUTER_MODEL
	
-
	
مثلاً google/gemma-4-31b-it:free
EMBEDDING_MODEL
	
paraphrase-multilingual-MiniLM-L12-v2
	
مدل embedding
EMBEDDING_DIMENSION
	
384
	
باید با مدل embedding هم‌خوان باشد
CHUNK_SIZE
	
1000
	
اندازه هر chunk بر حسب کاراکتر
CHUNK_OVERLAP
	
200
	
هم‌پوشانی بین chunk ها
RETRIEVER_TOP_K
	
6
	
تعداد chunk های نهایی برای LLM
MAX_UPLOAD_SIZE_MB
	
10
	
حداکثر سایز فایل آپلودی
مدل‌های رایگان OpenRouter (تست‌شده در آگوست 2026)

1
2
3
4
5
6
7
8

هشدار: لیست مدل‌های رایگان OpenRouter مرتباً تغییر می‌کند. برای دیدن لیست به‌روز:

1
2

🌐 Endpoint ها و URL ها
URL
	
توضیح
/admin/
	
پنل مدیریت Django
/api/health/
	
بررسی وضعیت سیستم شامل DB و pgvector و LLM
/api/docs/
	
مستندات تعاملی Swagger
/api/schema/
	
خروجی OpenAPI schema
/api/documents/
	
CRUD اسناد شامل آپلود، لیست، ویرایش، حذف
/api/questions/
	
پرسش سوال و مشاهده تاریخچه
نمونه پاسخ /api/health/

1
2
3
4
5
6

    status برابر ok یعنی همه اجزا سالم هستند
    status برابر degraded یعنی یکی از اجزا مشکل دارد و جزئیات در فیلد مربوطه آمده است

🧪 تست و بررسی
بررسی سلامت سیستم

1

آپلود سند

1
2
3

پرسش سوال

1
2
3

اجرای تست‌ها

1
2
3
4
5

📊 وضعیت Milestone ها

    Milestone 1 — زیرساخت: Docker، PostgreSQL، DRF، Health API، Swagger
    Milestone 2 — مدیریت اسناد: مدل، آپلود، استخراج متن، Admin
    Milestone 3 — Chunking و Embeddings
    Milestone 4 — Retrieval و Reranking
    Milestone 5 — LLM و RAG با OpenRouter
    Milestone 6 — تاریخچه پرسش و پاسخ
    Milestone 7 — تکمیل API و مستندات
    Milestone 8 — تست‌ها و داده نمونه
    Milestone 9 — نهایی‌سازی، اسکرین‌شات‌ها و ارائه

🔒 امنیت
این پروژه از اصول OWASP Top 10 پیروی می‌کند:

    جلوگیری از SQL Injection با استفاده انحصاری از Django ORM
    مدیریت Secrets فقط از طریق .env و هرگز داخل کد یا گیت
    اعتبارسنجی همه ورودی‌ها با DRF serializers
    امنیت آپلود فایل: whitelist فقط docx و محدودیت سایز
    فعال بودن CSRF Protection
    فعال بودن XSS Protection با SecurityMiddleware
    فعال بودن Clickjacking Protection با XFrameOptionsMiddleware

برای production حتماً این موارد اضافه شود:

    DEBUG=False
    SECRET_KEY قوی و تصادفی
    HTTPS با Nginx و Let's Encrypt
    Rate Limiting
    احراز هویت کاربران نهایی

🐛 عیب‌یابی
خطای NameError: name 'settings' is not defined
علت: فراموش شدن import در بالای فایل. راه‌حل:

1

دیتابیس وصل نمی‌شود

1
2
3
4
5

مقدار llm_configured برابر false است
فایل .env فقط هنگام استارت خوانده می‌شود. بعد از تغییر آن:

1
2
3
4
5

مدل OpenRouter خطای 404 یا 402 می‌دهد
لیست مدل‌های رایگان تغییر کرده است. با دستور curl بالا یک مدل رایگان جدید پیدا کنید و در .env بگذارید.
اولین دانلود مدل embedding طولانی است
طبیعی است. مدل حدود 120 مگابایت است و در volume مربوط به hf_cache ذخیره می‌شود؛ اجراهای بعدی سریع خواهند بود.
📁 ساختار پروژه

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19

🎓 توضیح تصمیمات فنی مهم
چرا pgvector به جای Pinecone یا Weaviate؟

    یکپارچه با PostgreSQL؛ یک دیتابیس به جای دو سیستم جدا
    بدون هزینه SaaS
    ساده‌تر برای deploy با Docker
    کاملاً کافی برای حجم داده این پروژه

چرا Embedding محلی به جای سرویس ابری؟

    رایگان و بدون هزینه API
    بدون تأخیر شبکه
    حفظ حریم خصوصی؛ متن اسناد جایی ارسال نمی‌شود

چرا Django Admin به جای فرانت‌اند جداگانه؟

    مطابق صورت‌مسئله پروژه
    صرفه‌جویی در زمان با مهلت ۷ روزه
    battle-tested و امن
    تمام عملیات CRUD به صورت آماده

چرا Reranking ترکیبی ۷۰٪ برداری و ۳۰٪ کلیدواژه؟

    جست‌وجوی برداری گاهی کلمات کلیدی دقیق را نادیده می‌گیرد
    هم‌پوشانی کلیدواژه به ویژه برای متن فارسی کمک‌کننده است
    فرمول ساده، قابل تفسیر و قابل تنظیم
    سربار محاسباتی ناچیز

📦 موارد تحویل

    ✅ سورس کد کامل پروژه
    ✅ Dockerfile و docker-compose.yml
    ✅ مستندات API با Swagger و OpenAPI
    ✅ README با راهنمای نصب کامل
    ⏳ اسکرین‌شات از پنل مدیریت
    ⏳ داده نمونه با دستور create_sample_data
    ⏳ تست‌های خودکار
    ⏳ ارائه ۱۰ دقیقه‌ای

📚 منابع مفید

    مستندات رسمی Django
    مستندات Django REST Framework
    مستندات LangChain
    مخزن رسمی pgvector در GitHub
    فهرست مدل‌های رایگان OpenRouter
    مستندات Sentence Transformers

<div align="center">

ساخته‌شده برای دوره LLM Roshan — آخرین به‌روزرسانی: آگوست 2026
</div>
