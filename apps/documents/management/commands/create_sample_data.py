"""
Create reproducible sample DOCX documents via the real ingestion pipeline.

Usage:
    python manage.py create_sample_data

Idempotent by title: existing sample titles are skipped (not duplicated).
Embeddings use the normal embedding service (real model in production;
mock in unit tests).
"""

from __future__ import annotations

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from docx import Document as DocxDocument

from apps.documents.models import Document
from apps.documents.services import create_document


# Deterministic titles used for skip-if-exists idempotency.
SAMPLE_DOCUMENTS: list[dict] = [
    {
        "title": "راهنمای منابع انسانی (نمونه)",
        "paragraphs": [
            "این سند راهنمای منابع انسانی شرکت نمونه است.",
            "مرخصی سالانه کارکنان ۲۶ روز کاری است.",
            "ساعات کاری رسمی از ساعت ۸ صبح تا ۱۶ بعدازظهر است.",
            "کار از راه دور حداکثر دو روز در هفته با تأیید مدیر مجاز است.",
            "مرخصی استعلاجی با ارائه گواهی پزشکی قابل استفاده است.",
            "اضافه‌کاری فقط با تأیید قبلی مدیر بخش محاسبه می‌شود.",
        ],
    },
    {
        "title": "راهنمای فنی سیستم (نمونه)",
        "paragraphs": [
            "این سند معماری فنی سامانه پرسش و پاسخ اسنادی را توضیح می‌دهد.",
            "پایگاه داده اصلی سیستم PostgreSQL است و از افزونه pgvector استفاده می‌کند.",
            "برای بردارسازی متن از مدل paraphrase-multilingual-MiniLM-L12-v2 استفاده می‌شود.",
            "ابعاد بردارهای ذخیره‌شده ۳۸۴ است.",
            "بازیابی اطلاعات به صورت ترکیبی از امتیاز برداری و امتیاز کلیدواژه انجام می‌شود.",
            "پاسخ‌ها فقط بر اساس زمینه بازیابی‌شده از اسناد تولید می‌شوند.",
        ],
    },
    {
        "title": "راهنمای شرکت (نمونه)",
        "paragraphs": [
            "شرکت نمونه یک سازمان نرم‌افزاری فرضی برای آزمایش سامانه است.",
            "دپارتمان‌های اصلی شامل مهندسی، منابع انسانی و پشتیبانی هستند.",
            "نشانی دفتر مرکزی: تهران، خیابان نمونه، پلاک ۱۲۳ است.",
            "ایمیل پشتیبانی فرضی: support@example-company.local است.",
            "سیاست پاسخگویی به تیکت‌ها حداکثر ۴۸ ساعت کاری است.",
        ],
    },
]


def build_docx_bytes(paragraphs: list[str]) -> bytes:
    document = DocxDocument()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


class Command(BaseCommand):
    help = (
        "Create sample Persian DOCX documents through the real "
        "document ingestion pipeline (validate → extract → chunk → embed)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Re-create sample documents even if titles already exist "
                "(deletes existing rows with the same sample titles first)."
            ),
        )

    def handle(self, *args, **options):
        force = options.get("force", False)
        self.stdout.write("Creating sample documents...")

        created = 0
        skipped = 0

        for spec in SAMPLE_DOCUMENTS:
            title = spec["title"]
            existing = Document.objects.filter(title=title).first()

            if existing is not None and not force:
                self.stdout.write(
                    self.style.WARNING(f"Skip existing: {title}")
                )
                skipped += 1
                continue

            if existing is not None and force:
                from apps.documents.services import delete_document

                delete_document(existing)
                self.stdout.write(
                    self.style.WARNING(f"Removed existing: {title}")
                )

            content = build_docx_bytes(spec["paragraphs"])
            upload = SimpleUploadedFile(
                name="sample.docx",
                content=content,
                content_type=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            )

            document = create_document(
                title=title,
                uploaded_file=upload,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created: {document.title} "
                    f"(id={document.pk}, chunks={document.chunk_count})"
                )
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sample data ready. created={created}, skipped={skipped}"
            )
        )
