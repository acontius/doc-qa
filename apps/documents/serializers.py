from pathlib import Path

from rest_framework import serializers

from .models import Document, Question
from .services import (
    DocumentIngestionError,
    validate_docx_upload,
)


class DocumentWriteSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        required=False,
        allow_empty_file=False,
        write_only=True,
        help_text="DOCX file only. Max size controlled by MAX_UPLOAD_SIZE_MB.",
    )

    class Meta:
        model = Document
        fields = [
            "title",
            "file",
        ]
        extra_kwargs = {
            "title": {
                "help_text": "Human-readable document title.",
            },
        }

    def validate_title(self, value: str) -> str:
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "عنوان سند نمی‌تواند خالی باشد."
            )

        return value

    def validate_file(self, value):
        try:
            validate_docx_upload(value)
        except DocumentIngestionError as exc:
            raise serializers.ValidationError(
                {
                    "code": exc.code,
                    "message": exc.message,
                }
            ) from exc

        return value

    def validate(self, attrs):
        if (
            self.instance is None
            and "file" not in attrs
        ):
            raise serializers.ValidationError(
                {
                    "file": (
                        "ارسال فایل DOCX برای ایجاد سند الزامی است."
                    )
                }
            )

        return attrs


class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "chunk_count",
            "embedding_model",
            "created_at",
            "updated_at",
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "file_name",
            "full_text",
            "chunk_count",
            "embedding_model",
            "created_at",
            "updated_at",
        ]

    def get_file_name(
        self,
        obj: Document,
    ) -> str | None:
        if not obj.file:
            return None

        return Path(
            obj.file.name
        ).name


class RetrievalRequestSerializer(serializers.Serializer):
    question = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )
    top_k = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
    )
    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
    )

    def validate_question(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "سوال نمی‌تواند خالی باشد."
            )
        return value


class RetrievedChunkSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()
    chunk_index = serializers.IntegerField()
    text = serializers.CharField()
    distance = serializers.FloatField()
    vector_score = serializers.FloatField()
    keyword_score = serializers.FloatField()
    final_score = serializers.FloatField()


class RetrievalResponseSerializer(serializers.Serializer):
    question = serializers.CharField()
    results = RetrievedChunkSerializer(many=True)


class QuestionRequestSerializer(serializers.Serializer):
    question = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        help_text="User question in Persian or English.",
    )
    top_k = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        help_text="Retrieval top_k (default: RETRIEVER_TOP_K).",
    )
    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
        help_text="Optional: only search these document IDs.",
    )

    def validate_question(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "سؤال نمی‌تواند خالی باشد."
            )
        return value


class AnswerSourceSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()
    chunk_index = serializers.IntegerField()
    excerpt = serializers.CharField()


class QuestionResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        required=False,
        help_text="Persisted Question history id.",
    )
    question = serializers.CharField()
    answer = serializers.CharField()
    sources = AnswerSourceSerializer(many=True)
    confidence = serializers.ChoiceField(
        choices=["low", "medium", "high"],
    )
    latency_ms = serializers.IntegerField()


class QuestionListSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source="text")
    answer_preview = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    latency_ms = serializers.SerializerMethodField()
    has_error = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "question",
            "answer_preview",
            "confidence",
            "model_name",
            "latency_ms",
            "has_error",
            "created_at",
        ]

    def get_answer_preview(self, obj) -> str:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return ""
        if answer.error and not answer.text:
            return ""
        preview = (answer.text or "")[:160]
        if len(answer.text or "") > 160:
            preview += "…"
        return preview

    def get_confidence(self, obj) -> str | None:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return None
        return answer.confidence

    def get_model_name(self, obj) -> str | None:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return None
        return answer.model_name or None

    def get_latency_ms(self, obj) -> int | None:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return None
        return answer.latency_ms

    def get_has_error(self, obj) -> bool:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return False
        return bool(answer.error)


class QuestionDetailSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source="text")
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "question",
            "top_k",
            "document_ids",
            "created_at",
            "answer",
        ]

    def get_answer(self, obj) -> dict | None:
        ans = getattr(obj, "answer", None)
        if ans is None:
            return None
        return {
            "text": ans.text,
            "raw_llm_output": ans.raw_llm_output,
            "confidence": ans.confidence,
            "sources": ans.sources_json or [],
            "model_name": ans.model_name,
            "latency_ms": ans.latency_ms,
            "error": ans.error or None,
        }


class APIErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(required=False)


class APIErrorSerializer(serializers.Serializer):
    """Standard API error envelope."""

    error = APIErrorBodySerializer()

