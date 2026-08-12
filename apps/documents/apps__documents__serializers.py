from pathlib import Path

from rest_framework import serializers

from .models import Document
from .services import (
    DocumentIngestionError,
    validate_docx_upload,
)


class DocumentWriteSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        required=False,
        allow_empty_file=False,
        write_only=True,
    )

    class Meta:
        model = Document
        fields = [
            "title",
            "file",
        ]

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
                "سؤال نمی‌تواند خالی باشد."
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

