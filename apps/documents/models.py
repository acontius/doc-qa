from uuid import uuid4

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from pgvector.django import HnswIndex, VectorField


def document_upload_path(instance: "Document", filename: str) -> str:
    """
    Generate a non-user-controlled storage path for uploaded DOCX files.
    """
    date_path = timezone.now().strftime("%Y/%m")
    return f"documents/{date_path}/{uuid4().hex}.docx"


class Document(models.Model):
    title = models.CharField(
        max_length=255,
    )

    file = models.FileField(
        upload_to=document_upload_path,
        max_length=255,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["docx"],
            ),
        ],
    )

    full_text = models.TextField(
        default="",
        blank=True,
    )

    chunk_count = models.PositiveIntegerField(
        default=0,
    )

    embedding_model = models.CharField(
        max_length=255,
        default="",
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    chunk_index = models.PositiveIntegerField()

    text = models.TextField()

    embedding = VectorField(
        dimensions=settings.EMBEDDING_DIMENSION,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["document_id", "chunk_index"]

        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"],
                name="unique_document_chunk_index",
            ),
        ]

        indexes = [
            HnswIndex(
                name="document_chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.document.title} - "
            f"chunk {self.chunk_index}"
        )


class Question(models.Model):
    """Persisted user question for Q&A history."""

    text = models.TextField()

    top_k = models.PositiveIntegerField(
        default=6,
    )

    document_ids = models.JSONField(
        null=True,
        blank=True,
        default=None,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        preview = self.text[:60]
        if len(self.text) > 60:
            preview += "…"
        return f"Q{self.pk}: {preview}"


class Answer(models.Model):
    """Persisted RAG answer snapshot for a Question."""

    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="answer",
    )

    text = models.TextField(
        blank=True,
        default="",
    )

    raw_llm_output = models.TextField(
        blank=True,
        default="",
    )

    confidence = models.CharField(
        max_length=16,
        blank=True,
        default="low",
    )

    sources_json = models.JSONField(
        default=list,
        blank=True,
    )

    model_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    latency_ms = models.PositiveIntegerField(
        default=0,
    )

    error = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        status = "error" if self.error else self.confidence
        return f"A for Q{self.question_id} ({status})"

